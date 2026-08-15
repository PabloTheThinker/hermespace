"""Hermespace — open-source Access Engine for Hermes agents."""

from __future__ import annotations

__version__ = "0.25.0"

from hermespace.desk import Desk
from hermespace.engine import HermespaceEngine
from hermespace.inject import build_inject_block
from hermespace.io_contract import HermespaceInput, HermespaceOutput
from hermespace import ops as ops
from hermespace.memory_db import HermespaceMemory
from hermespace.neural_space import NeuralSpace
from hermespace.workflow import TurnResult, Workflow
from hermespace import agent_api
from hermespace.workbench import Workbench
from hermespace.environment import probe_environment, environment_markdown
from hermespace.agent_api import (
    rank_skills,
    fabric_snapshot,
    remember_learning,
    encode_message,
    run_turn,
    decode_for_user,
    decode_for_model,
    decode_bundle,
    quick_reply,
)
from hermespace.grid import Grid
from hermespace import pulse
from hermespace.world import WorldModel, get_world, world_context
from hermespace.access import AccessHub, get_access_hub, AccessEnv, get_env
from hermespace.access import evaluate_material_turn
from hermespace.access import AccessEngine, ACCESS_ROLES
from hermespace import cube_module
from hermespace import insight_module
from hermespace.hermes_base import HermesBase

__all__ = [
    "Desk",
    "HermespaceEngine",
    "AccessEngine",
    "ACCESS_ROLES",
    "Workflow",
    "TurnResult",
    "HermespaceInput",
    "HermespaceOutput",
    "HermespaceMemory",
    "NeuralSpace",
    "encode_message",
    "run_turn",
    "decode_for_user",
    "decode_for_model",
    "decode_bundle",
    "quick_reply",
    "rank_skills",
    "fabric_snapshot",
    "remember_learning",
    "agent_api",
    "Workbench",
    "Grid",
    "pulse",
    "WorldModel",
    "get_world",
    "world_context",
    "AccessHub",
    "get_access_hub",
    "AccessEnv",
    "get_env",
    "evaluate_material_turn",
    "cube_module",
    "insight_module",
    "HermesBase",
    "probe_environment",
    "environment_markdown",
    "build_inject_block",
    "__version__",
]
