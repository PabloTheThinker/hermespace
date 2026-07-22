from __future__ import annotations
import os, sys, tempfile, unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

class TestAccessConverse(unittest.TestCase):
    def setUp(self):
        self.p = tempfile.TemporaryDirectory()
        self.u = tempfile.TemporaryDirectory()
        os.environ["HERMESPACE_HOME"] = self.p.name
        os.environ["HERMESPACE_AUTONOMY"] = "0"
        self.proj = Path(self.u.name) / "repo"
        self.proj.mkdir()

    def tearDown(self):
        self.p.cleanup(); self.u.cleanup()

    def test_request_approve_chat(self):
        from hermespace.grid import access
        from hermespace.grid.converse import regulate
        from hermespace.grid.boundary import check_path
        r = access.request_access(str(self.proj), agent_id="a", reason="build", hours=1)
        self.assertEqual(r.status, "pending")
        self.assertFalse(check_path(self.proj / "x.py", "write").allowed)
        out = regulate(f"approve request {r.id}", agent_id="a")
        self.assertTrue(out.handled)
        self.assertEqual(out.action, "approve")
        self.assertTrue(check_path(self.proj / "x.py", "write").allowed)

    def test_allow_path_phrase(self):
        from hermespace.grid.converse import regulate
        from hermespace.grid.boundary import check_path
        out = regulate(f"allow {self.proj} for 2h", agent_id="b")
        self.assertTrue(out.handled)
        self.assertTrue(check_path(self.proj / "f", "write").allowed)

    def test_show_boundary(self):
        from hermespace.grid.converse import regulate
        out = regulate("show the boundary", agent_id="c")
        self.assertTrue(out.handled)
        self.assertIn("Pocket root", out.message)

if __name__ == "__main__":
    unittest.main()
