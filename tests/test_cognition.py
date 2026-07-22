"""Tests for cognitive science layer."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from hermespace.cognition import (  # noqa: E402
    FOCUS_CAP,
    Modality,
    bind_episode,
    classify_message_load,
    compete_for_focus,
    parse_slot,
)
from hermespace.desk import Desk  # noqa: E402
from hermespace.inject import build_inject_block  # noqa: E402


class TestCognition(unittest.TestCase):
    def test_parse_modality(self) -> None:
        s = parse_slot("[struct|0.9] /tmp/example/hermespace")
        self.assertEqual(s.modality, Modality.STRUCT)
        self.assertGreaterEqual(s.salience, 0.89)

    def test_focus_cap(self) -> None:
        slots = [parse_slot(f"[verbal|{0.1*i}] c{i}") for i in range(10)]
        focus = compete_for_focus(slots)
        self.assertEqual(len(focus), FOCUS_CAP)
        self.assertEqual(focus[0].text, "c9")  # highest salience

    def test_bind(self) -> None:
        b = bind_episode("goal", "A", "say hi", ["p1"])
        self.assertIsNotNone(b)
        assert b is not None
        self.assertEqual(b.modality, Modality.BIND)

    def test_load_high_on_complex(self) -> None:
        load = classify_message_load(
            "build implement research architecture " + ("word " * 50),
            n_concepts=10,
            n_plan=5,
        )
        self.assertIn(load["level"], {"mid", "high"})

    def test_desk_recompute(self) -> None:
        d = Desk(
            goal="Improve Hermespace with neuroscience",
            concepts=["[verbal|0.8] working memory", "[struct|0.7] path/repo"],
            choices=["A"],
            decision="A",
            plan=["cognition module", "tests"],
            say="Cognitive upgrade shipped.",
        )
        d.recompute_cognition("study neuroscience and working memory please")
        self.assertTrue(d.focus)
        self.assertIn("level", d.load)
        self.assertTrue(any(c.lower().startswith("[bind") for c in d.concepts))

    def test_inject_mentions_load_or_focus(self) -> None:
        d = Desk(
            goal="g",
            concepts=["[verbal|0.9] important"],
            decision="A",
            say="hello",
        )
        d.recompute_cognition("research cognitive neuroscience carefully")
        block = build_inject_block(d, include_episodes=0)
        self.assertTrue("Load:" in block or "Focus" in block)


if __name__ == "__main__":
    unittest.main()
