"""Workflow + I/O + memory tests."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from hermespace.engine import HermespaceEngine  # noqa: E402
from hermespace.io_contract import HermespaceInput  # noqa: E402
from hermespace.memory_db import HermespaceMemory  # noqa: E402
from hermespace.workflow import Workflow  # noqa: E402


class TestWorkflow(unittest.TestCase):
    def _wf(self, td: str) -> Workflow:
        root = Path(td)
        eng = HermespaceEngine(desk_path=root / "ACTIVE.md")
        mem = HermespaceMemory(root=root)
        return Workflow(eng, mem)

    def test_turn_material(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            wf = self._wf(td)
            r = wf.turn(
                "proceed build hermespace workflow integration",
                goal="Integrate workflow",
                decision="A — ship workflow",
                plan=["orchestrator", "cli", "tests"],
                say="Workflow spine live.",
                force_enter=True,
            )
            self.assertFalse(r.skipped)
            self.assertTrue(r.ready)
            self.assertIn("Hermespace live desk", r.inject)
            self.assertTrue(r.say)
            self.assertTrue(r.memory_id)
            self.assertTrue((Path(td) / "hermespace.db").exists())
            self.assertTrue(list((Path(td) / "journal").glob("*.md")))

    def test_input_output_run(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            wf = self._wf(td)
            out = wf.run(
                HermespaceInput(
                    message="fix the bug please",
                    goal="Fix the bug",
                    decision="A — patch",
                    plan=["repro", "fix"],
                    say="Patching now.",
                    session_id="s1",
                    agent_id="agent-1",
                    force=True,
                )
            )
            self.assertEqual(out.report, "Patching now.")
            self.assertEqual(out.agent_reply_hint(), "Patching now.")
            hist = wf.history(session_id="s1", limit=5)
            self.assertGreaterEqual(len(hist), 1)
            found = wf.study("Fix the bug")
            self.assertGreaterEqual(len(found), 1)

    def test_turn_skips_trivial(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            wf = self._wf(td)
            wf.engine.enter(
                goal="g",
                decision="A",
                say="s",
                auto_load=False,
                user_message="build x",
            )
            r = wf.turn("ok", force_enter=False)
            self.assertTrue(r.skipped)

    def test_status(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            wf = self._wf(td)
            wf.engine.enter(goal="g", decision="A", say="hi", auto_load=False)
            st = wf.status()
            self.assertTrue(st["ready"])
            self.assertIn("memory", st)


if __name__ == "__main__":
    unittest.main()
