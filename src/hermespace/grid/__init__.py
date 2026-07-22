"""Hermespace Grid — autonomy world inside the pocket dimension."""

from __future__ import annotations

from hermespace.grid.api import Grid
from hermespace.grid.gates import check_autonomy_self_order, gate_status
from hermespace.grid.lenses import list_lenses
from hermespace.grid.boundary import check_path, load_policy
from hermespace.grid.viewport import snapshot, render_markdown, write_viewport_files

__all__ = [
    "Grid",
    "list_lenses",
    "gate_status",
    "check_autonomy_self_order",
    "check_path",
    "load_policy",
    "snapshot",
    "render_markdown",
    "write_viewport_files",
]
