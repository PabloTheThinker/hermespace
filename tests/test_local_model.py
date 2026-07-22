from __future__ import annotations
import sys
import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from hermespace.local_model import (  # noqa: E402
    ollama_embeddings_available,
    select_embed_backend,
    project_to_dim,
    local_capabilities,
)
from hermespace.neural_space import NeuralSpace, NeuralSpaceConfig  # noqa: E402
from hermespace.desk import Desk  # noqa: E402
import numpy as np


class TestLocalModel(unittest.TestCase):
    def test_select_backend(self) -> None:
        b = select_embed_backend("hash")
        self.assertEqual(b.name, "hash")
        v = b.embed("hello workspace")
        self.assertEqual(v.shape[0], 256)

    def test_project_dim(self) -> None:
        v = np.ones(768)
        p = project_to_dim(v, 256)
        self.assertEqual(p.shape[0], 256)

    def test_caps(self) -> None:
        c = local_capabilities()
        self.assertIn("embeddings_ok", c)
        self.assertIn("recommended_backend", c)

    def test_ollama_embed_if_up(self) -> None:
        if not ollama_embeddings_available():
            self.skipTest("ollama embeddings not available")
        b = select_embed_backend("ollama")
        self.assertEqual(b.name, "ollama_embed")
        v = b.embed("authentication timeout session")
        self.assertGreater(v.shape[0], 10)
        # cosine self
        from hermespace.neural_field import cosine
        self.assertGreater(cosine(v, b.embed("authentication timeout session")), 0.99)

    def test_neural_space_ollama_sync(self) -> None:
        cfg = NeuralSpaceConfig(backend="auto", verbalize=False)
        ns = NeuralSpace(cfg)
        d = Desk(
            goal="Fix auth timeout",
            concepts=["[verbal|0.5] session cookie", "[verbal|0.5] banana bread recipe"],
            decision="A",
            say="Fixing auth.",
            plan=["patch"],
        )
        snap = ns.sync_from_desk(d, user_message="fix login session timeout")
        self.assertTrue(snap.get("enabled"))
        self.assertIn(snap.get("backend"), {"ollama_embed", "hash"})


if __name__ == "__main__":
    unittest.main()
