"""Obligatory External Workspace — higher-order thinking orchestration.

This is the causal layer of the Access Workspace: material turns must park
silent intermediates; swaps redirect Report/broadcast; reflections seed the
next mid-band; ablations filter inject.

Default: ``HERMESPACE_OEW=1`` (higher-order on). Set ``0`` to soften.
"""

from __future__ import annotations

import os
import re
from typing import Any

from hermespace.access.hub import AccessHub
from hermespace.access.protocol import (
    ProtocolVerdict,
    evaluate_material_turn,
    oew_enabled,
)


_STEP_SPLIT = re.compile(
    r"\s*(?:→|->|;|\n|\d+[.)]\s+|\bthen\b|\bafter that\b|\bfinally\b|\band then\b)\s+",
    re.I,
)


def oew_default_on() -> bool:
    """Higher-order thinking is ON unless explicitly disabled."""
    raw = os.environ.get("HERMESPACE_OEW", "1").strip().lower()
    if raw in {"0", "false", "no", "off"}:
        return False
    return True


def ensure_oew_env_default() -> None:
    """Normalize env so unset HERMESPACE_OEW means enabled."""
    if "HERMESPACE_OEW" not in os.environ:
        os.environ["HERMESPACE_OEW"] = "1"


def auto_park_silent(
    js: AccessHub,
    *,
    desk: Any = None,
    user_message: str = "",
    min_steps: int = 1,
) -> list[str]:
    """Park verbalizable intermediates from goal/plan/message if missing.

    This is the core higher-order move: material work gets a mid-band chain
    even when the agent forgot to call reason_step.
    """
    parked: list[str] = []
    if len(js.state.silent_steps) >= min_steps:
        return parked

    from hermespace.execute_focus import (
        derive_plan,
        is_filler_step,
        is_near_dup,
        strip_slot_prefix,
    )

    candidates: list[str] = []
    plan = list(getattr(desk, "plan", None) or []) if desk is not None else []
    goal = str(getattr(desk, "goal", "") or "") if desk is not None else ""
    decision = str(getattr(desk, "decision", "") or "") if desk is not None else ""

    for step in plan:
        s = str(step).strip()
        if s and not is_filler_step(s):
            candidates.append(s[:160])

    msg = (user_message or "").strip()
    for step in derive_plan(msg or goal):
        candidates.append(step)

    if msg and re.search(
        r"\b(then|after|next|step\s*\d|first|second|finally|because|so that)\b",
        msg,
        re.I,
    ):
        chunks = [c.strip() for c in _STEP_SPLIT.split(msg) if c and c.strip()]
        for ch in chunks[:4]:
            short = strip_slot_prefix(ch)
            if len(short) > 8:
                candidates.append(short[:80])

    if decision and decision.lower() not in {"a — proceed", "a - proceed", "proceed"}:
        if len(decision) > 8 and not is_filler_step(decision):
            candidates.append(decision[:160])

    # Near-duplicate collapse (prefix-stripped gist), not exact casefold only
    existing = list(js.state.silent_steps)
    for c in candidates:
        body = strip_slot_prefix(c)
        if not body or any(is_near_dup(body, s) for s in existing):
            continue
        js.reason_step(body, salience=0.78)
        parked.append(body)
        existing.append(body)
        if len(parked) >= 3 or len(js.state.silent_steps) >= 3:
            break

    if not parked and min_steps > 0:
        fallback = (derive_plan(goal or msg) or [strip_slot_prefix(goal or msg or "task")])[0][:140]
        if fallback and not any(is_near_dup(fallback, s) for s in existing):
            js.reason_step(fallback, salience=0.72)
            parked.append(fallback)

    js.save()
    return parked


def shape_report(report: str, redirects: list[dict[str, str]]) -> str:
    """Apply sticky swaps to the user Report channel (causal redirect)."""
    out = report or ""
    for red in redirects or []:
        src = str(red.get("from") or "").strip()
        tgt = str(red.get("to") or "").strip()
        if not src or not tgt:
            continue
        # Case-insensitive replace preserving simple forms
        pattern = re.compile(re.escape(src), re.I)
        out = pattern.sub(tgt, out)
    return out


def filter_ablated(text: str, patterns: list[str]) -> str:
    """Drop lines matching ablated patterns (inject hygiene)."""
    if not patterns or not text:
        return text
    pats = [p.casefold() for p in patterns if p]
    kept: list[str] = []
    for line in text.splitlines():
        low = line.casefold()
        if any(p in low for p in pats):
            continue
        kept.append(line)
    return "\n".join(kept)


def inject_cap_chars(*, high_load: bool = False, protect: bool = False) -> int:
    """Quicksilver-safe inject budgets for Access Workspace blocks."""
    if protect or high_load:
        return 280
    return 640


