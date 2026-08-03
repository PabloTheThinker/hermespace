"""Hermes base as J-space — one facade for day-to-day higher-order use.

Anthropic's X video: read, audit, and shape what the model is thinking.
Hermes cannot J-lens arbitrary weights. The *base* (Hermespace OEW + optional
Cube heart) is the functional J-space for Hermes agents.

Connect path: the moment an agent joins Hermespace, Cube (or standalone
warehouse) charges the WorldModel and seeds the J-Space hub — a growing
room that can include hive peer agents when configured.

    from hermespace import HermesBase
    base = HermesBase(agent_id="my-agent")
    base.connect()   # gain world + hub + optional hive room
    base.status()
    base.lens()
    out = base.think("First repro then patch then verify", goal="Fix auth")
"""

from __future__ import annotations

import os
from typing import Any

from hermespace.jspace.oew import ensure_oew_env_default, oew_default_on
from hermespace.jspace.protocol import oew_enabled


class HermesBase:
    """Functional J-space of a Hermes base (Space ± Cube)."""

    def __init__(self, agent_id: str | None = None, session_id: str = "main") -> None:
        ensure_oew_env_default()
        self.agent_id = (agent_id or os.environ.get("HERMESPACE_AGENT_ID") or "hermes-agent").strip()
        self.session_id = session_id
        self._last_connect: dict[str, Any] | None = None

    # --- connect (intelligence gain) ---

    def connect(
        self,
        *,
        query: str = "",
        enter_world: bool = True,
        enter_workbench: bool = True,
        charge: bool = True,
        seed: bool = True,
    ) -> dict[str, Any]:
        """Enter Hermespace — heart, world, J-Space seed, optional hive room.

        Maps research memories into a live room:
        - Anthropic J-space → external hub the operator can lens
        - Baars GWT → limited FOA broadcast
        - Dehaene enduring memory → Cube / standalone warehouse charge
        - Multi-agent growth → hive soul presence when ``HERMESCUBE_HIVE`` set
        """
        from hermespace.cube_module import connect_agent

        out = connect_agent(
            self.agent_id,
            session_id=self.session_id,
            query=query,
            enter_world=enter_world,
            enter_workbench=enter_workbench,
            charge=charge,
            seed=seed,
        )
        self._last_connect = out
        return out

    def room(self) -> dict[str, Any]:
        """Hive / solo room status — who else is in the knowledge space."""
        from hermespace.cube_module import room_status

        return room_status(agent_id=self.agent_id)

    # --- readiness ---

    def status(self) -> dict[str, Any]:
        """Is this Hermes base operating as a J-space?"""
        out: dict[str, Any] = {
            "agent_id": self.agent_id,
            "session_id": self.session_id,
            "oew_enabled": oew_enabled(),
            "oew_default_on": oew_default_on(),
            "jspace": {},
            "cube": {},
            "world": {},
            "room": {},
            "ready": False,
            "connected": bool(self._last_connect and self._last_connect.get("ok")),
            "role": "external J-space for Hermes agents (access roles only)",
            "video_ops": ["read/lens", "audit", "shape/reflect", "swap", "ablate", "harvest"],
            "connect_ops": ["connect", "room", "pulse", "harvest"],
        }
        try:
            from hermespace.jspace import JSpace, JSpaceEnv

            js = JSpace(agent_id=self.agent_id)
            env = JSpaceEnv(agent_id=self.agent_id)
            out["jspace"] = {
                "hub_n": len(js.state.hub),
                "focus_n": len(js.state.focus),
                "silent_n": len(js.state.silent_steps),
                "band": env.band(),
                "pov": env.pov()[:120] if env.pov() else "",
                "protocol_enabled": bool(env._env.get("protocol_enabled", True)),
            }
        except Exception as exc:
            out["jspace"] = {"error": type(exc).__name__}

        try:
            from hermespace.cube_module import center_status, cube_available

            out["cube"] = {
                "available": bool(cube_available()),
                "status": center_status(),
            }
        except Exception as exc:
            out["cube"] = {"available": False, "error": type(exc).__name__}

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

        try:
            out["room"] = self.room()
        except Exception as exc:
            out["room"] = {"ok": False, "error": type(exc).__name__}

        if self._last_connect:
            out["last_connect"] = {
                "ok": self._last_connect.get("ok"),
                "gained": self._last_connect.get("gained"),
                "summary": self._last_connect.get("summary"),
            }

        out["ready"] = (
            oew_enabled()
            and "error" not in out["jspace"]
            and int(out["jspace"].get("hub_n", -1)) >= 0
        )
        return out

    # --- Anthropic video ops: read ---

    def lens(self, *, top_k: int = 12, include_silent: bool = True) -> str:
        from hermespace.jspace import JSpaceEnv

        return JSpaceEnv(agent_id=self.agent_id).lens_markdown(
            top_k=top_k, include_silent=include_silent
        )

    def audit(self) -> list[dict[str, Any]]:
        from hermespace.jspace import JSpaceEnv

        return [f.to_dict() for f in JSpaceEnv(agent_id=self.agent_id).audit()]

    def report(self, *, include_silent: bool = False) -> str:
        from hermespace.jspace import JSpace

        return JSpace(agent_id=self.agent_id).report(include_silent=include_silent)

    # --- scalpel ---

    def hold(self, text: str, *, silent: bool = False) -> dict[str, Any]:
        from hermespace.jspace import JSpace

        c = JSpace(agent_id=self.agent_id).hold(text, silent=silent)
        return {"ok": True, "concept": c.label()}

    def swap(self, source: str, target: str) -> dict[str, Any]:
        from hermespace.jspace import JSpaceEnv

        return JSpaceEnv(agent_id=self.agent_id).swap(source, target)

    def inject(self, text: str, *, silent: bool = True) -> dict[str, Any]:
        from hermespace.jspace import JSpaceEnv

        c = JSpaceEnv(agent_id=self.agent_id).inject_thought(text, silent=silent)
        return {"ok": True, "concept": c.label(), "silent": silent}

    def ablate(self, *patterns: str) -> dict[str, Any]:
        from hermespace.jspace import JSpaceEnv

        return JSpaceEnv(agent_id=self.agent_id).ablate(*patterns)

    # --- shape (CRT) ---

    def reflect(
        self,
        answer: str = "",
        *,
        principles: list[str] | None = None,
    ) -> dict[str, Any]:
        from hermespace.jspace import JSpaceEnv

        r = JSpaceEnv(agent_id=self.agent_id).reflect(
            answer=answer, principles=principles or []
        )
        return r.to_dict()

    def set_pov(self, text: str) -> dict[str, Any]:
        from hermespace.jspace import JSpaceEnv

        JSpaceEnv(agent_id=self.agent_id).set_pov(text)
        return {"ok": True, "pov": text[:200]}

    # --- deliberate turn (ignition) ---

    def think(
        self,
        message: str,
        *,
        goal: str = "",
        plan: list[str] | None = None,
        say: str = "",
        force: bool = True,
        connect_if_needed: bool = True,
    ) -> dict[str, Any]:
        """Run one higher-order Hermespace turn (OEW + Cube beat).

        On first think, auto-connects so the agent is not thinking in an empty room.
        """
        if connect_if_needed and not self._last_connect:
            try:
                self.connect(query=message[:120])
            except Exception:
                pass

        from hermespace.io_contract import HermespaceInput
        from hermespace.workflow import Workflow

        out = Workflow().run(
            HermespaceInput(
                message=message,
                goal=goal or message[:200],
                plan=list(plan or ["execute"]),
                say=say or "",
                force=force,
                agent_id=self.agent_id,
                session_id=self.session_id,
            )
        )
        return {
            "skipped": out.skipped,
            "reason": out.reason,
            "report": out.report,
            "context_chars": len(out.context or ""),
            "has_jspace_broadcast": "J-Space" in (out.context or ""),
            "oew": (out.meta or {}).get("jspace", {}).get("oew")
            or (out.meta or {}).get("oew")
            or {},
            "oew_ok": (out.meta or {}).get("jspace", {}).get("oew_ok"),
            "goal": out.goal,
            "decision": out.decision,
            "connected": bool(self._last_connect and self._last_connect.get("ok")),
        }

    # --- night ---

    def harvest(self, *, clear_silent: bool = False) -> dict[str, Any]:
        from hermespace.jspace import JSpaceEnv

        return JSpaceEnv(agent_id=self.agent_id).dream_harvest(
            seal_to_cube=True, clear_silent=clear_silent
        )

    def pulse(self) -> dict[str, Any]:
        try:
            from hermespace.cube_module import cube_pulse

            return cube_pulse(agent_id=self.agent_id)
        except Exception as exc:
            return {"ok": False, "error": type(exc).__name__}
