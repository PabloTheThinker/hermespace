"""AccessEngine — unified open-source J-space for Hermes Agent."""

from __future__ import annotations

import os
import tempfile
import unittest


class TestAccessEngine(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        os.environ["HERMESPACE_HOME"] = self.tmp.name
        os.environ["HERMESPACE_OEW"] = "1"
        os.environ.pop("HERMESCUBE_HIVE", None)

    def tearDown(self) -> None:
        self.tmp.cleanup()
        os.environ.pop("HERMESPACE_HOME", None)
        os.environ.pop("HERMESPACE_OEW", None)

    def test_connect_and_access_roles(self) -> None:
        from hermespace import ACCESS_ROLES, AccessEngine
        from hermespace.world import WorldModel

        aid = "eng-connect"
        wm = WorldModel(agent_id=aid)
        wm.add_belief("Prefer dual decode", 0.9, source="test")

        eng = AccessEngine(agent_id=aid)
        out = eng.connect(query="decode")
        self.assertTrue(out.get("ok"), msg=out)
        self.assertEqual(out.get("engine"), "AccessEngine")
        self.assertEqual(list(out.get("access_roles") or []), list(ACCESS_ROLES))
        self.assertGreaterEqual(int((out.get("gained") or {}).get("access_hub") or 0), 1)

        roles = eng.access_roles()
        for name in ACCESS_ROLES:
            self.assertIn(name, roles)
            self.assertTrue(roles[name].get("ok"))

        st = eng.status()
        self.assertTrue(st["ready"])
        self.assertEqual(st["engine"], "AccessEngine")
        self.assertIn("hub_pressure", st["metrics"])

    def test_chain_silent_not_in_user_report(self) -> None:
        from hermespace import AccessEngine

        eng = AccessEngine(agent_id="eng-chain")
        eng.chain("animal spins webs → spider", "spider has 8 legs")
        rep = eng.report(include_silent=False).casefold()
        full = eng.report(include_silent=True).casefold()
        self.assertIn("spider", full)
        # default report should not dump Silent reasoning section
        self.assertNotIn("silent reasoning", rep)
        m = eng.metrics()
        self.assertGreaterEqual(m["silent_n"], 2)

    def test_inject_silent_no_double_hold(self) -> None:
        from hermespace import AccessEngine

        eng = AccessEngine(agent_id="eng-inject")
        before = len(eng.hub.state.hub)
        eng.inject("lightning", silent=True)
        # Exactly one hub entry for lightning (not hold + reason_step duplicate)
        hits = [c for c in eng.hub.state.hub if "lightning" in c.text.casefold()]
        self.assertEqual(len(hits), 1, msg=[c.text for c in eng.hub.state.hub])
        self.assertTrue(hits[0].silent)
        self.assertEqual(len(eng.hub.state.hub), before + 1)

    def test_probe_selectivity(self) -> None:
        from hermespace import AccessEngine

        eng = AccessEngine(agent_id="eng-probe")
        trivial = eng.probe_material("thanks!")
        material = eng.probe_material(
            "First implement the auth fix then verify login stays alive"
        )
        self.assertFalse(trivial.get("material"))
        self.assertTrue(material.get("material"), msg=material)

    def test_turn_dual_decode(self) -> None:
        from hermespace import AccessEngine

        eng = AccessEngine(agent_id="eng-turn")
        out = eng.turn(
            "First analyze then implement finally verify",
            goal="Ship feature",
            say="On it.",
        )
        self.assertFalse(out.skipped)
        user = eng.decode_user(out)
        model = eng.decode_model(out)
        self.assertTrue(user)
        self.assertNotEqual(user.strip(), model.strip())
        self.assertIn("Access Workspace", model)
        self.assertTrue((out.meta or {}).get("access", {}).get("oew_ok") is not False)

    def test_hermes_base_is_engine(self) -> None:
        from hermespace import HermesBase, AccessEngine

        self.assertTrue(issubclass(HermesBase, AccessEngine))
        hb = HermesBase(agent_id="alias")
        self.assertEqual(hb.status()["engine"], "AccessEngine")

    def test_sessions_have_isolated_hubs_and_desks(self) -> None:
        from hermespace import AccessEngine

        first = AccessEngine(agent_id="shared-agent", session_id="session-a")
        second = AccessEngine(agent_id="shared-agent", session_id="session-b")
        self.assertNotEqual(first.workspace_id, second.workspace_id)
        self.assertNotEqual(first.desk_engine.desk_path, second.desk_engine.desk_path)

        first.hold("private-to-session-a")
        self.assertIn("private-to-session-a", first.lens())
        self.assertNotIn("private-to-session-a", second.lens())


if __name__ == "__main__":
    unittest.main()
