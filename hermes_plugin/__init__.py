"""Source-tree wrapper for the first-class Hermespace plugin."""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

__version__ = "0.25.0"

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


def register(ctx) -> None:
    """Resolve the runtime and delegate to the packaged plugin entry point."""
    if not _ensure_import():
        raise RuntimeError(
            "Hermespace runtime is not importable. Run ./scripts/install_hermes.sh "
            "or pip install the Hermespace checkout before enabling the plugin."
        )

    from hermespace.plugin import register as register_runtime

    register_runtime(ctx)
