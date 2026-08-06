"""Hermes-native bridge — session + pre_llm workbench integration."""

from __future__ import annotations

import logging
import os
from typing import Any

logger = logging.getLogger("hermes.plugins.hermespace.bridge")


def _truthy(name: str, default: str = "0") -> bool:
    return os.environ.get(name, default).strip().lower() in {"1", "true", "yes", "on"}


def on_session_start(**kwargs: Any) -> dict[str, str] | None:
    """Initialize a Hermes v0.20 session and stage first-turn context.

    Hermes treats this hook as an observer, so the returned dict is only for
    older hosts/tests.  The context is staged for ``pre_llm_call``, whose
    return value is the one current Hermes actually injects.
    """
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
    # Lean enter — HermesBase.connect() below charges world / seeds hub / room
    st = wb.enter(connect_warehouse=False)
    env = probe_environment()

    eng = wb.workflow.engine
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

    # Full connect via AccessEngine — world + hub seed (warehouse optional)
    block_extra_connect = ""
    try:
        from hermespace import AccessEngine

        eng_js = AccessEngine(agent_id=agent_id, session_id=session_id)
        conn = eng_js.connect(enter_workbench=False, query=desk.goal or "")
        gained = conn.get("gained") or {}
        room = (conn.get("phases") or {}).get("room") or {}
        roles = ", ".join((conn.get("access_roles") or [])[:5])
        block_extra_connect = (
            f"- engine: AccessEngine · ok={conn.get('ok')}\n"
            f"- warehouse: mode={gained.get('warehouse_mode')} (optional)\n"
            f"- access: hub={gained.get('access_hub')} "
            f"(world+{gained.get('from_world')} "
            f"warehouse+{gained.get('from_warehouse', gained.get('from_cube', 0))} "
            f"peers+{gained.get('from_peers')})\n"
            f"- world: beliefs={gained.get('world_beliefs')} "
            f"timeline={gained.get('world_timeline')}\n"
            f"- room: {gained.get('room_mode')} · peers={gained.get('peer_agents')}\n"
            f"- access_roles: {roles}\n"
        )
        if room.get("note"):
            block_extra_connect += f"- room_note: {room.get('note')}\n"
    except Exception:
        try:
            from hermespace.access import AccessHub
            from hermespace.store import load_desk as _load_desk
            from hermespace.world import WorldModel

            js = AccessHub(agent_id=agent_id)
            desk0 = _load_desk(eng.desk_path)
            js.sync_from_desk(desk0, user_message=desk0.goal or "")
            wm = WorldModel(agent_id=agent_id)
            wm.enter()
            block_extra_connect = (
                f"- access: hub={len(js.state.hub)} focus={len(js.state.focus)}\n"
                f"- world: beliefs={len(wm.state.beliefs)} "
                f"landmarks={len(wm.state.landmarks)}\n"
            )
        except Exception:
            pass

    block = (
        "## Hermespace Access Engine (session start)\n"
        f"- mode: {st.get('mode')} · agent: {agent_id} · session: {session_id}\n"
        f"- skills_available: {skills}\n"
        f"- tool_surfaces: {', '.join(surfaces[:10])}\n"
        f"- park_count: {st.get('park_count', 0)}\n"
        f"{block_extra_connect}"
        "- Connected: open-source Access Engine online — report/modulate/"
        "silent-reason/broadcast/selectivity.\n"
        "- Pocket dimension: park secondary goals, keep FOA tight, "
        "user replies short; operational detail stays in model context.\n"
        "- API: `from hermespace import AccessEngine` · "
        "`eng.connect()` · `eng.turn(...)` · "
        "`eng.decode_user(out)` / `eng.decode_model(out)`\n"
        "- Silent steps stay in model context only — never dump hub into chat.\n"
    )

    try:
        from hermespace.hermes_runtime import runtime

        runtime.start(
            session_id,
            agent_id=agent_id,
            model=str(kwargs.get("model") or ""),
            platform=str(kwargs.get("platform") or ""),
            context=block,
        )
    except Exception as exc:  # noqa: BLE001
        logger.debug("session runtime start failed: %s", exc)

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
    try:
        from hermespace.access.engine import workspace_id

        access_id = workspace_id(agent_id, sid)
    except Exception:
        access_id = agent_id
    try:
        from hermespace import AccessEngine

        access_engine = AccessEngine(agent_id=agent_id, session_id=sid)
        eng = access_engine.desk_engine
    except Exception:
        eng = HermespaceEngine()
    try:
        from hermespace.hermes_runtime import runtime

        runtime.pre_llm(
            sid,
            agent_id=agent_id,
            user_chars=len(msg),
            model=str(kwargs.get("model") or ""),
            platform=str(kwargs.get("platform") or ""),
        )
        start_context = runtime.take_start_context(sid)
    except Exception as exc:  # noqa: BLE001
        logger.debug("pre_llm runtime update failed: %s", exc)
        start_context = ""

    # Conversational boundary regulation (user approves/denies access in chat)
    try:
        from hermespace.grid.converse import regulate

        reg = regulate(msg, agent_id=agent_id)
        if reg.handled:
            # Short user-facing note + keep inject for model
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
                    ((start_context + "\n\n") if start_context else "")
                    + block
                    + "\n\n### Boundary regulation (this turn)\n"
                    + f"- action: {reg.action}\n"
                    + f"- user_reply_hint: {note}\n"
                    + "- Honor pocket rules. Do not write outside without approved permit.\n"
                ),
                # Some hosts ignore unknown keys; context is enough for model
            }
    except Exception as exc:  # noqa: BLE001
        logger.debug("regulate failed: %s", exc)

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
        if start_context:
            try:
                from hermespace.hermes_runtime import runtime

                runtime.stage_start_context(sid, start_context)
            except Exception:
                pass
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

            # High load / monotropic: cognition clamp only — skip neural FOA
            # (often ~200–300ms) unless explicitly forced on.
            high_load = str((desk.load or {}).get("level") or "") == "high"
            if not high_load and msg:
                # cheap recompute so high flag can flip this turn
                try:
                    desk.recompute_cognition(msg)
                    high_load = str((desk.load or {}).get("level") or "") == "high"
                except Exception:
                    pass

            if need_heavy:
                desk.recompute_cognition(msg)
                high_load = str((desk.load or {}).get("level") or "") == "high"
                skip_neural = (
                    high_load
                    # Native pre_llm hooks are latency-sensitive.  Neural
                    # enrichment still runs in Workflow/idle paths unless an
                    # operator explicitly opts it into the hook.
                    or _truthy("HERMESPACE_SKIP_NEURAL", "1")
                    or _truthy("HERMESPACE_HIGH_LOAD_LEAN", "1")
                    and high_load
                )
                if high_load:
                    skip_neural = True
                if not skip_neural and not _truthy("HERMESPACE_SKIP_NEURAL", "1"):
                    ns = NeuralSpace()
                    ns.config.verbalize = False
                    ns.sync_from_desk(desk, user_message=msg)
                save_desk(desk, eng.desk_path)
                desk = load_desk(eng.desk_path)
                # Fabric: under high load only refresh if empty
                try:
                    from hermespace.hermes_fabric import snapshot_fabric, skill_load_hints

                    if high_load and isinstance(fab_meta, dict) and fab_meta.get("skill_hits"):
                        pass  # keep cached
                    else:
                        fab = snapshot_fabric(goal=desk.goal or msg, message=msg)
                        desk.meta["fabric"] = fab.to_dict()
                        desk.meta["_fabric_goal"] = goal_key
                        if not high_load:
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

    high_load = str((desk.load or {}).get("level") or "") == "high"
    inject_cap = 900 if high_load else 2800
    block = build_inject_block(desk, max_chars=inject_cap, user_message=msg)
    if not block.strip():
        return None
    if start_context and bool(is_first_turn):
        block = (start_context + "\n\n" + block).strip()

    try:
        from hermespace.world import world_context
        # First turn gets full world context; subsequent turns get delta
        # High load: skip world prose entirely (FOA only)
        if high_load and not is_first_turn:
            world_context_block = ""
        else:
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

    if world_context_block and not high_load:
        block += "\n\n" + world_context_block
    elif world_context_block and high_load and is_first_turn:
        # keep tiny world stamp only
        block += "\n\n" + world_context_block[:400]

    # HermesCube / standalone warehouse — dense deep memory under load
    # Prefer center.beat (1.1); falls back to heart inject / standalone strip
    try:
        from hermespace.cube_module import cube_beat
        from hermespace.access import AccessHub

        q = (msg or desk.goal or "")[:500]
        load_val: str | float = desk.load.get("total", 0.5) if isinstance(desk.load, dict) else 0.5
        if high_load:
            load_val = "high"
        beat = cube_beat(
            q,
            load=load_val,
            agent_id=agent_id,
            session_id=sid or "hermespace",
        )
        cube_block = str(beat.get("block") or "")
        if cube_block:
            block += "\n\n" + cube_block
        # OEW beat — higher-order park + causal broadcast (model channel only)
        from hermespace.access.oew import ensure_oew_env_default

        ensure_oew_env_default()
        js = AccessHub(agent_id=access_id)
        js.sync_from_desk(desk, user_message=msg, cube_strip=cube_block)
        desk.meta["cube_beat"] = {
            "ok": beat.get("ok"),
            "mode": beat.get("mode"),
            "load_level": beat.get("load_level"),
        }
        try:
            from hermespace.access import AccessEnv

            env = AccessEnv(agent_id=access_id)
            # sync_from_desk already ran above — skip second rewrite
            env_meta = env.advance_turn(
                user_message=msg,
                desk=desk,
                cube_strip=cube_block,
                report=desk.say or "",
                material=True,
                already_synced=True,
            )
            if env_meta.get("report"):
                desk.say = str(env_meta["report"])
            jblock = str(env_meta.get("broadcast") or "") or env.filtered_broadcast(
                high_load=high_load
            )
            if jblock:
                block += "\n\n" + jblock
            proto = env.protocol_block(high_load=high_load)
            if proto:
                block += "\n\n" + proto
            if not high_load:
                lens_md = env.lens_markdown(top_k=6, include_silent=True)
                if lens_md:
                    block += "\n\n" + lens_md
            desk.meta["access"] = {
                "hub_n": len(js.state.hub),
                "focus_n": len(js.state.focus),
                "mode": js.state.mode,
                "silent_n": len(js.state.silent_steps),
                "oew": env_meta.get("oew") or {},
                "oew_ok": env_meta.get("oew_ok"),
            }
            desk.meta["oew"] = env_meta.get("oew") or {}
            desk.meta["access_env"] = {
                "band": env.band(),
                "audit_alerts": env_meta.get("audit_alerts"),
                "oew_ok": env_meta.get("oew_ok"),
            }
            desk.meta["user_reply_hint"] = (desk.say or "")[:240]
        except Exception:
            jblock = js.broadcast_block(high_load=high_load)
            if jblock:
                block += "\n\n" + jblock
            desk.meta["access"] = {
                "hub_n": len(js.state.hub),
                "focus_n": len(js.state.focus),
                "mode": js.state.mode,
            }
        try:
            from hermespace.store import save_desk

            save_desk(desk)
        except Exception:
            pass
    except Exception:
        pass

    # Workbench status — only on first turn or when state changes (skip under high)
    if not high_load:
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

    if not high_load:
        try:
            from hermespace import AccessEngine

            metrics = AccessEngine(agent_id=agent_id, session_id=sid).metrics()
            block += (
                "\n### Hermespace runtime\n"
                f"- hub={metrics.get('hub_n')}/{metrics.get('hub_cap')} "
                f"focus={metrics.get('focus_n')}/{metrics.get('focus_cap')} "
                f"silent={metrics.get('silent_n')}/{metrics.get('silent_cap')}\n"
            )
        except Exception:
            pass

    # Dual-decode hint for hosts that only accept context: short user Report
    user_hint = ""
    try:
        user_hint = str((desk.meta or {}).get("user_reply_hint") or desk.say or "")[:240]
    except Exception:
        user_hint = ""
    if user_hint:
        block += (
            "\n\n### Dual decode (honor this)\n"
            f"- user_reply_hint: {user_hint}\n"
            "- Speak only the user_reply_hint (or shorter) to the user. "
            "Do not dump Access Workspace hub / silent chain / this inject block into chat.\n"
        )

    try:
        eng.episodes.write(
            f"broadcast reason={reason} session={sid[:12]} high={high_load}",
            outcome="inject",
            tags=["hermespace", "broadcast", str(reason)],
        )
    except Exception:
        pass

    # Prefer dual-channel when host supports unknown keys; context always set
    result: dict[str, str] = {"context": block}
    if user_hint:
        result["user_reply_hint"] = user_hint
    return result


