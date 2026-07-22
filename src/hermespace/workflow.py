"""Turn orchestrator — INPUT → Hermespace → OUTPUT (+ memory).

Any Hermes agent:

  inp = HermespaceInput(message=user_text, goal=..., decision=..., plan=[...])
  out = Workflow().run(inp)
  reply_to_user(out.report)          # output → user
  # out.context is for model context / pre_llm
  # out.memory_id is studyable history
"""

from __future__ import annotations

from typing import Any

from hermespace.engine import HermespaceEngine
from hermespace.gate import should_inject
from hermespace.inject import build_inject_block
from hermespace.io_contract import HermespaceInput, HermespaceOutput, new_turn_id
from hermespace.memory_db import HermespaceMemory
from hermespace.store import load_desk, save_desk
from hermespace.neural_space import NeuralSpace
from hermespace.hermes_fabric import snapshot_fabric, skill_load_hints


class Workflow:
    """End-to-end Hermespace turn with durable memory."""

    def __init__(
        self,
        engine: HermespaceEngine | None = None,
        memory: HermespaceMemory | None = None,
    ) -> None:
        self.engine = engine or HermespaceEngine()
        self.memory = memory or HermespaceMemory()
        self.neural = NeuralSpace()

    def run(self, inp: HermespaceInput | dict[str, Any]) -> HermespaceOutput:
        """Primary API: Input → Output."""
        if isinstance(inp, dict):
            payload = HermespaceInput.from_dict(inp)
        else:
            payload = inp.normalized()

        turn_id = new_turn_id()
        msg = payload.message
        existing = load_desk(self.engine.desk_path)
        ready_now = existing.is_ready()

        # 1. GATE
        if not payload.force:
            do_it, reason = should_inject(
                msg,
                desk_ready=ready_now or bool(payload.goal or payload.decision),
                is_first_turn=False,
            )
            if not do_it and reason in {"trivial_ack", "explicit_off", "HERMESPACE_OFF"}:
                out = HermespaceOutput(
                    turn_id=turn_id,
                    skipped=True,
                    reason=reason,
                    report="",
                    context="",
                    decision=existing.decision,
                    goal=existing.goal,
                    plan=list(existing.plan),
                    ready=ready_now,
                    session_id=payload.session_id,
                    desk_path=str(self.engine.desk_path),
                )
                mid = self.memory.record(
                    turn_id=turn_id,
                    session_id=payload.session_id,
                    agent_id=payload.agent_id,
                    message=msg,
                    goal=payload.goal,
                    decision=out.decision,
                    report="",
                    plan=out.plan,
                    context="",
                    skipped=True,
                    reason=reason,
                    tags=payload.tags,
                    meta=payload.meta,
                )
                out.memory_id = mid
                out.memory_path = str(self.memory.db_path)
                return out

        # 2–5 desk
        g = payload.goal or existing.goal or msg[:200]
        dec = payload.decision or existing.decision or "A — proceed"
        pl = payload.plan or existing.plan or ["execute"]
        sy = payload.say if payload.say else existing.say
        cons = payload.concepts or existing.concepts
        ch = payload.choices or existing.choices or ["A — proceed"]

        if payload.force or not existing.goal or payload.goal:
            desk = self.engine.enter(
                goal=g,
                concepts=list(cons or []),
                choices=list(ch or []),
                decision=str(dec),
                plan=list(pl or []),
                say=sy or "",
                auto_load=True,
                user_message=msg,
            )
        else:
            desk = self.engine.update(
                user_message=msg,
                decision=str(dec),
                plan=list(pl or []),
                say=sy or "",
                concepts=list(cons or []),
                choices=list(ch or []),
            )
            desk.recompute_cognition(msg)
            save_desk(desk, self.engine.desk_path)

        # 5b neural space sync (continuous field ↔ desk)
        try:
            neural_snap = self.neural.sync_from_desk(desk, user_message=msg)
            save_desk(desk, self.engine.desk_path)
            if desk.say:
                self.neural.remember_report(desk.say, desk.goal)
        except Exception:
            neural_snap = {"enabled": False, "error": "neural_sync_failed"}

        # 5c Hermes fabric — user's skills + MEMORY/USER inside the space
        fabric_snap = {}
        try:
            fab = snapshot_fabric(goal=desk.goal or g, message=msg)
            fabric_snap = fab.to_dict()
            desk.meta["fabric"] = fabric_snap
            for hint in skill_load_hints(fab.skill_hits):
                if hint not in desk.concepts:
                    desk.concepts.append(hint)
            desk.concepts = desk.concepts[-12:]
            save_desk(desk, self.engine.desk_path)
        except Exception as exc:
            fabric_snap = {"error": type(exc).__name__}

        # 6 broadcast context
        block = build_inject_block(desk, user_message=msg)
        report = (desk.say or "").strip()

        if payload.seal:
            self.engine.seal(payload.seal_note or f"turn seal: {desk.decision[:120]}")

        out = HermespaceOutput(
            turn_id=turn_id,
            skipped=False,
            reason="ok",
            report=report,
            context=block,
            decision=desk.decision,
            goal=desk.goal,
            plan=list(desk.plan),
            ready=desk.is_ready(),
            executive=desk.executive,
            load_level=str(desk.load.get("level", "")),
            streams=dict(desk.meta.get("streams") or {}),
            session_id=payload.session_id,
            desk_path=str(self.engine.desk_path),
            meta={
                "production": desk.meta.get("production"),
                "focus": desk.focus,
                "load": desk.load,
                "agent_id": payload.agent_id,
                "neural": neural_snap,
                "fabric": fabric_snap,
            },
        )

        # durable study memory
        mid = self.memory.record(
            turn_id=turn_id,
            session_id=payload.session_id,
            agent_id=payload.agent_id,
            message=msg,
            goal=out.goal,
            decision=out.decision,
            report=out.report,
            plan=out.plan,
            context=out.context,
            load_level=out.load_level,
            executive=out.executive,
            skipped=False,
            reason="ok",
            tags=payload.tags,
            meta={**payload.meta, "streams": out.streams, "fabric_skills": [h.get("name") for h in (fabric_snap.get("skill_hits") or []) if isinstance(h, dict)]},
        )
        out.memory_id = mid
        out.memory_path = str(self.memory.db_path)
        return out

    # Back-compat for earlier callers
    def turn(self, user_message: str, **kwargs: Any) -> HermespaceOutput:
        inp = HermespaceInput(
            message=user_message,
            goal=kwargs.get("goal") or "",
            decision=kwargs.get("decision") or "",
            plan=list(kwargs.get("plan") or []),
            say=kwargs.get("say") or "",
            concepts=list(kwargs.get("concepts") or []),
            choices=list(kwargs.get("choices") or []),
            force=bool(kwargs.get("force_enter") or kwargs.get("force") or False),
            seal=bool(kwargs.get("seal") or False),
            seal_note=kwargs.get("seal_note") or "",
            session_id=kwargs.get("session_id") or "",
            agent_id=kwargs.get("agent_id") or "",
        )
        return self.run(inp)

    def status(self) -> dict[str, Any]:
        desk = load_desk(self.engine.desk_path)
        return {
            "ready": desk.is_ready(),
            "goal": desk.goal[:120],
            "decision": desk.decision[:80],
            "report": desk.say[:120],
            "executive": desk.executive,
            "load": desk.load,
            "streams": desk.meta.get("streams"),
            "path": str(self.engine.desk_path),
            "memory": self.memory.paths(),
        }

    def history(self, **kwargs: Any) -> list[dict[str, Any]]:
        return self.memory.history(**kwargs)

    def study(self, query: str, **kwargs: Any) -> list[dict[str, Any]]:
        return self.memory.study(query, **kwargs)


# Back-compat alias used by older tests
TurnResult = HermespaceOutput
