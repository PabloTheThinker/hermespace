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
_CLAUSE_SPLIT = re.compile(
    r"\s*(?:,\s*)?(?:\bthen\b|\bafter that\b|\bfinally\b|\band then\b|;|→|->)\s+",
    re.I,
)
_SLOT_PREFIX = re.compile(
    r"^(?:lang_stream|intention|step|report-ready|plan|decision-path|"
    r"working|multi-step context|production|partner|privacy|continuity):\s*",
    re.I,
)
_PROTOCOL_DUMP = re.compile(
    r"production:|partner:|privacy:|lang_stream:|intention:|"
    r"→\s*A\s+[—-]\s*proceed|\[production:",
    re.I,
)
_FILLER_STEPS = {
    "execute",
    "proceed",
    "do it",
    "go",
    "a — proceed",
    "a - proceed",
    "a — go",
}
_PROTOCOL_SLOT_PREFIXES = (
    "production:",
    "partner:",
    "privacy:",
    "continuity:",
)


def short_name(goal: str, *, cap: int = 40) -> str:
    g = " ".join((goal or "").split())
    if not g:
        return "untitled"
    return g if len(g) <= cap else g[: cap - 1].rstrip() + "…"


def strip_slot_prefix(text: str) -> str:
    """Drop lang_stream:/intention:/step: (and slot labels) for gist compare."""
    raw = (text or "").strip()
    if raw.startswith("[") and "]" in raw[:24]:
        raw = raw.split("]", 1)[1].strip()
    return _SLOT_PREFIX.sub("", raw).strip()


def gist_key(text: str) -> str:
    body = strip_slot_prefix(text)
    body = re.sub(r"[^\w\s]+", " ", body).casefold()
    return " ".join(body.split())


def is_filler_step(text: str) -> bool:
    return gist_key(text) in _FILLER_STEPS or strip_slot_prefix(text).casefold() in _FILLER_STEPS


def is_protocol_slot(text: str) -> bool:
    body = strip_slot_prefix(text)
    # strip_slot_prefix already removed the prefix — check the original
    raw = (text or "").strip()
    if raw.startswith("[") and "]" in raw[:24]:
        raw = raw.split("]", 1)[1].strip()
    low = raw.casefold()
    return low.startswith(_PROTOCOL_SLOT_PREFIXES)


def is_bind_restatement(text: str) -> bool:
    """Episodic bind blob: ``goal | A — proceed | plan:…`` — not a FOA thought."""
    body = strip_slot_prefix(text)
    if " | " not in body:
        return False
    low = body.casefold()
    return "plan:" in low or "a — proceed" in low or "a - proceed" in low


def is_near_dup(a: str, b: str) -> bool:
    ka, kb = gist_key(a), gist_key(b)
    if not ka or not kb:
        return False
    if ka == kb:
        return True
    shorter, longer = (ka, kb) if len(ka) <= len(kb) else (kb, ka)
    if len(shorter) < 8:
        return False
    if shorter in longer and len(shorter) / max(len(longer), 1) >= 0.55:
        return True
    return False


def collapse_near_dups(
    items: Sequence[str],
    *,
    prefer_shorter: bool = False,
) -> list[str]:
    """Collapse near-duplicate gists. Order preserved.

    ``prefer_shorter`` keeps the clause when a later short step is a
    near-dup of an earlier full-sentence echo.
    """
    out: list[str] = []
    for raw in items:
        s = str(raw or "").strip()
        if not s:
            continue
        hit = next((i for i, prev in enumerate(out) if is_near_dup(s, prev)), None)
        if hit is None:
            out.append(s)
            continue
        if prefer_shorter and len(gist_key(s)) < len(gist_key(out[hit])):
            out[hit] = s
    return out


def shape_focus(
    labels: Sequence[str],
    *,
    message: str = "",
    goal: str = "",
    plan: Sequence[str] | None = None,
    cap: int = 4,
) -> list[str]:
    """FOA: distinct clauses, not copies of the user sentence or bind blob."""
    clauses = plan_or_derived(plan, message, goal)
    raw_full = " ".join((message or goal or "").split())
    out: list[str] = []
    for c in clauses:
        if c and not is_filler_step(c) and not any(is_near_dup(c, prev) for prev in out):
            out.append(c)
    for raw in labels:
        s = str(raw or "").strip()
        if not s or is_protocol_slot(s) or is_bind_restatement(s) or is_filler_step(s):
            continue
        body = strip_slot_prefix(s)
        if (
            raw_full
            and clauses
            and is_near_dup(body, raw_full)
            and len(gist_key(body)) >= len(gist_key(raw_full)) * 0.8
        ):
            continue
        if any(is_near_dup(s, prev) for prev in out):
            continue
        out.append(s)
        if len(out) >= cap:
            break
    return collapse_near_dups(out, prefer_shorter=True)[:cap]


