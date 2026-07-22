"""Self-talk — agent internal dialogue channel (meta-brain loop).

Dual-channel discipline:
- selftalk log is *internal* (model / study)
- never auto-dumps to user chat; optional extract for closeout
"""

from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from hermespace.grid.secure_store import grid_root, safe_name


def _utcnow() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


@dataclass
class Utterance:
    id: str
    role: str  # self | critic | planner | memory
    text: str
    created: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _path(agent_id: str) -> Path:
    p = grid_root() / "selftalk" / f"{safe_name(agent_id)}.jsonl"
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def say(
    text: str,
    *,
    agent_id: str = "default",
    role: str = "self",
) -> Utterance:
    text = (text or "").strip()
    if not text:
        raise ValueError("empty selftalk")
    if len(text) > 4000:
        text = text[:4000]
    u = Utterance(
        id=uuid.uuid4().hex[:10],
        role=(role or "self")[:32],
        text=text,
        created=_utcnow(),
    )
    with _path(agent_id).open("a", encoding="utf-8") as f:
        f.write(json.dumps(u.to_dict(), ensure_ascii=False) + "\n")
    return u


def dialogue(
    turns: list[tuple[str, str]],
    *,
    agent_id: str = "default",
) -> list[Utterance]:
    """Multi-role internal exchange: [(role, text), ...]."""
    out = []
    for role, text in turns:
        out.append(say(text, agent_id=agent_id, role=role))
    return out


def recent(agent_id: str = "default", limit: int = 20) -> list[dict[str, Any]]:
    path = _path(agent_id)
    if not path.is_file():
        return []
    lines = path.read_text(encoding="utf-8").strip().splitlines()
    out = []
    for line in lines[-limit:]:
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return out


def as_model_context(agent_id: str = "default", limit: int = 12) -> str:
    rows = recent(agent_id, limit=limit)
    if not rows:
        return ""
    lines = ["### Hermespace self-talk (internal — not user channel)"]
    for r in rows:
        lines.append(f"- **{r.get('role')}**: {r.get('text')}")
    return "\n".join(lines)