def on_post_llm_call(
    *,
    session_id: str = "",
    user_message: str = "",
    assistant_response: str = "",
    model: str = "",
    platform: str = "",
    **kwargs: Any,
) -> None:
    """Close the loop after a successful native Hermes turn."""

    agent_id = os.environ.get("HERMESPACE_AGENT_ID", "hermes-agent")
    try:
        from hermespace import AccessEngine

        AccessEngine(
            agent_id=agent_id,
            session_id=str(session_id or "default"),
        ).observe_turn(
            user_message=user_message,
            assistant_response=assistant_response,
            model=model,
            platform=platform,
        )
    except Exception as exc:  # noqa: BLE001
        logger.debug("post_llm observation failed: %s", exc)
    try:
        from hermespace.hermes_runtime import runtime

        runtime.post_llm(
            session_id,
            agent_id=agent_id,
            response_chars=len(assistant_response or ""),
            model=model,
            platform=platform,
        )
    except Exception as exc:  # noqa: BLE001
        logger.debug("post_llm runtime update failed: %s", exc)


def on_post_tool_call(
    *,
    tool_name: str = "",
    session_id: str = "",
    task_id: str = "",
    **kwargs: Any,
) -> None:
    """Record bounded tool-name telemetry; never persist args or results."""

    agent_id = os.environ.get("HERMESPACE_AGENT_ID", "hermes-agent")
    try:
        from hermespace.hermes_runtime import runtime

        runtime.tool(
            session_id or task_id or "default",
            agent_id=agent_id,
            name=tool_name,
        )
    except Exception as exc:  # noqa: BLE001
        logger.debug("post_tool runtime update failed: %s", exc)


