from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


class TestWorldLandmarks(unittest.TestCase):
    def test_leave_does_not_add_session_ended_landmark(self):
        with tempfile.TemporaryDirectory() as td:
            os.environ["HERMESPACE_HOME"] = td
            from hermespace.world import WorldModel

            wm = WorldModel(agent_id="landmark-test")
            wm.enter()
            wm.leave("session ended")
            self.assertFalse(any("session ended" in lm.lower() for lm in wm.state.landmarks))

    def test_add_landmark_purges_legacy_session_end_spam(self):
        with tempfile.TemporaryDirectory() as td:
            os.environ["HERMESPACE_HOME"] = td
            from hermespace.world import WorldModel

            wm = WorldModel(agent_id="landmark-test")
            wm.state.landmarks = [
                "[2026-01-01T00:00:00Z] session ended",
                "[2026-01-02T00:00:00Z] session end",
                "[2026-01-03T00:00:00Z] Deploy v2 shipped",
            ]
            wm.add_landmark("session ended")
            self.assertEqual(wm.state.landmarks, ["[2026-01-03T00:00:00Z] Deploy v2 shipped"])

    def test_growth_render_uses_cleaned_landmarks(self):
        with tempfile.TemporaryDirectory() as td:
            os.environ["HERMESPACE_HOME"] = td
            from hermespace.world import WorldModel

            wm = WorldModel(agent_id="landmark-test")
            wm.state.landmarks = [
                "[2026-01-01T00:00:00Z] session ended",
                "[2026-01-02T00:00:00Z] Real milestone reached",
            ]
            wm.state.epoch = "Growth"
            md = wm.render_markdown()
            self.assertIn("Real milestone reached", md)
            self.assertNotIn("session ended", md.lower())
            self.assertFalse(any("session ended" in lm.lower() for lm in wm.state.landmarks))


if __name__ == "__main__":
    unittest.main()
