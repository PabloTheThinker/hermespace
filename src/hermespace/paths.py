"""Paths — no host-specific defaults. Override with env."""

from __future__ import annotations

import os
import hashlib
import re
from pathlib import Path


def canonical_agent_id(agent_id: str | None = None) -> str:
    """Resolve the one agent identity used by world, grid, ops, and hooks."""

    value = (agent_id or "").strip()
    if not value or value == "default":
        value = os.environ.get("HERMESPACE_AGENT_ID", "").strip()
    return value or "hermes-agent"


def hermespace_home() -> Path:
    """State root for desk + episodes.

    Order:
      HERMESPACE_HOME
      ~/.hermespace
    """
    raw = os.environ.get("HERMESPACE_HOME", "").strip()
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


def session_scope_id(agent_id: str, session_id: str = "") -> str:
    """Stable path-safe ID that does not expose opaque Hermes session IDs."""

    agent = re.sub(r"[^a-zA-Z0-9._-]+", "_", agent_id or "hermes-agent")[:64]
    session = (session_id or "").strip()
    if not session or session in {"main", "default"}:
        return agent or "hermes-agent"
    digest = hashlib.sha256(session.encode("utf-8", errors="replace")).hexdigest()[:16]
    return f"{agent or 'hermes-agent'}--{digest}"


def session_desk_path(agent_id: str, session_id: str = "") -> Path:
    """Per-session desk for Hermes CLI/gateway/A2A isolation."""

    if not session_id or session_id in {"main", "default"}:
        return desk_path()
    return state_dir() / "sessions" / session_scope_id(agent_id, session_id) / "ACTIVE.md"


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