def _short_action(text: str) -> str:
    t = " ".join((text or "").split()).strip(" .,")
    t = re.sub(r"^(then|after that|after|finally|and)\s+", "", t, flags=re.I)
    if not t or is_filler_step(t):
        return ""
    if t[0].islower():
        t = t[0].upper() + t[1:]
    return t[:80] if len(t) <= 80 else t[:79].rstrip() + "…"


def derive_plan(message: str, *, max_n: int = 3) -> list[str]:
    """1–3 real steps from a user sentence. Never the filler ``execute``."""
    msg = " ".join((message or "").strip().split())
    if not msg:
        return []
    parts = [p.strip(" .,") for p in _CLAUSE_SPLIT.split(msg) if p and p.strip()]
    if len(parts) <= 1:
        step = _short_action(msg)
        return [step] if step else []
    out: list[str] = []
    for part in parts[: max(1, max_n)]:
        step = _short_action(part)
        if step and not any(is_near_dup(step, prev) for prev in out):
            out.append(step)
    return out[:max_n]


def plan_or_derived(
    plan: Sequence[str] | None,
    message: str = "",
    goal: str = "",
) -> list[str]:
    """Use a real plan when present; otherwise derive 1–3 steps from the message."""
    cleaned = [
        str(p).strip()
        for p in (plan or [])
        if str(p).strip() and not is_filler_step(p)
    ]
    if cleaned:
        return cleaned[:3]
    return derive_plan(message or goal)


def _is_bad_lead(line: str) -> bool:
    s = (line or "").strip()
    if not s:
        return True
    if _QUIZ_LEAD.match(s) or s.endswith("?"):
        return True
    if _PROTOCOL_DUMP.search(s):
        return True
    if is_filler_step(s):
        return True
    if s.casefold().startswith("→ ") or s.casefold().startswith("-> "):
        return True
    return False


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
    message: str = "",
) -> str:
    for step in plan_or_derived(plan, message, goal):
        s = str(step or "").strip()
        if s and not is_filler_step(s) and not _is_bad_lead(s):
            return s[:160]
    for raw in (say or "").splitlines():
        s = raw.strip().lstrip("-* ").lstrip("0123456789.) ")
        if s and not _is_bad_lead(s):
            return s[:160]
    dec = (decision or "").strip()
    if (
        dec
        and len(dec) > 8
        and not dec.lower().startswith("a —")
        and not dec.lower().startswith("a -")
        and not _is_bad_lead(dec)
        and not is_filler_step(dec)
    ):
        return dec[:160]
    derived = derive_plan(message or goal)
    if derived:
        return derived[0][:160]
    g = (goal or "").strip()
    if g and not _is_bad_lead(g):
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
    message: str = "",
) -> str:
    """Line 1 = next action. Lists ≤5. Never quiz/restate as the lead.

    When operator ``say`` is empty, always use ``next_action_line``.
    Protocol dumps (production:/partner:/→ A — proceed) never win the lead.
    """
    provided = (say or "").strip()
    lead = next_action_line(
        goal=goal,
        plan=plan,
        say=provided,
        decision=decision,
        message=message,
    )
    body = _cap_lists((report or "").strip())
    if not provided:
        if not body or _is_bad_lead(body.splitlines()[0]):
            return lead
        first = body.splitlines()[0].strip()
        if first == lead:
            return body
        if _LIST_LINE.match(first):
            return f"{lead}\n{body}".strip()
        return lead
    if not body:
        return lead
    first = body.splitlines()[0]
    if _is_bad_lead(first):
        rest = "\n".join(body.splitlines()[1:]).strip()
        if rest and not _PROTOCOL_DUMP.search(rest):
            return f"{lead}\n{rest}".strip()
        return lead
    if first.strip() != lead and not _LIST_LINE.match(first):
        # Operator supplied a clean say — keep that action lead.
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
