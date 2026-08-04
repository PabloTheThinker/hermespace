"""Deprecated shim — prefer ``hermespace.access`` (Access Workspace).

Old Anthropic-inspired product name removed to keep Hermespace's own brand.
"""

from __future__ import annotations

from hermespace.access import *  # noqa: F403
from hermespace.access import (
    ACCESS_ROLES,
    AccessEngine,
    AccessEnv,
    AccessHub,
    AUDIT_LEXICON,
    BANDS,
    HermespaceAccessEngine,
    HUB_CAP,
    LensHit,
    ProtocolGate,
    ProtocolVerdict,
    WorkspaceConcept,
    auto_park_silent,
    evaluate_material_turn,
    filter_ablated,
    get_access_hub,
    get_env,
    oew_enabled,
    run_oew_beat,
    shape_report,
)

# Legacy aliases (do not use in new code)
JSpace = AccessHub
JSpaceEnv = AccessEnv
JSpaceEngine = AccessEngine
get_jspace = get_access_hub
HermespaceJSpaceEngine = HermespaceAccessEngine

__all__ = [
    "ACCESS_ROLES",
    "AccessEngine",
    "AccessEnv",
    "AccessHub",
    "AUDIT_LEXICON",
    "BANDS",
    "HermespaceAccessEngine",
    "HUB_CAP",
    "LensHit",
    "ProtocolGate",
    "ProtocolVerdict",
    "WorkspaceConcept",
    "auto_park_silent",
    "evaluate_material_turn",
    "filter_ablated",
    "get_access_hub",
    "get_env",
    "oew_enabled",
    "run_oew_beat",
    "shape_report",
    "JSpace",
    "JSpaceEnv",
    "JSpaceEngine",
    "get_jspace",
    "HermespaceJSpaceEngine",
]
