from __future__ import annotations
import sys, tempfile, unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from hermespace.engine import HermespaceEngine
from hermespace.memory_db import HermespaceMemory
from hermespace.workflow import Workflow
from hermespace.workbench import Workbench

class TestWorkbench(unittest.TestCase):
    def test_idle_and_order(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            wf = Workflow(HermespaceEngine(desk_path=root/"ACTIVE.md"), HermespaceMemory(root=root))
            wf.neural.config.verbalize = False
            wb = Workbench("agent-a", session_id="s1", workflow=wf, root=root/"wb")
            st = wb.enter()
            self.assertEqual(st["mode"], "idle")
            wb.park_goal("Later docs")
            self.assertEqual(wb.status()["park_count"], 1)
            idle = wb.idle_tick(consolidate_every=1)
            self.assertIn("idle_actions", idle)
            res = wb.receive_order(
                "Fix auth now",
                goal="Fix auth",
                decision="A",
                plan=["patch"],
                say="Fixing auth.",
                force=True,
            )
            self.assertFalse(res["skipped"])
            self.assertIn("Fixing", res["user_reply"])
            self.assertTrue(res["model_context"])
            self.assertEqual(wb.status()["mode"], "idle")

if __name__ == "__main__":
    unittest.main()
