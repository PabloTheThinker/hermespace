"""Additional unit tests for gate + plugin payload shape."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from hermespace.gate import should_inject  # noqa: E402
from hermespace.patterns import PATTERNS  # noqa: E402


class TestGate(unittest.TestCase):
    def test_trivial(self) -> None:
        ok, reason = should_inject("ok", desk_ready=True)
        self.assertFalse(ok)
        self.assertEqual(reason, "trivial_ack")

    def test_material(self) -> None:
        ok, reason = should_inject("proceed build the hermespace plugin", desk_ready=True)
        self.assertTrue(ok)

    def test_material_no_desk(self) -> None:
        ok, reason = should_inject("proceed build something big", desk_ready=False)
        self.assertFalse(ok)
        self.assertIn("not_ready", reason)


class TestPatterns(unittest.TestCase):
    def test_majority_confirmed(self) -> None:
        n = sum(1 for p in PATTERNS if p.confirmed)
        self.assertGreaterEqual(n, 14)
        # neural jlens must remain explicit gap
        gaps = [p for p in PATTERNS if not p.confirmed]
        self.assertTrue(any(p.component == "neural.jlens" for p in gaps))


if __name__ == "__main__":
    unittest.main()
