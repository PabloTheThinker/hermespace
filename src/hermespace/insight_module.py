"""Hermes Insight adapter — thin soft-import, never required.

Insight stays a standalone package. This module is the cable only:

  from hermes_insight import HermesInsight
  hasattr(HermesInsight, "perceive_card")
  HermesInsight().perceive_card(goal, load=...)

Hang the returned card next to ``cube_beat`` on ``pre_llm_call``.
Skip entirely on high/protect load. Until ``perceive_card`` exists, skip —
do not format ``perceive()`` output (unbounded lattice). Do not call
``insight_plan`` / ``HermesInsight.plan`` on the hot path. Do not register
Insight hooks. Do not vendor Insight source.

See docs/architecture/INSIGHT.md.
"""

from __future__ import annotations

from typing import Any

SPACE_INSIGHT_ADAPTER_VERSION = "1.1"
INSIGHT_CARD_CHARS = 400


def _high_or_protect(load: str | float | None = None, *, high_load: bool = False) -> bool:
    if high_load:
        return True
    if isinstance(load, (int, float)):
        return float(load) >= 0.65
    s = str(load or "").strip().lower()
    return s in {"high", "protect", "protected", "mono", "monotropic"}


def _bound_card(text: str, *, cap: int = INSIGHT_CARD_CHARS) -> str:
    s = (text or "").strip()
    if len(s) <= cap:
        return s
    return s[: cap - 3].rstrip() + "..."


def insight_available() -> bool:
    try:
        from hermes_insight import HermesInsight

        return hasattr(HermesInsight, "perceive_card")
    except Exception:
        return False


def insight_status() -> dict[str, Any]:
    """Feature-detect ``perceive_card`` only — never required."""
    out: dict[str, Any] = {
        "adapter": SPACE_INSIGHT_ADAPTER_VERSION,
        "available": False,
        "required": False,
        "mode": "missing",
        "ok": True,
        "note": "optional soft-import — Hermespace runs without Insight",
    }
    try:
        import hermes_insight
        from hermes_insight import HermesInsight

        out["version"] = getattr(hermes_insight, "__version__", None)
        if hasattr(HermesInsight, "perceive_card"):
            out["available"] = True
            out["mode"] = "insight"
        else:
            out["mode"] = "no_perceive_card"
            out["skipped"] = "no_perceive_card"
        return out
    except Exception as e:
        out["error"] = type(e).__name__
        return out


def insight_card(
    goal: str,
    *,
    load: str | float | None = None,
    high_load: bool = False,
    max_chars: int = INSIGHT_CARD_CHARS,
) -> dict[str, Any]:
    """Call ``HermesInsight().perceive_card`` and return only that card.

    Soft-fail if Insight is absent or ``perceive_card`` is missing.
    Never calls ``perceive`` / ``plan``. Never formats a lattice dump.
    """
    out: dict[str, Any] = {
        "ok": True,
        "adapter": SPACE_INSIGHT_ADAPTER_VERSION,
        "mode": "missing",
        "card": "",
        "required": False,
    }
    if _high_or_protect(load, high_load=high_load):
        out["mode"] = "skipped"
        out["skipped"] = "high_load"
        return out
    if not (goal or "").strip():
        out["mode"] = "skipped"
        out["skipped"] = "empty"
        return out
    try:
        from hermes_insight import HermesInsight
    except Exception:
        out["mode"] = "missing"
        out["skipped"] = "not_installed"
        return out
    if not hasattr(HermesInsight, "perceive_card"):
        out["mode"] = "no_perceive_card"
        out["skipped"] = "no_perceive_card"
        return out
    try:
        rec = HermesInsight().perceive_card((goal or "").strip(), load=load)
    except Exception as e:
        out["mode"] = "soft_fail"
        out["error"] = type(e).__name__
        return out

    if isinstance(rec, str):
        card = rec
    elif isinstance(rec, dict):
        card = str(rec.get("card") or "")
    else:
        card = str(rec or "")
    cap = max_chars if max_chars and max_chars > 0 else INSIGHT_CARD_CHARS
    out.update({"mode": "insight", "card": _bound_card(card, cap=cap)})
    return out
