"""Cube-centered connect — agent gains world + J-Space + optional hive room."""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock


class TestConnectRoom(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        os.environ["HERMESPACE_HOME"] = self.tmp.name
        os.environ["HERMESPACE_OEW"] = "1"
        os.environ.pop("HERMESCUBE_HIVE", None)

    def tearDown(self) -> None:
        self.tmp.cleanup()
        os.environ.pop("HERMESPACE_HOME", None)
        os.environ.pop("HERMESPACE_OEW", None)
        os.environ.pop("HERMESCUBE_HIVE", None)

    def test_connect_standalone_gains_world_and_hub(self) -> None:
        from hermespace import HermesBase
        from hermespace.world import WorldModel

        aid = "connect-solo"
        wm = WorldModel(agent_id=aid)
        wm.add_belief("Deploys need canaries", 0.9, source="test")
        wm.add_belief("Prefer dual decode", 0.85, source="test")

        hb = HermesBase(agent_id=aid, session_id="s1")
        out = hb.connect(query="deploy")
        self.assertTrue(out.get("ok"), msg=out)
        gained = out.get("gained") or {}
        self.assertGreaterEqual(int(gained.get("world_beliefs") or 0), 1)
        self.assertGreaterEqual(int(gained.get("jspace_hub") or 0), 1)
        self.assertEqual(gained.get("room_mode"), "solo")
        self.assertRegex(out.get("summary") or "", r"(?i)connected")

        st = hb.status()
        self.assertTrue(st["ready"])
        self.assertTrue(st.get("connected"))
        self.assertGreaterEqual(int(st["jspace"].get("hub_n") or 0), 1)

    def test_room_solo_and_hive_env(self) -> None:
        import types

        from hermespace.cube_module import room_status

        solo = room_status(agent_id="a1")
        self.assertEqual(solo["mode"], "solo")
        self.assertFalse(solo["hive_configured"])

        hive = Path(self.tmp.name) / "hive"
        os.environ["HERMESCUBE_HIVE"] = str(hive)

        hive_mod = types.ModuleType("hermescube.hive")

        def hive_status(_root):
            return {"ok": True, "name": "test-hive", "entries": 3}

        def list_souls(_root):
            return [
                {"agent_id": "a1", "wisdom": ["self"]},
                {"agent_id": "peer-x", "wisdom": ["shared canary rule", "two"]},
            ]

        hive_mod.hive_status = hive_status  # type: ignore[attr-defined]
        hive_mod.list_souls = list_souls  # type: ignore[attr-defined]
        pkg = types.ModuleType("hermescube")
        with mock.patch.dict(
            "sys.modules",
            {"hermescube": pkg, "hermescube.hive": hive_mod},
        ):
            st = room_status(agent_id="a1")
        self.assertTrue(st["hive_configured"])
        self.assertEqual(st["mode"], "hive")
        self.assertEqual(st["peer_n"], 1)
        self.assertEqual(st["soul_n"], 2)

    def test_seed_peers_silent(self) -> None:
        from hermespace.cube_module import seed_jspace_from_warehouse
        from hermespace.jspace import JSpace

        aid = "peer-seed"
        room = {
            "mode": "hive",
            "souls": [
                {"agent_id": aid, "self": True, "wisdom_n": 0},
                {"agent_id": "alice-agent", "self": False, "wisdom_n": 3},
                {"agent_id": "bob-agent", "self": False, "wisdom_n": 1},
            ],
        }
        rep = seed_jspace_from_warehouse(aid, room=room)
        self.assertTrue(rep.get("ok"))
        self.assertGreaterEqual(int(rep.get("enriched_peers") or 0), 1)
        js = JSpace(agent_id=aid)
        labels = " ".join(c.text for c in js.state.hub).casefold()
        self.assertIn("alice-agent", labels)
        # Peer presence should be silent (not Report by default)
        silent_texts = " ".join(c.text for c in js.state.hub if c.silent).casefold()
        self.assertIn("peer agent", silent_texts)

    def test_hermes_base_think_autoconnect(self) -> None:
        from hermespace import HermesBase

        hb = HermesBase(agent_id="auto-conn")
        out = hb.think(
            "First analyze then implement finally verify",
            goal="Ship",
            say="On it.",
        )
        self.assertFalse(out["skipped"])
        self.assertTrue(out.get("connected"))


if __name__ == "__main__":
    unittest.main()
