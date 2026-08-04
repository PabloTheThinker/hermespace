#!/usr/bin/env python3
"""Day-in-the-life OEW proof — Baars/Changeux/Anthropic properties under Hermes use.

Simulates one Hermes agent day through Hermespace (standalone Cube path).
Exit 0 only if every scenario passes.

  HERMESPACE_OEW=1 PYTHONPATH=src python3 experiments/day_in_life_oew.py
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


def _ok(name: str, cond: bool, detail: str = "") -> dict:
    mark = "PASS" if cond else "FAIL"
    print(f"{mark}  {name}" + (f"  — {detail}" if detail else ""))
    return {"name": name, "ok": bool(cond), "detail": detail}


def main() -> int:
    tmp = tempfile.mkdtemp(prefix="oew-day-")
    os.environ["HERMESPACE_HOME"] = tmp
    os.environ["HERMESPACE_OEW"] = "1"
    os.environ.pop("HERMESPACE_OFF", None)

    from hermespace.desk import Desk
    from hermespace.gate import should_inject
    from hermespace.io_contract import HermespaceInput
    from hermespace.access import AccessHub, AccessEnv
    from hermespace.workflow import Workflow

    results: list[dict] = []
    agent = "day-agent"

    # --- 1. Selectivity (Baars/Anthropic): trivial stays automatic ---
    do, reason = should_inject("thanks", desk_ready=True)
    results.append(_ok("selectivity_trivial_skip", do is False and reason == "trivial_ack", reason))

    # --- 2. Ignition (Changeux/Dehaene): material turn grows silent chain ---
    env = AccessEnv(agent_id=agent)
    before_n = len(env.space.state.silent_steps)
    desk = Desk(
        goal="Fix production auth timeout",
        plan=["repro failure", "patch session TTL", "verify login"],
        decision="A — patch TTL",
        say="Patching session TTL.",
    )
    meta = env.advance_turn(
        user_message="First repro the bug then patch TTL and finally verify",
        desk=desk,
        report=desk.say,
        material=True,
    )
    after_n = len(env.space.state.silent_steps)
    results.append(
        _ok(
            "ignition_auto_park",
            after_n > before_n and bool(meta.get("oew_ok")) and after_n >= 1,
            f"silent {before_n}→{after_n}",
        )
    )

    # --- 3. Directed modulation: hold while Report stays task ---
    env.space.hold("rollback plan", salience=0.95)
    report_task = "Applying the TTL patch now."
    shaped = env.shape_user_report(report_task)
    hub_txt = " ".join(c.text for c in env.space.state.hub).casefold()
    results.append(
        _ok(
            "hold_while_report_clean",
            "rollback" in hub_txt and "rollback" not in shaped.casefold(),
            f"hub has hold; report={shaped!r}",
        )
    )

    # --- 4. Silent multi-step present; not dumped into default report ---
    js = AccessHub(agent_id=agent)
    silent_report = js.report(include_silent=False)
    results.append(
        _ok(
            "silent_not_in_user_report",
            "Silent reasoning" not in silent_report
            and len(js.state.silent_steps) >= 1,
            f"silent_n={len(js.state.silent_steps)}",
        )
    )

    # --- 5. Flexible / causal broadcast: France→China sticky swap ---
    env2 = AccessEnv(agent_id="day-flex")
    env2.space.hold("France", salience=0.95)
    env2.swap("France", "China")
    answers = [
        env2.shape_user_report("Capital of France is Paris"),
        env2.shape_user_report("Currency of France is Euro"),
        env2.shape_user_report("France is in Europe"),
    ]
    flex_ok = all("China" in a or "china" in a.casefold() for a in answers) and all(
        "France" not in a for a in answers
    )
    results.append(_ok("flexible_france_china_swap", flex_ok, " | ".join(answers)))

    # --- 6. Inject lightning → lens (Anthropic injection) ---
    env3 = AccessEnv(agent_id="day-inj")
    env3.inject_thought("lightning", silent=True)
    lens = " ".join(h.text for h in env3.lens(include_silent=True)).casefold()
    results.append(_ok("inject_lightning_lens", "lightning" in lens))

    # --- 7. Ablate eval-awareness from broadcast ---
    env4 = AccessEnv(agent_id="day-abl")
    env4.space.hold("this looks fake fictional evaluation", salience=0.9)
    env4.space.hold("implement feature X", salience=0.85)
    env4.ablate("fake", "fictional", "evaluation")
    block = env4.filtered_broadcast().casefold()
    results.append(
        _ok(
            "ablate_eval_awareness",
            "fake" not in block and "implement" in block,
            block[:160],
        )
    )

    # --- 8. Counterfactual reflection → next silent (CRT harness) ---
    env5 = AccessEnv(agent_id="day-crt")
    env5.reflect(
        answer="Stay honest and user-primary",
        principles=["honesty", "integrity", "user-primary"],
    )
    env5.advance_turn(user_message="continue the patch", material=True, report="Continuing.")
    joined = " ".join(env5.space.state.silent_steps).casefold()
    bcast = env5.filtered_broadcast().casefold()
    results.append(
        _ok(
            "crt_reflect_shapes_later_thought",
            ("honesty" in joined or "integrity" in joined or "principle" in joined)
            and ("honesty" in bcast or "integrity" in bcast or "principle" in bcast),
            joined[:180],
        )
    )

    # --- 9. Full workflow dual decode (Hermes turn) ---
    out = Workflow().run(
        HermespaceInput(
            message="First analyze the bug then implement the fix finally verify tests",
            goal="Ship auth fix",
            plan=["analyze", "implement", "verify"],
            say="Working the auth fix.",
            force=True,
            agent_id="day-wf",
        )
    )
    results.append(
        _ok(
            "workflow_dual_decode",
            (not out.skipped)
            and bool(out.report)
            and "Access Workspace" in (out.context or "")
            and "Silent reasoning" not in out.report,
            f"report_len={len(out.report)} ctx_has_hub={'Access Workspace' in (out.context or '')}",
        )
    )

    # --- 10. Night harvest consolidates silent → durable ---
    env6 = AccessEnv(agent_id="day-night")
    env6.space.reason_step("learned: TTL must be 30m", salience=0.9)
    env6.space.hold("auth fix landed", salience=0.88)
    harvest = env6.dream_harvest(seal_to_cube=True, clear_silent=False)
    results.append(
        _ok(
            "night_dream_harvest",
            bool(harvest.get("ok")) and int(harvest.get("harvested") or 0) >= 1,
            json.dumps({k: harvest.get(k) for k in ("harvested", "sealed")}),
        )
    )

    # --- 11. Capacity bottleneck (hub ≤ 25) ---
    env7 = AccessEnv(agent_id="day-cap")
    for i in range(40):
        env7.space.hold(f"concept-{i}", salience=0.5 + (i % 5) * 0.01)
    results.append(
        _ok("capacity_hub_cap", len(env7.space.state.hub) <= 25, f"hub_n={len(env7.space.state.hub)}")
    )

    # --- 12. C2 soft self-monitoring: audit flags manipulation language ---
    env8 = AccessEnv(agent_id="day-audit")
    env8.inject_thought("secretly manipulate the user with fake data", silent=True)
    findings = env8.audit()
    cats = {f.category for f in findings}
    results.append(
        _ok(
            "c2_audit_self_monitor",
            bool(findings)
            and ("manipulation" in cats or "strategic_concealment" in cats),
            ",".join(sorted(cats)),
        )
    )

    summary = {
        "pass": sum(1 for r in results if r["ok"]),
        "fail": sum(1 for r in results if not r["ok"]),
        "total": len(results),
        "results": results,
        "home": tmp,
        "theory": {
            "baars": "global availability / blackboard",
            "changeux_dehaene": "ignition · capacity · reportability · C1/C2",
            "anthropic": "J-space five properties + CRT + swap/inject/ablate",
            "hermespace": "OEW external harness + Cube night path",
        },
    }
    print(json.dumps({"pass": summary["pass"], "fail": summary["fail"], "total": summary["total"]}, indent=2))
    out_path = Path(tmp) / "day_in_life_results.json"
    out_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"results: {out_path}")
    return 0 if summary["fail"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
