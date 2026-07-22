"""Agent API door tests."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from hermespace.agent_api import (  # noqa: E402
    decode_bundle,
    decode_for_model,
    decode_for_user,
    encode_message,
    run_turn,
)
from hermespace.engine import HermespaceEngine  # noqa: E402
from hermespace.memory_db import HermespaceMemory  # noqa: E402
from hermespace.workflow import Workflow  # noqa: E402


class TestAgentApi(unittest.TestCase):
    def test_doors(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            wf = Workflow(
                HermespaceEngine(desk_path=root / "ACTIVE.md"),
                HermespaceMemory(root=root),
            )
            wf.neural.config.verbalize = False
            inp = encode_message(
                "Fix login timeout",
                goal="Fix login timeout",
                decision="A — patch",
                plan=["patch"],
                say="Patching login timeout now.",
                session_id="t1",
                force=True,
            )
            out = run_turn(inp, workflow=wf)
            self.assertFalse(out.skipped)
            self.assertIn("Patching", decode_for_user(out))
            self.assertTrue(len(decode_for_model(out)) > 20)
            b = decode_bundle(out)
            self.assertEqual(b["user_reply"], decode_for_user(out))
            self.assertTrue(b["memory_id"])


if __name__ == "__main__":
    unittest.main()
