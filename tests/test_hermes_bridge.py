from __future__ import annotations
import os, sys, tempfile, unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

class TestHermesBridge(unittest.TestCase):
    def test_session_and_pre_llm(self):
        with tempfile.TemporaryDirectory() as td:
            os.environ["HERMESPACE_HOME"] = td
            os.environ["HERMESPACE_NEURAL_VERBALIZE"] = "0"
            os.environ["HERMESPACE_AUTO_ORDER"] = "0"
            from hermespace.hermes_bridge import on_session_start, on_pre_llm_call, on_session_end
            from hermespace.engine import HermespaceEngine
            from hermespace.store import load_desk
            r = on_session_start(session_id="bridge-test")
            self.assertIsInstance(r, dict)
            self.assertIn("context", r)
            self.assertIn("Workbench", r["context"])
            desk = load_desk()
            self.assertTrue(desk.goal)
            # material message should inject after desk ready
            inj = on_pre_llm_call(
                user_message="proceed build the feature please",
                session_id="bridge-test",
                is_first_turn=False,
            )
            self.assertIsNotNone(inj)
            self.assertIn("context", inj)
            on_session_end(session_id="bridge-test")

if __name__ == "__main__":
    unittest.main()
