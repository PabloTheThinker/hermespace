"""AuDHD execute/focus shapes for Access Engine report + park stack.

Stolen from hermes-audhd-skills (standalone repo) — shapes only:

  one live goal
  named parking lot: ``Name — state — next crumb``
  report line 1 = next action; lists ≤5; never quiz/restate as the lead

Do not vendor that skill tree. Do not hint ``audhd-emotion`` into a generic
ops profile. Public reference:
https://github.com/PabloTheThinker/hermes-audhd-skills
"""

from __future__ import annotations

import re
from typing import Any, Sequence

PARK_SEP = " — "
LIST_CAP = 5
AUDHD_HINT_NAMES = (
    "audhd-core",
    "audhd-execute",
    "audhd-focus",
    "audhd-communicate",
    "audhd-integrate",
)

_QUIZ_LEAD = re.compile(
    r"^\s*("
    r"remember when|as i (said|mentioned)|we should think|"
    r"what do you (think|want|remember)|did you want|"
    r"just to recap|as mentioned earlier"
    r")\b",
    re.IGNORECASE,
)
_LIST_LINE = re.compile(r"^\s*(?:[-*]|\d+[.)])\s+\S")


def short_name(goal: str, *, cap: int = 40) -> str:
    g = " ".join((goal or "").split())
    if not g:
        return "untitled"
    return g if len(g) <= cap else g[: cap - 1].rstrip() + "…"


def format_park_line(item: dict[str, Any] | str) -> str:
    """Named parking lot: Name — state — next crumb."""
    if isinstance(item, str):
        return f"{short_name(item)}{PARK_SEP}parked{PARK_SEP}resume"
    name = str(item.get("name") or short_name(str(item.get("goal") or ""))).strip()
    state = str(item.get("state") or "parked").strip() or "parked"
    crumb = str(
        item.get("next_crumb") or item.get("note") or "resume"
    ).strip() or "resume"
    return f"{name}{PARK_SEP}{state}{PARK_SEP}{crumb}"


def park_record(
    goal: str,
    *,
    name: str = "",
    state: str = "parked",
    next_crumb: str = "",
    note: str = "",
) -> dict[str, Any]:
    g = (goal or "").strip()
    return {
        "goal": g,
        "name": (name or short_name(g)).strip(),
        "state": (state or "parked").strip(),
        "next_crumb": (next_crumb or note or "resume").strip(),
        "note": (note or next_crumb or "").strip(),
    }


def next_action_line(
    *,
    goal: str = "",
    plan: Sequence[str] | None = None,
    say: str = "",
    decision: str = "",
) -> str:
    for step in plan or []:
        s = str(step or "").strip()
        if s:
            return s[:160]
    for raw in (say or "").splitlines():
        s = raw.strip().lstrip("-* ").lstrip("0123456789.) ")
        if s and not _QUIZ_LEAD.match(s) and not s.endswith("?"):
            return s[:160]
    dec = (decision or "").strip()
    if dec and not dec.lower().startswith("a — proceed"):
        return dec[:160]
    g = (goal or "").strip()
    if g:
        return f"Do the next step on: {short_name(g, cap=80)}"
    return "Name the first action (under 2 minutes)."


def _cap_lists(text: str, *, cap: int = LIST_CAP) -> str:
    out: list[str] = []
    listed = 0
    for line in (text or "").splitlines():
        if _LIST_LINE.match(line):
            listed += 1
            if listed > cap:
                continue
        out.append(line)
    return "\n".join(out).strip()


def shape_execute_report(
    report: str,
    *,
    goal: str = "",
    plan: Sequence[str] | None = None,
    say: str = "",
    decision: str = "",
) -> str:
    """Line 1 = next action. Lists ≤5. Never quiz/restate as the lead."""
    body = _cap_lists((report or "").strip())
    lead = next_action_line(goal=goal, plan=plan, say=say or body, decision=decision)
    if not body:
        return lead
    first = body.splitlines()[0]
    if _QUIZ_LEAD.match(first) or first.strip().endswith("?"):
        rest = "\n".join(body.splitlines()[1:]).strip()
        return f"{lead}\n{rest}".strip() if rest else lead
    if first.strip() != lead and not _LIST_LINE.match(first):
        # Keep an existing action lead; only prepend when the body starts as a list.
        return body
    if _LIST_LINE.match(first):
        return f"{lead}\n{body}".strip()
    return body


def execute_report_block(
    *,
    goal: str = "",
    plan: Sequence[str] | None = None,
    say: str = "",
    decision: str = "",
    parked: Sequence[dict[str, Any] | str] | None = None,
) -> str:
    lines = [next_action_line(goal=goal, plan=plan, say=say, decision=decision)]
    if goal:
        lines.append(f"Live: {short_name(goal, cap=80)}")
    items = list(parked or [])[:LIST_CAP]
    if items:
        lines.append("Parked:")
        for item in items:
            lines.append(f"- {format_park_line(item)}")
    return "\n".join(lines)


def audhd_skill_hints(*, hermes_home: Any = None) -> list[str]:
    """Fabric-hint audhd-* SKILL.md files when present. Skip emotion. Skip if missing."""
    from pathlib import Path

    from hermespace.environment import hermes_home as _hh

    root = Path(hermes_home) if hermes_home else _hh()
    skills = root / "skills"
    if not skills.is_dir():
        return []
    found: list[str] = []
    try:
        for p in skills.rglob("SKILL.md"):
            name = p.parent.name
            if name == "audhd-emotion" or "emotion" in name:
                continue
            if name.startswith("audhd-") and name in AUDHD_HINT_NAMES:
                found.append(name)
    except OSError:
        return []
    out: list[str] = []
    for name in AUDHD_HINT_NAMES:
        if name in found:
            out.append(f"[exec|0.70] skill_hint:{name} (use skill_view name={name})")
    return out[:LIST_CAP]
