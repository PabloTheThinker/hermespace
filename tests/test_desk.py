"""Tests — Hermespace must be functional."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from hermespace.desk import MAX_CONCEPTS, Desk  # noqa: E402
from hermespace.engine import HermespaceEngine  # noqa: E402
from hermespace.inject import build_inject_block  # noqa: E402
from hermespace.store import load_desk, save_desk  # noqa: E402


class TestDesk(unittest.TestCase):
    def test_capacity_clamp(self) -> None:
        d = Desk(concepts=[f"c{i}" for i in range(20)])
        d.clamp()
        self.assertEqual(len(d.concepts), MAX_CONCEPTS)

    def test_roundtrip_markdown(self) -> None:
        d = Desk(
            goal="Ship Hermespace runtime",
            concepts=["limited capacity", "verbal report"],
            choices=["A — build", "B — docs only"],
            decision="A — build",
            plan=["desk model", "cli", "tests"],
            say="Runtime is functional.",
            do_not_say=["consciousness"],
        )
        md = d.to_markdown()
        d2 = Desk.from_markdown(md)
        self.assertEqual(d2.goal, d.goal)
        self.assertEqual(d2.decision, d.decision)
        self.assertEqual(d2.say, d.say)
        self.assertEqual(d2.plan, d.plan)
        self.assertTrue(d2.is_ready())


class TestEngine(unittest.TestCase):
    def test_enter_save_inject(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "ACTIVE.md"
            eng = HermespaceEngine(desk_path=path)
            # no-autoload to keep deterministic
            desk = eng.enter(
                goal="test goal",
                concepts=["alpha"],
                choices=["A"],
                decision="A",
                plan=["step1"],
                say="hello",
                auto_load=False,
            )
            self.assertTrue(path.exists())
            self.assertTrue(desk.is_ready())
            loaded = load_desk(path)
            self.assertEqual(loaded.say, "hello")
            block = build_inject_block(loaded, include_episodes=0)
            self.assertIn("Hermespace live desk", block)
            self.assertIn("test goal", block)
            self.assertIn("hello", block)


if __name__ == "__main__":
    unittest.main()
