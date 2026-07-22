"""Dream — bounded consolidation on the grid (meta-brain night cycle)."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from hermespace.grid.lenses import set_active_lens
from hermespace.grid.missions import list_missions
from hermespace.grid.scars import list_scars
from hermespace.grid.secure_store import grid_root, safe_name
from hermespace.grid.skillbench import list_modules, list_proposals
from hermespace.grid.title_tree import get_profile
from hermespace.semantic import consolidate


def _utcnow() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


@dataclass
class DreamReport:
    agent_id: str
    created: str
    material: bool
    summary: str
    actions: list[str] = field(default_factory=list)
    missions_open: int = 0
    scars_open: int = 0
    proposals: int = 0
    silent_user: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _log_path(agent_id: str) -> Path:
    return grid_root() / "dreams" / f"{safe_name(agent_id)}.jsonl"


def run_dream(agent_id: str = "default", *, force_material: bool = False) -> DreamReport:
    """Consolidate semantic memory + snapshot grid health. Silent unless material."""
    actions: list[str] = []
    # optional semantic consolidate (may no-op)
    try:
        consolidate()
        actions.append("semantic_consolidate")
    except Exception as e:  # noqa: BLE001 — dream must not crash host
        actions.append(f"semantic_skip:{type(e).__name__}")

    set_active_lens("dreamer", agent_id=agent_id)  # temporary mode stamp for log
    missions = list_missions(agent_id)
    open_m = [m for m in missions if m.status in ("open", "active", "blocked")]
    scars = list_scars(agent_id, open_only=True)
    props = list_proposals(agent_id)
    mods = list_modules(agent_id)
    profile = get_profile(agent_id)

    material = force_material or bool(open_m) or bool(scars) or bool(props)
    # restore builder if was dreamer-only stamp — keep partner/builder default
    # only set dreamer for report; leave active as dreamer is ok for night, operators can switch
    summary_parts = [
        f"missions_open={len(open_m)}",
        f"scars_open={len(scars)}",
        f"skill_proposals={len(props)}",
        f"modules={len(mods)}",
        f"title={profile.get('title') or 'unset'}",
    ]
    if open_m:
        summary_parts.append("top_mission=" + open_m[0].title[:80])
    if scars:
        summary_parts.append("top_scar=" + scars[-1].summary[:80])

    report = DreamReport(
        agent_id=agent_id,
        created=_utcnow(),
        material=material,
        summary="; ".join(summary_parts),
        actions=actions,
        missions_open=len(open_m),
        scars_open=len(scars),
        proposals=len(props),
        silent_user=not material,
    )

    path = _log_path(agent_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        import json

        f.write(json.dumps(report.to_dict(), ensure_ascii=False) + "\n")

    # markdown human journal
    day = _utcnow()[:10]
    md = grid_root() / "dreams" / f"{day}.md"
    line = f"- {_utcnow()} agent={agent_id} material={material} {report.summary}\n"
    md.parent.mkdir(parents=True, exist_ok=True)
    with md.open("a", encoding="utf-8") as f:
        f.write(line)

    return report


def last_dreams(agent_id: str = "default", limit: int = 5) -> list[dict[str, Any]]:
    path = _log_path(agent_id)
    if not path.is_file():
        return []
    lines = path.read_text(encoding="utf-8").strip().splitlines()
    out: list[dict[str, Any]] = []
    import json

    for line in lines[-limit:]:
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return out
