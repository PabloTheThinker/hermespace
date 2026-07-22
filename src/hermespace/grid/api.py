"""Hermespace Grid facade — production entry for autonomy world."""

from __future__ import annotations

from typing import Any

from hermespace.grid import dream, gates, lenses, missions, scars, selftalk, skillbench, title_tree
from hermespace.grid.lenses import lens_inject_block
from hermespace.grid.selftalk import as_model_context


class Grid:
    """One agent’s Hermespace grid surface."""

    def __init__(self, agent_id: str = "default") -> None:
        self.agent_id = agent_id or "default"

    # --- missions ---
    def add_mission(self, title: str, **kw: Any):
        return missions.add_mission(title, agent_id=self.agent_id, **kw)

    def list_missions(self):
        return missions.list_missions(self.agent_id)

    def update_mission(self, mission_id: str, **kw: Any):
        return missions.update_mission(mission_id, agent_id=self.agent_id, **kw)

    # --- scars ---
    def open_scar(self, kind: str, summary: str, **kw: Any):
        return scars.open_scar(kind, summary, agent_id=self.agent_id, **kw)

    def list_scars(self, open_only: bool = False):
        return scars.list_scars(self.agent_id, open_only=open_only)

    def seal_scar(self, scar_id: str):
        return scars.seal_scar(scar_id, agent_id=self.agent_id)

    # --- lenses ---
    def set_lens(self, name: str):
        return lenses.set_active_lens(name, agent_id=self.agent_id)

    def lens(self):
        return lenses.get_active_lens(self.agent_id)

    # --- dream ---
    def dream(self, force_material: bool = False):
        return dream.run_dream(self.agent_id, force_material=force_material)

    # --- skillbench ---
    def register_skill(self, name: str, body: str, **kw: Any):
        return skillbench.register_module(name, body, agent_id=self.agent_id, **kw)

    def merge_skills(self, a: str, b: str, **kw: Any):
        return skillbench.merge_skills(a, b, agent_id=self.agent_id, **kw)

    def mutate_skill(self, name: str, delta: str, **kw: Any):
        return skillbench.mutate_skill(name, delta, agent_id=self.agent_id, **kw)

    def promote(self, proposal_id: str, to_hermes: bool = False):
        return skillbench.promote_proposal(proposal_id, agent_id=self.agent_id, to_hermes=to_hermes)

    def hot_skills(self):
        return skillbench.hot_modules(self.agent_id)

    # --- selftalk ---
    def think(self, text: str, role: str = "self"):
        return selftalk.say(text, agent_id=self.agent_id, role=role)

    def self_dialogue(self, turns: list[tuple[str, str]]):
        return selftalk.dialogue(turns, agent_id=self.agent_id)

    # --- title / tree ---
    def set_title(self, title: str, reason: str = ""):
        return title_tree.set_title(title, agent_id=self.agent_id, reason=reason)

    def adopt_title(self, reason: str = "auto"):
        t = title_tree.suggest_title(self.agent_id)
        return title_tree.set_title(t, agent_id=self.agent_id, reason=reason)

    def rebuild_tree(self):
        return title_tree.rebuild_tree_from_bench(self.agent_id)

    def request_access(self, path: str, **kw: Any):
        from hermespace.grid import access as access_mod

        return access_mod.request_access(path, agent_id=self.agent_id, **kw)

    def pending_access(self):
        from hermespace.grid import access as access_mod

        return access_mod.list_requests(agent_id=self.agent_id, status="pending")

    # --- inject ---
    def context_block(self) -> str:
        parts = [
            "## Hermespace grid",
            lens_inject_block(self.agent_id),
        ]
        am = missions.active_missions(self.agent_id, limit=3)
        if am:
            parts.append("**Missions:**")
            for m in am:
                parts.append(f"- [{m.status}] {m.title} ({m.id})")
        sc = scars.list_scars(self.agent_id, open_only=True)
        if sc:
            parts.append("**Open scars:**")
            for s in sc[-3:]:
                parts.append(f"- ({s.kind}) {s.summary[:120]}")
        prof = title_tree.get_profile(self.agent_id)
        if prof.get("title"):
            parts.append(f"**Title:** {prof['title']}")
        hot = skillbench.hot_modules(self.agent_id)
        if hot:
            parts.append("**Hot skill modules:** " + ", ".join(m.name for m in hot[:8]))
        st = as_model_context(self.agent_id, limit=8)
        if st:
            parts.append(st)
        parts.append(f"**Autonomy:** {'on' if gates.autonomy_enabled() else 'off'}")
        try:
            from hermespace.grid.access import pending_inject_block

            parts.append(pending_inject_block(self.agent_id))
        except Exception:
            pass
        return "\n".join(parts)

    def status(self) -> dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "lens": self.lens().to_dict(),
            "missions": len(self.list_missions()),
            "scars_open": len(self.list_scars(open_only=True)),
            "hot_modules": len(self.hot_skills()),
            "title": title_tree.get_profile(self.agent_id).get("title") or "",
            "gates": gates.gate_status(),
        }
