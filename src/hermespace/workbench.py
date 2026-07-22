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
        self.workflow = workflow or Workflow()
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
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(asdict(self.state), indent=2), encoding="utf-8")
        return self.path

    def enter(self) -> dict[str, Any]:
        """Agent enters the pocket dimension (idle ready) with full env kit."""
        if self.state.mode != "working":
            self.state.mode = "idle"
        env = probe_environment()
        self.state.meta["environment"] = env.to_dict()
        # stamp env concepts onto desk lightly via workflow engine
        try:
            desk = self.workflow.engine  # type: ignore[attr-defined]
            from hermespace.store import load_desk, save_desk
            d = load_desk(self.workflow.engine.desk_path)
            for c in env.desk_concepts():
                if c not in d.concepts:
                    d.concepts.append(c)
            d.concepts = d.concepts[-12:]
            save_desk(d, self.workflow.engine.desk_path)
        except Exception:
            pass
        self.save()
        st = self.status()
        st["environment_summary"] = {
            "skills_count": env.skills_count,
            "surfaces_present": [s["id"] for s in env.surfaces if s.get("present")],
            "memory_files": env.memory_files,
            "plugins": env.plugins_sample[:8],
        }
        return st

    def park_goal(self, goal: str, note: str = "", tags: list[str] | None = None) -> dict[str, Any]:
        """Park a goal while staying monotropic on current work / idle."""
        g = (goal or "").strip()
        if not g:
            return self.status()
        self.state.park = [p for p in self.state.park if p.get("goal") != g]
        self.state.park.append(
            asdict(ParkedGoal(goal=g, note=note or "", tags=list(tags or [])))
        )
        # keep park bounded
        self.state.park = self.state.park[-20:]
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
            plan=list(plan or ["execute"]),
            say=say,
            session_id=self.session_id,
            agent_id=self.agent_id,
            force=force,
            seal=seal,
            tags=["workbench", "order"],
        )
        out = run_turn(inp, workflow=self.workflow)
        bundle = decode_bundle(out)

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
            "model_context": decode_for_model(out),
            "bundle": bundle,
            "skipped": out.skipped,
            "reason": out.reason,
        }

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
