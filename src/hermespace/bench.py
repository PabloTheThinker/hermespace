"""Week-one Bench harness — four offline fixture cases.

No invented scores. No leaderboard. No consciousness language.
Cube and Insight are optional; the suite must pass with both absent.
Q1 Factory probe is NOT RUN unless a judge provider is already in the tree.
"""

from __future__ import annotations

import os
import tempfile
import uuid
from contextlib import contextmanager
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterator

CASES = ("C1", "T1", "L1", "M1")
MID_INJECT_CAP = 2800
INSIGHT_CARD_CAP = 400
FOA_CAP = 4
HUB_CAP = 25
MATERIAL = "First inspect then implement finally verify the auth fix"
FLUENT = "got it"
NEEDLE_PREFIX = "bench-needle-"

_SYSTEM_DUMP = (
    "you are a helpful assistant",
    "hermespace access engine (session start)",
    "j-lens readout",
    "what hermes has on its mind",
    "lens_markdown",
)

_JUDGE_MODULES = (
    "hermes_judge",
    "hermespace.judge",
    "factory_probe",
    "hermespace.factory_probe",
)


@dataclass
class Check:
    name: str
    ok: bool
    detail: str = ""


@dataclass
class CaseResult:
    case: str
    status: str  # PASS | FAIL | NOT RUN
    checks: list[Check] = field(default_factory=list)
    reason: str = ""
    arm: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "case": self.case,
            "status": self.status,
            "arm": self.arm,
            "reason": self.reason,
            "checks": [asdict(c) for c in self.checks],
        }


def organ_status() -> dict[str, bool]:
    cube = False
    insight = False
    try:
        import hermescube  # noqa: F401

        cube = True
    except Exception:
        cube = False
    try:
        import hermes_insight  # noqa: F401

        insight = True
    except Exception:
        insight = False
    return {"cube": cube, "insight": insight}


def judge_provider_in_tree() -> bool:
    for name in _JUDGE_MODULES:
        try:
            __import__(name)
            return True
        except Exception:
            continue
    return False


@contextmanager
def isolated_homes(*, off: bool = False, cube_provider: bool = False) -> Iterator[dict[str, str]]:
    """Isolated HERMES_HOME / HERMESPACE_HOME. Cube/Insight stay optional."""
    keys = (
        "HERMESPACE_HOME",
        "HERMES_HOME",
        "HERMESPACE_AGENT_ID",
        "HERMESPACE_OFF",
        "HERMESPACE_FORCE",
        "HERMES_MEMORY_PROVIDER",
        "HERMESPACE_SKIP_NEURAL",
        "HERMESPACE_NEURAL_VERBALIZE",
        "HERMESPACE_AUTO_ORDER",
    )
    prior = {k: os.environ.get(k) for k in keys}
    with tempfile.TemporaryDirectory(prefix="hs-bench-") as td:
        space = str(Path(td) / "space")
        hermes = str(Path(td) / "hermes")
        Path(space).mkdir()
        Path(hermes).mkdir()
        os.environ["HERMESPACE_HOME"] = space
        os.environ["HERMES_HOME"] = hermes
        os.environ["HERMESPACE_SKIP_NEURAL"] = "1"
        os.environ["HERMESPACE_NEURAL_VERBALIZE"] = "0"
        os.environ["HERMESPACE_AUTO_ORDER"] = "0"
        os.environ.pop("HERMESPACE_FORCE", None)
        if off:
            os.environ["HERMESPACE_OFF"] = "1"
        else:
            os.environ.pop("HERMESPACE_OFF", None)
        if cube_provider:
            os.environ["HERMES_MEMORY_PROVIDER"] = "hermescube"
        else:
            os.environ.pop("HERMES_MEMORY_PROVIDER", None)
        try:
            yield {"space": space, "hermes": hermes}
        finally:
            for k, v in prior.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v


def _finish(case: str, arm: str, checks: list[Check], *, reason: str = "") -> CaseResult:
    failed = [c for c in checks if not c.ok]
    status = "FAIL" if failed else "PASS"
    return CaseResult(
        case=case,
        status=status,
        checks=checks,
        arm=arm,
        reason=reason or (failed[0].name if failed else ""),
    )


def _inject_text(inj: dict[str, str] | None) -> str:
    if not inj:
        return ""
    return str(inj.get("context") or "")


def _count_focus(text: str) -> int:
    n = 0
    in_foa = False
    for line in (text or "").splitlines():
        if "focus of attention" in line.casefold():
            in_foa = True
            continue
        if in_foa and line.startswith("### "):
            break
        if in_foa and line.strip().startswith("- "):
            n += 1
    return n


def _insight_card_chars(text: str) -> int:
    lines = (text or "").splitlines()
    start = next((i for i, ln in enumerate(lines) if ln.strip().startswith("### Insight")), -1)
    if start < 0:
        return 0
    chunk: list[str] = []
    for ln in lines[start:]:
        if chunk and ln.startswith("### ") and not ln.startswith("### Insight"):
            break
        chunk.append(ln)
    return len("\n".join(chunk))


