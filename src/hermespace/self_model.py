"""Bounded self-model: self-trace on the hub, then improve.

Product language: self-model / self-trace / improve.
Never “true self-conscious.” No phenomenal-consciousness claim.

After a material turn, Space already parks 1–3 intermediates from the
actual assistant text. This module adds a capped “what I just did”
record on the hub — readable via ``hs access view`` / FOA chip.
It is injected only on low load. reflect()/audit stay operator or
post_llm and write pending_silent for the *next* turn.
"""

from __future__ import annotations

from typing import Any

GOAL_CAP = 120
DECISION_CAP = 120
REPORT_CAP = 160
TOOL_CAP = 6
TRACE_INJECT_CAP = 280


def _first_line(text: str, cap: int) -> str:
    line = (text or "").strip().splitlines()[0] if (text or "").strip() else ""
    line = line.strip()
    if len(line) <= cap:
        return line
    return line[: cap - 1].rstrip() + "…"


def _tool_names(items: list[str] | None) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for raw in items or []:
        s = str(raw or "").strip()
        if not s.startswith("tool:"):
            name = s.split("(", 1)[0].strip()
            if name and not name.startswith("tool:"):
                s = f"tool:{name}"
            else:
                continue
        key = s.casefold()
        if key in seen:
            continue
        seen.add(key)
        out.append(s[:80])
        if len(out) >= TOOL_CAP:
            break
    return out


def build_self_trace(
    *,
    goal: str = "",
    decision: str = "",
    tools: list[str] | None = None,
    report: str = "",
) -> dict[str, Any]:
    """Capped self-trace dict — last goal / decision / tool:name list / Report line."""
    return {
        "goal": _first_line(goal, GOAL_CAP),
        "decision": _first_line(decision, DECISION_CAP),
        "tools": _tool_names(tools),
        "report": _first_line(report, REPORT_CAP),
    }


def record_self_trace(
    hub: Any,
    *,
    goal: str = "",
    decision: str = "",
    tools: list[str] | None = None,
    report: str = "",
) -> dict[str, Any]:
    """Park the self-trace on the hub (not the inject)."""
    silent = []
    try:
        silent = [str(s) for s in (hub.state.silent_steps or []) if str(s).startswith("tool:")]
    except Exception:
        silent = []
    merged = list(tools or []) + silent
    trace = build_self_trace(goal=goal, decision=decision, tools=merged, report=report)
    try:
        hub.state.meta["self_trace"] = dict(trace)
        if hasattr(hub, "save"):
            hub.save()
    except Exception:
        pass
    return trace


def format_self_trace(trace: dict[str, Any] | None, *, for_inject: bool = False) -> str:
    """Readable self-trace. Inject only when load is low."""
    t = dict(trace or {})
    if not any(t.get(k) for k in ("goal", "decision", "tools", "report")):
        return ""
    tools = ", ".join(str(x) for x in (t.get("tools") or [])[:TOOL_CAP])
    lines = [
        "### Self-trace",
        f"- goal: {t.get('goal') or '—'}",
        f"- decision: {t.get('decision') or '—'}",
        f"- tools: {tools or '—'}",
        f"- report: {t.get('report') or '—'}",
    ]
    block = "\n".join(lines)
    if for_inject and len(block) > TRACE_INJECT_CAP:
        block = block[: TRACE_INJECT_CAP - 3].rstrip() + "..."
    return block


def read_self_trace(hub: Any) -> dict[str, Any]:
    try:
        raw = (hub.state.meta or {}).get("self_trace") or {}
        return dict(raw) if isinstance(raw, dict) else {}
    except Exception:
        return {}


def maybe_seal_improve(desk: Any, *, agent_id: str) -> dict[str, Any]:
    """Seal a one-line learning into Cube when present. No second World warehouse."""
    meta = getattr(desk, "meta", None) or {}
    if not isinstance(meta, dict):
        return {"ok": False, "skipped": "no_meta"}
    line = ""
    for key in ("learn", "improve", "learning"):
        raw = meta.get(key)
        if isinstance(raw, str) and raw.strip():
            line = raw.strip().splitlines()[0][:200]
            break
    if not line:
        return {"ok": False, "skipped": "no_learning"}
    try:
        from hermespace.cube_module import seal_learning

        rec = seal_learning(
            line,
            entry_type="belief",
            agent_id=agent_id,
            source="self_model_improve",
        )
        return {
            "ok": bool(rec.get("ok")),
            "sealed": line,
            "mode": rec.get("mode"),
            "warehouse": "cube",
        }
    except Exception as exc:
        return {"ok": False, "error": type(exc).__name__}
