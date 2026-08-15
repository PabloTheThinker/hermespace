"""Access Engine — Hermespace's open-source access workspace for Hermes Agent.

Hermes agents typically cannot read model weights. This engine is Hermespace's
own Access Workspace — a privileged verbalizable hub the operator can read,
shape, and audit:

  report · modulate · silent reason · flexible broadcast · selectivity

It merges FOA hub, OEW protocol, dual decode, session connect, material
ignition, operator scalpel (lens/audit/swap/inject/ablate/reflect), and night
harvest into **one** operating surface.

Warehouse / Cube (if installed) is optional arterial supply only — the engine
runs fully standalone on WorldModel + SemanticStore + desk.

    from hermespace import AccessEngine
    eng = AccessEngine(agent_id="my-agent")
    eng.connect()
    out = eng.turn("First repro then patch then verify", goal="Fix auth")
    print(eng.decode_user(out))   # short Report
    print(eng.lens())             # what is on the agent's mind
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from hermespace.access.oew import ensure_oew_env_default, oew_default_on
from hermespace.access.protocol import oew_enabled
from hermespace.paths import session_desk_path, session_scope_id

# Five GWT-style access roles implemented by this harness
ACCESS_ROLES = (
    "verbal_report",
    "directed_modulation",
    "internal_reasoning",
    "flexible_broadcast",
    "selectivity",
)


def workspace_id(agent_id: str, session_id: str = "") -> str:
    """Backward-compatible name for the canonical session scope helper."""

    return session_scope_id(agent_id, session_id)


class AccessEngine:
    """True Hermespace Access Engine — open-source GWT harness for Hermes."""

    def __init__(
        self,
        agent_id: str | None = None,
        session_id: str = "main",
        *,
        desk_path: Path | None = None,
    ) -> None:
        ensure_oew_env_default()
        self.agent_id = (
            agent_id or os.environ.get("HERMESPACE_AGENT_ID") or "hermes-agent"
        ).strip()
        self.session_id = session_id
        self.desk_path = desk_path
        self._last_connect: dict[str, Any] | None = None
        self._last_gate: dict[str, Any] | None = None
        self._turn_count = 0
        self._ignitions = 0
        self._skips = 0

    @property
    def workspace_id(self) -> str:
        return workspace_id(self.agent_id, self.session_id)

    # --- core handles -------------------------------------------------------

    @property
    def hub(self):
        from hermespace.access import AccessHub

        return AccessHub(agent_id=self.workspace_id)

    @property
    def env(self):
        from hermespace.access import AccessEnv

        return AccessEnv(agent_id=self.workspace_id)

    @property
    def desk_engine(self):
        """Desk-only spine (legacy HermespaceEngine)."""
        from hermespace.engine import HermespaceEngine

        if self.desk_path is not None:
            return HermespaceEngine(desk_path=self.desk_path)
        return HermespaceEngine(
            desk_path=session_desk_path(self.agent_id, self.session_id)
        )

    # --- Access roles (live) -------------------------------------------------

    def access_roles(self) -> dict[str, Any]:
        """Report the five live Access Workspace roles."""
        js = self.hub
        return {
            "verbal_report": {
                "ok": True,
                "api": "report() / decode_user()",
                "hub_reportable": sum(1 for c in js.state.hub if not c.silent),
            },
            "directed_modulation": {
                "ok": True,
                "api": "hold() / swap() / inject() / ablate()",
                "held": sum(1 for c in js.state.hub if c.held),
            },
            "internal_reasoning": {
                "ok": True,
                "api": "chain() / reason_step / OEW auto-park",
                "silent_n": len(js.state.silent_steps),
                "band": self.env.band(),
            },
            "flexible_broadcast": {
                "ok": True,
                "api": "broadcast() → pre_llm / tools / skills",
                "focus_n": len(js.state.focus),
                "readers": ["pre_llm_inject", "desk", "neural_space", "fabric_hints"],
            },
            "selectivity": {
                "ok": True,
                "api": "probe_material() / gate.should_inject",
                "last_gate": self._last_gate,
                "ignitions": self._ignitions,
                "skips": self._skips,
            },
            "roles": list(ACCESS_ROLES),
            "honesty": "access-consciousness roles only — no phenomenal claims; no weight J-lens",
        }

    def metrics(self) -> dict[str, Any]:
        """Capacity / ignition pressure — push-limit observability."""
        from hermespace.access.hub import FOCUS_CAP, HUB_CAP, REASON_CAP

        js = self.hub
        hub_n = len(js.state.hub)
        silent_n = len(js.state.silent_steps)
        return {
            "hub_n": hub_n,
            "hub_cap": HUB_CAP,
            "hub_pressure": round(hub_n / HUB_CAP, 3) if HUB_CAP else 0.0,
            "focus_n": len(js.state.focus),
            "focus_cap": FOCUS_CAP,
            "silent_n": silent_n,
            "silent_cap": REASON_CAP,
            "silent_depth": round(silent_n / REASON_CAP, 3) if REASON_CAP else 0.0,
            "held_n": sum(1 for c in js.state.hub if c.held),
            "mode": js.state.mode,
            "load_level": js.state.load_level,
            "turn_count": self._turn_count,
            "ignitions": self._ignitions,
            "skips": self._skips,
            "ignition_rate": (
                round(self._ignitions / self._turn_count, 3) if self._turn_count else None
            ),
            "oew_enabled": oew_enabled(),
        }

    def properties(self) -> list[str]:
        return list(ACCESS_ROLES)

    # --- session -------------------------------------------------------------

    def connect(
        self,
        *,
        query: str = "",
        enter_world: bool = True,
        enter_workbench: bool = True,
        charge: bool = True,
        seed: bool = True,
        warehouse: bool = True,
    ) -> dict[str, Any]:
        """Join the engine — world + hub seed. Warehouse/Cube optional.

        Standalone-first: WorldModel + SemanticStore charge the room even when
        HermesCube is absent. Optional warehouse arterial strip only.
        """
        out: dict[str, Any] = {
            "ok": False,
            "agent_id": self.agent_id,
            "session_id": self.session_id,
            "workspace_id": self.workspace_id,
            "engine": "AccessEngine",
            "phases": {},
            "gained": {},
            "access_roles": list(ACCESS_ROLES),
        }

        # Ensure local state dirs (and Cube heart if present — soft)
        if warehouse:
            try:
                from hermespace.cube_module import ensure_heart

                out["phases"]["warehouse"] = ensure_heart()
            except Exception as exc:
                out["phases"]["warehouse"] = {"ok": False, "error": type(exc).__name__}

        if enter_workbench:
            try:
                from hermespace.workbench import Workbench

                wb = Workbench(agent_id=self.agent_id, session_id=self.session_id)
                out["phases"]["workbench"] = wb.enter(connect_warehouse=False)
            except Exception as exc:
                out["phases"]["workbench"] = {"ok": False, "error": type(exc).__name__}

        if enter_world:
            try:
                from hermespace.world import WorldModel

                wm = WorldModel(agent_id=self.agent_id)
                st = wm.enter()
                out["phases"]["world"] = {
                    "ok": True,
                    "state": getattr(st, "current_state", None) or wm.state.current_state,
                    "beliefs": len(wm.state.beliefs or []),
                    "landmarks": len(wm.state.landmarks or []),
                    "timeline": wm.archive.count(),
                }
            except Exception as exc:
                out["phases"]["world"] = {"ok": False, "error": type(exc).__name__}

        if charge:
            try:
                from hermespace.cube_module import cube_pulse

                out["phases"]["charge"] = cube_pulse(agent_id=self.agent_id, ensure=False)
            except Exception as exc:
                out["phases"]["charge"] = {"ok": False, "error": type(exc).__name__}

        # Soft room (hive if configured; else solo)
        try:
            from hermespace.cube_module import room_status

            out["phases"]["room"] = room_status(agent_id=self.agent_id)
        except Exception:
            out["phases"]["room"] = {"mode": "solo", "ok": True, "peer_n": 0}

        if seed:
            try:
                from hermespace.cube_module import seed_access_from_warehouse

                out["phases"]["seed"] = seed_access_from_warehouse(
                    self.agent_id,
                    query=query,
                    session_id=self.session_id,
                    room=out["phases"].get("room"),
                    workspace_id=self.workspace_id,
                )
            except Exception as exc:
                # Minimal standalone seed from world beliefs
                out["phases"]["seed"] = self._seed_from_world(query=query)
                if "error" not in out["phases"]["seed"]:
                    out["phases"]["seed"]["fallback"] = type(exc).__name__

        world = out["phases"].get("world") or {}
        seed_ph = out["phases"].get("seed") or {}
        room = out["phases"].get("room") or {}
        wh = out["phases"].get("warehouse") or {}
        out["gained"] = {
            "warehouse_mode": wh.get("mode") or "standalone",
            "world_beliefs": world.get("beliefs", 0),
            "world_timeline": world.get("timeline", 0),
            "access_hub": seed_ph.get("hub_n", len(self.hub.state.hub)),
            "from_world": seed_ph.get("enriched_world", 0),
            "from_warehouse": seed_ph.get("enriched_cube", 0),
            "from_peers": seed_ph.get("enriched_peers", 0),
            "room_mode": room.get("mode", "solo"),
            "peer_agents": room.get("peer_n", 0),
        }
        out["ok"] = bool(world.get("ok", True) if enter_world else True)
        out["metrics"] = self.metrics()
        out["summary"] = (
            f"AccessEngine connected {self.agent_id}: "
            f"hub={out['gained']['access_hub']} "
            f"beliefs={out['gained']['world_beliefs']} "
            f"room={out['gained']['room_mode']}"
        )
        self._last_connect = out
        return out

    def _seed_from_world(self, *, query: str = "") -> dict[str, Any]:
        beliefs: list[str] = []
        try:
            from hermespace.world import WorldModel

            wm = WorldModel(agent_id=self.agent_id)
            for b in list(wm.state.beliefs or [])[:10]:
                stmt = (
                    str(b.get("statement") or "").strip()
                    if isinstance(b, dict)
                    else str(getattr(b, "statement", "") or "").strip()
                )
                if stmt:
                    beliefs.append(stmt)
        except Exception as exc:
            return {"ok": False, "error": type(exc).__name__}
        n = self.hub.enrich_from_world(beliefs, limit=5)
        return {
            "ok": True,
            "enriched_world": n,
            "enriched_cube": 0,
            "enriched_peers": 0,
            "hub_n": len(self.hub.state.hub),
            "mode": "standalone_world",
            "query": query[:80],
        }

    def room(self) -> dict[str, Any]:
        try:
            from hermespace.cube_module import room_status

            return room_status(agent_id=self.agent_id)
        except Exception as exc:
            return {"ok": True, "mode": "solo", "error": type(exc).__name__, "peer_n": 0}

    # --- readiness -----------------------------------------------------------

    def status(self) -> dict[str, Any]:
        out: dict[str, Any] = {
            "engine": "AccessEngine",
            "agent_id": self.agent_id,
            "session_id": self.session_id,
            "workspace_id": self.workspace_id,
            "oew_enabled": oew_enabled(),
            "oew_default_on": oew_default_on(),
            "access": {},
            "world": {},
            "room": {},
            "warehouse": {},
            "ready": False,
            "connected": bool(self._last_connect and self._last_connect.get("ok")),
            "role": "Hermespace Access Workspace for Hermes agents",
            "access_roles": self.access_roles(),
            "metrics": self.metrics(),
            "ops": [
                "connect",
                "turn",
                "lens",
                "audit",
                "hold",
                "swap",
                "inject",
                "ablate",
                "chain",
                "reflect",
                "harvest",
                "probe_material",
            ],
            "open_weight_lens": self.jlens_status(),
        }
        try:
            js = self.hub
            env = self.env
            out["access"] = {
                "hub_n": len(js.state.hub),
                "focus_n": len(js.state.focus),
                "silent_n": len(js.state.silent_steps),
                "band": env.band(),
                "pov": env.pov()[:120] if env.pov() else "",
                "protocol_enabled": bool(env._env.get("protocol_enabled", True)),
            }
        except Exception as exc:
            out["access"] = {"error": type(exc).__name__}

        try:
            from hermespace.world import WorldModel

            wm = WorldModel(agent_id=self.agent_id)
            out["world"] = {
                "beliefs": len(wm.state.beliefs or []),
                "landmarks": len(wm.state.landmarks or []),
                "timeline": wm.archive.count(),
                "state": wm.state.current_state,
            }
        except Exception as exc:
            out["world"] = {"error": type(exc).__name__}

        out["room"] = self.room()
        try:
            from hermespace.cube_module import center_status, cube_available

            out["warehouse"] = {
                "cube_available": bool(cube_available()),
                "optional": True,
                "status": center_status(),
            }
        except Exception:
            out["warehouse"] = {"cube_available": False, "optional": True}
        try:
            from hermespace.insight_module import insight_status

            out["insight"] = insight_status()
        except Exception:
            out["insight"] = {"available": False, "required": False, "optional": True}

        if self._last_connect:
            out["last_connect"] = {
                "ok": self._last_connect.get("ok"),
                "gained": self._last_connect.get("gained"),
                "summary": self._last_connect.get("summary"),
            }

        out["ready"] = (
            oew_enabled()
            and "error" not in out["access"]
            and int(out["access"].get("hub_n", -1)) >= 0
        )
        return out

    # --- selectivity / probe -------------------------------------------------

    def probe_material(self, message: str, *, desk_ready: bool | None = None) -> dict[str, Any]:
        """Would this message ignite the Access Workspace?"""
        from hermespace.gate import should_inject
        from hermespace.store import load_desk

        ready = desk_ready
        if ready is None:
            try:
                ready = load_desk(self.desk_engine.desk_path).is_ready()
            except Exception:
                ready = False
        do_it, reason = should_inject(message or "", desk_ready=bool(ready), is_first_turn=False)
        # Material *intent* even when desk not ready yet (would ignite after connect)
        trivial = reason in {"trivial_ack", "explicit_off", "HERMESPACE_OFF"}
        material = (not trivial) and (
            bool(do_it)
            or reason in {"material_but_desk_not_ready", "material+ready", "long_msg+ready"}
            or "material" in reason
        )
        rec = {
            "material": material,
            "inject": bool(do_it),
            "reason": reason,
            "desk_ready": bool(ready),
            "oew_would_run": material and oew_enabled() and bool(do_it),
        }
        self._last_gate = rec
        return rec

    # --- operator / video ops ------------------------------------------------

    def lens(self, *, top_k: int = 12, include_silent: bool = True) -> str:
        return self.env.lens_markdown(top_k=top_k, include_silent=include_silent)

    def audit(self) -> list[dict[str, Any]]:
        return [f.to_dict() for f in self.env.audit()]

    def report(self, *, include_silent: bool = False) -> str:
        hub = self.hub.report(include_silent=include_silent)
        try:
            from hermespace.execute_focus import execute_report_block
            from hermespace.workbench import Workbench

            desk = self.desk
            parked = Workbench(
                agent_id=self.agent_id,
                session_id=self.session_id,
            ).state.park
            lead = execute_report_block(
                goal=desk.goal,
                plan=list(desk.plan or []),
                say=desk.say,
                decision=desk.decision,
                parked=parked,
            )
            return f"{lead}\n\n{hub}".strip()
        except Exception:
            return hub

    def broadcast(self, *, high_load: bool = False) -> str:
        return self.env.filtered_broadcast(high_load=high_load)

    def hold(self, text: str, *, silent: bool = False, salience: float = 0.9) -> dict[str, Any]:
        c = self.hub.hold(text, silent=silent, salience=salience)
        return {"ok": True, "concept": c.label(), "silent": silent}

    def swap(self, source: str, target: str) -> dict[str, Any]:
        return self.env.swap(source, target)

    def inject(self, text: str, *, silent: bool = True) -> dict[str, Any]:
        c = self.env.inject_thought(text, silent=silent)
        return {"ok": True, "concept": c.label(), "silent": silent}

    def ablate(self, *patterns: str) -> dict[str, Any]:
        return self.env.ablate(*patterns)

    def chain(self, *steps: str, salience: float = 0.85) -> dict[str, Any]:
        """Park a multi-step silent reasoning chain (internal reasoning role).

        Intermediate steps never appear in the spoken answer unless explicitly
        requested — required for multi-step work under OEW.
        """
        parked: list[str] = []
        js = self.hub
        for step in steps:
            s = (step or "").strip()
            if not s:
                continue
            js.reason_step(s, salience=salience)
            parked.append(s[:200])
        try:
            self.env.set_band("mid")
        except Exception:
            pass
        return {
            "ok": bool(parked),
            "parked": parked,
            "silent_n": len(js.state.silent_steps),
            "hub_n": len(js.state.hub),
        }

    def reflect(
        self,
        answer: str = "",
        *,
        principles: list[str] | None = None,
    ) -> dict[str, Any]:
        r = self.env.reflect(answer=answer, principles=principles or [])
        return r.to_dict()

    def set_pov(self, text: str) -> dict[str, Any]:
        self.env.set_pov(text)
        return {"ok": True, "pov": text[:200]}

    # --- material ignition (single path) -------------------------------------

    def turn(
        self,
        message: str,
        *,
        goal: str = "",
        plan: list[str] | None = None,
        say: str = "",
        decision: str = "",
        force: bool = True,
        seal: bool = False,
        connect_if_needed: bool = True,
    ) -> Any:
        """One higher-order material turn — the only ignition path.

        Returns ``HermespaceOutput`` (dual decode: ``.report`` vs ``.context``).
        """
        if connect_if_needed and not self._last_connect:
            try:
                self.connect(query=(message or "")[:120], enter_workbench=False)
            except Exception:
                pass

        from hermespace.io_contract import HermespaceInput
        from hermespace.workflow import Workflow

        self._turn_count += 1
        probe = self.probe_material(message)
        out = Workflow(engine=self.desk_engine).run(
            HermespaceInput(
                message=message,
                goal=goal or message[:200],
                plan=list(plan or []),
                say=say or "",
                decision=decision or "",
                force=force,
                seal=seal,
                agent_id=self.agent_id,
                session_id=self.session_id,
            )
        )
        if out.skipped:
            self._skips += 1
        else:
            self._ignitions += 1
        # Attach engine observability
        if isinstance(out.meta, dict):
            out.meta["engine"] = "AccessEngine"
            out.meta["probe"] = probe
            out.meta["metrics"] = self.metrics()
            out.meta["access_roles"] = list(ACCESS_ROLES)
        return out

    # Back-compat alias used by HermesBase
    def think(self, message: str, **kwargs: Any) -> dict[str, Any]:
        out = self.turn(message, **kwargs)
        return {
            "skipped": out.skipped,
            "reason": out.reason,
            "report": out.report,
            "context_chars": len(out.context or ""),
            "has_access_broadcast": "Access Workspace" in (out.context or ""),
            "oew": (out.meta or {}).get("access", {}).get("oew")
            or (out.meta or {}).get("oew")
            or {},
            "oew_ok": (out.meta or {}).get("access", {}).get("oew_ok"),
            "goal": out.goal,
            "decision": out.decision,
            "connected": bool(self._last_connect and self._last_connect.get("ok")),
            "engine": "AccessEngine",
            "metrics": (out.meta or {}).get("metrics") or self.metrics(),
        }

    def observe_turn(
        self,
        *,
        user_message: str = "",
        assistant_response: str = "",
        model: str = "",
        platform: str = "",
    ) -> dict[str, Any]:
        """Observe a completed native Hermes turn.

        ``pre_llm_call`` runs the workspace before generation; this closes the
        loop after Hermes finishes.  It updates the session workbench and an
        episodic receipt without mutating the conversation transcript.
        """

        report = (assistant_response or "").strip()
        user = (user_message or "").strip()
        result: dict[str, Any] = {
            "ok": True,
            "agent_id": self.agent_id,
            "session_id": self.session_id,
            "workspace_id": self.workspace_id,
            "user_chars": len(user),
            "response_chars": len(report),
            "model": (model or "")[:120],
            "platform": (platform or "")[:40],
        }
        try:
            from hermespace.access.loop import check_bound_report, park_spoken_intermediates
            from hermespace.context_surgery import is_fluent_ack

            if is_fluent_ack(user) or not report:
                parked = []
                result["spoken_parked"] = []
                result["skipped_park"] = "fluent_ack" if is_fluent_ack(user) else "empty"
            else:
                parked = park_spoken_intermediates(self.hub, report, max_n=3)
                result["spoken_parked"] = parked
            bound = check_bound_report(self.env, report)
            result["bound"] = {
                "checked": len(bound.get("checked") or []),
                "reseeded": len(bound.get("reseeded") or []),
            }
            if self.workspace_id != self.agent_id and parked:
                from hermespace.access.hub import AccessHub

                agent_hub = AccessHub(agent_id=self.agent_id)
                park_spoken_intermediates(agent_hub, report, max_n=3)
            try:
                from hermespace.self_model import maybe_seal_improve, record_self_trace
                from hermespace.store import load_desk

                desk = load_desk(self.desk_engine.desk_path)
                tools = [
                    s
                    for s in (self.hub.state.silent_steps or [])
                    if str(s).startswith("tool:")
                ]
                trace = record_self_trace(
                    self.hub,
                    goal=desk.goal,
                    decision=desk.decision,
                    tools=tools,
                    report=report,
                )
                result["self_trace"] = trace
                if self.workspace_id != self.agent_id:
                    from hermespace.access.hub import AccessHub

                    record_self_trace(
                        AccessHub(agent_id=self.agent_id),
                        goal=desk.goal,
                        decision=desk.decision,
                        tools=tools,
                        report=report,
                    )
                improve = maybe_seal_improve(desk, agent_id=self.agent_id)
                result["improve"] = {
                    "ok": improve.get("ok"),
                    "skipped": improve.get("skipped"),
                }
            except Exception as exc:
                result["self_model_error"] = type(exc).__name__
        except Exception as exc:
            result["loop_error"] = type(exc).__name__

        try:
            from hermespace.workbench import Workbench

            wb = Workbench(agent_id=self.agent_id, session_id=self.session_id)
            wb.state.last_order = user[:500]
            wb.state.last_report = report[:2000]
            wb.state.mode = "idle"
            wb.state.meta["last_native_turn"] = {
                "model": result["model"],
                "platform": result["platform"],
                "user_chars": len(user),
                "response_chars": len(report),
            }
            wb.save()
            result["workbench"] = True
        except Exception as exc:
            result["ok"] = False
            result["workbench_error"] = type(exc).__name__

        try:
            self.desk_engine.episodes.write(
                (
                    f"native turn complete: user_chars={len(user)} "
                    f"response_chars={len(report)} model={result['model']}"
                ),
                outcome="turn_complete",
                tags=["hermespace", "native_turn", result["platform"] or "unknown"],
            )
            result["episode"] = True
        except Exception as exc:
            result["episode_error"] = type(exc).__name__

        result["audit_alerts"] = sum(
            1 for finding in self.audit() if finding.get("severity") == "alert"
        )
        return result

    # --- dual decode ---------------------------------------------------------

    @staticmethod
    def decode_user(out: Any) -> str:
        from hermespace.agent_api import decode_for_user

        return decode_for_user(out)

    @staticmethod
    def decode_model(out: Any) -> str:
        from hermespace.agent_api import decode_for_model

        return decode_for_model(out)

    @staticmethod
    def decode_bundle(out: Any) -> dict[str, Any]:
        from hermespace.agent_api import decode_bundle

        return decode_bundle(out)

    # --- night ---------------------------------------------------------------

    def harvest(self, *, clear_silent: bool = False) -> dict[str, Any]:
        return self.env.dream_harvest(seal_to_cube=True, clear_silent=clear_silent)

    def pulse(self) -> dict[str, Any]:
        try:
            from hermespace.cube_module import cube_pulse

            return cube_pulse(agent_id=self.agent_id)
        except Exception as exc:
            return {"ok": False, "error": type(exc).__name__}

    # --- optional open-weight activation lens (not required) -----------------

    def jlens_status(self) -> dict[str, Any]:
        """Optional open-weight activation lens — not required for Access Engine.

        Hermespace Access Engine is harness-primary for Hermes Agent. Optional
        third-party open-weight lens tooling is separate and unnamed here.
        """
        out: dict[str, Any] = {
            "available": False,
            "role": "optional_open_weight_companion",
            "harness_primary": True,
            "note": (
                "Hermes Agent typically has no weight access — "
                "AccessEngine is Hermespace's Access Workspace."
            ),
        }
        try:
            import jlens  # type: ignore  # noqa: F401

            out["available"] = True
            out["package"] = "jlens"
        except Exception:
            try:
                import jacobian_lens  # type: ignore  # noqa: F401

                out["available"] = True
                out["package"] = "jacobian_lens"
            except Exception:
                pass
        return out


# Back-compat product name used in docs / older imports
HermespaceAccessEngine = AccessEngine
