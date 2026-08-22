"""Persistence contracts for the active desk."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from hermespace.desk import Desk
from hermespace.store import load_desk, save_desk


class TestDeskStore(unittest.TestCase):
    def test_sidecar_metadata_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "ACTIVE.md"
            desk = Desk(
                goal="Ship",
                decision="A — proceed",
                say="Proceeding.",
                focus=["[verbal|0.90] verify"],
                load={"level": "high", "total": 0.8},
                executive="protect",
                meta={
                    "fabric": {"skill_hits": [{"name": "pytest"}]},
                    "_fabric_goal": "Ship",
                    "world_entry_count": 17,
                    "neural": {"backend": "hash"},
                },
            )
            save_desk(desk, path)
            restored = load_desk(path)

            self.assertEqual(restored.meta, desk.meta)
            self.assertEqual(restored.load, desk.load)
            self.assertEqual(restored.focus, desk.focus)
            self.assertEqual(restored.executive, desk.executive)

    def test_corrupt_sidecar_falls_back_to_markdown(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "ACTIVE.md"
            desk = Desk(goal="Recover", decision="A", say="Ready")
            save_desk(desk, path)
            path.with_suffix(".json").write_text("{broken", encoding="utf-8")

            restored = load_desk(path)
            self.assertEqual(restored.goal, "Recover")
            self.assertEqual(restored.decision, "A")

    def test_atomic_save_leaves_valid_json(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "ACTIVE.md"
            for idx in range(20):
                desk = Desk(
                    goal=f"Goal {idx}",
                    decision="A",
                    say="Ready",
                    meta={"iteration": idx},
                )
                save_desk(desk, path)
                payload = json.loads(path.with_suffix(".json").read_text(encoding="utf-8"))
                self.assertEqual(payload["meta"]["iteration"], idx)
            self.assertEqual(list(Path(td).glob("*.tmp")), [])


if __name__ == "__main__":
    unittest.main()