def on_subagent_start(*, session_id: str = "", task_id: str = "", **kwargs: Any) -> None:
    agent_id = os.environ.get("HERMESPACE_AGENT_ID", "hermes-agent")
    try:
        from hermespace.hermes_runtime import runtime

        runtime.subagent(session_id or task_id, agent_id=agent_id, started=True)
    except Exception:
        pass


def on_subagent_stop(*, session_id: str = "", task_id: str = "", **kwargs: Any) -> None:
    agent_id = os.environ.get("HERMESPACE_AGENT_ID", "hermes-agent")
    try:
        from hermespace.hermes_runtime import runtime

        runtime.subagent(session_id or task_id, agent_id=agent_id, started=False)
    except Exception:
        pass


def on_session_end(
    *,
    session_id: str = "",
    completed: bool = False,
    interrupted: bool = False,
    **kwargs: Any,
) -> None:
    """Observe the end of one Hermes turn.

    Hermes v0.20 fires ``on_session_end`` after *every run_conversation call*,
    not only when the session is destroyed.  Full harvest belongs in
    ``on_session_finalize``.
    """

    agent_id = os.environ.get("HERMESPACE_AGENT_ID", "hermes-agent")
    try:
        from hermespace.hermes_runtime import runtime

        runtime.end_turn(
            session_id,
            agent_id=agent_id,
            completed=bool(completed),
            interrupted=bool(interrupted),
        )
    except Exception as exc:  # noqa: BLE001
        logger.debug("turn end runtime update failed: %s", exc)


