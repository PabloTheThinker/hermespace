"""Optional HermesCube adapter inside Hermespace (soft dependency)."""

from __future__ import annotations

from typing import Any


def cube_inject(query: str, *, high_load: bool = False, max_chars: int | None = None) -> str:
    try:
        from hermescube.space_bridge import build_space_inject

        return build_space_inject(query, high_load=high_load, max_chars=max_chars) or ""
    except Exception:
        return ""


def cube_status() -> dict[str, Any]:
    try:
        from hermescube.space_bridge import module_status

        return module_status()
    except Exception as e:
        return {"available": False, "error": str(e)}


def cube_seal(content: str, **kwargs: Any) -> bool:
    try:
        from hermescube.space_bridge import seal_to_cube

        return bool(seal_to_cube(content, **kwargs))
    except Exception:
        return False
