"""Hermespace Workbench — pocket dimension for Hermes agents.

Each agent gets a durable internal room:

- **ACTIVE desk** — current FOA / plan / report
- **Park stack** — goals waiting while idle or after monotropic switch
- **Idle tick** — maintain memory/neural while waiting for orders
- **Order turn** — when a user/system order arrives, run through Hermespace

This is the Conductor-era "pocket dimension" idea, realized as Hermespace
state + API — not a separate product brand.
"""

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from hermespace.atomic import atomic_write_text
from hermespace.agent_api import (
    decode_bundle,
    decode_for_model,
    decode_for_user,
    encode_message,
    run_turn,
)
from hermespace.paths import state_dir
from hermespace.semantic import consolidate
from hermespace.workflow import Workflow
from hermespace.environment import environment_markdown, probe_environment


def _utcnow() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


@dataclass
class ParkedGoal:
    goal: str
    note: str = ""
    name: str = ""
    state: str = "parked"
    next_crumb: str = ""
    parked_at: str = field(default_factory=_utcnow)
    tags: list[str] = field(default_factory=list)


@dataclass
class WorkbenchState:
    agent_id: str
    session_id: str = "default"
    mode: str = "idle"  # idle | working | paused
    park: list[dict[str, Any]] = field(default_factory=list)
    last_order: str = ""
    last_report: str = ""
    last_turn_id: str = ""
    idle_ticks: int = 0
    updated: str = field(default_factory=_utcnow)
    meta: dict[str, Any] = field(default_factory=dict)


