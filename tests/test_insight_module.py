"""Insight cable — fail-soft, bounded card, never required."""

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


class TestInsightPresent(unittest.TestCase):
    def setUp(self) -> None:
        self._td = tempfile.TemporaryDirectory()
        os.environ["HERMESPACE_HOME"] = self._td.name
        self._plan_calls = {"n": 0}

        class _Lat:
            def perceive(self, situation, **kwargs):
                return {
                    "usable": True,
                    "lever": "shared-token",
                    "action_hint": "Give each worker its own credential.",
                    "confidence": 0.7,
                    "top_score": 0.4,
                    "matches": [
                        {
                            "title": "duplicate consumer",
                            "kind": "rule",
                            "score": 0.4,
                        }
                    ],
                }

            def plan(self, situation, **kwargs):
                return {"steps": [{"title": "isolate credentials first"}]}

        lat = _Lat()
        orig_plan = lat.plan

        def _plan(situation, **kwargs):
            self._plan_calls["n"] += 1
            return orig_plan(situation, **kwargs)

        lat.plan = _plan  # type: ignore[method-assign]

        pkg = types.ModuleType("hermes_insight")
        pkg.HermesInsight = lambda *a, **k: lat  # type: ignore[attr-defined]
        pkg.__version__ = "0.8.0-test"
        self._mod = mock.patch.dict(sys.modules, {"hermes_insight": pkg})
        self._mod.start()
        self._lat = lat

    def tearDown(self) -> None:
        self._mod.stop()
        self._td.cleanup()
        os.environ.pop("HERMESPACE_HOME", None)

    def test_bounded_card_and_plan_on_multistep(self) -> None:
        from hermespace.insight_module import insight_card, insight_status

        st = insight_status()
        self.assertTrue(st.get("available"))
        rec = insight_card(
            "two workers share one bot token",
            goal="First isolate credentials then restart finally verify",
            plan=["isolate", "restart", "verify"],
        )
        self.assertTrue(rec.get("ok"))
        self.assertTrue(rec.get("usable"))
        self.assertIn("shared-token", rec.get("card") or "")
        self.assertLessEqual(len(rec.get("card") or ""), 400)
        self.assertTrue(rec.get("planned"))
        self.assertEqual(self._plan_calls["n"], 1)
        self.assertNotIn("lattice", (rec.get("card") or "").lower())

    def test_no_plan_on_single_step(self) -> None:
        from hermespace.insight_module import insight_card

        rec = insight_card("what is the status", goal="status")
        self.assertTrue(rec.get("ok"))
        self.assertFalse(rec.get("planned"))
        self.assertEqual(self._plan_calls["n"], 0)

    def test_high_load_skip(self) -> None:
        from hermespace.insight_module import insight_card

        rec = insight_card(
            "First reproduce then patch then verify",
            high_load=True,
            plan=["a", "b"],
        )
        self.assertTrue(rec.get("ok"))
        self.assertEqual(rec.get("skipped"), "high_load")
        self.assertEqual(rec.get("card"), "")
        self.assertEqual(self._plan_calls["n"], 0)


class TestWorkflowInsightMeta(unittest.TestCase):
    def setUp(self) -> None:
        self._td = tempfile.TemporaryDirectory()
        os.environ["HERMESPACE_HOME"] = self._td.name

    def tearDown(self) -> None:
        self._td.cleanup()
        os.environ.pop("HERMESPACE_HOME", None)

    def test_turn_records_insight_meta(self) -> None:
        from hermespace.io_contract import HermespaceInput
        from hermespace.workflow import Workflow

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
        self.assertIn("insight", out.meta or {})
        self.assertIn((out.meta or {}).get("insight", {}).get("mode"), ("missing", "insight", "soft_fail", "skipped"))


if __name__ == "__main__":
    unittest.main()