def run_oew_beat(
    js: AccessHub,
    env: Any,
    *,
    desk: Any = None,
    user_message: str = "",
    report: str = "",
    material: bool = True,
    high_load: bool = False,
) -> dict[str, Any]:
    """Full higher-order beat: seed · park · evaluate · shape · filter.

    ``env`` is a AccessEnv instance (duck-typed to avoid circular imports).
    """
    ensure_oew_env_default()
    meta: dict[str, Any] = {"oew": True, "material": material}

    # 1) Seed pending silent from prior reflect()
    pending = list((getattr(env, "_env", {}) or {}).get("pending_silent") or [])
    seeded: list[str] = []
    for step in pending:
        s = str(step).strip()
        if s:
            js.reason_step(s, salience=0.82)
            seeded.append(s)
    if pending and hasattr(env, "_env"):
        env._env["pending_silent"] = []
        if hasattr(env, "_save_env"):
            env._save_env()
    meta["seeded_from_reflect"] = seeded

    # 2) Auto-park if material
    parked: list[str] = []
    if material:
        parked = auto_park_silent(js, desk=desk, user_message=user_message, min_steps=1)
    meta["auto_parked"] = parked

    # 3) Ensure reportable speech exists for material turns
    shaped = report or ""
    if material and desk is not None and not shaped.strip():
        say = str(getattr(desk, "say", "") or "").strip()
        if say:
            shaped = say
        else:
            goal = str(getattr(desk, "goal", "") or user_message or "working")[:160]
            shaped = f"Working on: {goal}"
            try:
                desk.say = shaped
            except Exception:
                pass

    # 4) Sticky redirects on Report
    redirects = list((getattr(env, "_env", {}) or {}).get("redirects") or [])
    shaped = shape_report(shaped, redirects)
    meta["redirects_applied"] = len(redirects)

    # 5) Protocol verdict
    silent_n = len(js.state.silent_steps)
    hub_holds = sum(1 for c in js.state.hub if getattr(c, "held", False))
    verdict = evaluate_material_turn(
        material=material,
        silent_steps=silent_n,
        has_report=bool(shaped.strip()),
        hub_holds=hub_holds,
        gated_skip=not material,
    )
    # If hard OEW and incomplete after auto-park, re-eval (auto-park should satisfy)
    if not verdict.ok and oew_enabled() and material:
        # Force one more park attempt
        auto_park_silent(js, desk=desk, user_message=user_message or shaped, min_steps=1)
        verdict = evaluate_material_turn(
            material=True,
            silent_steps=len(js.state.silent_steps),
            has_report=bool(shaped.strip()),
            hub_holds=sum(1 for c in js.state.hub if getattr(c, "held", False)),
        )
    meta["verdict"] = verdict.to_dict()

    # 6) Broadcast with ablate filter + Quicksilver cap
    ablated = list((getattr(env, "_env", {}) or {}).get("ablated_patterns") or [])
    raw_broadcast = js.broadcast_block(
        max_chars=inject_cap_chars(high_load=high_load),
        high_load=high_load,
    )
    broadcast = filter_ablated(raw_broadcast, ablated)
    meta["ablated_patterns"] = ablated
    meta["broadcast_chars"] = len(broadcast)

    return {
        "ok": bool(verdict.ok),
        "report": shaped,
        "broadcast": broadcast,
        "meta": meta,
        "verdict": verdict,
    }


def record_redirect(env: Any, source: str, target: str) -> None:
    """Persist sticky swap for subsequent Report shaping."""
    if not hasattr(env, "_env"):
        return
    reds = list(env._env.get("redirects") or [])
    src, tgt = source.strip(), target.strip()
    # Replace existing from same source
    reds = [r for r in reds if str(r.get("from", "")).casefold() != src.casefold()]
    reds.append({"from": src, "to": tgt})
    env._env["redirects"] = reds[-12:]
    if hasattr(env, "_save_env"):
        env._save_env()


def record_ablate(env: Any, patterns: list[str]) -> None:
    if not hasattr(env, "_env"):
        return
    cur = list(env._env.get("ablated_patterns") or [])
    for p in patterns:
        p = p.strip().casefold()
        if p and p not in cur:
            cur.append(p)
    env._env["ablated_patterns"] = cur[-24:]
    if hasattr(env, "_save_env"):
        env._save_env()


def queue_reflect_seeds(env: Any, principles: list[str], answer: str = "") -> None:
    """Queue mid-band seeds for the *next* turn after reflection."""
    if not hasattr(env, "_env"):
        return
    pending = list(env._env.get("pending_silent") or [])
    for p in principles[:6]:
        pending.append(f"principle-active: {p}")
    if answer:
        pending.append(f"reflection-seed: {answer[:160]}")
    env._env["pending_silent"] = pending[-12:]
    if hasattr(env, "_save_env"):
        env._save_env()
