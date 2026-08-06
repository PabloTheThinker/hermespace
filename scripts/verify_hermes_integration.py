#!/usr/bin/env python3
"""Hermes v0.20 host-contract verification for installed Hermespace.

This executes the repository plugin entry point with a faithful minimal
PluginContext, then drives the native lifecycle.  It uses an isolated state
home and never requires credentials, a model, Ollama, or HermesCube.
"""

from __future__ import annotations

import importlib.util
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


class HostContext:
    def __init__(self) -> None:
        self.hooks: dict[str, Any] = {}
        self.commands: dict[str, Any] = {}
        self.cli_commands: dict[str, Any] = {}
        self.skills: dict[str, Path] = {}

    def register_hook(self, name: str, callback: Any) -> None:
        self.hooks[name] = callback

    def register_command(
        self,
        name: str,
        handler: Any,
        description: str = "",
        args_hint: str = "",
    ) -> None:
        self.commands[name] = {
            "handler": handler,
            "description": description,
            "args_hint": args_hint,
        }

    def register_cli_command(self, **kwargs: Any) -> None:
        self.cli_commands[str(kwargs["name"])] = kwargs

    def register_skill(self, name: str, path: Path) -> None:
        self.skills[name] = Path(path)


def _load_repo_plugin() -> Any:
    spec = importlib.util.spec_from_file_location(
        "hermespace_repo_plugin",
        ROOT / "__init__.py",
        submodule_search_locations=[str(ROOT)],
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load repository plugin entry point")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="hermespace-host-contract-") as tmp:
        old_home = os.environ.get("HERMESPACE_HOME")
        old_agent = os.environ.get("HERMESPACE_AGENT_ID")
        os.environ["HERMESPACE_HOME"] = tmp
        os.environ["HERMESPACE_AGENT_ID"] = "contract-agent"
        os.environ["HERMESPACE_NEURAL_VERBALIZE"] = "0"
        os.environ["HERMESPACE_SKIP_NEURAL"] = "1"
        try:
            module = _load_repo_plugin()
            ctx = HostContext()
            module.register(ctx)

            required = {
                "on_session_start",
                "pre_llm_call",
                "post_llm_call",
                "post_tool_call",
                "on_session_end",
                "on_session_finalize",
            }
            missing = sorted(required - set(ctx.hooks))
            if missing:
                raise AssertionError(f"missing hooks: {missing}")
            if "hermespace" not in ctx.commands:
                raise AssertionError("/hermespace command not registered")
            if "hermespace" not in ctx.cli_commands:
                raise AssertionError("hermes hermespace command not registered")

            common = {
                "session_id": "contract-session",
                "model": "test/model",
                "platform": "cli",
            }
            ctx.hooks["on_session_start"](**common)
            injected = ctx.hooks["pre_llm_call"](
                **common,
                user_message="First inspect the issue, then fix it and verify the result",
                conversation_history=[],
                is_first_turn=True,
            )
            if not isinstance(injected, dict) or not injected.get("context"):
                raise AssertionError("pre_llm_call did not inject context")
            if len(str(injected["context"])) > 15_000:
                raise AssertionError("hook context exceeded 15,000 chars")

            ctx.hooks["post_tool_call"](
                **common,
                tool_name="read_file",
                args={"path": "redacted"},
                result='{"ok": true}',
                task_id="contract-session",
                duration_ms=1,
            )
            ctx.hooks["post_llm_call"](
                **common,
                user_message="fix and verify",
                assistant_response="Implemented and verified.",
                conversation_history=[],
            )
            ctx.hooks["on_session_end"](
                **common,
                completed=True,
                interrupted=False,
            )

            from hermespace.hermes_runtime import runtime

            before = runtime.status("contract-session")
            if before.get("finalized"):
                raise AssertionError("on_session_end incorrectly finalized the session")
            ctx.hooks["on_session_finalize"](**common)
            after = runtime.status("contract-session")
            if not after.get("finalized"):
                raise AssertionError("on_session_finalize did not finalize runtime state")
            # Host teardown paths may converge; finalization must be idempotent.
            ctx.hooks["on_session_finalize"](**common)

            command_output = ctx.commands["hermespace"]["handler"]("runtime")
            if "tracked_sessions" not in command_output:
                raise AssertionError("/hermespace runtime returned unexpected output")

            report = {
                "ok": True,
                "hooks": sorted(ctx.hooks),
                "slash_command": True,
                "cli_command": True,
                "skill": "hermespace" in ctx.skills,
                "context_chars": len(str(injected["context"])),
                "turns": after.get("completed_turns"),
                "tools": after.get("tool_calls"),
                "finalized": after.get("finalized"),
            }
            print(json.dumps(report, indent=2))
            return 0
        finally:
            if old_home is None:
                os.environ.pop("HERMESPACE_HOME", None)
            else:
                os.environ["HERMESPACE_HOME"] = old_home
            if old_agent is None:
                os.environ.pop("HERMESPACE_AGENT_ID", None)
            else:
                os.environ["HERMESPACE_AGENT_ID"] = old_agent


if __name__ == "__main__":
    raise SystemExit(main())
