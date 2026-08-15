"""Doctor FAIL + plugins.enabled union (grokbot shape, no mailbox/SSH)."""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class _EnvHome:
    def __init__(self) -> None:
        self._td = tempfile.TemporaryDirectory()
        self.space = Path(self._td.name) / "space"
        self.hermes = Path(self._td.name) / "hermes"
        self.space.mkdir()
        self.hermes.mkdir()
        self._old_space = os.environ.get("HERMESPACE_HOME")
        self._old_hermes = os.environ.get("HERMES_HOME")
        os.environ["HERMESPACE_HOME"] = str(self.space)
        os.environ["HERMES_HOME"] = str(self.hermes)

    def close(self) -> None:
        if self._old_space is None:
            os.environ.pop("HERMESPACE_HOME", None)
        else:
            os.environ["HERMESPACE_HOME"] = self._old_space
        if self._old_hermes is None:
            os.environ.pop("HERMES_HOME", None)
        else:
            os.environ["HERMES_HOME"] = self._old_hermes
        self._td.cleanup()


class TestUnionPluginsEnabled(unittest.TestCase):
    def test_appends_keeps_cube_insight_grokbot(self) -> None:
        from hermespace.hermes_enable import read_plugins_enabled, union_plugins_enabled

        with tempfile.TemporaryDirectory() as td:
            home = Path(td)
            cfg = home / "config.yaml"
            cfg.write_text(
                "# keep-me\n"
                "model:\n"
                "  name: x\n"
                "plugins:\n"
                "  enabled:\n"
                "    - hermescube\n"
                "    - hermes-insight\n"
                "    - grokbot\n"
                "memory:\n"
                "  provider: hermescube\n",
                encoding="utf-8",
            )
            out = union_plugins_enabled("hermespace", home=home)
            self.assertTrue(out.get("ok"), out)
            self.assertEqual(out.get("action"), "appended")
            enabled = read_plugins_enabled(cfg)
            self.assertIn("hermescube", enabled)
            self.assertIn("hermes-insight", enabled)
            self.assertIn("grokbot", enabled)
            self.assertIn("hermespace", enabled)
            text = cfg.read_text(encoding="utf-8")
            self.assertIn("# keep-me", text)
            self.assertIn("provider: hermescube", text)
            self.assertIn("name: x", text)

    def test_inline_list_appends(self) -> None:
        from hermespace.hermes_enable import read_plugins_enabled, union_plugins_enabled

        with tempfile.TemporaryDirectory() as td:
            home = Path(td)
            cfg = home / "config.yaml"
            cfg.write_text(
                "plugins:\n  enabled: [hermescube, hermes-insight]\n",
                encoding="utf-8",
            )
            out = union_plugins_enabled("hermespace", home=home)
            self.assertTrue(out.get("ok"), out)
            self.assertEqual(
                read_plugins_enabled(cfg),
                ["hermescube", "hermes-insight", "hermespace"],
            )

    def test_already_present_is_noop(self) -> None:
        from hermespace.hermes_enable import union_plugins_enabled

        with tempfile.TemporaryDirectory() as td:
            home = Path(td)
            (home / "config.yaml").write_text(
                "plugins:\n  enabled:\n    - hermespace\n    - hermescube\n",
                encoding="utf-8",
            )
            before = (home / "config.yaml").read_text(encoding="utf-8")
            out = union_plugins_enabled("hermespace", home=home)
            self.assertEqual(out.get("action"), "already")
            self.assertEqual(out.get("enabled"), ["hermespace", "hermescube"])
            self.assertEqual((home / "config.yaml").read_text(encoding="utf-8"), before)

    def test_creates_minimal_when_missing(self) -> None:
        from hermespace.hermes_enable import read_plugins_enabled, union_plugins_enabled

        with tempfile.TemporaryDirectory() as td:
            home = Path(td)
            out = union_plugins_enabled("hermespace", home=home)
            self.assertTrue(out.get("ok"), out)
            self.assertEqual(out.get("action"), "created")
            self.assertEqual(read_plugins_enabled(home / "config.yaml"), ["hermespace"])


class TestDoctorFail(unittest.TestCase):
    def setUp(self) -> None:
        self.env = _EnvHome()

    def tearDown(self) -> None:
        self.env.close()

    def _by_name(self, d: dict) -> dict:
        return {c["name"]: c for c in d.get("checks") or []}

    def test_fails_when_plugin_skill_or_enabled_missing(self) -> None:
        from hermespace.ops import doctor

        d = doctor(agent_id="doc-fail")
        by = self._by_name(d)
        self.assertFalse(by["hermes_plugin"]["ok"], by["hermes_plugin"])
        self.assertFalse(by["hermes_skill"]["ok"], by["hermes_skill"])
        self.assertFalse(by["plugins_enabled"]["ok"], by["plugins_enabled"])
        self.assertFalse(d.get("ok"))

    def test_passes_when_plugin_skill_and_enabled_seeded(self) -> None:
        from hermespace.hermes_enable import union_plugins_enabled
        from hermespace.ops import doctor

        plug = self.env.hermes / "plugins" / "hermespace"
        skill = self.env.hermes / "skills" / "hermespace"
        plug.parent.mkdir(parents=True)
        skill.parent.mkdir(parents=True)
        plug.symlink_to(ROOT)
        skill.symlink_to(ROOT / "skills" / "hermespace")
        union_plugins_enabled("hermespace", home=self.env.hermes)

        d = doctor(agent_id="doc-pass")
        by = self._by_name(d)
        self.assertTrue(by["hermes_plugin"]["ok"], by["hermes_plugin"])
        self.assertTrue(by["hermes_skill"]["ok"], by["hermes_skill"])
        self.assertTrue(by["plugins_enabled"]["ok"], by["plugins_enabled"])
        self.assertTrue(d.get("ok"), d)


if __name__ == "__main__":
    unittest.main()
