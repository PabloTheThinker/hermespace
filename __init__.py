"""Hermes source-repository plugin entry point.

``hermes plugins install PabloTheThinker/hermespace --enable`` clones this
repository as one plugin.  Add the repository's ``src`` directory, then load
the same registration module used by wheel entry-point installs.
"""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent
_SRC = _ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from hermespace.plugin import register  # noqa: E402,F401

__all__ = ["register"]
