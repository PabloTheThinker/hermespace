"""OEW protocol gate — soft by default, hard when HERMESPACE_OEW=1."""

from __future__ import annotations

import os
import unittest


class TestOEWProtocol(unittest.TestCase):
    def tearDown(self) -> None:
        os.environ.pop("HERMESPACE_OEW", None)

    def test_non_material_always_ok(self) -> None:
        from hermespace.jspace.protocol import evaluate_material_turn

        v = evaluate_material_turn(material=False)
        self.assertTrue(v.ok)
        self.assertFalse(v.material)

    def test_soft_mode_notes_missing_but_ok(self) -> None:
        os.environ["HERMESPACE_OEW"] = "0"
        from hermespace.jspace.protocol import evaluate_material_turn

        v = evaluate_material_turn(
            material=True, silent_steps=0, has_report=True, hub_holds=0
        )
        self.assertTrue(v.ok)
        self.assertTrue(v.missing)
        self.assertIn("silent_steps", v.missing[0])

    def test_default_on_blocks_incomplete(self) -> None:
        os.environ.pop("HERMESPACE_OEW", None)  # default ON
        from hermespace.jspace.protocol import evaluate_material_turn, oew_enabled

        self.assertTrue(oew_enabled())
        v = evaluate_material_turn(
            material=True, silent_steps=0, has_report=True, hub_holds=0
        )
        self.assertFalse(v.ok)
        self.assertTrue(v.missing)

    def test_hard_mode_blocks_incomplete(self) -> None:
        os.environ["HERMESPACE_OEW"] = "1"
        from hermespace.jspace.protocol import evaluate_material_turn

        v = evaluate_material_turn(
            material=True, silent_steps=0, has_report=True, hub_holds=0
        )
        self.assertFalse(v.ok)
        self.assertTrue(v.missing)

    def test_hard_mode_passes_complete(self) -> None:
        os.environ["HERMESPACE_OEW"] = "1"
        from hermespace.jspace.protocol import evaluate_material_turn

        v = evaluate_material_turn(
            material=True, silent_steps=1, has_report=True, hub_holds=0
        )
        self.assertTrue(v.ok)
        self.assertFalse(v.missing)

    def test_package_exports(self) -> None:
        from hermespace.jspace import (
            JSpace,
            JSpaceEnv,
            ProtocolGate,
            evaluate_material_turn,
        )

        self.assertTrue(callable(evaluate_material_turn))
        self.assertTrue(ProtocolGate)
        self.assertTrue(JSpace)
        self.assertTrue(JSpaceEnv)


if __name__ == "__main__":
    unittest.main()
