"""HermesBase — thin product alias of ``JSpaceEngine``.

Prefer ``from hermespace import JSpaceEngine`` for new code.
``HermesBase`` remains for day-to-day CLI / docs compatibility.
"""

from __future__ import annotations

from hermespace.jspace.engine import JSpaceEngine


class HermesBase(JSpaceEngine):
    """Functional J-space of a Hermes base — alias of JSpaceEngine."""

    pass
