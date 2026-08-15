"""Insight cable — perceive_card only, fail-soft, never required."""

from __future__ import annotations

import os
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


class TestInsightMissing(unittest.TestCase):
    def setUp(self) -> None:
        self._td = tempfile.TemporaryDirectory()
        os.environ["HERMESPACE_HOME"] = self._td.name
        import builtins

        real_import = builtins.__import__

        def _block(name, *args, **kwargs):
            if name == "hermes_insight" or name.startswith("hermes_insight."):
                raise ImportError("blocked for missing-insight test")
            return real_import(name, *args, **kwargs)

        self._imp = mock.patch("builtins.__import__", side_effect=_block)
        self._imp.start()

    def tearDown(self) -> None:
        self._imp.stop()
        self._td.cleanup()
        os.environ.pop("HERMESPACE_HOME", None)

    def test_status_and_card_soft_fail(self) -> None:
        from hermespace.insight_module import insight_available, insight_card, insight_status

        self.assertFalse(insight_available())
        st = insight_status()
        self.assertFalse(st.get("available"))
        self.assertFalse(st.get("required"))
        rec = insight_card("First reproduce then patch then verify")
        self.assertTrue(rec.get("ok"))
        self.assertEqual(rec.get("mode"), "missing")
        self.assertEqual(rec.get("card"), "")


class TestInsightNoPerceiveCard(unittest.TestCase):
    def setUp(self) -> None:
        self._td = tempfile.TemporaryDirectory()
        os.environ["HERMESPACE_HOME"] = self._td.name
        self._perceive_calls = {"n": 0}
        self._plan_calls = {"n": 0}

        class _Lat:
            def perceive(self_lat, situation, **kwargs):
                self._perceive_calls["n"] += 1
                return {
                    "card": "UNBOUNDED LATTICE DUMP " + ("x" * 800),
                    "usable": True,
                    "matches": [{"title": "should-not-appear"}],
                }

            def plan(self_lat, situation, **kwargs):
                self._plan_calls["n"] += 1
                return {"steps": [{"title": "should-not-plan"}]}

        pkg = types.ModuleType("hermes_insight")
        pkg.HermesInsight = _Lat  # type: ignore[attr-defined]
        pkg.__version__ = "0.8.0-test"
        self.assertFalse(hasattr(pkg.HermesInsight, "perceive_card"))
        self._mod = mock.patch.dict(sys.modules, {"hermes_insight": pkg})
        self._mod.start()

    def tearDown(self) -> None:
        self._mod.stop()
        self._td.cleanup()
        os.environ.pop("HERMESPACE_HOME", None)

    def test_skip_until_perceive_card_exists(self) -> None:
        from hermespace.insight_module import insight_available, insight_card, insight_status

        self.assertFalse(insight_available())
        st = insight_status()
        self.assertEqual(st.get("mode"), "no_perceive_card")
        rec = insight_card("two workers share one bot token", load="mid")
        self.assertTrue(rec.get("ok"))
        self.assertEqual(rec.get("skipped"), "no_perceive_card")
        self.assertEqual(rec.get("card"), "")
        self.assertEqual(self._perceive_calls["n"], 0)
        self.assertEqual(self._plan_calls["n"], 0)
        self.assertNotIn("UNBOUNDED", rec.get("card") or "")


class TestInsightPerceiveCard(unittest.TestCase):
    def setUp(self) -> None:
        self._td = tempfile.TemporaryDirectory()
        os.environ["HERMESPACE_HOME"] = self._td.name
        self._calls = {"perceive_card": 0, "perceive": 0, "plan": 0, "recall": 0}
        self._last_load = None
        outer = self

        class _Cls:
            def __init__(self, *a, **k):
                pass

            def perceive_card(self, goal, load=None, **kwargs):
                outer._calls["perceive_card"] += 1
                outer._last_load = load
                return (
                    "### Insight\n- lever: shared-token\n"
                    "- rule: duplicate consumer\n- usable: true\n"
                    "- hint: Give each worker its own credential."
                )

            def perceive(self, situation, **kwargs):
                outer._calls["perceive"] += 1
                return {"card": "UNBOUNDED " + ("x" * 800)}

            def plan(self, situation, **kwargs):
                outer._calls["plan"] += 1
                return {"steps": [{"title": "should-not-plan"}]}

            def recall(self, *a, **k):
                outer._calls["recall"] = outer._calls.get("recall", 0) + 1
                return {"brief": "SHOULD-NOT-INJECT-RECALL-BRIEF"}

        pkg = types.ModuleType("hermes_insight")
        pkg.HermesInsight = _Cls  # type: ignore[attr-defined]
        pkg.__version__ = "0.9.0-test"
        self._mod = mock.patch.dict(sys.modules, {"hermes_insight": pkg})
        self._mod.start()

    def tearDown(self) -> None:
        self._mod.stop()
        self._td.cleanup()
        os.environ.pop("HERMESPACE_HOME", None)

    def test_appends_bounded_perceive_card_only(self) -> None:
        from hermespace.insight_module import insight_available, insight_card, insight_status

        self.assertTrue(insight_available())
        self.assertEqual(insight_status().get("mode"), "insight")
        rec = insight_card("First isolate credentials then restart", load="mid")
        self.assertTrue(rec.get("ok"))
        self.assertIn("shared-token", rec.get("card") or "")
        self.assertLessEqual(len(rec.get("card") or ""), 400)
        self.assertEqual(self._calls["perceive_card"], 1)
        self.assertEqual(self._calls["perceive"], 0)
        self.assertEqual(self._calls["plan"], 0)
        self.assertEqual(self._calls["recall"], 0)
        self.assertEqual(self._last_load, "mid")
        self.assertNotIn("SHOULD-NOT-INJECT", rec.get("card") or "")

    def test_high_and_protect_skip(self) -> None:
        from hermespace.insight_module import insight_card

        for load in ("high", "protect", 0.7, 0.9):
            rec = insight_card("First reproduce then patch then verify", load=load)
            self.assertTrue(rec.get("ok"), load)
            self.assertEqual(rec.get("skipped"), "high_load", load)
            self.assertEqual(rec.get("card"), "", load)
        self.assertEqual(self._calls["perceive_card"], 0)
        self.assertEqual(self._calls["plan"], 0)

        rec = insight_card("goal", high_load=True, load="low")
        self.assertEqual(rec.get("skipped"), "high_load")
        self.assertEqual(self._calls["perceive_card"], 0)

    def test_caps_returned_card(self) -> None:
        from hermespace.insight_module import insight_card

        huge = "Y" * 900

        def _huge(*_a, **_k):
            self._calls["perceive_card"] += 1
            return huge

        with mock.patch.object(
            sys.modules["hermes_insight"].HermesInsight,
            "perceive_card",
            _huge,
        ):
            rec = insight_card("a long goal", load="low")
        self.assertTrue(rec.get("ok"))
        self.assertLessEqual(len(rec.get("card") or ""), 400)
        self.assertTrue((rec.get("card") or "").endswith("..."))


