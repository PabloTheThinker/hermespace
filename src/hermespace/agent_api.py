"""Public integration doors for any Hermes agent.

Door map
--------
1. encode_message  — user text → HermespaceInput
2. run_turn        — Input → HermespaceOutput (desk + neural + memory)
3. decode_for_user — Output → plain string to send the user
4. decode_for_model— Output → context string for pre_llm / next completion
5. study_memory    — query past turns
6. plugin hook     — hermes_plugin pre_llm_call (broadcast only)

Typical agent loop::

    from hermespace.agent_api import encode_message, run_turn, decode_for_user, decode_for_model

    inp = encode_message(user_text, session_id=sid, agent_id="my-agent", force=True)
    out = run_turn(inp)
    if not out.skipped:
        reply = decode_for_user(out)       # → user channel
        ctx = decode_for_model(out)        # → model context
"""

from __future__ import annotations

from typing import Any

from hermespace.io_contract import HermespaceInput, HermespaceOutput
from hermespace.memory_db import HermespaceMemory
from hermespace.workflow import Workflow

# Shared default workflow (lazy)
_wf: Workflow | None = None


def get_workflow() -> Workflow:
    global _wf
    if _wf is None:
        _wf = Workflow()
    return _wf


def encode_message(
    message: str,
    *,
    goal: str = "",
    decision: str = "",
    plan: list[str] | None = None,
    say: str = "",
    session_id: str = "default",
    agent_id: str = "hermes-agent",
    force: bool = False,
    seal: bool = False,
    concepts: list[str] | None = None,
    choices: list[str] | None = None,
    tags: list[str] | None = None,
    meta: dict[str, Any] | None = None,
) -> HermespaceInput:
    """Door 1 — build a validated INPUT from a user message."""
    return HermespaceInput(
        message=message or "",
        goal=goal or "",
        decision=decision or "",
        plan=list(plan or []),
        say=say or "",
        concepts=list(concepts or []),
        choices=list(choices or []),
        session_id=session_id or "default",
        agent_id=agent_id or "hermes-agent",
        force=force,
        seal=seal,
        tags=list(tags or []),
        meta=dict(meta or {}),
    ).normalized()


def run_turn(
    inp: HermespaceInput | dict[str, Any] | str,
    *,
    workflow: Workflow | None = None,
) -> HermespaceOutput:
    """Door 2 — execute Hermespace turn (desk + neural + memory)."""
    wf = workflow or get_workflow()
    if isinstance(inp, str):
        inp = encode_message(inp, force=True)
    return wf.run(inp)


def decode_for_user(out: HermespaceOutput) -> str:
    """Door 3 — string to send the human user (never dump full inject)."""
    if out.skipped:
        return ""
    return (out.report or out.agent_reply_hint() or "").strip()


def decode_for_model(out: HermespaceOutput) -> str:
    """Door 4 — context block for the model (pre_llm / next step)."""
    if out.skipped:
        return ""
    return (out.context or "").strip()


def decode_bundle(out: HermespaceOutput) -> dict[str, Any]:
    """Structured decode for agents that want both channels + meta."""
    return {
        "skipped": out.skipped,
        "reason": out.reason,
        "user_reply": decode_for_user(out),
        "model_context": decode_for_model(out),
        "decision": out.decision,
        "goal": out.goal,
        "plan": list(out.plan),
        "ready": out.ready,
        "load_level": out.load_level,
        "executive": out.executive,
        "neural": (out.meta or {}).get("neural"),
        "fabric": (out.meta or {}).get("fabric"),
        "memory_id": out.memory_id,
        "memory_path": out.memory_path,
        "session_id": out.session_id,
        "turn_id": out.turn_id,
    }


def study_memory(
    query: str,
    *,
    limit: int = 10,
    workflow: Workflow | None = None,
) -> list[dict[str, Any]]:
    """Door 5 — search prior Hermespace turns."""
    wf = workflow or get_workflow()
    return wf.study(query, limit=limit)


def history(
    *,
    session_id: str | None = None,
    limit: int = 20,
    workflow: Workflow | None = None,
) -> list[dict[str, Any]]:
    wf = workflow or get_workflow()
    return wf.history(session_id=session_id, limit=limit)


def memory_paths(workflow: Workflow | None = None) -> dict[str, str]:
    wf = workflow or get_workflow()
    return wf.memory.paths()


def quick_reply(
    message: str,
    *,
    goal: str = "",
    session_id: str = "default",
    agent_id: str = "hermes-agent",
    force: bool = True,
) -> dict[str, Any]:
    """One-shot: message in → user_reply + model_context out."""
    inp = encode_message(
        message,
        goal=goal,
        session_id=session_id,
        agent_id=agent_id,
        force=force,
    )
    # default decision/plan so desk is ready for multi-step
    if not inp.decision:
        inp.decision = "A — proceed"
    if not inp.plan:
        inp.plan = ["execute"]
    if not inp.say:
        # leave empty → decode_to_report may fill
        pass
    out = run_turn(inp)
    return decode_bundle(out)


def rank_skills(goal: str, message: str = "", limit: int = 5):
    """Rank this user's Hermes skills for a goal (inside the space)."""
    from hermespace.hermes_fabric import rank_skills_for_goal
    return [h.to_dict() for h in rank_skills_for_goal(goal, message=message, limit=limit)]


def fabric_snapshot(goal: str = "", message: str = ""):
    """MEMORY/USER excerpts + ranked skills for inject."""
    from hermespace.hermes_fabric import snapshot_fabric
    return snapshot_fabric(goal=goal, message=message).to_dict()


def remember_learning(
    content: str,
    *,
    session_id: str = "default",
    agent_id: str = "hermes-agent",
    goal: str = "",
    tags: list | None = None,
) -> str:
    """Record a learning into Hermespace study DB (does not overwrite Hermes MEMORY.md)."""
    from hermespace.memory_db import HermespaceMemory
    import uuid
    mid = str(uuid.uuid4())
    HermespaceMemory().record(
        turn_id=mid,
        session_id=session_id,
        agent_id=agent_id,
        message=goal or "learning",
        goal=goal or "learning",
        decision="seal-learning",
        report=content[:2000],
        plan=[],
        context="",
        tags=list(tags or []) + ["learning"],
        meta={"kind": "learning"},
    )
    return mid
