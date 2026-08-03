"""HermesBase facade — Hermes base as functional J-space."""

from __future__ import annotations

import os
import tempfile
import unittest


class TestHermesBase(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        os.environ["HERMESPACE_HOME"] = self.tmp.name
        os.environ["HERMESPACE_OEW"] = "1"

    def tearDown(self) -> None:
        self.tmp.cleanup()
        os.environ.pop("HERMESPACE_HOME", None)
        os.environ.pop("HERMESPACE_OEW", None)

    def test_status_ready(self) -> None:
        from hermespace import HermesBase

        st = HermesBase(agent_id="base-test").status()
        self.assertTrue(st["oew_enabled"])
        self.assertTrue(st["ready"])
        self.assertIn("read/lens", st["video_ops"])

    def test_think_ignites(self) -> None:
        from hermespace import HermesBase

        hb = HermesBase(agent_id="base-think")
        out = hb.think(
            "First analyze then implement finally verify",
            goal="Ship feature",
            say="On it.",
        )
        self.assertFalse(out["skipped"])
        self.assertTrue(out["has_jspace_broadcast"])
        self.assertTrue(out.get("report"))

    def test_video_ops_chain(self) -> None:
        from hermespace import HermesBase

        hb = HermesBase(agent_id="base-ops")
        hb.hold("rollback")
        hb.inject("lightning", silent=True)
        hb.swap("rollback", "canary")
        hb.reflect(answer="Stay honest", principles=["honesty"])
        lens = hb.lens().casefold()
        self.assertTrue("lightning" in lens or "canary" in lens or "honesty" in lens)
        findings = hb.audit()
        self.assertIsInstance(findings, list)
        harvest = hb.harvest()
        self.assertTrue(harvest.get("ok"))


if __name__ == "__main__":
    unittest.main()
