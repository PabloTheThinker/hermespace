from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


class TestPulse(unittest.TestCase):
    def setUp(self) -> None:
        self._td = tempfile.TemporaryDirectory(prefix="hs-pulse-")
        os.environ["HERMESPACE_HOME"] = self._td.name
        os.environ["HERMESPACE_AUTONOMY"] = "0"

    def tearDown(self) -> None:
        self._td.cleanup()

    def test_defaults_and_tick(self) -> None:
        from hermespace import pulse

        jobs = pulse.ensure_defaults("default")
        self.assertGreaterEqual(len(jobs), 4)
        ids = {j.id for j in jobs}
        self.assertIn("idle_maintain", ids)
        self.assertIn("dream_cycle", ids)

        # first tick should run due never_run jobs (conditions may skip some)
        summary = pulse.tick(agent_id="default")
        self.assertIn("ran", summary)
        self.assertIn("skipped", summary)
        self.assertEqual(summary["ran"] + summary["skipped"] + summary["errors"], summary["jobs"])

    def test_force_run_viewport(self) -> None:
        from hermespace import pulse

        pulse.ensure_defaults()
        j = pulse.get_job("viewport_refresh")
        self.assertIsNotNone(j)
        out = pulse.run_job(j, force=True)  # type: ignore[arg-type]
        self.assertTrue(out.get("ok"), out)
        html = Path(os.environ["HERMESPACE_HOME"]) / "viewport" / "index.html"
        self.assertTrue(html.is_file())

    def test_disable_skips(self) -> None:
        from hermespace import pulse

        pulse.ensure_defaults()
        pulse.set_enabled("dream_cycle", False)
        j = pulse.get_job("dream_cycle")
        assert j is not None
        due, why = pulse.job_due(j)
        self.assertFalse(due)
        self.assertEqual(why, "disabled")

    def test_coalesce_not_due_twice(self) -> None:
        from hermespace import pulse

        pulse.ensure_defaults()
        j = pulse.get_job("viewport_refresh")
        assert j is not None
        j.every_sec = 3600
        out1 = pulse.run_job(j, force=True)
        self.assertTrue(out1["ok"])
        j2 = pulse.get_job("viewport_refresh")
        assert j2 is not None
        due, why = pulse.job_due(j2)
        self.assertFalse(due)
        self.assertTrue(why.startswith("wait_") or why == "wait_3600s" or "wait_" in why)

    def test_daemon_max_ticks(self) -> None:
        from hermespace import pulse

        # should return after 1 tick
        pulse.daemon_loop(interval_sec=5, max_ticks=1)


if __name__ == "__main__":
    unittest.main()
