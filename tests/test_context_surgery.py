"""Context budgets + skip-if-unneeded + self-trace. No consciousness claim."""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
import sys

sys.path.insert(0, str(ROOT / "src"))


class TestContextSurgery(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        os.environ["HERMESPACE_HOME"] = self.tmp.name
        os.environ["HERMESPACE_AGENT_ID"] = "surgery-agent"
        os.environ["HERMESPACE_SKIP_NEURAL"] = "1"
        os.environ["HERMESPACE_NEURAL_VERBALIZE"] = "0"
        os.environ["HERMESPACE_AUTO_ORDER"] = "0"

    def tearDown(self) -> None:
        self.tmp.cleanup()
        for key in (
            "HERMESPACE_HOME",
            "HERMESPACE_AGENT_ID",
            "HERMESPACE_SKIP_NEURAL",
            "HERMESPACE_NEURAL_VERBALIZE",
            "HERMESPACE_AUTO_ORDER",
        ):
            os.environ.pop(key, None)

    def test_budgets_and_fluent_ack(self) -> None:
        from hermespace.context_surgery import (
            HIGH_INJECT_CAP,
            INJECT_HARD_CAP,
            MID_INJECT_CAP,
            assemble_inject,
            inject_budget,
            is_fluent_ack,
            sanitize_inject,
            strip_needed,
        )

        self.assertEqual(MID_INJECT_CAP, 2800)
        self.assertEqual(HIGH_INJECT_CAP, 900)
        self.assertLess(INJECT_HARD_CAP, 9000)
        self.assertEqual(inject_budget("mid"), 2800)
        self.assertEqual(inject_budget("high"), 900)
        self.assertTrue(is_fluent_ack("got it"))
        self.assertTrue(is_fluent_ack("thanks"))
        self.assertFalse(is_fluent_ack("First build then verify"))
        self.assertFalse(strip_needed(message="ok", load_level="mid"))
        self.assertFalse(
            strip_needed(message="First build then verify", load_level="high")
        )
        self.assertTrue(
            strip_needed(
                message="First build then verify",
                load_level="high",
                is_first_turn=True,
            )
        )
        blob = assemble_inject(["a" * 4000, "b" * 4000], budget=2800)
        self.assertLessEqual(len(blob), 2800)
        from hermespace.context_surgery import silent_chain_strip

        t2 = "Now write the install section."
        strip = silent_chain_strip(
            [
                "older-noise",
                "Write the README",
                "Stop",
                t2,
            ],
            t2,
        )
        self.assertIn("### Silent (prior)", strip)
        self.assertIn("Stop", strip)
        self.assertIn("Write the README", strip)
        self.assertNotIn("older-noise", strip)
        self.assertNotIn(t2, strip)
        self.assertNotIn("What Hermes has on its mind", strip)
        self.assertNotIn("J-Lens", strip)
        self.assertLessEqual(strip.count("\n- "), 3)
        self.assertEqual(silent_chain_strip([], t2), "")
        dirty = sanitize_inject("keep\nJ-Lens readout: secret\ntrue self-conscious\nok")
        self.assertIn("keep", dirty)
        self.assertNotIn("J-Lens", dirty)
        self.assertNotIn("true self-conscious", dirty)

    def test_pre_llm_skips_fluent_and_respects_mid_cap(self) -> None:
        from hermespace.hermes_bridge import on_pre_llm_call, on_session_start

        on_session_start(session_id="surgery-mid")
        self.assertIsNone(
            on_pre_llm_call(
                user_message="got it",
                session_id="surgery-mid",
                is_first_turn=False,
            )
        )
        inj = on_pre_llm_call(
            user_message="First inspect then implement finally verify",
            session_id="surgery-mid",
            is_first_turn=False,
        )
        self.assertIsNotNone(inj)
        ctx = (inj or {}).get("context") or ""
        self.assertLessEqual(len(ctx), 2800)
        self.assertIn("Access Workspace", ctx)
        self.assertIn("next action", ctx)
        self.assertNotIn("J-Lens readout", ctx)
        self.assertNotIn("What Hermes has on its mind", ctx)
        self.assertNotIn("### Workbench", ctx)
        self.assertNotIn("### Hermespace runtime", ctx)
        self.assertNotIn("dream_harvest", ctx)
        self.assertNotIn("true self-conscious", ctx)
        self.assertNotIn("phenomenal consciousness", ctx)

    def test_pre_llm_appends_hub_silent_after_bound(self) -> None:
        from hermespace.access import AccessHub
        from hermespace.access.engine import workspace_id
        from hermespace.hermes_bridge import on_pre_llm_call, on_session_start

        on_session_start(session_id="surgery-silent")
        js = AccessHub(agent_id=workspace_id("surgery-agent", "surgery-silent"))
        js.reason_step("Stop", salience=0.82)
        js.save()
        inj = on_pre_llm_call(
            user_message="Now write the install section.",
            session_id="surgery-silent",
            is_first_turn=False,
        )
        ctx = (inj or {}).get("context") or ""
        self.assertTrue(ctx, inj)
        self.assertLessEqual(len(ctx), 2800)
        self.assertIn("### Silent (prior)", ctx)
        self.assertIn("Stop", ctx.split("### Silent (prior)", 1)[-1])
        self.assertNotIn(
            "Now write the install section.",
            ctx.split("### Silent (prior)", 1)[-1],
        )
        self.assertNotIn("J-Lens readout", ctx)
        self.assertNotIn("What Hermes has on its mind", ctx)

    def test_high_load_injects_nothing_without_bind(self) -> None:
        from hermespace import AccessEngine
        from hermespace.hermes_bridge import on_pre_llm_call, on_session_start
        from hermespace.store import load_desk, save_desk

        on_session_start(session_id="surgery-high")
        eng = AccessEngine(agent_id="surgery-agent", session_id="surgery-high")
        desk = load_desk(eng.desk_engine.desk_path)
        desk.load = {"level": "protect", "total": 0.8}
        save_desk(desk, eng.desk_engine.desk_path)
        inj = on_pre_llm_call(
            user_message="First build the feature then verify please",
            session_id="surgery-high",
            is_first_turn=False,
        )
        self.assertIsNone(inj)

    def test_subagent_does_not_inject_full_copy(self) -> None:
        from hermespace.hermes_bridge import (
            on_pre_llm_call,
            on_session_start,
            on_subagent_start,
        )

        on_session_start(session_id="surgery-child")
        on_subagent_start(session_id="surgery-child", task_id="t1")
        inj = on_pre_llm_call(
            user_message="First inspect then implement finally verify",
            session_id="surgery-child",
            is_first_turn=False,
        )
        self.assertIsNone(inj)

    def test_insight_writeback_stays_on_desk_meta(self) -> None:
        from hermespace import AccessEngine
        from hermespace.hermes_bridge import on_pre_llm_call, on_session_start
        from hermespace.store import load_desk

        on_session_start(session_id="surgery-insight")
        with mock.patch(
            "hermespace.insight_module.insight_card",
            return_value={
                "ok": True,
                "mode": "insight",
                "card": "### Insight\n- lever: test",
                "writeback": {"usable": "ship", "lever": "test"},
            },
        ):
            inj = on_pre_llm_call(
                user_message="First build the feature then verify please",
                session_id="surgery-insight",
                is_first_turn=False,
            )
        ctx = (inj or {}).get("context") or ""
        self.assertIn("### Insight", ctx)
        self.assertNotIn("insight_lattice", ctx)
        desk = load_desk(
            AccessEngine(
                agent_id="surgery-agent", session_id="surgery-insight"
            ).desk_engine.desk_path
        )
        self.assertEqual((desk.meta or {}).get("insight_writeback", {}).get("lever"), "test")


class TestSelfModel(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        os.environ["HERMESPACE_HOME"] = self.tmp.name
        os.environ["HERMESPACE_AGENT_ID"] = "trace-agent"

    def tearDown(self) -> None:
        self.tmp.cleanup()
        os.environ.pop("HERMESPACE_HOME", None)
        os.environ.pop("HERMESPACE_AGENT_ID", None)

    def test_self_trace_capped_and_on_hub(self) -> None:
        from hermespace import AccessEngine
        from hermespace.access.loop import park_tool_step
        from hermespace.grid.viewport import snapshot
        from hermespace.self_model import format_self_trace, read_self_trace

        eng = AccessEngine(agent_id="trace-agent", session_id="default")
        park_tool_step(eng.hub, "read_file")
        out = eng.observe_turn(
            user_message="fix auth",
            assistant_response="Patched TTL. Next: verify login.",
        )
        self.assertTrue(out.get("self_trace"), out)
        trace = read_self_trace(eng.hub)
        self.assertLessEqual(len(trace.get("goal") or ""), 120)
        self.assertLessEqual(len(trace.get("report") or ""), 160)
        self.assertTrue(any(str(t).startswith("tool:") for t in (trace.get("tools") or [])))
        painted = format_self_trace(trace, for_inject=True)
        self.assertLessEqual(len(painted), 280)
        self.assertNotIn("true self-conscious", painted)
        view = eng.env.operator_view()
        self.assertIn("self_trace", view)
        self.assertIn("self-trace", view["theory"]["self_model"])
        self.assertNotIn("true self-conscious", view["theory"]["self_model"])
        foa = snapshot("trace-agent")["foa"]
        self.assertIn("self_trace", foa)
        self.assertTrue(foa["self_trace"].get("report"))

    def test_improve_seals_cube_not_world(self) -> None:
        from hermespace.desk import Desk
        from hermespace.self_model import maybe_seal_improve

        desk = Desk()
        desk.meta["learn"] = "Prefer one live goal."
        with mock.patch("hermespace.cube_module.seal_learning") as seal:
            seal.return_value = {"ok": True, "mode": "cube"}
            rec = maybe_seal_improve(desk, agent_id="trace-agent")
        self.assertTrue(rec.get("ok"))
        seal.assert_called_once()
        self.assertEqual(rec.get("warehouse"), "cube")
        empty = maybe_seal_improve(Desk(), agent_id="trace-agent")
        self.assertEqual(empty.get("skipped"), "no_learning")


if __name__ == "__main__":
    unittest.main()
