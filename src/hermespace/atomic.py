"""Small, dependency-free atomic persistence helpers.

Hermes runs plugins in CLI, gateway, cron, and subagent processes.  A process
must never leave a half-written JSON or Markdown state file behind if it is
interrupted while saving.  These helpers keep the write contract local and
portable without adding a file-lock dependency.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path


def atomic_write_text(
    path: Path,
    text: str,
    *,
    encoding: str = "utf-8",
    mode: int | None = None,
) -> Path:
    """Atomically replace *path* with *text* and return *path*.

    The temporary file is created beside the destination so ``os.replace`` is
    on the same filesystem.  Data is flushed before replacement.  Existing
    permissions are preserved unless ``mode`` is supplied for a new file.
    """

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    existing_mode: int | None = None
    try:
        existing_mode = path.stat().st_mode & 0o777
    except OSError:
        pass

    fd, raw_tmp = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    tmp = Path(raw_tmp)
    try:
        with os.fdopen(fd, "w", encoding=encoding) as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
            desired_mode = existing_mode if existing_mode is not None else mode
            if desired_mode is not None:
                try:
                    os.fchmod(handle.fileno(), desired_mode)
                except (AttributeError, OSError):
                    pass
        os.replace(tmp, path)
        return path
    finally:
        try:
            tmp.unlink(missing_ok=True)
        except OSError:
            pass
