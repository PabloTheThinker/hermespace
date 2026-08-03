"""Compat shim — prefer ``from hermespace.jspace import JSpaceEnv``."""

from __future__ import annotations

from hermespace.jspace.env import *  # noqa: F403
from hermespace.jspace.env import AUDIT_LEXICON, BANDS, JSpaceEnv, LensHit, get_env

__all__ = ["AUDIT_LEXICON", "BANDS", "JSpaceEnv", "LensHit", "get_env"]
