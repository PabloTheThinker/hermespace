"""Hermes v0.20 plugin runtime state and lifecycle telemetry.

The Hermes hook host is multi-surface and potentially concurrent (CLI,
gateways, A2A, subagents).  This registry keeps bounded, session-scoped
operational facts and persists snapshots atomically for doctor/status commands.
It deliberately stores lengths and names rather than prompt or tool payloads.
"""

from __future__ import annotations

import hashlib
import json
import threading
import time
from collections import OrderedDict
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any

from hermespace.atomic import atomic_write_text
from hermespace.paths import state_dir

MAX_SESSIONS = 128
MAX_RECENT_TOOLS = 24


def _utcnow() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _session_key(session_id: str | None) -> str:
    raw = str(session_id or "no-session")
    return hashlib.sha256(raw.encode("utf-8", errors="replace")).hexdigest()[:20]


@dataclass
class SessionRuntime:
    session_key: str
    agent_id: str
    model: str = ""
    platform: str = ""
    started_at: str = field(default_factory=_utcnow)
    updated_at: str = field(default_factory=_utcnow)
    pre_llm_calls: int = 0
    completed_turns: int = 0
    interrupted_turns: int = 0
    failed_turns: int = 0
    tool_calls: int = 0
    subagent_starts: int = 0
    subagent_stops: int = 0
    last_user_chars: int = 0
    last_response_chars: int = 0
    last_event: str = "session_start"
    finalized: bool = False
    shared_hub: bool = False
    recent_tools: list[str] = field(default_factory=list)


class RuntimeRegistry:
    """Thread-safe, bounded runtime registry."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._sessions: OrderedDict[str, SessionRuntime] = OrderedDict()
        self._start_context: dict[str, str] = {}

    def _get(
        self,
        session_id: str | None,
        *,
        agent_id: str = "hermes-agent",
        model: str = "",
        platform: str = "",
    ) -> SessionRuntime:
        key = _session_key(session_id)
        item = self._sessions.get(key)
        if item is None:
            item = SessionRuntime(
                session_key=key,
                agent_id=agent_id or "hermes-agent",
                model=model or "",
                platform=platform or "",
            )
            self._sessions[key] = item
        else:
            if model:
                item.model = model
            if platform:
                item.platform = platform
            self._sessions.move_to_end(key)
        while len(self._sessions) > MAX_SESSIONS:
            old_key, _ = self._sessions.popitem(last=False)
            self._start_context.pop(old_key, None)
        return item

    def _save(self, item: SessionRuntime) -> None:
        item.updated_at = _utcnow()
        path = state_dir() / "runtime" / f"{item.session_key}.json"
        atomic_write_text(path, json.dumps(asdict(item), indent=2), mode=0o600)

    def start(
        self,
        session_id: str | None,
        *,
        agent_id: str,
        model: str = "",
        platform: str = "",
        context: str = "",
    ) -> dict[str, Any]:
        with self._lock:
            item = self._get(
                session_id,
                agent_id=agent_id,
                model=model,
                platform=platform,
            )
            item.last_event = "session_start"
            item.finalized = False
            if context:
                self._start_context[item.session_key] = context
            self._save(item)
            return asdict(item)

    def take_start_context(self, session_id: str | None) -> str:
        with self._lock:
            return self._start_context.pop(_session_key(session_id), "")

    def stage_start_context(self, session_id: str | None, context: str) -> None:
        """Restore first-turn context when a trivial turn skipped injection."""

        if not context:
            return
        with self._lock:
            self._start_context[_session_key(session_id)] = context

    def pre_llm(
        self,
        session_id: str | None,
        *,
        agent_id: str,
        user_chars: int,
        model: str = "",
        platform: str = "",
    ) -> None:
        with self._lock:
            item = self._get(
                session_id,
                agent_id=agent_id,
                model=model,
                platform=platform,
            )
            item.pre_llm_calls += 1
            item.last_user_chars = max(0, int(user_chars))
            item.last_event = "pre_llm_call"
            self._save(item)

    def post_llm(
        self,
        session_id: str | None,
        *,
        agent_id: str,
        response_chars: int,
        model: str = "",
        platform: str = "",
    ) -> None:
        with self._lock:
            item = self._get(
                session_id,
                agent_id=agent_id,
                model=model,
                platform=platform,
            )
            item.completed_turns += 1
            item.last_response_chars = max(0, int(response_chars))
            item.last_event = "post_llm_call"
            self._save(item)

    def tool(self, session_id: str | None, *, agent_id: str, name: str) -> None:
        with self._lock:
            item = self._get(session_id, agent_id=agent_id)
            item.tool_calls += 1
            clean = (name or "unknown")[:80]
            item.recent_tools = (item.recent_tools + [clean])[-MAX_RECENT_TOOLS:]
            item.last_event = "post_tool_call"
            # Keep the tool loop cheap; checkpoints and turn-finalization flush.
            if item.tool_calls == 1 or item.tool_calls % 10 == 0:
                self._save(item)

    def mark_shared_hub(self, session_id: str | None, *, agent_id: str) -> None:
        """Kanban / subagent workers share the one desk — no full inject copy."""
        with self._lock:
            item = self._get(session_id, agent_id=agent_id)
            item.shared_hub = True
            item.last_event = "shared_hub"
            self._save(item)

    def subagent(self, session_id: str | None, *, agent_id: str, started: bool) -> None:
        with self._lock:
            item = self._get(session_id, agent_id=agent_id)
            if started:
                item.subagent_starts += 1
                item.shared_hub = True
                item.last_event = "subagent_start"
            else:
                item.subagent_stops += 1
                item.last_event = "subagent_stop"
            self._save(item)

    def end_turn(
        self,
        session_id: str | None,
        *,
        agent_id: str,
        completed: bool,
        interrupted: bool,
    ) -> None:
        with self._lock:
            item = self._get(session_id, agent_id=agent_id)
            if interrupted:
                item.interrupted_turns += 1
            elif not completed:
                item.failed_turns += 1
            item.last_event = "turn_end"
            self._save(item)

    def finalize(self, session_id: str | None, *, agent_id: str) -> bool:
        """Mark finalized and return True only for the first finalizer."""

        with self._lock:
            item = self._get(session_id, agent_id=agent_id)
            if item.finalized:
                return False
            item.finalized = True
            item.last_event = "session_finalize"
            self._start_context.pop(item.session_key, None)
            self._save(item)
            return True

    def status(self, session_id: str | None = None) -> dict[str, Any]:
        with self._lock:
            if session_id is not None:
                item = self._sessions.get(_session_key(session_id))
                return asdict(item) if item else {}
            active = [asdict(v) for v in self._sessions.values() if not v.finalized]
            return {
                "active_sessions": len(active),
                "tracked_sessions": len(self._sessions),
                "sessions": active[-10:],
                "monotonic_ms": int(time.monotonic() * 1000),
            }


runtime = RuntimeRegistry()
