"""Hermes-native bridge — session + pre_llm workbench integration."""

from __future__ import annotations

import logging
import os
from typing import Any

logger = logging.getLogger("hermes.plugins.hermespace.bridge")


def _truthy(name: str, default: str = "0") -> bool:
    return os.environ.get(name, default).strip().lower() in {"1", "true", "yes", "on"}


def on_session_start(**kwargs: Any) -> dict[str, str] | None:
    """Enter pocket dimension; stamp Hermes env kit into starting context."""
    try:
        from hermespace.environment import probe_environment
        from hermespace.engine import HermespaceEngine
        from hermespace.neural_space import NeuralSpace
        from hermespace.store import load_desk, save_desk
        from hermespace.workbench import Workbench
    except ImportError:
        logger.debug("hermespace not importable on session start")
        return None

    session_id = str(kwargs.get("session_id") or "default")
    agent_id = os.environ.get("HERMESPACE_AGENT_ID", "hermes-agent")

    wb = Workbench(agent_id=agent_id, session_id=session_id)
    st = wb.enter()
    env = probe_environment()

    eng = HermespaceEngine()
    desk = load_desk(eng.desk_path)
    if not desk.goal:
        desk.goal = "Hermes agent session workbench"
        desk.decision = desk.decision or "A — operate"
        desk.plan = desk.plan or ["await orders", "use tools", "report"]
        desk.say = desk.say or "Workbench online. Ready for orders."
    for c in env.desk_concepts():
        if c not in desk.concepts:
            desk.concepts.append(c)
    desk.concepts = desk.concepts[-12:]
    save_desk(desk, eng.desk_path)
    try:
        ns = NeuralSpace()
        ns.config.verbalize = False
        ns.sync_from_desk(desk, user_message=desk.goal)
        save_desk(desk, eng.desk_path)
    except Exception:
        pass

    try:
        from hermespace.hermes_fabric import snapshot_fabric, skill_load_hints
        fab = snapshot_fabric(goal=desk.goal, message="")
        desk.meta["fabric"] = fab.to_dict()
        for hint in skill_load_hints(fab.skill_hits):
            if hint not in desk.concepts:
                desk.concepts.append(hint)
        desk.concepts = desk.concepts[-12:]
        save_desk(desk, eng.desk_path)
        desk = load_desk(eng.desk_path)
    except Exception:
        pass

    skills = (st.get("environment_summary") or {}).get("skills_count") or env.skills_count
    surfaces = (st.get("environment_summary") or {}).get("surfaces_present") or [
        s["id"] for s in env.surfaces if s.get("present")
    ]

    # Everyday ops boot (pulse defaults) — Quicksilver: no tick on critical path
    try:
        from hermespace import ops as ops_mod

        # tick=False: session start must not block on pulse cycle
        ops_mod.boot(
            agent_id=agent_id if agent_id != "hermes-agent" else "default",
            tick=False,
        )
    except Exception:
        pass

    block = (
        "## Hermespace workbench (session start)\n"
        f"- mode: {st.get('mode')} · agent: {agent_id} · session: {session_id}\n"
        f"- skills_available: {skills}\n"
        f"- tool_surfaces: {', '.join(surfaces[:10])}\n"
        f"- park_count: {st.get('park_count', 0)}\n"
        "- Pocket dimension online: park secondary goals, keep FOA tight, "
        "user replies short; put operational detail in workspace context.\n"
        "- API: `from hermespace import Workbench` · "
        "`from hermespace.agent_api import encode_message, run_turn, decode_for_user`\n"
    )

    # World enter — agent enters persistent world
    try:
        from hermespace.world import WorldModel
        wm = WorldModel(agent_id=agent_id)
        wm.enter()
        block += (
            "\n## World\n"
            f"- agent: {agent_id} · state: {wm.state.current_state}\n"
            f"- beliefs: {len(wm.state.beliefs)} · landmarks: {len(wm.state.landmarks)}\n"
            f"- evolutions: {wm.state.evolution_count}\n"
        )
    except Exception:
        pass

    return {"context": block}