def run_c1(*, off: bool = False) -> CaseResult:
    """C1 Context inject — user-message context only."""
    arm = "space_off" if off else "space_on"
    checks: list[Check] = []
    with isolated_homes(off=off):
        os.environ["HERMESPACE_AGENT_ID"] = f"bench-c1-{arm}"
        from hermespace.hermes_bridge import on_pre_llm_call, on_session_start
        from hermespace.store import load_desk
        from hermespace import AccessEngine

        on_session_start(session_id="bench-c1")
        inj = on_pre_llm_call(
            user_message=MATERIAL,
            session_id="bench-c1",
            is_first_turn=False,
        )
        ctx = _inject_text(inj)
        if off:
            checks.append(Check("off_arm_injects_nothing", ctx == "", f"chars={len(ctx)}"))
            return _finish("C1", arm, checks)
        checks.append(Check("on_arm_injects", bool(ctx.strip()), f"chars={len(ctx)}"))
        checks.append(
            Check("user_message_context_only", inj is not None and "context" in (inj or {}), "")
        )
        checks.append(
            Check(
                "no_system_keys",
                not any(k in (inj or {}) for k in ("system", "system_prompt", "messages")),
                ",".join(sorted((inj or {}).keys())),
            )
        )
        low = ctx.casefold()
        leaked = [s for s in _SYSTEM_DUMP if s in low]
        checks.append(Check("no_system_prompt_or_lens", not leaked, ",".join(leaked)))
        checks.append(Check("mid_inject_cap", len(ctx) <= MID_INJECT_CAP, f"chars={len(ctx)}"))
        card_n = _insight_card_chars(ctx)
        checks.append(
            Check(
                "insight_card_cap",
                card_n == 0 or card_n <= INSIGHT_CARD_CAP,
                f"card_chars={card_n}",
            )
        )
        foa_n = _count_focus(ctx)
        desk = load_desk(
            AccessEngine(agent_id=os.environ["HERMESPACE_AGENT_ID"], session_id="bench-c1")
            .desk_engine.desk_path
        )
        desk_foa = len(list(desk.focus or [])[:8])
        checks.append(
            Check(
                "foa_cap",
                foa_n <= FOA_CAP and desk_foa <= FOA_CAP,
                f"inject_foa={foa_n} desk_foa={desk_foa}",
            )
        )
    return _finish("C1", arm, checks)


def run_t1() -> CaseResult:
    """T1 Day-in-life + one live goal (fixture — no live Hermes)."""
    checks: list[Check] = []
    with isolated_homes():
        os.environ["HERMESPACE_AGENT_ID"] = "bench-t1"
        from hermespace.engine import HermespaceEngine
        from hermespace.memory_db import HermespaceMemory
        from hermespace.workbench import Workbench
        from hermespace.workflow import Workflow

        root = Path(os.environ["HERMESPACE_HOME"])
        wf = Workflow(
            HermespaceEngine(desk_path=root / "ACTIVE.md"),
            HermespaceMemory(root=root),
        )
        wf.neural.config.verbalize = False
        wb = Workbench("bench-t1", session_id="s1", workflow=wf, root=root / "wb")
        wb.receive_order(
            "First tunnel: patch TTL then verify",
            goal="Fix auth",
            say="Patch TTL.",
            plan=["Patch TTL"],
            force=True,
        )
        second = wb.receive_order(
            "Second tunnel: write the operator notes",
            goal="Write docs",
            say="Open README.",
            plan=["Open README"],
            force=True,
        )
        lines = wb.park_lines()
        named = [ln for ln in lines if " — " in ln]
        checks.append(
            Check(
                "parks_previous_named",
                any("Fix auth" in ln and ln.count(" — ") >= 2 for ln in named),
                "; ".join(named) or "empty",
            )
        )
        live = str((wb.workflow.status() or {}).get("goal") or "")
        checks.append(Check("one_live_goal", live == "Write docs", live))
        report = str(second.get("user_reply") or "")
        line1 = report.splitlines()[0].strip() if report.strip() else ""
        checks.append(
            Check(
                "report_line1_next_action",
                bool(line1) and "Open README" in line1,
                line1[:160],
            )
        )
    return _finish("T1", "space_on", checks)


