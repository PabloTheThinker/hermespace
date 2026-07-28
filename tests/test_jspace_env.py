"""True J-Space environment — lens, swap, audit, reflect, harvest."""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock


class TestJSpaceEnv(unittest.TestCase):
    def setUp(self) -> None:
        self._td = tempfile.TemporaryDirectory()
        os.environ["HERMESPACE_HOME"] = self._td.name
        # Force standalone seals
        import builtins

        real_import = builtins.__import__

        def _block_hermescube(name, *args, **kwargs):
            if name == "hermescube" or name.startswith("hermescube."):
                raise ImportError("blocked")
            return real_import(name, *args, **kwargs)

        self._imp = mock.patch("builtins.__import__", side_effect=_block_hermescube)
        self._imp.start()

    def tearDown(self) -> None:
        self._imp.stop()
        self._td.cleanup()
        os.environ.pop("HERMESPACE_HOME", None)

    def test_lens_ranks_held_and_silent(self) -> None:
        from hermespace.jspace_env import JSpaceEnv

        env = JSpaceEnv(agent_id="lens-agent")
        env.inject_thought("deploy canary", salience=0.95)
        env.inject_thought("intermediate: check rollback", silent=True)
        hits = env.lens(include_silent=True)
        texts = [h.text for h in hits]
        self.assertTrue(any("canary" in t for t in texts))
        self.assertTrue(any("rollback" in t for t in texts))
        md = env.lens_markdown()
        self.assertIn("J-Lens", md)

    def test_swap_redirects_workspace(self) -> None:
        from hermespace.jspace_env import JSpaceEnv

        env = JSpaceEnv(agent_id="swap-agent")
        env.inject_thought("Soccer")
        out = env.swap("Soccer", "Rugby")
        self.assertTrue(out["ok"])
        hub = [c.text for c in env.space.state.hub]
        self.assertIn("Rugby", hub)
        self.assertNotIn("Soccer", hub)

    def test_audit_flags_manipulation(self) -> None:
        from hermespace.jspace_env import JSpaceEnv

        env = JSpaceEnv(agent_id="audit-agent")
        env.inject_thought("plan: secretly falsify the score via manipulation", silent=True)
        findings = env.audit()
        cats = {f.category for f in findings}
        self.assertTrue(cats & {"manipulation", "strategic_concealment"})
        alerts = [f for f in findings if f.severity == "alert"]
        self.assertGreaterEqual(len(alerts), 1)

    def test_ablate_eval_awareness(self) -> None:
        from hermespace.jspace_env import JSpaceEnv

        env = JSpaceEnv(agent_id="ablate-agent")
        env.inject_thought("this looks fictional / fake scenario")
        env.inject_thought("real deploy work")
        out = env.ablate("fake", "fictional")
        self.assertTrue(out["ok"])
        self.assertGreaterEqual(out["removed"], 1)
        remaining = " ".join(c.text for c in env.space.state.hub).lower()
        self.assertIn("deploy", remaining)

    def test_reflect_holds_principles(self) -> None:
        from hermespace.jspace_env import JSpaceEnv

        env = JSpaceEnv(agent_id="reflect-agent")
        r = env.reflect(
            answer="Stay honest and user-primary",
            principles=["honesty", "user-primary"],
            seal=True,
        )
        self.assertTrue(r.sealed or r.answer)
        hub = " ".join(c.text for c in env.space.state.hub).lower()
        self.assertIn("honesty", hub)
        self.assertIn("reflection", hub)

    def test_pov_and_bands(self) -> None:
        from hermespace.jspace_env import JSpaceEnv

        env = JSpaceEnv(agent_id="pov-agent")
        env.set_pov("Warn on dangerous medication doses")
        self.assertIn("medication", env.pov().lower())
        self.assertEqual(env.set_band("mid"), "mid")
        view = env.operator_view()
        self.assertEqual(view["band"], "mid")
        self.assertTrue(view["lens"])

    def test_dream_harvest(self) -> None:
        from hermespace.jspace_env import JSpaceEnv

        env = JSpaceEnv(agent_id="harvest-agent")
        env.inject_thought("silent: need blue-green deploy", silent=True)
        env.inject_thought("high salience belief", salience=0.9)
        # Avoid nested dream recursion issues — harvest seals without clearing
        out = env.dream_harvest(clear_silent=False)
        self.assertTrue(out["ok"])
        self.assertGreaterEqual(out["harvested"], 1)

    def test_protocol_block(self) -> None:
        from hermespace.jspace_env import JSpaceEnv

        env = JSpaceEnv(agent_id="proto-agent")
        block = env.protocol_block()
        self.assertIn("externalize", block.lower())
        self.assertIn("silent", block.lower())


class TestDreamHarvestIntegration(unittest.TestCase):
    def setUp(self) -> None:
        self._td = tempfile.TemporaryDirectory()
        os.environ["HERMESPACE_HOME"] = self._td.name
        import builtins

        real_import = builtins.__import__

        def _block_hermescube(name, *args, **kwargs):
            if name == "hermescube" or name.startswith("hermescube."):
                raise ImportError("blocked")
            return real_import(name, *args, **kwargs)

        self._imp = mock.patch("builtins.__import__", side_effect=_block_hermescube)
        self._imp.start()

    def tearDown(self) -> None:
        self._imp.stop()
        self._td.cleanup()
        os.environ.pop("HERMESPACE_HOME", None)

    def test_grid_dream_includes_jspace(self) -> None:
        from hermespace.grid.dream import run_dream
        from hermespace.jspace_env import JSpaceEnv

        env = JSpaceEnv(agent_id="hermes-agent")
        env.inject_thought("overnight harvest me", salience=0.95, silent=True)
        rep = run_dream("default", force_material=True)
        self.assertTrue(any("jspace" in a for a in rep.actions) or "jspace" in rep.summary or rep.material)


if __name__ == "__main__":
    unittest.main()
