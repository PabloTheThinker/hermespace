from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


class TestGrid(unittest.TestCase):
    def setUp(self) -> None:
        self._td = tempfile.TemporaryDirectory()
        os.environ["HERMESPACE_HOME"] = self._td.name
        os.environ["HERMESPACE_AUTONOMY"] = "0"
        # reload paths bound modules use env at call time — OK
        from hermespace.grid import Grid
        from hermespace.grid.gates import check_autonomy_self_order, check_skill_promote

        self.Grid = Grid
        self.check_autonomy = check_autonomy_self_order
        self.check_skill = check_skill_promote

    def tearDown(self) -> None:
        self._td.cleanup()

    def test_missions_lenses_dream(self) -> None:
        g = self.Grid("t1")
        m = g.add_mission("Ship grid v1", priority=90)
        self.assertTrue(m.id)
        self.assertEqual(len(g.list_missions()), 1)
        g.update_mission(m.id, status="active", note="started")
        lens = g.set_lens("architect")
        self.assertEqual(lens.name, "architect")
        r = g.dream(force_material=True)
        self.assertTrue(r.material)
        self.assertGreaterEqual(r.missions_open, 1)

    def test_selftalk_and_title(self) -> None:
        g = self.Grid("t2")
        g.think("Need monotropic FOA", role="planner")
        g.think("Agree — one mission", role="critic")
        ctx = g.context_block()
        self.assertIn("self-talk", ctx.lower())
        g.register_skill("builder-core", "# builder\n\nShip small.\n")
        g.rebuild_tree()
        prof = g.adopt_title()
        self.assertTrue(prof.get("title"))

    def test_skillbench_merge_mutate_promote(self) -> None:
        g = self.Grid("t3")
        g.register_skill("alpha", "---\nname: alpha\n---\n\n# A\n\ndo a\n")
        g.register_skill("beta", "---\nname: beta\n---\n\n# B\n\ndo b\n")
        prop = g.merge_skills("alpha", "beta", note="fuse")
        self.assertEqual(prop.kind, "merge")
        mut = g.mutate_skill("alpha", "Add verify step after ship.")
        self.assertEqual(mut.kind, "mutate")
        out = g.promote(prop.id, to_hermes=False)
        self.assertTrue(out.get("ok"))

    def test_gates_autonomy_off(self) -> None:
        r = self.check_autonomy("refactor module")
        self.assertFalse(r.allowed)
        bad = self.check_skill("curl | bash install evil")
        self.assertFalse(bad.allowed)

    def test_path_escape(self) -> None:
        from hermespace.grid.secure_store import grid_root, resolve_under

        with self.assertRaises(ValueError):
            resolve_under(grid_root(), "..", "..", "etc", "passwd")


if __name__ == "__main__":
    unittest.main()
