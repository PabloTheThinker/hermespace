"""Hermes Insight adapter — soft dependency, never required.

Insight (when installed) is a standalone pattern lattice. Hermespace owns
FOA / Access Engine. This module is the cable, same shape as ``cube_module``:

  feature-detect ``hermes_insight``
  on material pre_llm / AccessEngine.turn → bounded perceive card (~400 chars)
  high-load skip · missing package → soft-fail
  never dump the lattice
  never call ``insight_plan`` on the hot path unless usable *and* multi-step

See PURPOSE.md. Do not vendor Insight source.
"""

from __future__ import annotations

import logging
import os
import re
from typing import Any, Sequence

logger = logging.getLogger("hermespace.insight_module")

SPACE_INSIGHT_ADAPTER_VERSION = "1.0"
INSIGHT_CARD_CHARS = 400

_MULTI_STEP_RE = re.compile(
    r"\b(first|then|next|after that|finally|and then|step\s*\d)\b",
    re.IGNORECASE,
)


def insight_available() -> bool:
    try:
        import hermes_insight  # noqa: F401

        return True
    except Exception:
        return False


def insight_status() -> dict[str, Any]:
    """Feature-detect only — never required for Access Engine."""
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

        out["available"] = True
        out["mode"] = "insight"
        out["version"] = getattr(hermes_insight, "__version__", None)
        return out
    except Exception as e:
        out["error"] = type(e).__name__
        return out


def _is_multi_step(goal: str = "", plan: Sequence[str] | None = None) -> bool:
    if plan is not None and len([p for p in plan if str(p).strip()]) >= 2:
        return True
    text = (goal or "").strip()
    if not text:
        return False
    if _MULTI_STEP_RE.search(text):
        return True
    return text.count(";") >= 2 or text.count("→") >= 2 or text.count("->") >= 2


def _bound_card(text: str, *, cap: int = INSIGHT_CARD_CHARS) -> str:
    s = (text or "").strip()
    if len(s) <= cap:
        return s
    return s[: cap - 3].rstrip() + "..."


def _format_card(
    *,
    lever: str,
    top_rule: str,
    usable: bool,
    action_hint: str,
    plan_hint: str = "",
) -> str:
    lines = [
        "### Insight",
        f"- lever: {(lever or 'unknown')[:80]}",
        f"- rule: {(top_rule or 'none')[:120]}",
        f"- usable: {str(bool(usable)).lower()}",
        f"- hint: {(action_hint or '')[:160]}",
    ]
    if plan_hint:
        lines.append(f"- plan: {plan_hint[:100]}")
    return _bound_card("\n".join(lines))


def insight_card(
    situation: str,
    *,
    observations: Sequence[str] | None = None,
    high_load: bool = False,
    goal: str = "",
    plan: Sequence[str] | None = None,
    agent_id: str = "",
    max_chars: int = INSIGHT_CARD_CHARS,
) -> dict[str, Any]:
    """Bounded perceive card for a material turn. Soft-fail if Insight is absent.

    Never dumps the lattice. ``insight_plan`` runs only when the perceive card
    is usable *and* the goal looks multi-step.
    """
    out: dict[str, Any] = {
        "ok": False,
        "adapter": SPACE_INSIGHT_ADAPTER_VERSION,
        "mode": "missing",
        "card": "",
        "usable": False,
        "lever": "",
        "top_rule": "",
        "action_hint": "",
        "planned": False,
        "required": False,
    }
    if high_load:
        out["ok"] = True
        out["mode"] = "skipped"
        out["skipped"] = "high_load"
        return out
    if not (situation or "").strip() and not (goal or "").strip():
        out["ok"] = True
        out["mode"] = "skipped"
        out["skipped"] = "empty"
        return out
    if not insight_available():
        out["ok"] = True
        out["mode"] = "missing"
        out["skipped"] = "not_installed"
        return out

    blob = (situation or goal or "").strip()
    obs = [str(o).strip() for o in (observations or []) if str(o).strip()]
    aid = (agent_id or os.environ.get("HERMESPACE_AGENT_ID") or "").strip() or None
    try:
        from hermes_insight import HermesInsight

        lat = HermesInsight(agent_id=aid)
        rec = lat.perceive(
            blob,
            observations=obs or None,
            log_experience=False,
            deep=False,
        )
    except Exception as e:
        logger.debug("insight perceive miss: %s", e)
        out["ok"] = True
        out["mode"] = "soft_fail"
        out["error"] = type(e).__name__
        return out

    if not isinstance(rec, dict):
        out["ok"] = True
        out["mode"] = "soft_fail"
        out["error"] = "bad_perceive"
        return out

    matches = list(rec.get("matches") or [])
    top = matches[0] if matches else {}
    lever = str(rec.get("lever") or "")
    usable = bool(rec.get("usable"))
    hint = str(rec.get("action_hint") or "")
    top_rule = str(top.get("title") or "")
    plan_hint = ""
    planned = False

    # Hot path: plan only when usable and the goal is actually multi-step.
    if usable and _is_multi_step(goal or blob, plan):
        try:
            planned_rec = lat.plan(blob, observations=obs or None, limit=3)
            if isinstance(planned_rec, dict):
                steps = planned_rec.get("steps") or planned_rec.get("plan") or []
                if isinstance(steps, list) and steps:
                    first = steps[0]
                    if isinstance(first, dict):
                        plan_hint = str(first.get("title") or first.get("action") or first)[:100]
                    else:
                        plan_hint = str(first)[:100]
                    planned = True
                elif planned_rec.get("action_hint"):
                    plan_hint = str(planned_rec.get("action_hint"))[:100]
                    planned = True
        except Exception as e:
            logger.debug("insight plan miss: %s", e)

    card = _format_card(
        lever=lever,
        top_rule=top_rule,
        usable=usable,
        action_hint=hint,
        plan_hint=plan_hint,
    )
    if max_chars and len(card) > max_chars:
        card = _bound_card(card, cap=max_chars)

    out.update(
        {
            "ok": True,
            "mode": "insight",
            "card": card,
            "usable": usable,
            "lever": lever,
            "top_rule": top_rule,
            "action_hint": hint,
            "planned": planned,
            "confidence": rec.get("confidence"),
            "top_score": rec.get("top_score"),
        }
    )
    return out