class TestWorkflowDoesNotHangInsight(unittest.TestCase):
    def setUp(self) -> None:
        self._td = tempfile.TemporaryDirectory()
        os.environ["HERMESPACE_HOME"] = self._td.name

    def tearDown(self) -> None:
        self._td.cleanup()
        os.environ.pop("HERMESPACE_HOME", None)

    def test_turn_does_not_inject_insight_strip(self) -> None:
        from hermespace.io_contract import HermespaceInput
        from hermespace.workflow import Workflow

        with mock.patch("hermespace.insight_module.insight_card") as mocked:
            out = Workflow().run(
                HermespaceInput(
                    message="First inspect then implement finally verify",
                    goal="Ship the fix",
                    decision="A — implement",
                    plan=["inspect", "implement", "verify"],
                    say="Working the fix.",
                    force=True,
                    agent_id="insight-wf",
                )
            )
            self.assertFalse(out.skipped)
            mocked.assert_not_called()
            self.assertNotIn("insight", out.meta or {})


class TestPreLlmHangsInsightNextToCube(unittest.TestCase):
    def setUp(self) -> None:
        self._td = tempfile.TemporaryDirectory()
        os.environ["HERMESPACE_HOME"] = self._td.name
        os.environ["HERMESPACE_NEURAL_VERBALIZE"] = "0"
        os.environ["HERMESPACE_AUTO_ORDER"] = "0"

    def tearDown(self) -> None:
        self._td.cleanup()
        for key in (
            "HERMESPACE_HOME",
            "HERMESPACE_NEURAL_VERBALIZE",
            "HERMESPACE_AUTO_ORDER",
        ):
            os.environ.pop(key, None)

    def test_pre_llm_appends_perceive_card(self) -> None:
        from hermespace.hermes_bridge import on_pre_llm_call, on_session_start

        on_session_start(session_id="insight-bridge")
        with mock.patch(
            "hermespace.insight_module.insight_card",
            return_value={"ok": True, "mode": "insight", "card": "### Insight\n- lever: test"},
        ) as mocked:
            inj = on_pre_llm_call(
                user_message="First build the feature then verify please",
                session_id="insight-bridge",
                is_first_turn=False,
            )
        self.assertIsNotNone(inj)
        mocked.assert_called()
        self.assertIn("### Insight", (inj or {}).get("context") or "")

    def test_pre_llm_skips_insight_on_high_load(self) -> None:
        from hermespace import AccessEngine
        from hermespace.hermes_bridge import on_pre_llm_call, on_session_start
        from hermespace.store import load_desk, save_desk

        on_session_start(session_id="insight-high")
        eng = AccessEngine(agent_id="hermes-agent", session_id="insight-high")
        desk = load_desk(eng.desk_engine.desk_path)
        desk.load = {"level": "protect", "total": 0.8}
        save_desk(desk, eng.desk_engine.desk_path)

        with mock.patch(
            "hermespace.insight_module.insight_card",
            wraps=None,
        ) as mocked:
            mocked.return_value = {"ok": True, "mode": "skipped", "skipped": "high_load", "card": ""}
            inj = on_pre_llm_call(
                user_message="First build the feature then verify please",
                session_id="insight-high",
                is_first_turn=False,
            )
        mocked.assert_called()
        ctx = (inj or {}).get("context") or ""
        self.assertNotIn("### Insight", ctx)
        # high load + no bind → inject nothing (strip not needed)
        self.assertTrue(inj is None or "### Insight" not in ctx)


if __name__ == "__main__":
    unittest.main()
