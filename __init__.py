"""Hermes source-repository plugin entry point.

``hermes plugins install PabloTheThinker/hermespace --enable`` clones this
repository as one plugin.  The checkout folder is often named ``hermespace``,
which would shadow ``src/hermespace``.  Pop this shim from ``sys.modules``
before importing the real ``register``.
"""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent
_SRC = _ROOT / "src"

# Prefer src/ over a parent-cwd folder also named hermespace.
if str(_SRC) in sys.path:
    sys.path.remove(str(_SRC))
sys.path.insert(0, str(_SRC))

# Parent-cwd / folder-name shadow: drop this file so src/hermespace can load.
if __name__ == "hermespace":
    sys.modules.pop("hermespace", None)

from hermespace.plugin import register

__all__ = ["register"]