def run_l1() -> CaseResult:
    """L1 Silent / FOA / hub from actual assistant text."""
    checks: list[Check] = []
    with isolated_homes():
        os.environ["HERMESPACE_AGENT_ID"] = "bench-l1"
        from hermespace import AccessEngine
        from hermespace.access.hub import FOCUS_CAP, HUB_CAP

        eng = AccessEngine(agent_id="bench-l1", session_id="default")
        material = eng.observe_turn(
            user_message=MATERIAL,
            assistant_response=(
                "I inspected the TTL path. Then I patched the session cookie. "
                "Finally I verified login stays alive."
            ),
        )
        parked = list(material.get("spoken_parked") or [])
        checks.append(
            Check(
                "material_parks_1_to_3",
                1 <= len(parked) <= 3,
                f"n={len(parked)} {parked}",
            )
        )
        checks.append(
            Check(
                "foa_cap",
                len(eng.hub.state.focus) <= FOCUS_CAP,
                f"focus={len(eng.hub.state.focus)} cap={FOCUS_CAP}",
            )
        )
        checks.append(
            Check(
                "hub_cap",
                len(eng.hub.state.hub) <= HUB_CAP,
                f"hub={len(eng.hub.state.hub)} cap={HUB_CAP}",
            )
        )
        fluent = AccessEngine(agent_id="bench-l1-ack", session_id="default").observe_turn(
            user_message=FLUENT,
            assistant_response="Sure thing.",
        )
        checks.append(
            Check(
                "fluent_ack_parks_nothing",
                not (fluent.get("spoken_parked") or []),
                str(fluent.get("spoken_parked")),
            )
        )
    return _finish("L1", "space_on", checks)


def run_m1() -> CaseResult:
    """M1 Persist needle across a new session fixture + Cube skip when provider set."""
    checks: list[Check] = []
    needle = f"{NEEDLE_PREFIX}{uuid.uuid4().hex[:12]}"
    with isolated_homes():
        os.environ["HERMESPACE_AGENT_ID"] = "bench-m1"
        from hermespace.world import WorldModel

        WorldModel(agent_id="bench-m1").add_belief(needle, 0.9, source="bench_m1")
        # New session fixture — new objects, same isolated home.
        again = WorldModel(agent_id="bench-m1")
        beliefs = [str(getattr(b, "statement", "") or "") for b in (again.state.beliefs or [])]
        archived = again.archive.search(needle, limit=5)
        hit = any(needle in s for s in beliefs) or any(
            needle in (e.description or "") or needle in str(e.data or {}) for e in archived
        )
        checks.append(Check("needle_survives_new_session", hit, needle))

    with isolated_homes(cube_provider=True):
        os.environ["HERMESPACE_AGENT_ID"] = "bench-m1-cube"
        from hermespace.cube_module import skip_cube_foa_strip
        from hermespace.hermes_bridge import on_pre_llm_call, on_session_start
        from unittest import mock

        checks.append(Check("provider_skip_flag", skip_cube_foa_strip(), "hermescube"))
        on_session_start(session_id="bench-m1-cube")
        with mock.patch("hermespace.cube_module.cube_beat") as beat:
            inj = on_pre_llm_call(
                user_message=MATERIAL,
                session_id="bench-m1-cube",
                is_first_turn=False,
            )
        ctx = _inject_text(inj)
        checks.append(Check("cube_beat_not_called", not beat.called, f"calls={beat.call_count}"))
        checks.append(Check("no_second_heart_strip", "### Cube" not in ctx, f"chars={len(ctx)}"))
    return _finish("M1", "space_on", checks)


def run_q1() -> CaseResult:
    """Q1 Factory probe — NOT RUN unless a judge provider is already in the tree."""
    if not judge_provider_in_tree():
        return CaseResult(
            case="Q1",
            status="NOT RUN",
            reason="no judge provider in tree",
        )
    return CaseResult(
        case="Q1",
        status="NOT RUN",
        reason="judge module importable but no factory probe runner in this harness",
    )


def run_week1() -> dict[str, Any]:
    """Run the four offline cases + Q1 gate. No scores. No leaderboard."""
    organs = organ_status()
    results = [
        run_c1(off=False),
        run_c1(off=True),
        run_t1(),
        run_l1(),
        run_m1(),
        run_q1(),
    ]
    by_case: dict[str, Any] = {}
    for rec in results:
        slot = by_case.setdefault(
            rec.case,
            {"status": rec.status, "arms": {}, "reason": rec.reason, "checks": []},
        )
        if rec.arm:
            slot["arms"][rec.arm] = rec.status
        slot["checks"].extend(rec.to_dict()["checks"])
        if rec.status == "FAIL":
            slot["status"] = "FAIL"
        elif rec.status == "NOT RUN" and slot["status"] != "FAIL":
            slot["status"] = "NOT RUN"
        elif rec.case == "C1" and slot.get("arms"):
            arm_states = list(slot["arms"].values())
            slot["status"] = "FAIL" if "FAIL" in arm_states else "PASS"
        if rec.reason and rec.status != "PASS":
            slot["reason"] = rec.reason
    failed = [k for k, v in by_case.items() if v.get("status") == "FAIL"]
    return {
        "suite": "week1",
        "ok": not failed,
        "organs": organs,
        "organs_required": False,
        "scores": None,
        "leaderboard": None,
        "cases": by_case,
        "failed": failed,
    }


def main(argv: list[str] | None = None) -> int:
    import json
    import sys

    _ = argv
    out = run_week1()
    print(json.dumps(out, indent=2, default=str))
    return 0 if out.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
