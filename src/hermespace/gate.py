"""Gate — when Hermespace should inject (selective access = J-space selectivity)."""

from __future__ import annotations

import os
import re

# Force flags
ENV_FORCE_ON = "HERMESPACE_FORCE"
ENV_FORCE_OFF = "HERMESPACE_OFF"

_MATERIAL_RE = re.compile(
    r"\b("
    r"build|fix|deploy|implement|research|integrat|refactor|ship|commit|"
    r"hermespace|j-?space|plan|proceed|debug|investigate|design|architect|"
    r"multi-?step|remember|continue|where did|cross.?exam|"
    r"neuroscience|cognitive|working.?memory|attention|monotrop"
    r")\b",
    re.I,
)

_TRIVIAL_RE = re.compile(
    r"^\s*(ok|okay|k|thanks|thank you|ty|cool|nice|good|perfect|boom|"
    r"heartbeat_ok|👍|❤️|yes|yep|nope|no)\s*[.!]*\s*$",
    re.I,
)


def should_inject(
    user_message: str = "",
    *,
    desk_ready: bool = False,
    is_first_turn: bool = False,
) -> tuple[bool, str]:
    """Return (inject?, reason)."""
    if os.environ.get(ENV_FORCE_OFF, "").strip() in {"1", "true", "yes"}:
        return False, "HERMESPACE_OFF"
    if os.environ.get(ENV_FORCE_ON, "").strip() in {"1", "true", "yes"}:
        return True, "HERMESPACE_FORCE"

    msg = (user_message or "").strip()
    if not msg:
        return desk_ready, "empty_msg_desk" if desk_ready else "empty_msg"

    if _TRIVIAL_RE.match(msg) and len(msg) < 40:
        return False, "trivial_ack"

    # Explicit commands
    low = msg.lower()
    if "show hermespace" in low or "show desk" in low or "hermespace on" in low:
        return True, "explicit_command"
    if "hermespace off" in low:
        return False, "explicit_off"

    if desk_ready and _MATERIAL_RE.search(msg):
        return True, "material+ready"
    if desk_ready and len(msg) > 80:
        return True, "long_msg+ready"
    if desk_ready and is_first_turn:
        return True, "first_turn+ready"

    # Material but no desk — still skip inject (nothing useful) but reason logged
    if _MATERIAL_RE.search(msg) and not desk_ready:
        return False, "material_but_desk_not_ready"

    if desk_ready:
        return True, "desk_ready_default"

    return False, "no_desk"
