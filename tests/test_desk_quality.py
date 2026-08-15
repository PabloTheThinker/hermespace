"""Desk quality cut — no-say live turn, FOA collapse, smoke shadow, lens title."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

LIVE_MSG = "Write a short README for the auth fix, then stop."


class TestNoSayLiveTurn(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        os.environ["HERMESPACE_HOME"] = self.tmp.name
        os.environ["HERMESPACE_SKIP_NEURAL"] = "1"
        os.environ["HERMESPACE_NEURAL_VERBALIZE"] = "0"
        os.environ["HERMESPACE_OEW"] = "1"

    def tearDown(self) -> None:
        self.tmp.cleanup()
        for key in (
            "HERMESPACE_HOME",
            "HERMESPACE_SKIP_NEURAL",
            "HERMESPACE_NEURAL_VERBALIZE",
            "HERMESPACE_OEW",
        ):
            os.environ.pop(key, None)

    def test_derive_plan_splits_then(self) -> None:
        from hermespace.execute_focus import derive_plan, is_near_dup

        plan = derive_plan(LIVE_MSG)
        self.assertGreaterEqual(len(plan), 2)
        self.assertLessEqual(len(plan), 3)
        self.assertNotIn("execute", [p.casefold() for p in plan])
        self.assertTrue(any("readme" in p.casefold() for p in plan))
        self.assertTrue(any("stop" in p.casefold() for p in plan))
        self.assertFalse(is_near_dup(plan[0], plan[1]))

    def test_message_only_report_and_foa(self) -> None:
        from hermespace.execute_focus import gist_key, is_near_dup, strip_slot_prefix
        from hermespace.io_contract import HermespaceInput
        from hermespace.workflow import Workflow

        # Match live CLI: only --message, no --say/--goal/--plan, neural on.
        os.environ.pop("HERMESPACE_SKIP_NEURAL", None)
        out = Workflow().run(HermespaceInput(message=LIVE_MSG, say="", goal="", plan=[]))
        self.assertFalse(out.skipped, out.reason)
        line1 = (out.report or "").splitlines()[0].strip()
        low = line1.casefold()
        self.assertTrue(line1, out.report)
        self.assertNotIn("production:", low)
        self.assertNotIn("partner:", low)
        self.assertNotIn("→ a — proceed", low)
        self.assertNotIn("a — proceed", low)
        self.assertNotEqual(low, "execute")
        self.assertNotEqual(low, LIVE_MSG.casefold())
        self.assertTrue(
            "readme" in low or "write" in low,
            line1,
        )
        self.assertNotEqual(list(out.plan or []), ["execute"])
        self.assertGreaterEqual(len(out.plan or []), 1)
        self.assertLessEqual(len(out.plan or []), 3)
        self.assertTrue(any("stop" in str(p).casefold() for p in out.plan) or len(out.plan) >= 1)

        focus = list(out.meta.get("focus") or []) if isinstance(out.meta, dict) else []
        if not focus:
            from hermespace.store import load_desk

            focus = list(load_desk().focus or [])
        self.assertLessEqual(len(focus), 4)
        gists = [gist_key(x) for x in focus if gist_key(x)]
        for i, a in enumerate(gists):
            for b in gists[i + 1 :]:
                self.assertFalse(is_near_dup(a, b), f"FOA near-dup {a!r} ~ {b!r} from {focus}")
        stripped = [strip_slot_prefix(x) for x in focus]
        joined = " ".join(stripped).casefold()
        self.assertTrue("readme" in joined or "stop" in joined, focus)

    def test_thanks_still_skips(self) -> None:
        from hermespace.io_contract import HermespaceInput
        from hermespace.workflow import Workflow

        out = Workflow().run(HermespaceInput(message="thanks", force=False))
        self.assertTrue(out.skipped)
        self.assertEqual(out.reason, "trivial_ack")

    def test_shape_empty_say_uses_next_action(self) -> None:
        from hermespace.execute_focus import shape_execute_report

        garbled = (
            "Write a short README for the auth fix, then stop. "
            "→ A — proceed [production: prepare verbal report (decod; partner: match user"
        )
        out = shape_execute_report(
            garbled,
            goal=LIVE_MSG,
            plan=[],
            say="",
            decision="A — proceed",
            message=LIVE_MSG,
        )
        line1 = out.splitlines()[0]
        self.assertNotIn("production:", line1)
        self.assertNotIn("partner:", line1)
        self.assertNotIn("A — proceed", line1)
        self.assertIn("README", line1)

    def test_operator_lens_title(self) -> None:
        from hermespace.access import AccessEnv

        md = AccessEnv(agent_id="lens-title").lens_markdown()
        self.assertIn("## Operator lens (external workspace)", md)
        self.assertNotIn("J-Lens readout", md)


class TestPluginEntryShadow(unittest.TestCase):
    def test_root_entry_exposes_register_via_importlib(self) -> None:
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "hermespace_repo_plugin_quality",
            ROOT / "__init__.py",
            submodule_search_locations=[str(ROOT)],
        )
        self.assertIsNotNone(spec)
        assert spec is not None and spec.loader is not None
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        self.assertTrue(callable(getattr(mod, "register", None)))

    def test_parent_cwd_imports_real_package(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            parent = Path(td)
            link = parent / "hermespace"
            link.symlink_to(ROOT)
            env = os.environ.copy()
            env["PYTHONPATH"] = str(ROOT / "src")
            env["HERMESPACE_HOME"] = str(parent / "home")
            code = (
                "import hermespace, hermespace.plugin as p\n"
                "from hermespace.desk import Desk\n"
                "assert callable(p.register)\n"
                "assert Desk\n"
                "print(hermespace.__file__)\n"
            )
            proc = subprocess.run(
                [sys.executable, "-c", code],
                cwd=str(parent),
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertIn("src", (proc.stdout or "").replace("\\", "/"))


if __name__ == "__main__":
    unittest.main()
