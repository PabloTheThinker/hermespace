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
            from hermespace import AccessEngine
            from hermespace.hermes_bridge import (
                on_pre_llm_call,
                on_session_end,
                on_session_finalize,
                on_session_start,
            )
            from hermespace.store import load_desk
            r = on_session_start(session_id="bridge-test")
            self.assertIsInstance(r, dict)
            self.assertIn("context", r)
            self.assertTrue(
                "Access Engine" in r["context"] or "Workbench" in r["context"]
            )
            desk = load_desk(
                AccessEngine(
                    agent_id="hermes-agent",
                    session_id="bridge-test",
                ).desk_engine.desk_path
            )
            self.assertTrue(desk.goal)
            # material message should inject after desk ready
            inj = on_pre_llm_call(
                user_message="First build the feature then verify please",
                session_id="bridge-test",
                is_first_turn=False,
            )
            self.assertIsNotNone(inj)
            self.assertIn("context", inj)
            # Dual-decode hint for hosts that only get context
            self.assertTrue(
                "user_reply_hint" in inj
                or "Dual decode" in inj["context"]
                or "Access Workspace" in inj["context"]
            )
            self.assertNotIn("J-Lens readout", inj["context"])
            self.assertNotIn("What Hermes has on its mind", inj["context"])
            on_session_end(
                session_id="bridge-test",
                completed=True,
                interrupted=False,
            )
            on_session_finalize(session_id="bridge-test")

if __name__ == "__main__":
    unittest.main()
