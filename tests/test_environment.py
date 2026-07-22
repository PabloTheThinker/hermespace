"""Environment kit tests."""
from __future__ import annotations
import sys, tempfile, unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from hermespace.environment import probe_environment, environment_markdown
from hermespace.workbench import Workbench
from hermespace.engine import HermespaceEngine
from hermespace.memory_db import HermespaceMemory
from hermespace.workflow import Workflow

class TestEnvironment(unittest.TestCase):
    def test_probe(self):
        rep = probe_environment()
        self.assertTrue(rep.surfaces)
        self.assertTrue(any(s["id"] == "skills" for s in rep.surfaces))
        md = environment_markdown(rep)
        self.assertIn("Tool surfaces", md)

    def test_workbench_env(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            # fake hermes home
            hh = root / "hermes"
            (hh / "skills" / "demo").mkdir(parents=True)
            (hh / "skills" / "demo" / "SKILL.md").write_text("# demo\n")
            (hh / "memories").mkdir()
            (hh / "memories" / "MEMORY.md").write_text("x")
            (hh / "plugins" / "hermespace").mkdir(parents=True)
            import os
            os.environ["HERMES_HOME"] = str(hh)
            wf = Workflow(HermespaceEngine(desk_path=root/"ACTIVE.md"), HermespaceMemory(root=root))
            wf.neural.config.verbalize = False
            wb = Workbench("a", session_id="s", workflow=wf, root=root/"wb")
            st = wb.enter()
            self.assertIn("environment_summary", st)
            env = wb.environment()
            self.assertGreaterEqual(env.get("skills_count", 0), 1)
            self.assertIn("MEMORY.md", env.get("memory_files") or [])

if __name__ == "__main__":
    unittest.main()
