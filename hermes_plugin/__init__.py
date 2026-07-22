"""Hermes file-plugin — first-class Hermespace workbench integration."""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

__version__ = "0.18.4"

logger = logging.getLogger("hermes.plugins.hermespace")


def _plugin_dir() -> Path:
    return Path(__file__).resolve().parent


def _ensure_import() -> bool:
    """Make hermespace importable. Prefer env, then checkout next to this plugin."""
    try:
        import hermespace  # noqa: F401

        return True
    except ImportError:
        pass

    roots: list[Path] = []
    env = os.environ.get("HERMESPACE_ROOT", "").strip()
    if env:
        roots.append(Path(env).expanduser())

    plug = _plugin_dir()
    try:
        roots.append(plug.resolve().parent)
    except OSError:
        roots.append(plug.parent)

    roots.append(Path.cwd())
    roots.append(Path.home() / "projects" / "hermespace")
    roots.append(Path.home() / "src" / "hermespace")
    roots.append(Path.home() / "hermespace")

    seen: set[str] = set()
    for root in roots:
        try:
            root = root.expanduser().resolve()
        except OSError:
            continue
        key = str(root)
        if key in seen:
            continue
        seen.add(key)
        src = root / "src"
        if (src / "hermespace" / "__init__.py").is_file():
            s = str(src)
            if s not in sys.path:
                sys.path.insert(0, s)
            try:
                import hermespace  # noqa: F401

                os.environ.setdefault("HERMESPACE_ROOT", str(root))
                logger.debug("hermespace imported from %s", src)
                return True
            except ImportError:
                continue

    logger.warning(
        "hermespace package not importable — plugin no-op. "
        "pip install -e <checkout> or set HERMESPACE_ROOT / PYTHONPATH=…/src"
    )
    return False


_IMPORT_OK = _ensure_import()


def register(ctx) -> None:
    """Register Hermes lifecycle hooks — workbench is part of the framework path."""
    if not _IMPORT_OK and not _ensure_import():
        logger.error("Hermespace plugin registered but package missing — hooks skipped")
        return

    from hermespace.hermes_bridge import (
        on_pre_llm_call,
        on_session_end,
        on_session_start,
    )

    ctx.register_hook("on_session_start", on_session_start)
    ctx.register_hook("pre_llm_call", on_pre_llm_call)
    ctx.register_hook("on_session_end", on_session_end)
    logger.info(
        "Hermespace v%s registered: on_session_start + pre_llm_call + on_session_end",
        __version__,
    )
