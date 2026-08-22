"""One-install front door — union organs, memory.provider, doctor WARN."""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class TestInstallKit(unittest.TestCase):
    def setUp(self) -> None:
        self._td = tempfile.TemporaryDirectory()
        self.home = Path(self._td.name) / "hermes"
        self.space = Path(self._td.name) / "space"
        self.home.mkdir()
        self.space.mkdir()
        self._old_h = os.environ.get("HERMES_HOME")
        self._old_s = os.environ.get("HERMESPACE_HOME")
        os.environ["HERMES_HOME"] = str(self.home)
        os.environ["HERMESPACE_HOME"] = str(self.space)

    def tearDown(self) -> None:
        if self._old_h is None:
            os.environ.pop("HERMES_HOME", None)
        else:
            os.environ["HERMES_HOME"] = self._old_h
        if self._old_s is None:
            os.environ.pop("HERMESPACE_HOME", None)
        else:
            os.environ["HERMESPACE_HOME"] = self._old_s
        self._td.cleanup()

    def test_union_keeps_existing_and_adds_space(self) -> None:
        from hermespace.hermes_enable import union_plugins_enabled
        from hermespace.install_kit import union_front_door

        cfg = self.home / "config.yaml"
        cfg.write_text(
            "plugins:\n  enabled:\n    - grokbot\n    - hermescube\n",
            encoding="utf-8",
        )
        (self.home / "plugins" / "hermescube").mkdir(parents=True)
        out = union_front_door(home=self.home)
        self.assertTrue(out["ok"], out)
        enabled = out["enabled"]
        self.assertIn("grokbot", enabled)
        self.assertIn("hermescube", enabled)
        self.assertIn("hermespace", enabled)
        again = union_plugins_enabled("hermespace", home=self.home)
        self.assertEqual(again["action"], "already")

    def test_memory_provider_does_not_clobber(self) -> None:
        from hermespace.hermes_enable import (
            ensure_cube_memory_provider,
            read_memory_provider,
        )

        cfg = self.home / "config.yaml"
        cfg.write_text("memory:\n  provider: notes\n", encoding="utf-8")
        out = ensure_cube_memory_provider(home=self.home)
        self.assertEqual(out["action"], "kept")
        self.assertFalse(out["clobbered"])
        self.assertEqual(read_memory_provider(cfg), "notes")

    def test_memory_provider_set_only_when_unset(self) -> None:
        from hermespace.hermes_enable import (
            ensure_cube_memory_provider,
            read_memory_provider,
        )

        cfg = self.home / "config.yaml"
        cfg.write_text("plugins:\n  enabled:\n    - hermespace\n", encoding="utf-8")
        out = ensure_cube_memory_provider(home=self.home)
        self.assertIn(out["action"], {"set", "created"})
        self.assertEqual(read_memory_provider(cfg), "hermescube")
        self.assertIn("hermespace", cfg.read_text(encoding="utf-8"))

    def test_install_no_organs_links_space_and_unions(self) -> None:
        from hermespace.install_kit import install_front_door

        out = install_front_door(
            checkout=ROOT,
            home=self.home,
            yes=False,
            no_organs=True,
            enable=True,
        )
        self.assertTrue(out["ok"], out)
        self.assertTrue((self.home / "plugins" / "hermespace").exists())
        self.assertTrue((self.home / "skills" / "hermespace" / "SKILL.md").is_file())
        self.assertIn("hermespace", out["union"]["enabled"])
        self.assertEqual(out["organs"].get("skipped"), True)

    def test_doctor_warns_not_fails_when_organs_missing(self) -> None:
        from hermespace.install_kit import install_front_door
        from hermespace.ops import doctor

        install_front_door(checkout=ROOT, home=self.home, no_organs=True, enable=True)
        d = doctor(agent_id="kit-doc")
        by = {c["name"]: c for c in d["checks"]}
        self.assertTrue(d["ok"], d)
        self.assertFalse(by["cube_organ"]["ok"])
        self.assertFalse(by["insight_organ"]["ok"])
        self.assertTrue(any("Cube" in w for w in d.get("warnings") or []))
        self.assertTrue(any("Insight" in w for w in d.get("warnings") or []))


class TestInjectCapAndHooks(unittest.TestCase):
    def test_harvest_budget_fail_open(self) -> None:
        import time

        from hermespace.hermes_bridge import _run_fail_open

        started = time.monotonic()

        def _slow() -> None:
            time.sleep(2)

        _run_fail_open("test_budget", _slow, seconds=0.05)
        self.assertLess(time.monotonic() - started, 1.0)

    def test_bounded_context_stays_under_9k(self) -> None:
        from hermespace.hermes_bridge import INJECT_HARD_CAP, _bounded_context

        self.assertLess(INJECT_HARD_CAP, 9000)
        blob = "x" * 20_000
        out = _bounded_context(blob)
        self.assertLess(len(out), 9000)

    def test_new_hooks_park_names_only(self) -> None:
        from hermespace.access.hub import AccessHub
        from hermespace.hermes_bridge import (
            on_kanban_task_claimed,
            on_pre_tool_call,
            on_skill_lifecycle,
        )

        with tempfile.TemporaryDirectory() as td:
            os.environ["HERMESPACE_HOME"] = td
            os.environ["HERMESPACE_AGENT_ID"] = "hook-agent"
            on_pre_tool_call(
                tool_name="read_file",
                session_id="default",
                args={"secret": "must-not-persist"},
            )
            on_skill_lifecycle(skill_name="demo", event="loaded", session_id="default")
            on_kanban_task_claimed(task_id="card-1", title="secret title", session_id="default")
            hub = AccessHub(agent_id="hook-agent")
            silent = " ".join(hub.state.silent_steps)
            self.assertIn("skill:demo:loaded", silent)
            self.assertIn("kanban:claimed:card-1", silent)
            self.assertNotIn("must-not-persist", silent)
            self.assertNotIn("secret title", silent)
            os.environ.pop("HERMESPACE_HOME", None)
            os.environ.pop("HERMESPACE_AGENT_ID", None)


if __name__ == "__main__":
    unittest.main()
