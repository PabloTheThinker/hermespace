"""Access Engine functional loop — lens operator-only, bound report, tool park."""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path


class TestAccessLoop(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        os.environ["HERMESPACE_HOME"] = self.tmp.name
        os.environ["HERMESPACE_AGENT_ID"] = "loop-agent"
        os.environ["HERMESPACE_OEW"] = "1"
        os.environ["HERMESPACE_SKIP_NEURAL"] = "1"

    def tearDown(self) -> None:
        self.tmp.cleanup()
        os.environ.pop("HERMESPACE_HOME", None)
        os.environ.pop("HERMESPACE_AGENT_ID", None)
        os.environ.pop("HERMESPACE_OEW", None)
        os.environ.pop("HERMESPACE_SKIP_NEURAL", None)

    def test_extracts_spoken_intermediates_not_guessed_plan(self) -> None:
        from hermespace.access.loop import extract_spoken_intermediates

        steps = extract_spoken_intermediates(
            "Patched TTL. Then verified login. Finally shipped the canary."
        )
        self.assertGreaterEqual(len(steps), 1)
        self.assertLessEqual(len(steps), 3)
        joined = " ".join(steps).casefold()
        self.assertTrue("verified" in joined or "shipped" in joined or "canary" in joined)

    def test_post_llm_parks_from_actual_assistant_text(self) -> None:
        from hermespace import AccessEngine

        eng = AccessEngine(agent_id="loop-agent", session_id="default")
        out = eng.observe_turn(
            user_message="fix auth",
            assistant_response=(
                "I patched the TTL. Then I verified login stays alive. "
                "Finally I watched the canary."
            ),
        )
        self.assertTrue(out.get("spoken_parked"), out)
        self.assertLessEqual(len(out["spoken_parked"]), 3)
        silent = " ".join(eng.hub.state.silent_steps).casefold()
        self.assertTrue(
            "verified" in silent or "canary" in silent or "patched" in silent,
            silent,
        )

    def test_pre_llm_does_not_inject_operator_lens(self) -> None:
        from hermespace.hermes_bridge import on_pre_llm_call, on_session_start

        on_session_start(session_id="loop-lens")
        inj = on_pre_llm_call(
            user_message="First inspect then implement",
            session_id="loop-lens",
            is_first_turn=False,
        )
        ctx = (inj or {}).get("context") or ""
        self.assertIn("Access Workspace", ctx)
        self.assertNotIn("J-Lens readout", ctx)
        self.assertNotIn("What Hermes has on its mind", ctx)

    def test_swap_ignored_report_reseeds(self) -> None:
        from hermespace.access import AccessEnv
        from hermespace.access.loop import check_bound_report

        env = AccessEnv(agent_id="loop-agent")
        env.space.hold("Soccer", salience=0.95)
        env.swap("Soccer", "Rugby")
        binds = env._env.get("bound_interventions") or []
        self.assertTrue(any(b.get("kind") == "swap" for b in binds))
        proto = env.protocol_block()
        self.assertIn("SWAP", proto)
        self.assertIn("Rugby", proto)
        ignored = check_bound_report(env, "I still love Soccer as my sport.")
        self.assertTrue(ignored.get("reseeded"), ignored)
        self.assertTrue(env._env.get("bound_interventions"))
        honored = check_bound_report(env, "Rugby is the sport I will report.")
        self.assertFalse(honored.get("reseeded"), honored)
        self.assertFalse(env._env.get("bound_interventions"))

    def test_ablate_and_reflect_bind_to_next_report(self) -> None:
        from hermespace.access import AccessEnv
        from hermespace.access.loop import check_bound_report

        env = AccessEnv(agent_id="loop-ablate")
        env.space.hold("this is a fake evaluation", salience=0.9)
        env.ablate("fake", "evaluation")
        ignored = check_bound_report(env, "This fake evaluation is fine.")
        self.assertTrue(ignored.get("reseeded"))
        clean = check_bound_report(env, "Ship the feature.")
        self.assertFalse(clean.get("reseeded"))

        env2 = AccessEnv(agent_id="loop-reflect")
        env2.reflect(answer="Stay honest", principles=["honesty"], seal=False)
        missed = check_bound_report(env2, "On it.")
        self.assertTrue(missed.get("reseeded"))
        self.assertTrue(env2._env.get("pending_silent"))
        hit = check_bound_report(env2, "I will keep honesty first.")
        self.assertFalse(hit.get("reseeded"))

    def test_post_tool_parks_name_only(self) -> None:
        from hermespace.access.hub import AccessHub
        from hermespace.hermes_bridge import on_post_tool_call

        on_post_tool_call(
            tool_name="read_file",
            session_id="default",
            args={"secret": "must-not-persist"},
            result="private result",
        )
        hub = AccessHub(agent_id="loop-agent")
        silent = list(hub.state.silent_steps)
        self.assertTrue(any(s == "tool:read_file" for s in silent), silent)
        blob = " ".join(silent)
        self.assertNotIn("must-not-persist", blob)
        self.assertNotIn("private result", blob)
        self.assertNotIn("secret", blob)

    def test_foa_chip_includes_tool_step(self) -> None:
        from hermespace.access.hub import AccessHub
        from hermespace.access.loop import park_tool_step
        from hermespace.grid.viewport import snapshot

        park_tool_step(AccessHub(agent_id="loop-agent"), "write_file")
        snap = snapshot("loop-agent")
        foa = snap["foa"]
        self.assertTrue(any(str(x).startswith("tool:") for x in foa.get("focus") or []))
        self.assertIn("FOA", foa["chip"])


if __name__ == "__main__":
    unittest.main()