class Workbench:
    """Per-agent pocket dimension inside Hermespace."""

    def __init__(
        self,
        agent_id: str = "hermes-agent",
        *,
        session_id: str = "default",
        workflow: Workflow | None = None,
        root: Path | None = None,
    ) -> None:
        self.agent_id = (agent_id or "hermes-agent").strip()
        self.session_id = (session_id or "default").strip()
        if workflow is None:
            from hermespace.engine import HermespaceEngine
            from hermespace.paths import session_desk_path

            workflow = Workflow(
                engine=HermespaceEngine(
                    desk_path=session_desk_path(self.agent_id, self.session_id)
                )
            )
        self.workflow = workflow
        self.root = (root or state_dir() / "workbenches").resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.path = self.root / f"{self._safe(self.agent_id)}__{self._safe(self.session_id)}.json"
        self.state = self._load()

    @staticmethod
    def _safe(s: str) -> str:
        return "".join(c if c.isalnum() or c in "-_" else "_" for c in s)[:80] or "agent"

    def _load(self) -> WorkbenchState:
        if not self.path.is_file():
            return WorkbenchState(agent_id=self.agent_id, session_id=self.session_id)
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
            return WorkbenchState(
                agent_id=str(raw.get("agent_id") or self.agent_id),
                session_id=str(raw.get("session_id") or self.session_id),
                mode=str(raw.get("mode") or "idle"),
                park=list(raw.get("park") or []),
                last_order=str(raw.get("last_order") or ""),
                last_report=str(raw.get("last_report") or ""),
                last_turn_id=str(raw.get("last_turn_id") or ""),
                idle_ticks=int(raw.get("idle_ticks") or 0),
                updated=str(raw.get("updated") or _utcnow()),
                meta=dict(raw.get("meta") or {}),
            )
        except (OSError, json.JSONDecodeError, TypeError, ValueError):
            return WorkbenchState(agent_id=self.agent_id, session_id=self.session_id)

    def save(self) -> Path:
        self.state.updated = _utcnow()
        atomic_write_text(self.path, json.dumps(asdict(self.state), indent=2))
        return self.path

    def enter(self, *, connect_warehouse: bool = True) -> dict[str, Any]:
        """Agent enters the pocket dimension (idle ready) with full env kit.

        When ``connect_warehouse`` is True (default), also charge Cube/world
        wisdom into Access Workspace and surface hive room presence — the intelligence
        gain on join. Set False when ``cube_module.connect_agent`` already
        orchestrates those phases (avoids recursion).
        """
        if self.state.mode != "working":
            self.state.mode = "idle"
        try:
            from hermespace.access.engine import workspace_id

            access_id = workspace_id(self.agent_id, self.session_id)
        except Exception:
            access_id = self.agent_id
        env = probe_environment()
        self.state.meta["environment"] = env.to_dict()
        # stamp env concepts onto desk lightly via workflow engine
        try:
            from hermespace.store import load_desk, save_desk
            d = load_desk(self.workflow.engine.desk_path)
            for c in env.desk_concepts():
                if c not in d.concepts:
                    d.concepts.append(c)
            d.concepts = d.concepts[-12:]
            save_desk(d, self.workflow.engine.desk_path)
        except Exception:
            pass
        # Ensure durable warehouse (Cube heart or standalone) + Access Workspace hub
        try:
            from hermespace.cube_module import ensure_heart

            heart = ensure_heart()
            self.state.meta["heart"] = {
                "ok": heart.get("ok"),
                "mode": heart.get("mode"),
                "created": heart.get("created"),
            }
        except Exception as exc:  # noqa: BLE001
            self.state.meta["heart"] = {"ok": False, "error": type(exc).__name__}
        try:
            from hermespace.access import AccessHub
            from hermespace.store import load_desk

            js = AccessHub(agent_id=access_id)
            desk = load_desk(self.workflow.engine.desk_path)
            js.sync_from_desk(desk, user_message=desk.goal or "")
            self.state.meta["access"] = {
                "hub_n": len(js.state.hub),
                "focus_n": len(js.state.focus),
                "mode": js.state.mode,
            }
        except Exception as exc:  # noqa: BLE001
            self.state.meta["access"] = {"error": type(exc).__name__}

        if connect_warehouse:
            try:
                from hermespace.cube_module import room_status, seed_access_from_warehouse
                from hermespace.cube_module import cube_pulse
                from hermespace.world import WorldModel

                WorldModel(agent_id=self.agent_id).enter()
                pulse = cube_pulse(agent_id=self.agent_id, ensure=False)
                room = room_status(agent_id=self.agent_id)
                seed = seed_access_from_warehouse(
                    self.agent_id,
                    query="",
                    session_id=self.session_id,
                    room=room,
                    workspace_id=access_id,
                )
                self.state.meta["connect"] = {
                    "pulse_ok": pulse.get("ok"),
                    "room_mode": room.get("mode"),
                    "peer_n": room.get("peer_n", 0),
                    "hub_n": seed.get("hub_n"),
                    "from_world": seed.get("enriched_world"),
                    "from_cube": seed.get("enriched_cube"),
                    "from_peers": seed.get("enriched_peers"),
                }
                if seed.get("hub_n") is not None:
                    self.state.meta["access"] = {
                        **(self.state.meta.get("access") or {}),
                        "hub_n": seed.get("hub_n"),
                        "focus_n": seed.get("focus_n"),
                    }
            except Exception as exc:  # noqa: BLE001
                self.state.meta["connect"] = {"ok": False, "error": type(exc).__name__}

        self.save()
        st = self.status()
        st["environment_summary"] = {
            "skills_count": env.skills_count,
            "surfaces_present": [s["id"] for s in env.surfaces if s.get("present")],
            "memory_files": env.memory_files,
            "plugins": env.plugins_sample[:8],
        }
        st["heart"] = self.state.meta.get("heart")
        st["access"] = self.state.meta.get("access")
        st["connect"] = self.state.meta.get("connect")
        st["room"] = (self.state.meta.get("connect") or {}).get("room_mode")
        return st

    def park_goal(
        self,
        goal: str,
        note: str = "",
        tags: list[str] | None = None,
        *,
        name: str = "",
        state: str = "parked",
        next_crumb: str = "",
    ) -> dict[str, Any]:
        """Park a goal while staying monotropic on current work / idle.

        Named lot format: ``Name — state — next crumb``.
        """
        from hermespace.execute_focus import format_park_line, park_record

        g = (goal or "").strip()
        if not g:
            return self.status()
        rec = park_record(
            g,
            name=name,
            state=state,
            next_crumb=next_crumb or note,
            note=note,
        )
        rec["tags"] = list(tags or [])
        rec["parked_at"] = _utcnow()
        self.state.park = [p for p in self.state.park if p.get("goal") != g]
        self.state.park.append(rec)
        self.state.park = self.state.park[-20:]
        self.state.meta["last_park_line"] = format_park_line(rec)
        self.save()
        return self.status()

    def pop_park(self) -> dict[str, Any] | None:
        if not self.state.park:
            return None
        item = self.state.park.pop(0)
        self.save()
        return item

    def idle_tick(self, *, consolidate_every: int = 5) -> dict[str, Any]:
        """Maintenance while waiting for orders — no user spam.

        - bump idle counter
        - periodically semantic consolidate
        - refresh neural attractors from last report
        - autonomic Cube pulse (or standalone world charge)
        - return status for logs (not for user channel)
        """
        self.state.mode = "idle"
        self.state.idle_ticks += 1
        actions: list[str] = ["tick"]

        # refresh environment inventory periodically
        if self.state.idle_ticks % max(1, consolidate_every) == 0:
            try:
                env = probe_environment()
                self.state.meta["environment"] = env.to_dict()
                actions.append(f"env_skills={env.skills_count}")
            except Exception as exc:  # noqa: BLE001
                actions.append(f"env_error:{type(exc).__name__}")
        if self.state.idle_ticks % max(1, consolidate_every) == 0:
            try:
                cons = consolidate(limit=40)
                actions.append(f"consolidate scanned={cons.get('scanned')}")
                self.state.meta["last_consolidate"] = cons
            except Exception as exc:  # noqa: BLE001
                actions.append(f"consolidate_error:{type(exc).__name__}")

        try:
            ns = self.workflow.neural
            if self.state.last_report:
                ns.remember_report(self.state.last_report, goal=self.state.last_order)
                actions.append("neural_attractors")
        except Exception as exc:  # noqa: BLE001
            actions.append(f"neural_error:{type(exc).__name__}")

        # Autonomic rhythm — Cube pulse_charge or standalone world+access
        if self.state.idle_ticks % max(1, consolidate_every) == 0:
            try:
                from hermespace.cube_module import cube_pulse

                pulse = cube_pulse(agent_id=self.agent_id)
                self.state.meta["last_cube_pulse"] = {
                    "ok": pulse.get("ok"),
                    "mode": pulse.get("mode"),
                }
                actions.append(f"cube_pulse:{pulse.get('mode')}")
            except Exception as exc:  # noqa: BLE001
                actions.append(f"cube_pulse_error:{type(exc).__name__}")

        # optional: surface top parked goal in meta for next order
        if self.state.park:
            self.state.meta["next_parked"] = self.state.park[0]

        self.save()
        st = self.status()
        st["idle_actions"] = actions
        return st

    def receive_order(
        self,
        message: str,
        *,
        goal: str = "",
        decision: str = "",
        plan: list[str] | None = None,
        say: str = "",
        force: bool = True,
        seal: bool = False,
        use_parked_if_empty_goal: bool = True,
    ) -> dict[str, Any]:
        """Order arrives → leave idle, run Hermespace turn, return dual decode."""
        msg = (message or "").strip()
        g = (goal or "").strip()
        try:
            live = str((self.workflow.status() or {}).get("goal") or "").strip()
            if live and g and live != g:
                self.park_goal(
                    live,
                    note="switched",
                    state="parked",
                    next_crumb="resume when this tunnel yields",
                )
        except Exception:
            pass
        if not g and use_parked_if_empty_goal and self.state.park:
            parked = self.pop_park()
            if parked:
                g = str(parked.get("goal") or "")
                if not msg:
                    msg = g

        self.state.mode = "working"
        self.state.last_order = msg or g
        self.save()

        inp = encode_message(
            msg or g,
            goal=g or msg,
            decision=decision or "A — proceed",
            plan=list(plan or []),
            say=say,
            session_id=self.session_id,
            agent_id=self.agent_id,
            force=force,
            seal=seal,
            tags=["workbench", "order"],
        )
        # Single ignition path — Workflow/AccessEngine already ran OEW + warehouse beat.
        # Do not double cube_beat / hub sync here (that inflated hub pressure).
        out = run_turn(inp, workflow=self.workflow)
        bundle = decode_bundle(out)
        try:
            jmeta = (out.meta or {}).get("access") or {}
            cmeta = (out.meta or {}).get("cube_beat") or {}
            self.state.meta["last_beat"] = {
                "ok": cmeta.get("ok"),
                "mode": cmeta.get("mode"),
                "load_level": cmeta.get("load_level"),
                "chars": cmeta.get("chars"),
                "single_path": True,
            }
            self.state.meta["access"] = {
                "hub_n": jmeta.get("hub_n"),
                "focus_n": jmeta.get("focus_n"),
                "silent_n": jmeta.get("silent_n"),
                "oew_ok": jmeta.get("oew_ok"),
            }
        except Exception as exc:  # noqa: BLE001
            self.state.meta["last_beat"] = {"ok": False, "error": type(exc).__name__}

        self.state.last_report = decode_for_user(out)
        self.state.last_turn_id = out.turn_id
        if out.skipped:
            self.state.mode = "idle"
        else:
            # after order, return to idle unless agent keeps working
            self.state.mode = "idle"
        self.save()

        return {
            "workbench": self.status(),
            "user_reply": decode_for_user(out),
            "model_context": bundle.get("model_context") if isinstance(bundle, dict) else decode_for_model(out),
            "bundle": bundle,
            "skipped": out.skipped,
            "reason": out.reason,
        }

    def park_lines(self) -> list[str]:
        from hermespace.execute_focus import format_park_line

        return [format_park_line(p) for p in self.state.park[-5:]]

    def environment(self) -> dict[str, Any]:
        """Full pocket-dimension tool/memory/skills inventory."""
        rep = probe_environment()
        self.state.meta["environment"] = rep.to_dict()
        self.save()
        d = rep.to_dict()
        d["markdown"] = environment_markdown(rep)
        return d

    def status(self) -> dict[str, Any]:
        desk = self.workflow.status()
        return {
            "agent_id": self.state.agent_id,
            "session_id": self.state.session_id,
            "mode": self.state.mode,
            "park_count": len(self.state.park),
            "park": self.state.park[-5:],
            "park_lines": self.park_lines(),
            "last_order": self.state.last_order[:160],
            "last_report": self.state.last_report[:200],
            "last_turn_id": self.state.last_turn_id,
            "idle_ticks": self.state.idle_ticks,
            "updated": self.state.updated,
            "path": str(self.path),
            "desk": {
                "ready": desk.get("ready"),
                "goal": desk.get("goal"),
                "decision": desk.get("decision"),
            },
            "memory": desk.get("memory"),
        }
