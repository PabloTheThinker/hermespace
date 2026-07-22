"""Scars — typed failure memory on the grid (inspired by heal/scar *role*, not a port)."""

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
class Scar:
    id: str
    kind: str
    summary: str
    status: str = "open"  # open | sealed | ignored
    advance: str = ""
    created: str = field(default_factory=_utcnow)
    sealed_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "Scar":
        return cls(
            id=str(d.get("id") or uuid.uuid4().hex[:10]),
            kind=str(d.get("kind") or "tool_error")[:64],
            summary=str(d.get("summary") or "")[:500],
            status=str(d.get("status") or "open"),
            advance=str(d.get("advance") or "")[:500],
            created=str(d.get("created") or _utcnow()),
            sealed_at=str(d.get("sealed_at") or ""),
        )


def _path(agent_id: str = "default") -> Path:
    return grid_root() / "scars" / f"{safe_name(agent_id)}.json"


def list_scars(agent_id: str = "default", *, open_only: bool = False) -> list[Scar]:
    raw = read_json(_path(agent_id), {"scars": []})
    items = [Scar.from_dict(x) for x in (raw.get("scars") or []) if isinstance(x, dict)]
    if open_only:
        items = [s for s in items if s.status == "open"]
    return items[-100:]


def open_scar(
    kind: str,
    summary: str,
    *,
    agent_id: str = "default",
    advance: str = "",
) -> Scar:
    scars = list_scars(agent_id)
    s = Scar(
        id=uuid.uuid4().hex[:10],
        kind=(kind or "error")[:64],
        summary=(summary or "")[:500],
        advance=(advance or "change approach; do not thrash")[:500],
    )
    scars.append(s)
    atomic_write_json(_path(agent_id), {"scars": [x.to_dict() for x in scars[-100:]]})
    return s


def seal_scar(scar_id: str, *, agent_id: str = "default") -> Scar | None:
    scars = list_scars(agent_id)
    for s in scars:
        if s.id == scar_id:
            s.status = "sealed"
            s.sealed_at = _utcnow()
            atomic_write_json(_path(agent_id), {"scars": [x.to_dict() for x in scars]})
            return s
    return None
