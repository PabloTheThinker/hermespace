"""Functional Access Workspace + Cube adapter (standalone) tests."""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock


class TestAccessHub(unittest.TestCase):
    def setUp(self) -> None:
        self._td = tempfile.TemporaryDirectory()
        self.root = Path(self._td.name)
        os.environ["HERMESPACE_HOME"] = str(self.root)

    def tearDown(self) -> None:
        self._td.cleanup()
        os.environ.pop("HERMESPACE_HOME", None)

    def test_hold_report_broadcast(self) -> None:
        from hermespace.access import AccessHub

        js = AccessHub(agent_id="test-agent")
        js.hold("deploy pipeline", salience=0.95)
        js.hold("rollback plan", salience=0.7)
        rep = js.report()
        self.assertIn("deploy pipeline", rep)
        self.assertIn("Access Workspace", rep)
        block = js.broadcast_block()
        self.assertIn("broadcast", block.lower())
        self.assertIn("deploy", block.lower())
        st = js.status()
        self.assertGreaterEqual(st["hub_n"], 2)
        self.assertLessEqual(st["focus_n"], 4)
        self.assertIn("verbal_report", st["properties"])

    def test_silent_reasoning_not_in_default_report(self) -> None:
        from hermespace.access import AccessHub

        js = AccessHub(agent_id="silent-agent")
        js.reason_step("intermediate: spider has 8 legs")
        bare = js.report(include_silent=False)
        full = js.report(include_silent=True)
        self.assertIn("spider", full.lower())
        # silent steps section only when include_silent
        self.assertIn("Silent reasoning", full)
        self.assertNotIn("Silent reasoning", bare)

    def test_modulation_parse(self) -> None:
        from hermespace.access import AccessHub

        js = AccessHub(agent_id="mod-agent")
        m = js.parse_modulation("please hold: citrus fruits while copying")
        self.assertEqual(m["hold"], "citrus fruits while copying")
        m2 = js.parse_modulation("show desk")
        self.assertTrue(m2["summon"])

    def test_release(self) -> None:
        from hermespace.access import AccessHub

        js = AccessHub(agent_id="rel-agent")
        js.hold("temp concept")
        self.assertTrue(js.release("temp concept"))
        self.assertFalse(js.release("temp concept"))

    def test_sync_from_desk(self) -> None:
        from hermespace.desk import Desk
        from hermespace.access import AccessHub

        desk = Desk(
            goal="Ship Hermespace Access Workspace",
            concepts=["[verbal|0.8] FOA cap", "[struct|0.6] ACTIVE.md"],
            decision="A — implement",
            plan=["code", "test"],
            say="Building the workspace.",
        )
        desk.recompute_cognition("implement functional jspace")
        js = AccessHub(agent_id="sync-agent")
        st = js.sync_from_desk(desk, user_message="hold: arterial strip")
        self.assertGreaterEqual(len(st.hub), 1)
        self.assertTrue(any("arterial" in c.text.lower() for c in st.hub))


class TestCubeModuleStandalone(unittest.TestCase):
    def setUp(self) -> None:
        self._td = tempfile.TemporaryDirectory()
        self.root = Path(self._td.name)
        os.environ["HERMESPACE_HOME"] = str(self.root)
        # Force standalone even if hermescube is installed in the agent env
        import builtins

        real_import = builtins.__import__

        def _block_hermescube(name, *args, **kwargs):
            if name == "hermescube" or name.startswith("hermescube."):
                raise ImportError("blocked for standalone test")
            return real_import(name, *args, **kwargs)

        self._imp = mock.patch("builtins.__import__", side_effect=_block_hermescube)
        self._imp.start()

    def tearDown(self) -> None:
        self._imp.stop()
        self._td.cleanup()
        os.environ.pop("HERMESPACE_HOME", None)

    def test_ensure_and_status(self) -> None:
        from hermespace.cube_module import center_status, ensure_heart, heart_status

        eh = ensure_heart()
        self.assertTrue(eh.get("ok"))
        self.assertEqual(eh.get("mode"), "standalone")
        hs = heart_status()
        self.assertTrue(hs.get("standalone_ready"))
        cs = center_status()
        self.assertEqual(cs.get("mode"), "standalone")

    def test_seal_and_inject(self) -> None:
        from hermespace.cube_module import cube_beat, seal_learning

        rec = seal_learning(
            "Fast deploys reduce risk",
            entry_type="belief",
            agent_id="seal-agent",
        )
        self.assertTrue(rec.get("ok"))
        beat = cube_beat(
            "deploy",
            seals="Prefer blue-green",
            load=0.4,
            agent_id="seal-agent",
        )
        self.assertTrue(beat.get("ok"))
        self.assertIn("block", beat)
        self.assertEqual(beat.get("mode"), "standalone")

    def test_strip_budget(self) -> None:
        from hermespace.cube_module import normalize_load, strip_budget

        self.assertEqual(normalize_load(0.9), "protect")
        self.assertEqual(normalize_load(0.7), "high")
        self.assertEqual(strip_budget("protect"), 280)
        self.assertEqual(strip_budget("low"), 900)

    def test_pulse_standalone(self) -> None:
        from hermespace.cube_module import cube_pulse, seal_learning

        seal_learning("Standalone pulse belief", agent_id="pulse-agent")
        out = cube_pulse(agent_id="pulse-agent")
        self.assertTrue(out.get("ok"))
        self.assertEqual(out.get("mode"), "standalone")


class TestCubeModuleWhenAvailable(unittest.TestCase):
    """Soft checks — pass whether or not hermescube is installed."""

    def setUp(self) -> None:
        self._td = tempfile.TemporaryDirectory()
        os.environ["HERMESPACE_HOME"] = self._td.name
        os.environ["HERMES_HOME"] = self._td.name

    def tearDown(self) -> None:
        self._td.cleanup()
        os.environ.pop("HERMESPACE_HOME", None)
        os.environ.pop("HERMES_HOME", None)

    def test_beat_always_ok_shape(self) -> None:
        from hermespace.cube_module import cube_beat, center_status

        st = center_status()
        self.assertIn("mode", st)
        out = cube_beat("probe", load="mid", agent_id="avail-agent")
        self.assertIn("ok", out)
        self.assertIn("block", out)
        self.assertIn(out.get("mode"), ("center", "heart", "standalone"))


class TestWorkflowAccessHubIntegration(unittest.TestCase):
    def setUp(self) -> None:
        self._td = tempfile.TemporaryDirectory()
        self.root = Path(self._td.name)
        os.environ["HERMESPACE_HOME"] = str(self.root)

    def tearDown(self) -> None:
        self._td.cleanup()
        os.environ.pop("HERMESPACE_HOME", None)

    def test_turn_includes_access_meta(self) -> None:
        from hermespace.workflow import Workflow
        from hermespace.io_contract import HermespaceInput

        wf = Workflow()
        out = wf.run(
            HermespaceInput(
                message="hold: citrus while we plan the deploy",
                goal="Plan deploy",
                decision="A — plan",
                plan=["audit", "rollout"],
                say="Planning the deploy.",
                force=True,
                agent_id="wf-agent",
            )
        )
        self.assertFalse(out.skipped)
        self.assertIn("access", out.meta or {})
        self.assertIn("cube_beat", out.meta or {})
        # context should carry broadcast or warehouse strip
        self.assertTrue(out.context)


if __name__ == "__main__":
    unittest.main()
