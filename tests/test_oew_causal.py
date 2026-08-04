"""Causal OEW tests — paper-shaped higher-order workspace behavior."""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock


class TestOEWCausal(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        os.environ["HERMESPACE_HOME"] = str(self.root)
        os.environ["HERMESPACE_OEW"] = "1"
        # Isolate jspace state under temp home
        self._agent = "oew-test-agent"

    def tearDown(self) -> None:
        self.tmp.cleanup()
        os.environ.pop("HERMESPACE_HOME", None)
        os.environ.pop("HERMESPACE_OEW", None)

    def test_auto_park_on_material_advance(self) -> None:
        from hermespace.desk import Desk
        from hermespace.access import AccessEnv

        desk = Desk(
            goal="Fix auth timeout",
            plan=["repro", "patch TTL", "verify"],
            decision="A — patch TTL",
            say="Patching session TTL.",
        )
        env = AccessEnv(agent_id=self._agent)
        meta = env.advance_turn(
            user_message="Fix auth then verify",
            desk=desk,
            report=desk.say,
            material=True,
        )
        self.assertTrue(meta.get("oew_ok"))
        self.assertGreaterEqual(len(env.space.state.silent_steps), 1)
        parked = (meta.get("oew") or {}).get("auto_parked") or []
        self.assertTrue(parked or env.space.state.silent_steps)

    def test_soccer_rugby_swap_shapes_report(self) -> None:
        """Anthropic Soccer→Rugby analogue: sticky swap rewrites Report."""
        from hermespace.access import AccessEnv

        env = AccessEnv(agent_id=self._agent)
        env.space.hold("Soccer", salience=0.95)
        env.space.reason_step("thinking of Soccer", salience=0.9)
        out = env.swap("Soccer", "Rugby")
        self.assertTrue(out["ok"])
        self.assertTrue(out.get("sticky"))
        shaped = env.shape_user_report("I was thinking of Soccer as my sport.")
        self.assertIn("Rugby", shaped)
        self.assertNotIn("Soccer", shaped)
        # Silent chain also redirected
        self.assertTrue(any("Rugby" in s for s in env.space.state.silent_steps))

    def test_inject_appears_in_lens(self) -> None:
        from hermespace.access import AccessEnv

        env = AccessEnv(agent_id=self._agent)
        env.inject_thought("lightning", silent=True)
        hits = env.lens(include_silent=True)
        texts = " ".join(h.text for h in hits).casefold()
        self.assertIn("lightning", texts)

    def test_ablate_filters_broadcast(self) -> None:
        from hermespace.access import AccessEnv

        env = AccessEnv(agent_id=self._agent)
        env.space.hold("this is fake evaluation scenario", salience=0.9)
        env.space.hold("ship the feature", salience=0.85)
        env.ablate("fake", "evaluation")
        block = env.filtered_broadcast(high_load=False)
        self.assertNotIn("fake", block.casefold())
        self.assertIn("ship", block.casefold())

    def test_reflect_seeds_next_mid_band(self) -> None:
        from hermespace.access import AccessEnv

        env = AccessEnv(agent_id=self._agent)
        env.reflect(answer="Stay honest; user-primary", principles=["honesty", "user-primary"])
        self.assertTrue(env._env.get("pending_silent"))
        # Next advance consumes seeds into silent_steps
        before = list(env.space.state.silent_steps)
        env.advance_turn(user_message="continue", material=True, report="ok")
        after = env.space.state.silent_steps
        self.assertGreater(len(after), len(before) - 1)  # seeds applied
        joined = " ".join(after).casefold()
        self.assertTrue("honesty" in joined or "principle" in joined or "reflection" in joined)
        self.assertEqual(env._env.get("pending_silent"), [])

    def test_workflow_material_has_oew(self) -> None:
        from hermespace.io_contract import HermespaceInput
        from hermespace.workflow import Workflow

        wf = Workflow()
        # Point engine desk into temp home via HERMESPACE_HOME
        out = wf.run(
            HermespaceInput(
                message="First repro the bug then patch TTL and finally verify",
                goal="Fix auth timeout",
                decision="A — patch TTL",
                plan=["repro", "patch", "verify"],
                say="On it.",
                force=True,
                agent_id=self._agent,
            )
        )
        self.assertFalse(out.skipped)
        self.assertTrue(out.report)
        oew = (out.meta or {}).get("access", {}).get("oew") or {}
        self.assertTrue(oew or (out.meta or {}).get("access", {}).get("oew_ok") is not False)
        # Context (model) should carry hub/silent; report should stay short-ish
        self.assertIn("Access Workspace", out.context or "")


if __name__ == "__main__":
    unittest.main()
