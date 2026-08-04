#!/usr/bin/env python3
"""Falsifiable OEW eval — paper-shaped scenarios for higher-order Hermespace.

Run:
  HERMESPACE_HOME=/tmp/oew-eval PYTHONPATH=src python3 experiments/oew_eval.py
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


def _pass(name: str, ok: bool, detail: str = "") -> dict:
    print(("PASS" if ok else "FAIL"), name, detail)
    return {"name": name, "ok": ok, "detail": detail}


def main() -> int:
    tmp = tempfile.mkdtemp(prefix="oew-eval-")
    os.environ["HERMESPACE_HOME"] = tmp
    os.environ["HERMESPACE_OEW"] = "1"

    from hermespace.desk import Desk
    from hermespace.access import AccessEnv
    from hermespace.io_contract import HermespaceInput
    from hermespace.workflow import Workflow

    results = []

    # 1) Auto-park silent on material turn
    env = AccessEnv(agent_id="eval")
    desk = Desk(goal="Multi-step math", plan=["square", "subtract"], say="Working.")
    meta = env.advance_turn(
        user_message="First square 3 then subtract 2",
        desk=desk,
        report="Working.",
        material=True,
    )
    results.append(
        _pass("auto_park", len(env.space.state.silent_steps) >= 1 and bool(meta.get("oew_ok")))
    )

    # 2) Soccer→Rugby sticky swap
    env2 = AccessEnv(agent_id="eval-swap")
    env2.space.hold("Soccer", salience=0.9)
    env2.swap("Soccer", "Rugby")
    shaped = env2.shape_user_report("Sport on mind: Soccer")
    results.append(_pass("sticky_swap", "Rugby" in shaped and "Soccer" not in shaped, shaped))

    # 3) Inject lightning → lens
    env3 = AccessEnv(agent_id="eval-inj")
    env3.inject_thought("lightning", silent=True)
    hits = " ".join(h.text for h in env3.lens(include_silent=True)).lower()
    results.append(_pass("inject_lens", "lightning" in hits))

    # 4) Ablate eval-awareness from broadcast
    env4 = AccessEnv(agent_id="eval-abl")
    env4.space.hold("fake fictional evaluation", salience=0.9)
    env4.space.hold("real task", salience=0.8)
    env4.ablate("fake", "fictional", "evaluation")
    block = env4.filtered_broadcast().lower()
    results.append(_pass("ablate_broadcast", "fake" not in block and "real task" in block))

    # 5) Reflect seeds next silent
    env5 = AccessEnv(agent_id="eval-ref")
    env5.reflect(answer="Be honest", principles=["honesty"])
    env5.advance_turn(user_message="go", material=True, report="ok")
    joined = " ".join(env5.space.state.silent_steps).lower()
    results.append(_pass("reflect_seed", "honesty" in joined or "principle" in joined))

    # 6) Full workflow dual decode
    out = Workflow().run(
        HermespaceInput(
            message="First analyze then implement finally verify",
            goal="Ship feature",
            plan=["analyze", "implement", "verify"],
            say="Shipping.",
            force=True,
            agent_id="eval-wf",
        )
    )
    results.append(
        _pass(
            "workflow_dual_decode",
            bool(out.report) and "Access Workspace" in (out.context or "") and not out.skipped,
        )
    )

    summary = {
        "pass": sum(1 for r in results if r["ok"]),
        "fail": sum(1 for r in results if not r["ok"]),
        "results": results,
        "home": tmp,
    }
    print(json.dumps(summary, indent=2))
    return 0 if summary["fail"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
