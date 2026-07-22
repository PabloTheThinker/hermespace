from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


class TestBoundaryViewport(unittest.TestCase):
    def setUp(self) -> None:
        # Pocket and "user project" must be different trees
        self._pocket = tempfile.TemporaryDirectory(prefix="hs-pocket-")
        self._user = tempfile.TemporaryDirectory(prefix="hs-userproj-")
        os.environ["HERMESPACE_HOME"] = self._pocket.name
        os.environ["HERMESPACE_AUTONOMY"] = "0"
        self.proj = Path(self._user.name) / "app"
        self.proj.mkdir()
        (self.proj / "main.py").write_text("print(1)\n", encoding="utf-8")

    def tearDown(self) -> None:
        self._pocket.cleanup()
        self._user.cleanup()

    def test_deny_external_write(self) -> None:
        from hermespace.grid.boundary import check_path

        d = check_path(self.proj / "main.py", "write")
        self.assertFalse(d.allowed)
        self.assertIn("denied", d.reason)

    def test_permit_then_write(self) -> None:
        from hermespace.grid.boundary import check_path, grant_permit

        grant_permit(self.proj, hours=1, note="test")
        d = check_path(self.proj / "main.py", "write")
        self.assertTrue(d.allowed)

    def test_pocket_write_ok(self) -> None:
        from hermespace.grid.boundary import check_path, pocket_root

        p = pocket_root() / "memory" / "hermespace" / "grid" / "x.json"
        d = check_path(p, "write")
        self.assertTrue(d.allowed)
        self.assertTrue(d.in_pocket)

    def test_secretish_blocked(self) -> None:
        from hermespace.grid.boundary import check_path

        d = check_path(self.proj / ".env", "write")
        self.assertFalse(d.allowed)
        # even inside pocket
        from hermespace.grid.boundary import pocket_root

        d2 = check_path(pocket_root() / ".env", "write")
        self.assertFalse(d2.allowed)

    def test_external_delete_denied(self) -> None:
        from hermespace.grid.boundary import check_path, grant_permit

        grant_permit(self.proj, hours=1, mode="write")
        d = check_path(self.proj / "main.py", "delete")
        self.assertFalse(d.allowed)

    def test_viewport_snapshot(self) -> None:
        from hermespace import Grid
        from hermespace.grid.viewport import render_markdown, snapshot, write_viewport_files

        g = Grid("vp")
        g.add_mission("See inside")
        g.think("hello viewport", role="self")
        snap = snapshot("vp")
        self.assertEqual(snap["agent_id"], "vp")
        self.assertTrue(snap["missions"])
        md = render_markdown("vp")
        self.assertIn("Hermespace viewport", md)
        self.assertIn("See inside", md)
        paths = write_viewport_files("vp")
        self.assertTrue(Path(paths["html"]).is_file())
        self.assertTrue(Path(paths["markdown"]).is_file())


if __name__ == "__main__":
    unittest.main()
