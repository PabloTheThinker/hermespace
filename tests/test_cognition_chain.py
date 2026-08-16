"""Two-turn silent chain + live-goal refresh. Hub already keeps T1 silent."""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
import sys

sys.path.insert(0, str(ROOT / "src"))

T1 = "Write a short README for the auth fix, then stop."
T2 = "Now write the install section."


class TestSilentChainInject(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        os.environ["HERMESPACE_HOME"] = self.tmp.name
        os.environ["HERMESPACE_AGENT_ID"] = "chain-agent"
        os.environ["HERMESPACE_SKIP_NEURAL"] = "1"
        os.environ["HERMESPACE_NEURAL_VERBALIZE"] = "0"
        os.environ["HERMESPACE_OEW"] = "1"

    def tearDown(self) -> None:
        self.tmp.cleanup()
        for key in (
            "HERMESPACE_HOME",
            "HERMESPACE_AGENT_ID",
            "HERMESPACE_SKIP_NEURAL",
            "HERMESPACE_NEURAL_VERBALIZE",
            "HERMESPACE_OEW",
        ):
            os.environ.pop(key, None)

    def _hub(self, session_id: str = "chain"):
        from hermespace.access import AccessHub
        from hermespace.access.engine import workspace_id

        return AccessHub(agent_id=workspace_id("chain-agent", session_id))

    def test_message_is_new_goal(self) -> None:
        from hermespace.execute_focus import message_is_new_goal

        self.assertTrue(message_is_new_goal(T2, T1))
        self.assertFalse(message_is_new_goal(T1, T1))
        self.assertFalse(
            message_is_new_goal("Write a short README for the auth fix", T1)
        )
        self.assertFalse(message_is_new_goal("", T1))
        self.assertFalse(message_is_new_goal(T2, ""))

    def test_t2_inject_carries_t1_parked_silent(self) -> None:
        from hermespace.io_contract import HermespaceInput
        from hermespace.workflow import Workflow

        wf = Workflow()
        sid = "chain"
        t1 = wf.run(
            HermespaceInput(
                message=T1,
                say="",
                goal="",
                plan=[],
                session_id=sid,
                agent_id="chain-agent",
            )
        )
        self.assertFalse(t1.skipped, t1.reason)
        self.assertEqual((t1.report or "").splitlines()[0].strip(), "Write the README")
        self.assertEqual(
            list(t1.plan or []),
            ["Write a short README for the auth fix", "Stop"],
        )
        parked = [str(s) for s in self._hub(sid).state.silent_steps if str(s).strip()]
        self.assertTrue(parked, "T1 must park silent on the hub")
        parked_l = " ".join(parked).casefold()
        self.assertTrue(
            "stop" in parked_l or "readme" in parked_l,
            parked,
        )

        t2 = wf.run(
            HermespaceInput(
                message=T2,
                say="",
                goal="",
                plan=[],
                session_id=sid,
                agent_id="chain-agent",
            )
        )
        self.assertFalse(t2.skipped, t2.reason)
        line1 = (t2.report or "").splitlines()[0].strip()
        self.assertNotEqual(line1, "Write the README")
        self.assertIn("install", line1.casefold())
        self.assertEqual(line1, "Write the install section")
        self.assertEqual(list(t2.plan or []), ["Write the install section"])
        ctx = t2.context or ""
        self.assertLessEqual(len(ctx), 2800)
        self.assertIn("### Silent (prior)", ctx)
        self.assertIn("plan: Stop", ctx)
        self.assertNotIn("J-Lens readout", ctx)
        self.assertNotIn("What Hermes has on its mind", ctx)
        silent_body = ctx.split("### Silent (prior)", 1)[-1]
        self.assertIn("Stop", silent_body)
        self.assertNotIn(T2, silent_body)

        thanks = wf.run(
            HermespaceInput(
                message="thanks",
                session_id=sid,
                agent_id="chain-agent",
            )
        )
        self.assertTrue(thanks.skipped)
        self.assertEqual(thanks.reason, "trivial_ack")
        after = [str(s) for s in self._hub(sid).state.silent_steps if str(s).strip()]
        self.assertTrue(after, "thanks must not wipe T1 silent")
        self.assertTrue(
            any("stop" in s.casefold() or "readme" in s.casefold() for s in after),
            after,
        )


if __name__ == "__main__":
    unittest.main()
