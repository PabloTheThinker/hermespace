"""Title + skill tree — agent self-model on the grid."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from hermespace.grid.secure_store import atomic_write_json, grid_root, read_json, safe_name
from hermespace.grid.skillbench import hot_modules, list_modules


def _utcnow() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


@dataclass
class TreeNode:
    id: str
    label: str
    kind: str = "skill"  # skill | domain | title
    parent: str = ""
    level: int = 1

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _path(agent_id: str) -> Path:
    return grid_root() / "identity" / f"{safe_name(agent_id)}.json"


def get_profile(agent_id: str = "default") -> dict[str, Any]:
    raw = read_json(
        _path(agent_id),
        {
            "title": "",
            "titles_history": [],
            "tree": [],
            "updated": "",
        },
    )
    return raw if isinstance(raw, dict) else {}


def set_title(title: str, *, agent_id: str = "default", reason: str = "") -> dict[str, Any]:
    title = (title or "").strip()[:80]
    if not title:
        raise ValueError("title required")
    prof = get_profile(agent_id)
    hist = list(prof.get("titles_history") or [])
    if prof.get("title"):
        hist.append({"title": prof["title"], "until": _utcnow()})
    prof["title"] = title
    prof["titles_history"] = hist[-20:]
    prof["title_reason"] = (reason or "")[:300]
    prof["updated"] = _utcnow()
    atomic_write_json(_path(agent_id), prof)
    return prof


def rebuild_tree_from_bench(agent_id: str = "default") -> dict[str, Any]:
    """Skill tree nodes from skillbench modules (hot first)."""
    prof = get_profile(agent_id)
    nodes = []
    # root title node
    title = prof.get("title") or "Agent"
    nodes.append(TreeNode(id="root", label=str(title), kind="title", level=0).to_dict())
    for i, m in enumerate(list_modules(agent_id)):
        nodes.append(
            TreeNode(
                id=m.name,
                label=m.name,
                kind="skill",
                parent="root",
                level=1 if m.hot else 2,
            ).to_dict()
        )
    # domain buckets by prefix
    domains = sorted({n["label"].split("-")[0] for n in nodes if n["kind"] == "skill" and "-" in n["label"]})
    for d in domains[:20]:
        nodes.append(TreeNode(id=f"dom-{d}", label=d, kind="domain", parent="root", level=1).to_dict())
    prof["tree"] = nodes
    prof["updated"] = _utcnow()
    prof["hot_count"] = len(hot_modules(agent_id))
    atomic_write_json(_path(agent_id), prof)
    return prof


def suggest_title(agent_id: str = "default") -> str:
    """Heuristic title from hot modules + history (no LLM required)."""
    hot = hot_modules(agent_id)
    if not hot:
        return "Apprentice Operator"
    names = " ".join(m.name for m in hot)
    if "security" in names:
        return "Grid Sentinel"
    if "architect" in names or "plan" in names:
        return "Systems Architect"
    if "builder" in names or "ship" in names:
        return "Shipwright"
    if len(hot) >= 8:
        return "Workbench Adept"
    return "Hermespace Operator"
