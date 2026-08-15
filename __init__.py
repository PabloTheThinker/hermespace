"""Hermes source-repository plugin entry point.

``hermes plugins install PabloTheThinker/hermespace --enable`` clones this
repository as one plugin.  The checkout folder is often named ``hermespace``,
which would shadow ``src/hermespace`` if we ``from hermespace.plugin import
register`` while this file is already loaded as that package.  Load the real
plugin (and, when shadowed, the real package) via importlib from ``src/``.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent
_SRC = _ROOT / "src"
_PKG = _SRC / "hermespace"
_PLUGIN = _PKG / "plugin.py"


def _load_from_file(name: str, path: Path, *, package_dir: Path | None = None):
    spec = importlib.util.spec_from_file_location(
        name,
        path,
        submodule_search_locations=[str(package_dir)] if package_dir else None,
    )
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    # Bind before exec so src/hermespace relative imports do not re-enter this file.
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _load_plugin_register():
    mod = _load_from_file("_hermespace_plugin_entry", _PLUGIN)
    return mod.register


if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

if __name__ == "hermespace":
    # Parent-cwd / folder-name shadow: bind the real package from src/.
    real = _load_from_file(
        "hermespace",
        _PKG / "__init__.py",
        package_dir=_PKG,
    )
    sys.modules["hermespace"] = real
    register = _load_plugin_register()
    setattr(real, "register", register)
    for _name in getattr(real, "__all__", []):
        if hasattr(real, _name):
            globals()[_name] = getattr(real, _name)
else:
    register = _load_plugin_register()

__all__ = ["register"]
