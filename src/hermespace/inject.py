"""Prompt injection — GWT broadcast of workspace (+ load-aware compression)."""

from __future__ import annotations

from hermespace.cognition import partition_buffers
from hermespace.desk import Desk
from hermespace.episodic import EpisodicLog
from hermespace.store import load_desk


def build_inject_block(
    desk: Desk | None = None,
    *,
    max_chars: int = 2000,
    include_episodes: int = 4,
    user_message: str = "",
) -> str:
    desk = desk or load_desk()
    if user_message and not desk.load:
        desk.recompute_cognition(user_message)
    else:
        desk.clamp()
        if not desk.focus:
            desk.recompute_cognition(user_message or desk.goal)

    high = str(desk.load.get("level")) == "high"
    # GWT: under high load, broadcast only focus + goal/decision/say
    if high:
        max_chars = min(max_chars, 1400)
    elif desk.meta.get("fabric"):
        max_chars = max(max_chars, 2800)

    parts: list[str] = ["## Hermespace live desk (use before acting)"]

    if desk.goal:
        parts.append(f"**Goal:** {desk.goal[:300]}")

    # cognitive status
    if desk.load:
        parts.append(
            f"**Load:** {desk.load.get('level')} "
            f"(I={desk.load.get('intrinsic')} E={desk.load.get('extraneous')} "
            f"G={desk.load.get('germane')} tot={desk.load.get('total')}) "
            f"**Executive:** {desk.executive}"
        )
        if high:
            parts.append(
                "_High load — monotropic mode: one goal, short say, no option menus._"
            )

    streams = desk.meta.get("streams") or {}
    if streams:
        parts.append(
            f"**Streams (Meta TRIBE reverse):** text={streams.get('text',0)} "
            f"audio={streams.get('audio',0)} visual={streams.get('visual',0)} "
            f"prod={streams.get('production',0)}"
        )
    prod = desk.meta.get("production") or {}
    if prod and not high:
        parts.append(
            f"**Production hierarchy:** intention→semantics→report "
            f"({(prod.get('intention') or '')[:40]}…)"
        )

    neural = desk.meta.get("neural") or {}
    if neural.get("enabled"):
        parts.append(
            f"**Neural space:** backend={neural.get('backend')} traces={neural.get('n_traces')} "
            f"ignition={neural.get('ignition_threshold')} residual_n={neural.get('residual_norm')}"
        )
        if neural.get("focus"):
            parts.append("### Neural ignition (FOA)")
            for f in neural["focus"][:4]:
                parts.append(f"- {str(f)[:140]}")

    if desk.focus:
        parts.append("### Focus of attention (≤4)")
        for f in desk.focus[:4]:
            parts.append(f"- {f[:160]}")

    if not high and desk.concepts:
        parts.append("### Active concepts (activated WM)")
        for c in desk.concepts[:12]:
            parts.append(f"- {c[:160]}")
    elif high and desk.concepts:
        # only show non-focus if bind present
        binds = [c for c in desk.concepts if c.lower().startswith("[bind")]
        if binds:
            parts.append("### Episodic bind")
            parts.append(f"- {binds[-1][:180]}")

    # buffer summary (Baddeley)
    try:
        bufs = partition_buffers(desk.slots())
        if not high:
            parts.append("### Buffers")
            parts.append(
                f"- verbal: {len(bufs['verbal'])} · struct: {len(bufs['struct'])} · "
                f"bind: {len(bufs['bind'])} · exec: {len(bufs['exec'])}"
            )
    except Exception:  # noqa: BLE001
        pass

    if desk.choices and not high:
        parts.append("### Choices")
        for c in desk.choices:
            parts.append(f"- {c[:160]}")
    elif desk.choices and high:
        # only winning decision path
        pass

    if desk.decision:
        parts.append(f"**Decision:** {desk.decision[:240]}")
    if desk.plan:
        parts.append("### Plan")
        limit = 2 if high else len(desk.plan)
        for i, step in enumerate(desk.plan[:limit], 1):
            parts.append(f"{i}. {step[:160]}")
    if desk.say:
        say = desk.say[:180] if high else desk.say[:400]
        parts.append(f"**Report:** {say}")
    if desk.do_not_say:
        parts.append("### Inhibit (do not say)")
        for d in desk.do_not_say[:6]:
            parts.append(f"- {d[:120]}")

    if include_episodes and not high:
        eps = EpisodicLog().recent(limit=include_episodes)
        if eps:
            parts.append("### Recent episodes")
            for e in eps[:3]:
                parts.append(
                    f"- ({e.get('outcome', 'info')}) {str(e.get('content', ''))[:100]}"
                )

    # Hermes skills + MEMORY/USER (user's own fabric)
    fabric = desk.meta.get("fabric") or {}
    if fabric and not high:
        try:
            from hermespace.hermes_fabric import FabricSnapshot, SkillHit
            hits = [
                SkillHit(name=h["name"], path=h.get("path",""), score=float(h.get("score") or 0), preview=h.get("preview",""))
                for h in (fabric.get("skill_hits") or [])
                if isinstance(h, dict) and h.get("name")
            ]
            snap = FabricSnapshot(
                memory_excerpt=str(fabric.get("memory_excerpt") or ""),
                user_excerpt=str(fabric.get("user_excerpt") or ""),
                skill_hits=hits,
                hermes_home=str(fabric.get("hermes_home") or ""),
                notes=list(fabric.get("notes") or []),
            )
            parts.append(snap.inject_markdown())
        except Exception:
            if fabric.get("skill_hits"):
                parts.append("### Hermes skills (ranked)")
                for h in fabric["skill_hits"][:5]:
                    if isinstance(h, dict):
                        parts.append(f"- `{h.get('name')}` score={h.get('score')}")

    # Grid layer (missions, lens, selftalk, hot modules)
    if not high:
        try:
            import os
            from hermespace.grid import Grid

            aid = str(os.environ.get("HERMESPACE_AGENT_ID") or desk.meta.get("agent_id") or "default")
            gblock = Grid(aid).context_block()
            if gblock and len(gblock) > 40:
                parts.append(gblock)
        except Exception:  # noqa: BLE001
            pass

    if not high:
        try:
            from hermespace.semantic import SemanticStore

            notes = SemanticStore().list_notes(limit=3)
            if notes:
                parts.append("### Semantic seals")
                for n in notes:
                    parts.append(f"- {n.statement[:120]}")
        except Exception:  # noqa: BLE001
            pass

    if len(parts) <= 1:
        return ""

    block = "\n".join(parts)
    if len(block) > max_chars:
        block = block[: max_chars - 3] + "..."
    return block


def pre_llm_context_payload(user_message: str = "") -> dict[str, str] | None:
    block = build_inject_block(user_message=user_message)
    if not block.strip():
        return None
    return {"context": block}
