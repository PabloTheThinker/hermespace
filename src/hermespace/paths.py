"""Paths — no host-specific defaults. Override with env."""

from __future__ import annotations

import os
from pathlib import Path


def hermespace_home() -> Path:
    """State root for desk + episodes.

    Order:
      HERMESPACE_HOME
      ILO_HOME (compat)
      ~/.hermespace
    """
    for key in ("HERMESPACE_HOME", "ILO_HOME"):
        raw = os.environ.get(key, "").strip()
        if raw:
            return Path(raw).expanduser().resolve()
    return (Path.home() / ".hermespace").resolve()


def package_root() -> Path:
    """Install / checkout root if known."""
    raw = os.environ.get("HERMESPACE_ROOT", "").strip()
    if raw:
        return Path(raw).expanduser().resolve()
    # src/hermespace/paths.py -> parents[2] = package root when running from checkout
    here = Path(__file__).resolve()
    cand = here.parents[2]
    if (cand / "pyproject.toml").is_file():
        return cand
    return here.parents[1]


def desk_path() -> Path:
    return hermespace_home() / "memory" / "hermespace" / "ACTIVE.md"


def state_dir() -> Path:
    return hermespace_home() / "memory" / "hermespace"


def continuity_candidates() -> list[Path]:
    """Optional operator continuity files (generic names only)."""
    out: list[Path] = []
    raw = os.environ.get("HERMESPACE_CONTINUITY", "").strip()
    if raw:
        out.append(Path(raw).expanduser())
    home = hermespace_home()
    out.extend(
        [
            home / "CONTINUITY.md",
            home / "memory" / "CONTINUITY.md",
            home / "continuity.md",
        ]
    )
    return out
