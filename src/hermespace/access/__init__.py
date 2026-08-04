"""Hermespace Access Workspace package — external verbalizable workspace for Hermes.

Public surface:

    from hermespace import AccessEngine
    from hermespace.access import AccessHub, AccessEnv, run_oew_beat

OEW (Obligatory External Workspace) is ON by default — higher-order thinking
for any Hermes agent connected to Hermespace. Warehouse/Cube is optional.
"""

from __future__ import annotations

from hermespace.access.hub import (
    HUB_CAP,
    AccessHub,
    WorkspaceConcept,
    get_access_hub,
)
from hermespace.access.env import (
    AUDIT_LEXICON,
    BANDS,
    AccessEnv,
    LensHit,
    get_env,
)
from hermespace.access.protocol import (
    ProtocolGate,
    ProtocolVerdict,
    evaluate_material_turn,
    oew_enabled,
)
from hermespace.access.oew import (
    auto_park_silent,
    filter_ablated,
    run_oew_beat,
    shape_report,
)
from hermespace.access.engine import (
    ACCESS_ROLES,
    HermespaceAccessEngine,
    AccessEngine,
)

__all__ = [
    "HUB_CAP",
    "AccessHub",
    "WorkspaceConcept",
    "get_access_hub",
    "AUDIT_LEXICON",
    "BANDS",
    "AccessEnv",
    "LensHit",
    "get_env",
    "ProtocolGate",
    "ProtocolVerdict",
    "evaluate_material_turn",
    "oew_enabled",
    "auto_park_silent",
    "filter_ablated",
    "run_oew_beat",
    "shape_report",
    "ACCESS_ROLES",
    "AccessEngine",
    "HermespaceAccessEngine",
]
