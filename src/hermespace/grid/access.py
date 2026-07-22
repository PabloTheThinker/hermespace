"""Access requests — agent asks to leave the pocket; user grants in chat or UI."""

from __future__ import annotations

import time
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from hermespace.grid.boundary import grant_permit, load_policy
from hermespace.grid.secure_store import atomic_write_json, grid_root, read_json, safe_name


def _utcnow() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


@dataclass
class AccessRequest:
    id: str
    path: str
    mode: str = "write"  # write | write_delete | read
    hours: float = 1.0
    reason: str = ""
    agent_id: str = "default"
    status: str = "pending"  # pending | approved | denied | expired
    created: str = field(default_factory=_utcnow)
    resolved_at: str = ""
    resolver: str = ""  # user | cli | desktop | auto
    note: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "AccessRequest":
        return cls(
            id=str(d.get("id") or uuid.uuid4().hex[:10]),
            path=str(d.get("path") or ""),
            mode=str(d.get("mode") or "write"),
            hours=float(d.get("hours") or 1.0),
            reason=str(d.get("reason") or "")[:500],
            agent_id=str(d.get("agent_id") or "default"),
            status=str(d.get("status") or "pending"),
            created=str(d.get("created") or _utcnow()),
            resolved_at=str(d.get("resolved_at") or ""),
            resolver=str(d.get("resolver") or ""),
            note=str(d.get("note") or "")[:300],
        )


def _path() -> Path:
    return grid_root() / "access_requests.json"


def _load_all() -> list[AccessRequest]:
    raw = read_json(_path(), {"requests": []})
    items = [AccessRequest.from_dict(x) for x in (raw.get("requests") or []) if isinstance(x, dict)]
    return items[-200:]


def _save_all(items: list[AccessRequest]) -> None:
    atomic_write_json(_path(), {"requests": [r.to_dict() for r in items], "updated": _utcnow()})


def request_access(
    path: str,
    *,
    agent_id: str = "default",
    mode: str = "write",
    hours: float = 1.0,
    reason: str = "",
) -> AccessRequest:
    """Agent-side: open a pending request (does not grant)."""
    path = str(Path(path).expanduser())
    if hours <= 0 or hours > 72:
        hours = 1.0
    if mode not in ("write", "write_delete", "read"):
        mode = "write"
    items = _load_all()
    # dedupe pending same path
    for r in items:
        if r.status == "pending" and r.path == path and r.agent_id == safe_name(agent_id):
            r.reason = reason or r.reason
            r.hours = hours
            r.mode = mode
            _save_all(items)
            return r
    req = AccessRequest(
        id=uuid.uuid4().hex[:10],
        path=path,
        mode=mode,
        hours=float(hours),
        reason=(reason or "agent needs path for task")[:500],
        agent_id=safe_name(agent_id),
    )
    items.append(req)
    _save_all(items)
    return req


def list_requests(
    *,
    agent_id: str | None = None,
    status: str | None = "pending",
) -> list[AccessRequest]:
    items = _load_all()
    if agent_id:
        aid = safe_name(agent_id)
        items = [r for r in items if r.agent_id == aid]
    if status:
        items = [r for r in items if r.status == status]
    return items


def get_request(req_id: str) -> AccessRequest | None:
    for r in _load_all():
        if r.id == req_id:
            return r
    return None


def approve_request(
    req_id: str,
    *,
    resolver: str = "user",
    note: str = "",
    hours: float | None = None,
) -> dict[str, Any]:
    items = _load_all()
    req = next((r for r in items if r.id == req_id), None)
    if not req:
        return {"ok": False, "reason": "not_found"}
    if req.status != "pending":
        return {"ok": False, "reason": f"status={req.status}"}
    h = float(hours if hours is not None else req.hours)
    try:
        permit = grant_permit(req.path, hours=h, mode=req.mode, note=req.reason or note)
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "reason": str(e)}
    req.status = "approved"
    req.resolved_at = _utcnow()
    req.resolver = resolver
    req.note = note
    req.hours = h
    _save_all(items)
    return {"ok": True, "request": req.to_dict(), "permit": permit}


def deny_request(req_id: str, *, resolver: str = "user", note: str = "") -> dict[str, Any]:
    items = _load_all()
    req = next((r for r in items if r.id == req_id), None)
    if not req:
        return {"ok": False, "reason": "not_found"}
    if req.status != "pending":
        return {"ok": False, "reason": f"status={req.status}"}
    req.status = "denied"
    req.resolved_at = _utcnow()
    req.resolver = resolver
    req.note = note
    _save_all(items)
    return {"ok": True, "request": req.to_dict()}


def pending_inject_block(agent_id: str = "default") -> str:
    """Text for model+user: pending access + how to regulate in conversation."""
    pending = list_requests(agent_id=agent_id, status="pending")
    pol = load_policy()
    lines = [
        "### Pocket boundary (talkable)",
        "- Hermespace **cannot** write outside `$HERMESPACE_HOME` without your OK.",
        "- Agent may **request** access; you approve/deny in chat or Desktop viewport.",
        f"- Policy: external writes=`{pol.project_write_default}` · permits={len(pol.permits)} · allowlist={len(pol.allowlist)}",
        "- Say: `allow <path> for 2h` · `approve request <id>` · `deny request <id>` · `revoke permits` · `show boundary`",
        "- Agent API: `request_access(path, reason=...)` — never invents silent project writes.",
    ]
    if pending:
        lines.append("**Pending access requests:**")
        for r in pending[-8:]:
            lines.append(
                f"- `{r.id}` → `{r.path}` mode={r.mode} {r.hours}h — {r.reason[:100]}"
            )
        lines.append("_User: approve/deny by id or path. Agent: wait until approved._")
    else:
        lines.append("_No pending access requests._")
    return "\n".join(lines)
