"""Secure local JSON state for Hermespace grid.

Ground-up: no host fingerprints, path traversal blocked, atomic writes.
"""

from __future__ import annotations

import json
import os
import re
import tempfile
from pathlib import Path
from typing import Any

from hermespace.paths import state_dir

_SAFE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9._-]{0,79}$")


def grid_root() -> Path:
    root = state_dir() / "grid"
    root.mkdir(parents=True, exist_ok=True)
    return root


def safe_name(name: str, *, default: str = "default") -> str:
    s = (name or "").strip()
    if not s or not _SAFE.match(s):
        return default
    return s


def resolve_under(root: Path, *parts: str) -> Path:
    """Resolve path under root; raise if escape attempted."""
    base = root.resolve()
    cand = base.joinpath(*parts).resolve()
    if cand != base and base not in cand.parents:
        raise ValueError("path escape blocked")
    return cand


def atomic_write_json(path: Path, data: Any, *, fsync: bool = True) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(data, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
    fd, tmp = tempfile.mkstemp(prefix=".hs-", suffix=".json", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(text)
            f.flush()
            if fsync:
                os.fsync(f.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            try:
                os.unlink(tmp)
            except OSError:
                pass


def read_json(path: Path, default: Any) -> Any:
    if not path.is_file():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


def autonomy_enabled() -> bool:
    """Effective autonomy.

    Resolution:
      1. Pocket controls.json `autonomy` if file exists (viewport toggle)
      2. Else env HERMESPACE_AUTONOMY
    Force-off: HERMESPACE_AUTONOMY_FORCE=0 always wins off.
    Force-on: HERMESPACE_AUTONOMY_FORCE=1 always wins on.
    """
    force = os.environ.get("HERMESPACE_AUTONOMY_FORCE", "").strip().lower()
    if force in ("0", "false", "no", "off"):
        return False
    if force in ("1", "true", "yes", "on"):
        return True
    # pocket controls
    try:
        from hermespace.grid.controls import load_controls

        ctrl_path = grid_root() / "controls.json"
        if ctrl_path.is_file():
            return bool(load_controls().get("autonomy"))
    except Exception:
        pass
    return os.environ.get("HERMESPACE_AUTONOMY", "0").strip().lower() in ("1", "true", "yes", "on")
