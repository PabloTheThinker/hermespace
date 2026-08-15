"""Hermes-native bridge — session + pre_llm workbench integration."""

from __future__ import annotations

import logging
import os
from typing import Any

logger = logging.getLogger("hermes.plugins.hermespace.bridge")


def _truthy(name: str, default: str = "0") -> bool:
    return os.environ.get(name, default).strip().lower() in {"1", "true", "yes", "on"}


from hermespace.context_surgery import (  # noqa: E402
    INJECT_HARD_CAP,
    MID_INJECT_CAP,
    assemble_inject,
    dual_decode_line,
    inject_budget,
    is_fluent_ack,
    is_shared_hub_child,
    sanitize_inject,
    strip_needed,
)

HARVEST_BUDGET_S = 10.0


def _bounded_context(text: str) -> str:
    """Keep native hook output below 9k (Hermes spill is 10k)."""

    try:
        cap = int(os.environ.get("HERMESPACE_PRE_LLM_MAX_CHARS", str(INJECT_HARD_CAP)))
    except ValueError:
        cap = INJECT_HARD_CAP
    cap = max(2000, min(8999, cap))
    if len(text) <= cap:
        return text
    tail_n = min(1200, cap // 4)
    head_n = cap - tail_n - 120
    return (
        text[:head_n]
        + "\n\n[Hermespace context bounded; low-priority middle omitted]\n\n"
        + text[-tail_n:]
    )


def _run_fail_open(label: str, fn: Any, *, seconds: float = HARVEST_BUDGET_S) -> None:
    """Run ``fn`` with a wall budget. If it overruns, continue (fail-open)."""
    import threading

    worker = threading.Thread(target=fn, name=f"hs-{label}", daemon=True)
    worker.start()
    worker.join(seconds)
    if worker.is_alive():
        logger.warning("%s exceeded %.0fs budget — fail-open", label, seconds)


def _safe_token(name: str, *, cap: int = 48) -> str:
    raw = (name or "").strip().split("(", 1)[0].split()[0]
    out = "".join(c for c in raw if c.isalnum() or c in "._:-")[:cap]
    return out or "unknown"


def _park_label(session_id: str, label: str) -> None:
    """Park a name-only silent step. Never persist args or results."""
    if not label:
        return
    agent_id = os.environ.get("HERMESPACE_AGENT_ID", "hermes-agent")
    try:
        from hermespace import AccessEngine
        from hermespace.access.hub import AccessHub

        engine = AccessEngine(
            agent_id=agent_id,
            session_id=str(session_id or "default"),
        )
        engine.hub.reason_step(label, salience=0.74)
        if engine.workspace_id != engine.agent_id:
            AccessHub(agent_id=engine.agent_id).reason_step(label, salience=0.74)
    except Exception:
        pass


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
        try:
            from hermespace.execute_focus import audhd_skill_hints

            for hint in audhd_skill_hints():
                if hint not in desk.concepts:
                    desk.concepts.append(hint)
        except Exception:
            pass
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
            # Short user-facing note + one lean inject. Never prepend session-start.
            desk = load_desk(eng.desk_path)
            note = reg.message
            block = assemble_inject(
                [
                    dual_decode_line(),
                    build_inject_block(
                        desk, max_chars=MID_INJECT_CAP, user_message=msg, lean=True
                    ),
                    "### Boundary regulation (this turn)\n"
                    f"- action: {reg.action}\n"
                    f"- user_reply_hint: {note}\n"
                    "- Honor pocket rules. Do not write outside without approved permit.",
                ],
                budget=MID_INJECT_CAP,
            )
            return {"context": _bounded_context(block)}
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
    if not do_it or is_fluent_ack(msg):
        return None
    if is_shared_hub_child(sid, kwargs):
        # One desk: park on the shared agent hub. Do not inject a full copy.
        try:
            from hermespace.access import AccessHub

            AccessHub(agent_id=agent_id).sync_from_desk(
                load_desk(eng.desk_path), user_message=msg
            )
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
            # protect is operator-pinned and must not be recomputed away.
            pinned = str((desk.load or {}).get("level") or "")
            high_load = pinned in {"high", "protect"}
            if pinned != "protect" and not high_load and msg:
                # cheap recompute so high flag can flip this turn
                try:
                    desk.recompute_cognition(msg)
                    high_load = str((desk.load or {}).get("level") or "") in {"high", "protect"}
                except Exception:
                    pass

            if need_heavy:
                if pinned != "protect":
                    desk.recompute_cognition(msg)
                    high_load = str((desk.load or {}).get("level") or "") in {"high", "protect"}
                else:
                    high_load = True
                    if isinstance(desk.load, dict):
                        desk.load["level"] = "protect"
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
                            try:
                                from hermespace.execute_focus import audhd_skill_hints

                                for hint in audhd_skill_hints():
                                    if hint not in desk.concepts:
                                        desk.concepts.append(hint)
                            except Exception:
                                pass
                            desk.concepts = desk.concepts[-12:]
                        save_desk(desk, eng.desk_path)
                        desk = load_desk(eng.desk_path)
                except Exception:
                    pass
        except Exception as exc:  # noqa: BLE001
            logger.debug("neural refresh failed: %s", exc)

    load_level = str((desk.load or {}).get("level") or "mid")
    high_load = load_level in {"high", "protect"}
    inject_cap = inject_budget(load_level)
    # Session-start essay is observer-only. Never prepend it onto the inject.
    _ = start_context

    cube_block = ""
    insight_strip = ""
    bound_strip = ""
    try:
        from hermespace.cube_module import cube_beat, skip_cube_foa_strip
        from hermespace.access import AccessHub

        q = (msg or desk.goal or "")[:500]
        load_val: str | float = desk.load.get("total", 0.5) if isinstance(desk.load, dict) else 0.5
        if high_load:
            load_val = "high"
        # Cube as Hermes memory.provider: MemoryManager already prefetched.
        # Do not call cube_beat / supply / build_space_inject — that re-pumps.
        if skip_cube_foa_strip():
            cube_block = ""
            beat = {
                "ok": True,
                "mode": "skipped",
                "skipped": "provider_prefetch",
                "block": "",
                "load_level": load_val,
            }
        else:
            beat = cube_beat(
                q,
                load=load_val,
                agent_id=agent_id,
                session_id=sid or "hermespace",
            )
            cube_block = str(beat.get("block") or "")
        # Insight: perceive_card only. Write-back (usable/lever) on desk.meta.
        # Never inject perceive()["card"], recall brief, or the lattice.
        try:
            from hermespace.insight_module import insight_card

            icard = insight_card(desk.goal or msg or "", load=load_val)
            desk.meta["insight"] = {
                "ok": icard.get("ok"),
                "mode": icard.get("mode"),
                "skipped": icard.get("skipped"),
            }
            wb = icard.get("writeback") or {}
            if isinstance(wb, dict) and (wb.get("usable") is not None or wb.get("lever") is not None):
                desk.meta["insight_writeback"] = {
                    k: wb[k] for k in ("usable", "lever") if k in wb
                }
            if icard.get("card") and not high_load:
                insight_strip = str(icard["card"])
        except Exception:
            pass
        from hermespace.access.oew import ensure_oew_env_default

        ensure_oew_env_default()
        js = AccessHub(agent_id=access_id)
        js.sync_from_desk(desk, user_message=msg, cube_strip=cube_block)
        desk.meta["cube_beat"] = {
            "ok": beat.get("ok"),
            "mode": beat.get("mode"),
            "load_level": beat.get("load_level"),
            "skipped": beat.get("skipped"),
            "shrunk": beat.get("shrunk"),
        }
        try:
            from hermespace.access import AccessEnv

            env = AccessEnv(agent_id=access_id)
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
            # Bound lines only — not the protocol essay, not lens, not reflect dump.
            try:
                from hermespace.access.loop import bound_protocol_lines

                bound_strip = bound_protocol_lines(env)
            except Exception:
                bound_strip = ""
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
            desk.meta["access"] = {
                "hub_n": len(js.state.hub),
                "focus_n": len(js.state.focus),
                "mode": js.state.mode,
            }
        try:
            from hermespace.store import save_desk

            save_desk(desk, eng.desk_path)
        except Exception:
            pass
    except Exception:
        pass

    has_bind = bool((bound_strip or "").strip())
    if not strip_needed(
        message=msg,
        load_level=load_level,
        is_first_turn=bool(is_first_turn),
        has_bind=has_bind,
    ):
        return None

    desk_block = build_inject_block(
        desk, max_chars=inject_cap, user_message=msg, lean=True
    )
    parts = [dual_decode_line(), desk_block]
    if has_bind:
        parts.append(bound_strip)
    # One organ strip if it fits: Insight card preferred, else Cube (never dual-pump).
    organ = ""
    if not high_load:
        organ = insight_strip or cube_block
    if organ:
        parts.append(organ)
    if load_level == "low":
        try:
            from hermespace.self_model import format_self_trace, read_self_trace
            from hermespace.access import AccessHub

            parts.append(
                format_self_trace(
                    read_self_trace(AccessHub(agent_id=access_id)),
                    for_inject=True,
                )
            )
        except Exception:
            pass

    block = sanitize_inject(assemble_inject(parts, budget=inject_cap))
    if not block.strip():
        return None

    user_hint = ""
    try:
        user_hint = str((desk.meta or {}).get("user_reply_hint") or desk.say or "")[:240]
    except Exception:
        user_hint = ""

    try:
        eng.episodes.write(
            f"broadcast reason={reason} session={sid[:12]} high={high_load}",
            outcome="inject",
            tags=["hermespace", "broadcast", str(reason)],
        )
    except Exception:
        pass

    result: dict[str, str] = {"context": _bounded_context(block)}
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
        from hermespace import AccessEngine
        from hermespace.access.hub import AccessHub
        from hermespace.access.loop import park_tool_step

        engine = AccessEngine(
            agent_id=agent_id,
            session_id=str(session_id or task_id or "default"),
        )
        step = park_tool_step(engine.hub, tool_name)
        if engine.workspace_id != engine.agent_id:
            park_tool_step(AccessHub(agent_id=engine.agent_id), tool_name)
        logger.debug("post_tool parked %s", step)
    except Exception as exc:  # noqa: BLE001
        logger.debug("post_tool hub park failed: %s", exc)
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
    def _harvest_and_idle() -> None:
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

    _run_fail_open("session_finalize_harvest", _harvest_and_idle, seconds=HARVEST_BUDGET_S)


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


def on_pre_tool_call(*, tool_name: str = "", session_id: str = "", **kwargs: Any) -> None:
    """Observe a tool about to fire. Never persist args. Fail-open — do not deny."""

    _ = kwargs  # payloads stay out of the hub
    try:
        from hermespace.access import AccessEnv
        from hermespace.access.engine import workspace_id

        agent_id = os.environ.get("HERMESPACE_AGENT_ID", "hermes-agent")
        env = AccessEnv(agent_id=workspace_id(agent_id, session_id or "default"))
        alerts = sum(1 for f in env.audit() if f.severity == "alert")
        if alerts:
            logger.debug("pre_tool_call %s audit_alerts=%s", _safe_token(tool_name), alerts)
    except Exception:
        pass


def on_skill_lifecycle(
    *,
    skill_name: str = "",
    event: str = "",
    session_id: str = "",
    **kwargs: Any,
) -> None:
    """Park skill:{name}:{event} — name only, no skill body."""

    _ = kwargs
    name = _safe_token(skill_name or str(kwargs.get("name") or ""))
    ev = _safe_token(event or str(kwargs.get("action") or "event"), cap=24)
    _park_label(session_id, f"skill:{name}:{ev}")


def on_kanban_task_claimed(
    *,
    task_id: str = "",
    title: str = "",
    session_id: str = "",
    **kwargs: Any,
) -> None:
    """Park kanban:claimed:{id} so the hub moves when a card is claimed."""

    _ = title
    _ = kwargs
    tid = _safe_token(task_id or str(kwargs.get("id") or ""), cap=32)
    _park_label(session_id, f"kanban:claimed:{tid}")


def on_kanban_task_completed(
    *,
    task_id: str = "",
    session_id: str = "",
    **kwargs: Any,
) -> None:
    """Park kanban:done:{id} — id only."""

    _ = kwargs
    tid = _safe_token(task_id or str(kwargs.get("id") or ""), cap=32)
    _park_label(session_id, f"kanban:done:{tid}")


def on_pre_verify(*, session_id: str = "", **kwargs: Any) -> None:
    """Observe a verify gate. Fail-open. Do not persist payloads."""

    _ = kwargs
    _park_label(session_id, "verify")