def on_pre_llm_call(
    *,
    user_message: str = "",
    is_first_turn: bool = False,
    session_id: str = "",
    **kwargs: Any,
) -> dict[str, str] | None:
    try:
        from hermespace.engine import HermespaceEngine
        from hermespace.gate import should_inject
        from hermespace.inject import build_inject_block
        from hermespace.neural_space import NeuralSpace
        from hermespace.store import load_desk, save_desk
        from hermespace.workbench import Workbench
    except ImportError as exc:
        logger.debug("hermespace import failed: %s", exc)
        return None

    msg = user_message or ""
    sid = str(session_id or "default")
    agent_id = os.environ.get("HERMESPACE_AGENT_ID", "hermes-agent")

    # Conversational boundary regulation (user approves/denies access in chat)
    try:
        from hermespace.grid.converse import regulate

        reg = regulate(msg, agent_id=agent_id)
        if reg.handled:
            # Short user-facing note + keep inject for model
            eng = HermespaceEngine()
            desk = load_desk(eng.desk_path)
            note = reg.message
            block = build_inject_block(desk, max_chars=2000, user_message=msg)
            try:
                from hermespace.grid.access import pending_inject_block

                block = (block + "\n\n" + pending_inject_block(agent_id)).strip()
            except Exception:
                pass
            # Prefer explicit regulation reply as dual-channel: model sees full; user gets note via say path if auto
            return {
                "context": (
                    block
                    + "\n\n### Boundary regulation (this turn)\n"
                    + f"- action: {reg.action}\n"
                    + f"- user_reply_hint: {note}\n"
                    + "- Honor pocket rules. Do not write outside without approved permit.\n"
                ),
                # Some hosts ignore unknown keys; context is enough for model
            }
    except Exception as exc:  # noqa: BLE001
        logger.debug("regulate failed: %s", exc)

    eng = HermespaceEngine()
    desk = load_desk(eng.desk_path)

    auto_order = _truthy("HERMESPACE_AUTO_ORDER", "0")
    try:
        from hermespace.grid.controls import get_flag
        auto_order = auto_order or get_flag("auto_order", False)
    except Exception:
        pass
    if auto_order and msg.strip():
        do_auto, reason = should_inject(msg, desk_ready=True, is_first_turn=is_first_turn)
        if do_auto and reason not in {"trivial_ack", "explicit_off", "HERMESPACE_OFF"}:
            try:
                Workbench(agent_id=agent_id, session_id=sid).receive_order(
                    msg, force=True, say=""
                )
                desk = load_desk(eng.desk_path)
            except Exception as exc:  # noqa: BLE001
                logger.debug("auto_order failed: %s", exc)

    ready = desk.is_ready()
    do_it, reason = should_inject(
        msg, desk_ready=ready, is_first_turn=bool(is_first_turn)
    )
    if not do_it:
        return None

    if msg and ready:
        try:
            # Quicksilver: skip neural + fabric re-rank when desk already has
            # fresh fabric for same goal (TTL handled inside snapshot_fabric).
            goal_key = (desk.goal or msg)[:160]
            fab_meta = (desk.meta or {}).get("fabric") if isinstance(desk.meta, dict) else None
            need_heavy = True
            if isinstance(fab_meta, dict) and fab_meta.get("skill_hits") is not None:
                # Reuse cached fabric ranking when goal unchanged
                prev_goal = (desk.meta or {}).get("_fabric_goal")
                if prev_goal == goal_key and not is_first_turn:
                    need_heavy = False

            if need_heavy:
                desk.recompute_cognition(msg)
                # Neural FOA only when enabled (default off verbalize; skip if FORCE_OFF)
                if not _truthy("HERMESPACE_SKIP_NEURAL", "0"):
                    ns = NeuralSpace()
                    ns.config.verbalize = False
                    ns.sync_from_desk(desk, user_message=msg)
                save_desk(desk, eng.desk_path)
                desk = load_desk(eng.desk_path)
                try:
                    from hermespace.hermes_fabric import snapshot_fabric, skill_load_hints

                    fab = snapshot_fabric(goal=desk.goal or msg, message=msg)
                    desk.meta["fabric"] = fab.to_dict()
                    desk.meta["_fabric_goal"] = goal_key
                    for hint in skill_load_hints(fab.skill_hits):
                        if hint not in desk.concepts:
                            desk.concepts.append(hint)
                    desk.concepts = desk.concepts[-12:]
                    save_desk(desk, eng.desk_path)
                    desk = load_desk(eng.desk_path)
                except Exception:
                    pass
        except Exception as exc:  # noqa: BLE001
            logger.debug("neural refresh failed: %s", exc)

    block = build_inject_block(desk, max_chars=2800, user_message=msg)
    if not block.strip():
        return None

    try:
        from hermespace.world import world_context
        # First turn gets full world context; subsequent turns get delta
        last_count = desk.meta.get("world_entry_count", 0)
        world_context_block = world_context(
            agent_id,
            full=bool(is_first_turn) or last_count == 0,
            known_entries=last_count,
        )
        # Store entry count for next turn's delta
        try:
            from hermespace.world import WorldModel
            wm = WorldModel(agent_id=agent_id)
            desk.meta["world_entry_count"] = wm.archive.count()
            from hermespace.store import save_desk
            save_desk(desk)
        except Exception:
            pass
    except Exception:
        world_context_block = ""

    try:
        from hermespace.grid.access import pending_inject_block

        block += "\n\n" + pending_inject_block(agent_id)
    except Exception:
        pass

    if world_context_block:
        block += "\n\n" + world_context_block

    # Workbench status — only on first turn or when state changes
    try:
        st = Workbench(agent_id=agent_id, session_id=sid).status()
        last_mode = desk.meta.get("workbench_mode", "")
        if is_first_turn or st.get("mode") != last_mode:
            block += (
                f"\n### Workbench\n"
                f"- mode: {st.get('mode')} · park: {st.get('park_count')} · "
                f"idle_ticks: {st.get('idle_ticks')}\n"
                f"- last_report: {(st.get('last_report') or '')[:120]}\n"
            )
            desk.meta["workbench_mode"] = st.get("mode")
            try:
                from hermespace.store import save_desk
                save_desk(desk)
            except Exception:
                pass
    except Exception:
        pass

    try:
        from hermespace import ops as ops_mod

        block += "\n" + ops_mod.compact_status(
            agent_id=agent_id if agent_id != "hermes-agent" else "default"
        )
    except Exception:
        pass

    try:
        eng.episodes.write(
            f"broadcast reason={reason} session={sid[:12]}",
            outcome="inject",
            tags=["hermespace", "broadcast", str(reason)],
        )
    except Exception:
        pass

    return {"context": block}


def on_session_end(**kwargs: Any) -> None:
    if not _truthy("HERMESPACE_IDLE_ON_SESSION_END", "1"):
        return
    try:
        from hermespace.world import WorldModel
        agent_id = os.environ.get("HERMESPACE_AGENT_ID", "hermes-agent")
        WorldModel(agent_id=agent_id).leave("session ended")
    except Exception:
        pass
    try:
        from hermespace.workbench import Workbench

        sid = str(kwargs.get("session_id") or "default")
        agent_id = os.environ.get("HERMESPACE_AGENT_ID", "hermes-agent")
        Workbench(agent_id=agent_id, session_id=sid).idle_tick(consolidate_every=1)
    except Exception as exc:  # noqa: BLE001
        logger.debug("session_end idle failed: %s", exc)
