"""Conversational boundary regulation — clear user↔agent contract in chat."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from hermespace.grid import access
from hermespace.grid.boundary import (
    grant_permit,
    load_policy,
    policy_markdown,
    revoke_permits,
)


@dataclass
class RegulateResult:
    handled: bool
    action: str
    message: str  # user-facing short reply
    data: dict[str, Any] | None = None


_APPROVE_ID = re.compile(
    r"\b(?:approve|allow|grant)\s+(?:request\s+)?([a-f0-9]{6,12})\b",
    re.I,
)
_DENY_ID = re.compile(
    r"\b(?:deny|reject|refuse)\s+(?:request\s+)?([a-f0-9]{6,12})\b",
    re.I,
)
# allow /path for 2 hours
_ALLOW_PATH = re.compile(
    r"\b(?:allow|grant|permit)\s+(?:access\s+to\s+|write\s+to\s+|reads?\s+on\s+)?"
    r"[`'\"]?([~/][^\s,;'\"]+)[`'\"]?"
    r"(?:\s+for\s+(\d+(?:\.\d+)?)\s*h(?:ours?)?)?",
    re.I,
)
_REQUEST_PATH = re.compile(
    r"\b(?:request(?:ing)?|need)\s+(?:access\s+to\s+|write\s+to\s+|to\s+write\s+(?:in|to)\s+)"
    r"[`'\"]?([~/][^\s,;'\"]+)[`'\"]?"
    r"(?:\s+for\s+(\d+(?:\.\d+)?)\s*h(?:ours?)?)?"
    r"(?:\s*[:\-—]\s*(.+))?",
    re.I,
)
_SHOW = re.compile(
    r"\b(?:show|what(?:'s| is)|explain)\s+(?:the\s+)?(?:boundary|pocket|hermespace\s+rules|access|permits)\b",
    re.I,
)
_REVOKE = re.compile(r"\brevoke\s+(?:all\s+)?permits?\b", re.I)
_LIST_PENDING = re.compile(r"\b(?:list|show)\s+(?:pending\s+)?(?:access\s+)?requests?\b", re.I)


def regulate(
    user_message: str,
    *,
    agent_id: str = "default",
) -> RegulateResult:
    """Parse user/agent chat for boundary regulation. Returns handled=False if N/A."""
    msg = (user_message or "").strip()
    if not msg:
        return RegulateResult(False, "none", "")

    if _SHOW.search(msg):
        pol = load_policy()
        pending = access.list_requests(agent_id=agent_id, status="pending")
        text = (
            f"Pocket root: `{pol.pocket_root}`. External writes: **{pol.project_write_default}**. "
            f"Active permits: {len(pol.permits)}. Pending requests: {len(pending)}. "
            "I stay inside Hermespace unless you allow a path. "
            "Say `allow ~/project for 2h` or `approve request <id>`."
        )
        return RegulateResult(True, "show_boundary", text, {"policy": pol.to_dict()})

    if _REVOKE.search(msg):
        n = revoke_permits()
        return RegulateResult(True, "revoke", f"Revoked {n} permit(s). Back to pocket-only writes.")

    if _LIST_PENDING.search(msg):
        pending = access.list_requests(agent_id=agent_id, status="pending")
        if not pending:
            return RegulateResult(True, "list", "No pending access requests.")
        lines = [f"`{r.id}` → `{r.path}` ({r.mode}, {r.hours}h) — {r.reason}" for r in pending]
        return RegulateResult(True, "list", "Pending:\n- " + "\n- ".join(lines))

    m = _APPROVE_ID.search(msg)
    if m:
        out = access.approve_request(m.group(1), resolver="chat")
        if out.get("ok"):
            p = out["request"]["path"]
            return RegulateResult(
                True,
                "approve",
                f"Approved. Agent may write under `{p}` for the requested window.",
                out,
            )
        return RegulateResult(True, "approve_fail", f"Could not approve: {out.get('reason')}", out)

    m = _DENY_ID.search(msg)
    if m:
        out = access.deny_request(m.group(1), resolver="chat")
        if out.get("ok"):
            return RegulateResult(True, "deny", f"Denied request `{m.group(1)}`. Stays in pocket.", out)
        return RegulateResult(True, "deny_fail", f"Could not deny: {out.get('reason')}", out)

    m = _ALLOW_PATH.search(msg)
    if m:
        path = m.group(1)
        hours = float(m.group(2) or 1)
        try:
            permit = grant_permit(path, hours=hours, mode="write", note="chat allow")
            return RegulateResult(
                True,
                "allow_path",
                f"Allowed writes under `{Path(path).expanduser()}` for {hours}h. "
                "Say `revoke permits` anytime.",
                {"permit": permit},
            )
        except Exception as e:  # noqa: BLE001
            return RegulateResult(True, "allow_fail", f"Allow failed: {e}")

    m = _REQUEST_PATH.search(msg)
    if m:
        path = m.group(1)
        hours = float(m.group(2) or 1)
        reason = (m.group(3) or "conversational request").strip()
        req = access.request_access(
            path, agent_id=agent_id, hours=hours, reason=reason, mode="write"
        )
        return RegulateResult(
            True,
            "request",
            f"Access requested `{req.id}` for `{req.path}` ({req.hours}h). "
            f"Approve with: approve request {req.id} — or deny request {req.id}.",
            {"request": req.to_dict()},
        )

    return RegulateResult(False, "none", "")


def agent_should_request_not_reach(path: str, reason: str = "") -> str:
    """Helper copy for agents when a tool path is outside pocket."""
    return (
        f"Path `{path}` is outside the Hermespace pocket. "
        f"I will not write there without permission. "
        f"Requesting access" + (f" — {reason}" if reason else "") + ". "
        "You can say `allow <path> for 2h` or wait for Desktop approval."
    )
