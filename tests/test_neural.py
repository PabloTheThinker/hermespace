"""Neural space tests."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from hermespace.desk import Desk  # noqa: E402
from hermespace.neural_field import NeuralField, cosine, embed_text  # noqa: E402
from hermespace.neural_space import NeuralSpace  # noqa: E402
from hermespace.engine import HermespaceEngine  # noqa: E402
from hermespace.memory_db import HermespaceMemory  # noqa: E402
from hermespace.workflow import Workflow  # noqa: E402
from hermespace.io_contract import HermespaceInput  # noqa: E402


class TestNeural(unittest.TestCase):
    def test_embed_stable(self) -> None:
        a = embed_text("global workspace")
        b = embed_text("global workspace")
        self.assertTrue((a == b).all())
        self.assertGreater(cosine(a, embed_text("workspace global")), 0.2)

    def test_ignite(self) -> None:
        f = NeuralField()
        f.set_query("fix authentication timeout")
        f.add("login session TTL", energy=0.4)
        f.add("unrelated cooking recipe", energy=0.9)
        f.add("auth token refresh", energy=0.5)
        winners = f.ignite()
        texts = " ".join(t.text for t in winners).lower()
        self.assertTrue("auth" in texts or "login" in texts or "ttl" in texts)

    def test_sync_desk(self) -> None:
        d = Desk(
            goal="Fix auth timeout",
            concepts=["[verbal|0.4] session TTL", "[verbal|0.9] banana bread"],
            decision="A — patch TTL",
            say="Patching session TTL.",
            plan=["patch"],
        )
        ns = NeuralSpace(__import__("hermespace.neural_space", fromlist=["NeuralSpaceConfig"]).NeuralSpaceConfig(verbalize=False, backend="hash"))
        snap = ns.sync_from_desk(d, user_message="fix authentication timeout")
        self.assertTrue(snap.get("enabled"))
        self.assertIn("neural", d.meta)
        self.assertTrue(d.focus)

    def test_workflow_includes_neural(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            wf = Workflow(
                HermespaceEngine(desk_path=root / "ACTIVE.md"),
                HermespaceMemory(root=root),
            )
            # isolate neural cache
            wf.neural._cache_path = root / "neural_attractors.json"
            wf.neural.config.verbalize = False
            wf.neural.config.backend = "hash"
            from hermespace.local_model import HashEmbedBackend
            wf.neural.embed_backend = HashEmbedBackend()
            wf.neural.field.embed_fn = lambda text: wf.neural.embed_backend.embed(text, wf.neural.config.dim)
            out = wf.run(
                HermespaceInput(
                    message="multi-step auth refactor please",
                    goal="Refactor auth",
                    decision="A",
                    say="Refactoring auth modules.",
                    plan=["map", "patch"],
                    force=True,
                )
            )
            self.assertIn("neural", out.meta)
            self.assertTrue(out.meta["neural"].get("enabled"))


if __name__ == "__main__":
    unittest.main()
