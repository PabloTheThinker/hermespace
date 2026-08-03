"""Hermespace J-Space package — external verbalizable workspace for Hermes.

Public surface:

    from hermespace.jspace import JSpace, JSpaceEnv, run_oew_beat, evaluate_material_turn

OEW (Obligatory External Workspace) is ON by default — higher-order thinking
for any Hermes agent connected to Hermespace (+ HermesCube when present).
"""

from __future__ import annotations

from hermespace.jspace.hub import (
    HUB_CAP,
    JSpace,
    WorkspaceConcept,
    get_jspace,
)
from hermespace.jspace.env import (
    AUDIT_LEXICON,
    BANDS,
    JSpaceEnv,
    LensHit,
    get_env,
)
from hermespace.jspace.protocol import (
    ProtocolGate,
    ProtocolVerdict,
    evaluate_material_turn,
    oew_enabled,
)
from hermespace.jspace.oew import (
    auto_park_silent,
    filter_ablated,
    run_oew_beat,
    shape_report,
)

__all__ = [
    "HUB_CAP",
    "JSpace",
    "WorkspaceConcept",
    "get_jspace",
    "AUDIT_LEXICON",
    "BANDS",
    "JSpaceEnv",
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
]
