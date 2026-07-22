"""Missions — durable goals on the Hermespace grid."""

from __future__ import annotations

import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from hermespace.grid.secure_store import atomic_write_json, grid_root, read_json, safe_name


def _utcnow() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


@dataclass
class Mission:
    id: str
    title: str
    status: str = "open"  # open | active | blocked | done | cancelled
    priority: int = 50
    notes: str = ""
    progress: list[str] = field(default_factory=list)
    created: str = field(default_factory=_utcnow)
    updated: str = field(default_factory=_utcnow)
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "Mission":
        return cls(
            id=str(d.get("id") or uuid.uuid4().hex[:12]),
            title=str(d.get("title") or ""),
            status=str(d.get("status") or "open"),
            priority=int(d.get("priority") or 50),
            notes=str(d.get("notes") or ""),
            progress=list(d.get("progress") or []),
            created=str(d.get("created") or _utcnow()),
            updated=str(d.get("updated") or _utcnow()),
            tags=list(d.get("tags") or []),
        )


def _path(agent_id: str = "default") -> Path:
    return grid_root() / "missions" / f"{safe_name(agent_id)}.json"


def list_missions(agent_id: str = "default") -> list[Mission]:
    raw = read_json(_path(agent_id), {"missions": []})
    items = raw.get("missions") if isinstance(raw, dict) else []
    out = [Mission.from_dict(x) for x in (items or []) if isinstance(x, dict)]
    out.sort(key=lambda m: (-m.priority, m.updated), reverse=False)
    out.sort(key=lambda m: m.priority, reverse=True)
    return out


def save_all(agent_id: str, missions: list[Mission]) -> None:
    atomic_write_json(
        _path(agent_id),
        {"missions": [m.to_dict() for m in missions], "updated": _utcnow()},
    )


def add_mission(
    title: str,
    *,
    agent_id: str = "default",
    priority: int = 50,
    notes: str = "",
    tags: list[str] | None = None,
) -> Mission:
    title = (title or "").strip()
    if not title:
        raise ValueError("title required")
    ms = list_missions(agent_id)
    m = Mission(
        id=uuid.uuid4().hex[:12],
        title=title[:200],
        priority=int(priority),
        notes=(notes or "")[:2000],
        tags=list(tags or []),
    )
    ms.append(m)
    save_all(agent_id, ms)
    return m


def update_mission(
    mission_id: str,
    *,
    agent_id: str = "default",
    status: str | None = None,
    note: str | None = None,
    priority: int | None = None,
) -> Mission | None:
    ms = list_missions(agent_id)
    for m in ms:
        if m.id == mission_id or m.title == mission_id:
            if status:
                m.status = status
            if note:
                m.progress.append(f"{_utcnow()} {note[:300]}")
                m.progress = m.progress[-40:]
            if priority is not None:
                m.priority = int(priority)
            m.updated = _utcnow()
            save_all(agent_id, ms)
            return m
    return None


def active_missions(agent_id: str = "default", limit: int = 5) -> list[Mission]:
    openish = [m for m in list_missions(agent_id) if m.status in ("open", "active", "blocked")]
    return openish[:limit]
