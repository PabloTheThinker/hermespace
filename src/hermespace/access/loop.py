"""Access Engine functional loop — operator-side twin of public J-space research.

Public J-space (research, not a product): silent verbalizable workspace —
report, hold, reason, broadcast, skip on fluent work. Readable/editable only
with weights. Space is the file hub + user-message inject. No weight access.
No Jacobian math. No product rename.
"""

from __future__ import annotations

import re
from typing import Any

from hermespace.access.hub import AccessHub
from hermespace.access.oew import queue_reflect_seeds, record_ablate, record_redirect

_SENT_SPLIT = re.compile(r"(?<=[.!?])\s+|\n+")
_LIST_ITEM = re.compile(r"^\s*(?:[-*]|\d+[.)])\s+(\S.+)$")
_CLAUSE = re.compile(
    r"\s*(?:→|->|;|(?:,\s+)?(?:then|so that|because|after that)\s+)\s*",
    re.I,
)
_TOOL_SAFE = re.compile(r"[^A-Za-z0-9._:-]+")


def extract_spoken_intermediates(text: str, *, max_n: int = 3) -> list[str]:
    """Pull 1–3 silent intermediates from the *actual* spoken Report."""
    raw = (text or "").strip()
    if not raw:
        return []
    items: list[str] = []
    for line in raw.splitlines():
        m = _LIST_ITEM.match(line)
        if m:
            body = m.group(1).strip()[:160]
            if body:
                items.append(body)
    if items:
        return items[:max_n]
    sentences = [s.strip() for s in _SENT_SPLIT.split(raw) if s and s.strip()]
    if len(sentences) >= 2:
        rest = [s[:160] for s in sentences[1:] if len(s) > 8][:max_n]
        return rest or [sentences[0][:160]]
    clauses = [c.strip()[:160] for c in _CLAUSE.split(raw) if c and len(c.strip()) > 8]
    if len(clauses) >= 2:
        return clauses[:max_n]
    return [raw[:160]]


def park_spoken_intermediates(
    js: AccessHub,
    text: str,
    *,
    max_n: int = 3,
) -> list[str]:
    """Park 1–3 silent steps extracted from the actual assistant utterance."""
    existing = {s.casefold() for s in js.state.silent_steps}
    parked: list[str] = []
    for step in extract_spoken_intermediates(text, max_n=max_n):
        key = step.casefold()
        if not step or key in existing:
            continue
        js.reason_step(step, salience=0.76)
        parked.append(step)
        existing.add(key)
        if len(parked) >= max_n:
            break
    return parked


def safe_tool_step(name: str) -> str:
    """``tool:{name}`` only — never args or results."""
    n = (name or "").strip()
    n = n.split("(", 1)[0].split()[0] if n else ""
    n = _TOOL_SAFE.sub("", n)[:64]
    return f"tool:{n or 'unknown'}"


def park_tool_step(js: AccessHub, name: str) -> str:
    """Park a mid-turn tool fire as a silent hub step."""
    step = safe_tool_step(name)
    js.reason_step(step, salience=0.8)
    return step


def bind_intervention(env: Any, kind: str, **payload: Any) -> dict[str, Any]:
    """Bind swap / ablate / reflect to the next spoken Report."""
    if not hasattr(env, "_env"):
        return {}
    binds = list(env._env.get("bound_interventions") or [])
    rec: dict[str, Any] = {
        "kind": kind,
        "bound_to": "next_report",
        "honored": False,
        **payload,
    }
    if kind == "swap":
        src = str(payload.get("from") or "").casefold()
        binds = [
            b
            for b in binds
            if not (b.get("kind") == "swap" and str(b.get("from") or "").casefold() == src)
        ]
    elif kind == "ablate":
        binds = [b for b in binds if b.get("kind") != "ablate"]
    elif kind == "reflect":
        binds = [b for b in binds if b.get("kind") != "reflect"]
    binds.append(rec)
    env._env["bound_interventions"] = binds[-12:]
    if hasattr(env, "_save_env"):
        env._save_env()
    return rec


def bound_protocol_lines(env: Any) -> str:
    """Hard protocol lines the model must honor in the next spoken Report."""
    binds = list((getattr(env, "_env", {}) or {}).get("bound_interventions") or [])
    if not binds:
        return ""
    lines = [
        "### Bound intervention (honor in the next spoken Report)",
        "These are operator bindings. A spoken Report that ignores them is theater and will be reseeded.",
    ]
    for b in binds:
        kind = str(b.get("kind") or "")
        if kind == "swap":
            src = str(b.get("from") or "")
            tgt = str(b.get("to") or "")
            lines.append(
                f"- SWAP: say {tgt}, not {src}. A Report that still says {src} is ignored and reseeded."
            )
        elif kind == "ablate":
            pats = ", ".join(str(p) for p in (b.get("patterns") or []) if p)
            if pats:
                lines.append(f"- ABLATE: do not mention: {pats}")
        elif kind == "reflect":
            princ = ", ".join(str(p) for p in (b.get("principles") or []) if p)
            if princ:
                lines.append(f"- REFLECT: next Report must honor: {princ}")
    return "\n".join(lines)


def check_bound_report(env: Any, report: str) -> dict[str, Any]:
    """Check the actual spoken Report. Reseed any ignored binding."""
    if not hasattr(env, "_env"):
        return {"checked": [], "reseeded": []}
    text = report or ""
    low = text.casefold()
    binds = list(env._env.get("bound_interventions") or [])
    kept: list[dict[str, Any]] = []
    checked: list[dict[str, Any]] = []
    reseeded: list[dict[str, Any]] = []
    for b in binds:
        kind = str(b.get("kind") or "")
        honored = False
        if kind == "swap":
            src = str(b.get("from") or "")
            tgt = str(b.get("to") or "")
            if src and src.casefold() in low and (not tgt or tgt.casefold() not in low):
                honored = False
            elif tgt and tgt.casefold() in low:
                honored = True
            elif src and src.casefold() not in low:
                honored = True
        elif kind == "ablate":
            pats = [str(p).casefold() for p in (b.get("patterns") or []) if p]
            honored = not any(p in low for p in pats)
        elif kind == "reflect":
            princ = [str(p) for p in (b.get("principles") or []) if p]
            honored = any(p.casefold() in low for p in princ) if princ else True
        rec = {**b, "honored": honored}
        checked.append(rec)
        if honored:
            continue
        if kind == "swap":
            record_redirect(env, str(b.get("from") or ""), str(b.get("to") or ""))
        elif kind == "ablate":
            record_ablate(env, [str(p) for p in (b.get("patterns") or []) if p])
        elif kind == "reflect":
            queue_reflect_seeds(
                env,
                [str(p) for p in (b.get("principles") or []) if p],
                answer=str(b.get("answer") or ""),
            )
        rec = {**rec, "reseeded": True}
        kept.append(rec)
        reseeded.append(rec)
    env._env["bound_interventions"] = kept[-12:]
    env._env["last_bound_check"] = {"checked": checked, "reseeded_n": len(reseeded)}
    if hasattr(env, "_save_env"):
        env._save_env()
    return {"checked": checked, "reseeded": reseeded}
