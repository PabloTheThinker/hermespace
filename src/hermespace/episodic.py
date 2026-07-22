"""Episodic ring buffer for Hermespace events — strip inspired by Conductor EpisodicStore.

Capped newest-retained log so the workspace compounds without unbounded growth.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from hermespace.paths import state_dir as default_state_dir

EPISODIC_MAX = 500


def _utcnow() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


@dataclass
class Episode:
    entry_id: str
    content: str
    outcome: str = "info"
    tags: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=_utcnow)


class EpisodicLog:
    """File-backed episodic log (no Conductor SessionStore dependency)."""

    def __init__(self, path: Path | None = None) -> None:
        self.path = path or (default_state_dir() / "episodes.jsonl")
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def write(
        self,
        content: str,
        *,
        outcome: str = "info",
        tags: list[str] | None = None,
    ) -> Episode:
        ep = Episode(
            entry_id=str(uuid.uuid4()),
            content=content.strip(),
            outcome=outcome or "info",
            tags=list(tags or []),
        )
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(ep), ensure_ascii=False) + "\n")
        self._trim()
        return ep

    def _trim(self) -> None:
        if not self.path.exists():
            return
        lines = self.path.read_text(encoding="utf-8").splitlines()
        if len(lines) <= EPISODIC_MAX:
            return
        keep = lines[-EPISODIC_MAX:]
        self.path.write_text("\n".join(keep) + "\n", encoding="utf-8")

    def recent(self, limit: int = 8) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        lines = [ln for ln in self.path.read_text(encoding="utf-8").splitlines() if ln.strip()]
        out: list[dict[str, Any]] = []
        for ln in lines[-limit:]:
            try:
                out.append(json.loads(ln))
            except json.JSONDecodeError:
                continue
        return list(reversed(out))
