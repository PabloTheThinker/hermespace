"""AuDHD execute/focus shapes — one live goal, named park, report lead."""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path


class TestExecuteFocusShapes(unittest.TestCase):
    def test_park_line_format(self) -> None:
        from hermespace.execute_focus import format_park_line, park_record

        rec = park_record("Ship the auth fix", state="waiting", next_crumb="reopen PR")
        line = format_park_line(rec)
        self.assertEqual(line, "Ship the auth fix — waiting — reopen PR")

    def test_report_lead_is_next_action_not_quiz(self) -> None:
        from hermespace.execute_focus import shape_execute_report

        out = shape_execute_report(
            "Remember when we talked about auth?\nAlso docs.",
            goal="Fix auth",
            plan=["Run the failing test", "Patch TTL"],
        )
        self.assertTrue(out.startswith("Run the failing test"))
        self.assertNotIn("Remember when", out.splitlines()[0])

    def test_lists_capped_at_five(self) -> None:
        from hermespace.execute_focus import shape_execute_report

        body = "\n".join(f"{i}) step {i}" for i in range(1, 9))
        out = shape_execute_report(body, plan=["Start the first step"])
        listed = [ln for ln in out.splitlines() if ln[:1].isdigit()]
        self.assertLessEqual(len(listed), 5)

    def test_skips_missing_and_emotion_skills(self) -> None:
        from hermespace.execute_focus import audhd_skill_hints

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            skills = root / "skills"
            (skills / "audhd-execute").mkdir(parents=True)
            (skills / "audhd-execute" / "SKILL.md").write_text("# execute\n", encoding="utf-8")
            (skills / "audhd-emotion").mkdir(parents=True)
            (skills / "audhd-emotion" / "SKILL.md").write_text("# emotion\n", encoding="utf-8")
            hints = audhd_skill_hints(hermes_home=root)
            joined = " ".join(hints)
            self.assertIn("audhd-execute", joined)
            self.assertNotIn("emotion", joined)
            self.assertEqual(audhd_skill_hints(hermes_home=root / "missing"), [])

    def test_one_live_goal_parks_the_previous(self) -> None:
        from hermespace.engine import HermespaceEngine
        from hermespace.memory_db import HermespaceMemory
        from hermespace.workbench import Workbench
        from hermespace.workflow import Workflow

        with tempfile.TemporaryDirectory() as td:
            os.environ["HERMESPACE_HOME"] = td
            root = Path(td)
            wf = Workflow(
                HermespaceEngine(desk_path=root / "ACTIVE.md"),
                HermespaceMemory(root=root),
            )
            wf.neural.config.verbalize = False
            wb = Workbench("focus-agent", session_id="s1", workflow=wf, root=root / "wb")
            wb.receive_order("First tunnel", goal="Fix auth", say="Patch TTL.", force=True)
            wb.receive_order("Second tunnel", goal="Write docs", say="Open README.", force=True)
            lines = wb.park_lines()
            self.assertTrue(any("Fix auth" in ln and " — " in ln for ln in lines))
            self.assertEqual((wb.workflow.status() or {}).get("goal"), "Write docs")
            os.environ.pop("HERMESPACE_HOME", None)


if __name__ == "__main__":
    unittest.main()