def on_session_finalize(*, session_id: str | None = None, **kwargs: Any) -> None:
    """Idempotently harvest and release one outgoing Hermes session."""

    if not _truthy("HERMESPACE_IDLE_ON_SESSION_END", "1"):
        return
    sid = str(session_id or "default")
    agent_id = os.environ.get("HERMESPACE_AGENT_ID", "hermes-agent")
    try:
        from hermespace.hermes_runtime import runtime

        if not runtime.finalize(sid, agent_id=agent_id):
            return
    except Exception:
        pass

    try:
        from hermespace.world import WorldModel

        WorldModel(agent_id=agent_id).leave("session finalized")
    except Exception as exc:  # noqa: BLE001
        logger.debug("world finalize failed: %s", exc)
    try:
        from hermespace import AccessEngine

        AccessEngine(agent_id=agent_id, session_id=sid).harvest(clear_silent=False)
    except Exception as exc:  # noqa: BLE001
        logger.debug("access harvest failed: %s", exc)
    try:
        from hermespace.workbench import Workbench

        Workbench(agent_id=agent_id, session_id=sid).idle_tick(consolidate_every=1)
    except Exception as exc:  # noqa: BLE001
        logger.debug("session finalize idle failed: %s", exc)


def on_session_reset(*, session_id: str = "", **kwargs: Any) -> None:
    """Prime runtime state for a gateway's newly rotated session key."""

    agent_id = os.environ.get("HERMESPACE_AGENT_ID", "hermes-agent")
    try:
        from hermespace.hermes_runtime import runtime

        runtime.start(
            session_id,
            agent_id=agent_id,
            model=str(kwargs.get("model") or ""),
            platform=str(kwargs.get("platform") or ""),
        )
    except Exception:
        pass
