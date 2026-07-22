"""Agent I/O contract — how any Hermes agent enters and leaves Hermespace.

INPUT  = what the agent (or user) provides to start a workspace turn
OUTPUT = what Hermespace returns so the agent can reply to the user

Nothing here is operator-specific. Paths come from HERMESPACE_HOME.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


def _utcnow() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


@dataclass
class HermespaceInput:
    """Start-of-turn payload for any Hermes agent.

    Minimum useful fields: ``message`` + ``goal`` (goal may default from message).
    """

    message: str
    goal: str = ""
    decision: str = ""
    plan: list[str] = field(default_factory=list)
    say: str = ""
    concepts: list[str] = field(default_factory=list)
    choices: list[str] = field(default_factory=list)
    session_id: str = ""
    agent_id: str = ""
    force: bool = False
    seal: bool = False
    seal_note: str = ""
    tags: list[str] = field(default_factory=list)
    meta: dict[str, Any] = field(default_factory=dict)

    def normalized(self) -> HermespaceInput:
        msg = (self.message or "").strip()
        goal = (self.goal or "").strip() or msg[:200]
        return HermespaceInput(
            message=msg,
            goal=goal,
            decision=(self.decision or "").strip(),
            plan=[p.strip() for p in self.plan if p and str(p).strip()],
            say=(self.say or "").strip(),
            concepts=list(self.concepts or []),
            choices=list(self.choices or []),
            session_id=(self.session_id or "").strip() or "default",
            agent_id=(self.agent_id or "").strip() or "hermes-agent",
            force=bool(self.force),
            seal=bool(self.seal),
            seal_note=(self.seal_note or "").strip(),
            tags=list(self.tags or []),
            meta=dict(self.meta or {}),
        )

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> HermespaceInput:
        plan = data.get("plan") or []
        if isinstance(plan, str):
            plan = [plan]
        concepts = data.get("concepts") or []
        if isinstance(concepts, str):
            concepts = [concepts]
        choices = data.get("choices") or []
        if isinstance(choices, str):
            choices = [choices]
        return cls(
            message=str(data.get("message") or data.get("user_message") or ""),
            goal=str(data.get("goal") or ""),
            decision=str(data.get("decision") or ""),
            plan=list(plan),
            say=str(data.get("say") or data.get("report") or ""),
            concepts=list(concepts),
            choices=list(choices),
            session_id=str(data.get("session_id") or ""),
            agent_id=str(data.get("agent_id") or ""),
            force=bool(data.get("force") or False),
            seal=bool(data.get("seal") or False),
            seal_note=str(data.get("seal_note") or ""),
            tags=list(data.get("tags") or []),
            meta=dict(data.get("meta") or {}),
        ).normalized()

    def to_json(self) -> str:
        return json.dumps(asdict(self.normalized()), indent=2)


@dataclass
class HermespaceOutput:
    """End-of-turn payload — enough for the agent to answer the user."""

    turn_id: str
    skipped: bool
    reason: str
    # Primary user-facing speech
    report: str
    # Full inject block for model context (pre_llm / system-adjacent)
    context: str
    decision: str
    goal: str
    plan: list[str] = field(default_factory=list)
    ready: bool = False
    executive: str = ""
    load_level: str = ""
    streams: dict[str, int] = field(default_factory=dict)
    memory_id: str = ""
    memory_path: str = ""
    desk_path: str = ""
    session_id: str = ""
    created_at: str = field(default_factory=_utcnow)
    meta: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)

    def agent_reply_hint(self) -> str:
        """One block an agent can treat as 'what to say next'."""
        if self.skipped:
            return ""
        return (self.report or "").strip()

    # Back-compat aliases
    @property
    def say(self) -> str:
        return self.report

    @property
    def inject(self) -> str:
        return self.context

    def summary(self) -> str:
        if self.skipped:
            return f"skip:{self.reason}"
        return (
            f"ready={self.ready} load={self.load_level} exec={self.executive} "
            f"report={self.report[:80]!r} mem={self.memory_id[:8]}"
        )


def new_turn_id() -> str:
    return str(uuid.uuid4())
