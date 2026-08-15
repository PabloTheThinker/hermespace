"""Progressive disclosure for the one user-message inject.

Hard budgets — do not eat the turn:

  mid default ≤ 2.8k
  high/protect ≤ 900
  hard cap < 9k (8500 safety net)
  FOA ≤ 4 · silent chain ≤ 8 · Insight card ≤ 400

Spoken Report stays short (line 1 = next action). Dense context is not
also dumped into chat. Harvest never rides this path.
"""

from __future__ import annotations

import re
from typing import Any, Iterable

MID_INJECT_CAP = 2800
HIGH_INJECT_CAP = 900
INJECT_HARD_CAP = 8500  # strictly < 9k
INSIGHT_CARD_CHARS = 400
SELF_TRACE_INJECT_CHARS = 280
FOA_CAP = 4
SILENT_CHAIN_CAP = 8

_FLUENT_ACK_RE = re.compile(
    r"^\s*(ok|okay|k|thanks|thank you|ty|cool|nice|good|perfect|boom|"
    r"got it|gotcha|sure|np|lgtm|cheers|heartbeat_ok|👍|❤️|yes|yep|nope|no)"
    r"\s*[.!]*\s*$",
    re.I,
)

# Never appear on the inject path (operator / harvest / lattice / claims).
_FORBIDDEN_LINE = re.compile(
    r"J-Lens readout|What Hermes has on its mind|lens_markdown|"
    r"true self-conscious|phenomenal consciousness|"
    r"### Workbench|### Hermespace runtime|"
    r"dream_harvest|harvest items|recall brief|perceive\(\)\[.card.\]|"
    r"### Lattice|insight_lattice",
    re.I,
)


def is_fluent_ack(message: str) -> bool:
    """Short acknowledgement — inject nothing this turn."""
    msg = (message or "").strip()
    return bool(msg) and len(msg) < 48 and bool(_FLUENT_ACK_RE.match(msg))


def inject_budget(load_level: str | None) -> int:
    level = str(load_level or "mid").strip().lower()
    if level in {"high", "protect", "protected"}:
        return HIGH_INJECT_CAP
    return MID_INJECT_CAP


def strip_needed(
    *,
    message: str = "",
    load_level: str = "mid",
    is_first_turn: bool = False,
    has_bind: bool = False,
    missing_organ: bool = False,
) -> bool:
    """False → inject nothing (fluent ack, high load, missing organ)."""
    if is_fluent_ack(message):
        return False
    if missing_organ and not has_bind and not is_first_turn:
        return False
    level = str(load_level or "mid").strip().lower()
    if level in {"high", "protect", "protected"}:
        return bool(has_bind or is_first_turn)
    return True


def is_shared_hub_child(session_id: str = "", kwargs: dict[str, Any] | None = None) -> bool:
    """Subagent / kanban worker — share the one desk; do not inject a full copy."""
    kw = kwargs or {}
    for key in (
        "parent_session_id",
        "parent_task_id",
        "subagent_id",
        "is_subagent",
    ):
        if kw.get(key):
            return True
    role = str(kw.get("agent_role") or kw.get("role") or "").strip().lower()
    if role in {"subagent", "kanban", "worker"}:
        return True
    try:
        from hermespace.hermes_runtime import runtime

        st = runtime.status(session_id or "")
        return bool(st.get("shared_hub"))
    except Exception:
        return False


def dual_decode_line() -> str:
    """Tiny protocol — spoken Report stays short; dense context stays here."""
    return (
        "### Access Workspace\n"
        "- Report line 1 = next action. Dense context stays here — do not dump into chat."
    )


def assemble_inject(parts: Iterable[str], *, budget: int) -> str:
    """Join strips in order until the budget is spent. One user-message inject."""
    cap = max(80, min(int(budget), INJECT_HARD_CAP))
    out: list[str] = []
    used = 0
    for raw in parts:
        piece = sanitize_inject(str(raw or "")).strip()
        if not piece:
            continue
        sep = 2 if out else 0
        if used + sep + len(piece) <= cap:
            out.append(piece)
            used += sep + len(piece)
            continue
        remain = cap - used - sep
        if remain >= 40:
            out.append(piece[: remain - 3].rstrip() + "...")
        break
    block = "\n\n".join(out)
    if len(block) > cap:
        block = block[: cap - 3].rstrip() + "..."
    return block


def sanitize_inject(text: str) -> str:
    """Drop operator-lens / harvest / consciousness-claim lines if they leak in."""
    if not text:
        return ""
    kept: list[str] = []
    for line in text.splitlines():
        if _FORBIDDEN_LINE.search(line):
            continue
        kept.append(line)
    return "\n".join(kept)


def harvest_on_inject(text: str) -> bool:
    """True if harvest prose leaked onto the 9k/inject path (must stay false)."""
    low = (text or "").casefold()
    return "dream_harvest" in low or "harvest items" in low
