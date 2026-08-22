"""Week-one Bench — fixture cases only. No invented scores."""

from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


class TestWeek1Bench(unittest.TestCase):
    def test_suite_four_offline_cases(self) -> None:
        from hermespace.bench import judge_provider_in_tree, organ_status, run_week1

        organs = organ_status()
        self.assertFalse(organs.get("required", False) if isinstance(organs, dict) else False)
        out = run_week1()
        self.assertIsNone(out.get("scores"))
        self.assertIsNone(out.get("leaderboard"))
        cases = out.get("cases") or {}
        for key in ("C1", "T1", "L1", "M1"):
            self.assertIn(key, cases)
            self.assertEqual(cases[key]["status"], "PASS", cases[key])
        self.assertEqual(cases["Q1"]["status"], "NOT RUN")
        if not judge_provider_in_tree():
            self.assertIn("no judge provider", cases["Q1"].get("reason") or "")
        self.assertTrue(out.get("ok"), out.get("failed"))
        self.assertEqual(cases["C1"]["arms"].get("space_off"), "PASS")
        self.assertEqual(cases["C1"]["arms"].get("space_on"), "PASS")

    def test_fluent_ack_parks_nothing(self) -> None:
        from hermespace import AccessEngine

        with self._home():
            os.environ["HERMESPACE_AGENT_ID"] = "bench-ack"
            out = AccessEngine(agent_id="bench-ack").observe_turn(
                user_message="got it",
                assistant_response="Sure thing.",
            )
            self.assertFalse(out.get("spoken_parked"))

    def _home(self):
        import tempfile
        from contextlib import contextmanager

        @contextmanager
        def _ctx():
            td = tempfile.TemporaryDirectory()
            old = os.environ.get("HERMESPACE_HOME")
            os.environ["HERMESPACE_HOME"] = td.name
            try:
                yield
            finally:
                if old is None:
                    os.environ.pop("HERMESPACE_HOME", None)
                else:
                    os.environ["HERMESPACE_HOME"] = old
                td.cleanup()

        return _ctx()


if __name__ == "__main__":
    unittest.main()
