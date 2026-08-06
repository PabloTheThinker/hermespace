"""First-class Hermes Agent v0.20 plugin registration.

This module is both the wheel entry point and the implementation used by the
source-tree plugin wrappers.  Keeping registration inside the installed
package prevents the "enabled but no-op" split between checkout and pip modes.
"""

from __future__ import annotations

import json
import logging
from typing import Any

logger = logging.getLogger("hermes.plugins.hermespace")


def _status_payload(action: str = "status") -> Any:
    from hermespace import AccessEngine

    engine = AccessEngine()
    action = (action or "status").strip().lower()
    if action in {"status", "show"}:
        return engine.status()
    if action == "metrics":
        return engine.metrics()
    if action == "roles":
        return engine.access_roles()
    if action == "lens":
        return engine.lens(top_k=8, include_silent=False)
    if action == "runtime":
        from hermespace.hermes_runtime import runtime

        return runtime.status()
    if action == "doctor":
        from hermespace.ops import doctor

        return doctor(agent_id=engine.agent_id)
    return {
        "ok": False,
        "error": f"unknown action: {action}",
        "actions": ["status", "metrics", "roles", "lens", "runtime", "doctor"],
    }


def _slash_command(raw_args: str) -> str:
    payload = _status_payload((raw_args or "").strip() or "status")
    if isinstance(payload, str):
        return payload[:6000]
    return json.dumps(payload, indent=2, default=str)[:6000]


def _setup_cli(parser: Any) -> None:
    parser.add_argument(
        "action",
        nargs="?",
        default="status",
        choices=("status", "metrics", "roles", "lens", "runtime", "doctor"),
    )


def _handle_cli(args: Any) -> int:
    print(json.dumps(_status_payload(args.action), indent=2, default=str))
    return 0


def register(ctx: Any) -> None:
    """Register the supported Hermes v0.20 hooks and operator commands."""

    from hermespace import __version__
    from hermespace.hermes_bridge import (
        on_post_llm_call,
        on_post_tool_call,
        on_pre_llm_call,
        on_session_end,
        on_session_finalize,
        on_session_reset,
        on_session_start,
        on_subagent_start,
        on_subagent_stop,
    )

    hooks = {
        "on_session_start": on_session_start,
        "pre_llm_call": on_pre_llm_call,
        "post_llm_call": on_post_llm_call,
        "post_tool_call": on_post_tool_call,
        "on_session_end": on_session_end,
        "on_session_finalize": on_session_finalize,
        "on_session_reset": on_session_reset,
        "subagent_start": on_subagent_start,
        "subagent_stop": on_subagent_stop,
    }
    registered: list[str] = []
    for name, callback in hooks.items():
        try:
            ctx.register_hook(name, callback)
            registered.append(name)
        except Exception as exc:
            # Older Hermes versions may not know finalize/reset/subagent hooks.
            if name in {"on_session_start", "pre_llm_call", "on_session_end"}:
                raise RuntimeError(f"required Hermes hook unavailable: {name}") from exc
            logger.info("Hermespace optional hook unavailable: %s (%s)", name, exc)

    if hasattr(ctx, "register_command"):
        ctx.register_command(
            "hermespace",
            handler=_slash_command,
            description="Hermespace Access Engine status, lens, metrics, and doctor",
            args_hint="[status|metrics|roles|lens|runtime|doctor]",
        )
    if hasattr(ctx, "register_cli_command"):
        ctx.register_cli_command(
            name="hermespace",
            help="Inspect Hermespace Access Engine",
            description="Status, metrics, roles, runtime, lens, or doctor",
            setup_fn=_setup_cli,
            handler_fn=_handle_cli,
        )
    if hasattr(ctx, "register_skill"):
        try:
            from hermespace.paths import package_root

            skill = package_root() / "skills" / "hermespace"
            if skill.is_dir():
                ctx.register_skill("hermespace", skill)
        except Exception as exc:
            logger.debug("Hermespace skill registration skipped: %s", exc)

    logger.info(
        "Hermespace v%s registered %d hooks: %s",
        __version__,
        len(registered),
        ", ".join(registered),
    )
