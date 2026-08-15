"""Current Hermes Agent v0.20 plugin host contract."""

from __future__ import annotations

import argparse
import os
import tempfile
import unittest
from pathlib import Path
from typing import Any


class FakeContext:
    def __init__(self) -> None:
        self.hooks: dict[str, Any] = {}
        self.commands: dict[str, Any] = {}
        self.cli: dict[str, Any] = {}
        self.skills: dict[str, Path] = {}

    def register_hook(self, name: str, callback: Any) -> None:
        self.hooks[name] = callback

    def register_command(self, name: str, handler: Any, **kwargs: Any) -> None:
        self.commands[name] = {"handler": handler, **kwargs}

    def register_cli_command(self, **kwargs: Any) -> None:
        self.cli[kwargs["name"]] = kwargs

    def register_skill(self, name: str, path: Path) -> None:
        self.skills[name] = Path(path)


class TestPluginContract(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        os.environ["HERMESPACE_HOME"] = self.tmp.name
        os.environ["HERMESPACE_AGENT_ID"] = "plugin-contract"
        os.environ["HERMESPACE_SKIP_NEURAL"] = "1"

    def tearDown(self) -> None:
        self.tmp.cleanup()
        os.environ.pop("HERMESPACE_HOME", None)
        os.environ.pop("HERMESPACE_AGENT_ID", None)
        os.environ.pop("HERMESPACE_SKIP_NEURAL", None)

    def test_registration_and_native_lifecycle(self) -> None:
        from hermespace.plugin import register

        ctx = FakeContext()
        register(ctx)
        required = {
            "on_session_start",
            "pre_llm_call",
            "post_llm_call",
            "post_tool_call",
            "on_session_end",
            "on_session_finalize",
        }
        self.assertTrue(required.issubset(ctx.hooks), ctx.hooks)
        self.assertIn("hermespace", ctx.commands)
        self.assertIn("hermespace", ctx.cli)

        common = {
            "session_id": "native-session",
            "model": "test/model",
            "platform": "cli",
        }
        ctx.hooks["on_session_start"](**common)
        result = ctx.hooks["pre_llm_call"](
            **common,
            user_message="First inspect, then implement, finally verify",
            conversation_history=[],
            is_first_turn=True,
        )
        self.assertIsInstance(result, dict)
        self.assertIn("Access Workspace", result["context"])
        self.assertNotIn("J-Lens readout", result["context"])
        self.assertLess(len(result["context"]), 15_000)

        ctx.hooks["post_tool_call"](
            **common,
            tool_name="read_file",
            args={"secret": "must-not-persist"},
            result="private result",
            task_id="native-session",
            duration_ms=1,
        )
        ctx.hooks["post_llm_call"](
            **common,
            user_message="implement",
            assistant_response="Implemented and verified.",
            conversation_history=[],
        )
        ctx.hooks["on_session_end"](
            **common,
            completed=True,
            interrupted=False,
        )

        from hermespace.hermes_runtime import runtime

        before = runtime.status("native-session")
        self.assertFalse(before["finalized"])
        self.assertEqual(before["completed_turns"], 1)
        self.assertEqual(before["tool_calls"], 1)
        serialized = str(before)
        self.assertNotIn("must-not-persist", serialized)
        self.assertNotIn("private result", serialized)

        ctx.hooks["on_session_finalize"](**common)
        after = runtime.status("native-session")
        self.assertTrue(after["finalized"])
        ctx.hooks["on_session_finalize"](**common)  # idempotent

    def test_plugin_yaml_hygiene(self) -> None:
        text = (Path(__file__).resolve().parents[1] / "plugin.yaml").read_text(encoding="utf-8")
        expected = [
            "on_session_start",
            "pre_llm_call",
            "post_llm_call",
            "post_tool_call",
            "on_session_end",
            "on_session_finalize",
            "on_session_reset",
            "subagent_start",
            "subagent_stop",
        ]
        self.assertIn("provides_hooks:", text)
        self.assertIn("python_dependencies:", text)
        self.assertIn("numpy>=1.24,<3", text)
        after = text.split("provides_hooks:", 1)[1].split("python_dependencies:", 1)[0]
        for hook in expected:
            self.assertIn(f"- {hook}", after)

    def test_commands_are_operational(self) -> None:
        from hermespace.plugin import register

        ctx = FakeContext()
        register(ctx)
        output = ctx.commands["hermespace"]["handler"]("metrics")
        self.assertIn("hub_cap", output)

        parser = argparse.ArgumentParser()
        cli = ctx.cli["hermespace"]
        cli["setup_fn"](parser)
        args = parser.parse_args(["status"])
        self.assertEqual(args.action, "status")


if __name__ == "__main__":
    unittest.main()
