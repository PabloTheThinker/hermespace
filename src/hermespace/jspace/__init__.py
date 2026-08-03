"""Hermespace J-Space package — external verbalizable workspace for Hermes.

Public surface stays stable:

    from hermespace.jspace import JSpace, JSpaceEnv, get_jspace, get_env

Innovation target: Obligatory External Workspace (OEW) — see
``docs/assessment/28-hermes-agent-jspace-assessment.md`` and ``protocol.py``.
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
]
