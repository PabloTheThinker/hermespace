"""HermesBase — thin product alias of ``AccessEngine``.

Prefer ``from hermespace import AccessEngine`` for new code.
``HermesBase`` remains for day-to-day CLI / docs compatibility.
"""

from __future__ import annotations

from hermespace.access.engine import AccessEngine


class HermesBase(AccessEngine):
    """Hermespace Access Engine — alias of AccessEngine."""

    pass
