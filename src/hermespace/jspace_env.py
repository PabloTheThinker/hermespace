"""Deprecated shim — use ``hermespace.access_env`` or ``hermespace.access``."""

from __future__ import annotations

from hermespace.access_env import *  # noqa: F403
from hermespace.access_env import AUDIT_LEXICON, BANDS, AccessEnv, LensHit, get_env

__all__ = ["AUDIT_LEXICON", "BANDS", "AccessEnv", "LensHit", "get_env"]
