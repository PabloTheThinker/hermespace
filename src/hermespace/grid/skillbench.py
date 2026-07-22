"""Skillbench — hot-swap skill modules + merge/mutate evolution on the workbench.

Ground-up (AgentDrive *roles* only: learned/fused skills, growth merge):
- Modules live under HERMESPACE_HOME grid (not auto-installed to Hermes)
- Merge two skill bodies → draft proposal
- Mutate a skill with a delta note → draft proposal
- Promote requires explicit call + static gate (Hermes skills_guard *idea*)
"""

from __future__ import annotations

import hashlib
import re
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from hermespace.grid.gates import check_skill_promote
from hermespace.grid.secure_store import (
    atomic_write_json,
    grid_root,
    read_json,
    resolve_under,
    safe_name,
)

_FRONT = re.compile(r"^---\n(.*?)\n---\n", re.S)


def _utcnow() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _root(agent_id: str) -> Path:
    p = grid_root() / "skillbench" / safe_name(agent_id)
    p.mkdir(parents=True, exist_ok=True)
    (p / "modules").mkdir(exist_ok=True)
    (p / "drafts").mkdir(exist_ok=True)
    return p


@dataclass
class Module:
    name: str
    path: str
    sha256: str
    hot: bool = True
    source: str = "local"  # local | hermes_import | draft
    updated: str = field(default_factory=_utcnow)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def list_modules(agent_id: str = "default") -> list[Module]:
    raw = read_json(_root(agent_id) / "index.json", {"modules": []})
    return [Module(**{**m, "name": m.get("name", "")}) for m in (raw.get("modules") or []) if m.get("name")]


def _save_index(agent_id: str, modules: list[Module]) -> None:
    atomic_write_json(
        _root(agent_id) / "index.json",
        {"modules": [m.to_dict() for m in modules], "updated": _utcnow()},
    )


def register_module(
    name: str,
    body: str,
    *,
    agent_id: str = "default",
    hot: bool = True,
    source: str = "local",
) -> Module:
    name = safe_name(name, default="")
    if not name:
        raise ValueError("invalid module name")
    body = body or ""
    path = resolve_under(_root(agent_id) / "modules", f"{name}.md")
    path.write_text(body, encoding="utf-8")
    mod = Module(name=name, path=str(path), sha256=_sha(body), hot=hot, source=source)
    mods = [m for m in list_modules(agent_id) if m.name != name]
    mods.append(mod)
    _save_index(agent_id, mods)
    return mod


def import_hermes_skill(skill_path: Path, *, agent_id: str = "default") -> Module:
    """Import a Hermes SKILL.md into the bench (copy, sandboxed)."""
    skill_path = skill_path.expanduser().resolve()
    if skill_path.name != "SKILL.md" or not skill_path.is_file():
        raise ValueError("expected path to SKILL.md")
    # only allow under HERMES_HOME/skills if set
    import os

    hh = os.environ.get("HERMES_HOME", "").strip()
    if hh:
        base = Path(hh).expanduser().resolve() / "skills"
        if base not in skill_path.parents and skill_path.parent != base:
            # still allow if clearly a SKILL.md under skills tree
            if "skills" not in skill_path.parts:
                raise ValueError("skill path must be under a skills tree")
    body = skill_path.read_text(encoding="utf-8")
    name = skill_path.parent.name
    return register_module(name, body, agent_id=agent_id, source="hermes_import")


def get_module_body(name: str, *, agent_id: str = "default") -> str:
    name = safe_name(name)
    path = resolve_under(_root(agent_id) / "modules", f"{name}.md")
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8")


def set_hot(name: str, hot: bool, *, agent_id: str = "default") -> Module | None:
    mods = list_modules(agent_id)
    for m in mods:
        if m.name == safe_name(name):
            m.hot = bool(hot)
            m.updated = _utcnow()
            _save_index(agent_id, mods)
            return m
    return None


def hot_modules(agent_id: str = "default") -> list[Module]:
    return [m for m in list_modules(agent_id) if m.hot]


@dataclass
class Proposal:
    id: str
    kind: str  # merge | mutate
    name: str
    parents: list[str]
    draft_path: str
    created: str
    status: str = "draft"  # draft | promoted | rejected
    note: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def list_proposals(agent_id: str = "default") -> list[Proposal]:
    raw = read_json(_root(agent_id) / "proposals.json", {"proposals": []})
    out = []
    for p in raw.get("proposals") or []:
        if not isinstance(p, dict):
            continue
        out.append(
            Proposal(
                id=str(p.get("id")),
                kind=str(p.get("kind")),
                name=str(p.get("name")),
                parents=list(p.get("parents") or []),
                draft_path=str(p.get("draft_path")),
                created=str(p.get("created")),
                status=str(p.get("status") or "draft"),
                note=str(p.get("note") or ""),
            )
        )
    return out


def _save_proposals(agent_id: str, props: list[Proposal]) -> None:
    atomic_write_json(
        _root(agent_id) / "proposals.json",
        {"proposals": [p.to_dict() for p in props], "updated": _utcnow()},
    )


def merge_skills(
    name_a: str,
    name_b: str,
    *,
    agent_id: str = "default",
    new_name: str | None = None,
    note: str = "",
) -> Proposal:
    """Fuse two module bodies into a draft (AgentDrive fused-* *role*)."""
    a = get_module_body(name_a, agent_id=agent_id)
    b = get_module_body(name_b, agent_id=agent_id)
    if not a or not b:
        raise ValueError("both modules must exist on the bench")
    out_name = safe_name(new_name or f"fused-{safe_name(name_a)}-{safe_name(name_b)}")
    body = (
        f"---\nname: {out_name}\ndescription: >-\n  Fused draft from {name_a} + {name_b}. "
        f"Review before promote.\nversion: 0.1.0-draft\n---\n\n"
        f"# {out_name} (draft fusion)\n\n"
        f"_Note:_ {note or 'auto-merge'}\n\n"
        f"## From `{name_a}`\n\n{a}\n\n---\n\n## From `{name_b}`\n\n{b}\n"
    )
    draft = resolve_under(_root(agent_id) / "drafts", f"{out_name}.md")
    draft.write_text(body, encoding="utf-8")
    prop = Proposal(
        id=uuid.uuid4().hex[:12],
        kind="merge",
        name=out_name,
        parents=[safe_name(name_a), safe_name(name_b)],
        draft_path=str(draft),
        created=_utcnow(),
        note=note,
    )
    props = list_proposals(agent_id)
    props.append(prop)
    _save_proposals(agent_id, props)
    return prop


def mutate_skill(
    name: str,
    delta: str,
    *,
    agent_id: str = "default",
    note: str = "",
) -> Proposal:
    """Evolve a module with a mutation note (learned-* *role*)."""
    base = get_module_body(name, agent_id=agent_id)
    if not base:
        raise ValueError("module not on bench")
    out_name = safe_name(f"mut-{safe_name(name)}-{uuid.uuid4().hex[:6]}")
    body = (
        f"---\nname: {out_name}\ndescription: >-\n  Mutation draft of {name}. Review before promote.\n"
        f"version: 0.1.0-draft\n---\n\n"
        f"# {out_name}\n\n"
        f"## Mutation\n\n{delta.strip()}\n\n"
        f"## Parent body (`{name}`)\n\n{base}\n"
    )
    draft = resolve_under(_root(agent_id) / "drafts", f"{out_name}.md")
    draft.write_text(body, encoding="utf-8")
    prop = Proposal(
        id=uuid.uuid4().hex[:12],
        kind="mutate",
        name=out_name,
        parents=[safe_name(name)],
        draft_path=str(draft),
        created=_utcnow(),
        note=note or delta[:200],
    )
    props = list_proposals(agent_id)
    props.append(prop)
    _save_proposals(agent_id, props)
    return prop


def promote_proposal(
    proposal_id: str,
    *,
    agent_id: str = "default",
    to_hermes: bool = False,
) -> dict[str, Any]:
    """Promote draft onto bench as hot module; optional Hermes write is explicit+gated."""
    props = list_proposals(agent_id)
    prop = next((p for p in props if p.id == proposal_id), None)
    if not prop:
        raise ValueError("proposal not found")
    body = Path(prop.draft_path).read_text(encoding="utf-8")
    gate = check_skill_promote(body)
    if not gate.allowed:
        return {"ok": False, "reason": gate.reason}
    mod = register_module(prop.name, body, agent_id=agent_id, hot=True, source="draft")
    prop.status = "promoted"
    _save_proposals(agent_id, props)
    result: dict[str, Any] = {"ok": True, "module": mod.to_dict(), "hermes": None}
    if to_hermes:
        import os

        from hermespace.grid.boundary import hermes_promote_dest

        hh = os.environ.get("HERMES_HOME", "").strip()
        if not hh:
            result["hermes"] = {"ok": False, "reason": "HERMES_HOME unset"}
        else:
            dest = hermes_promote_dest(prop.name, Path(hh).expanduser())
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(body, encoding="utf-8")
            result["hermes"] = {"ok": True, "path": str(dest)}
    return result
