"""Cognitive lenses — mode packs for the desk (not character kits)."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from hermespace.grid.secure_store import atomic_write_json, grid_root, read_json, safe_name

# Built-in lenses (ground-up; Hermes-native operations language)
BUILTIN: dict[str, dict[str, Any]] = {
    "builder": {
        "title": "Builder",
        "bias": "Ship smallest working artifact; tests before claims",
        "fabric_boost": ["test-driven-development", "hermes-framework-coding", "simplify-code"],
        "inhibit": ["long multi-option menus", "process theater", "premature abstraction"],
        "report_style": "short_ship",
    },
    "architect": {
        "title": "Architect",
        "bias": "Interfaces, boundaries, long-term structure",
        "fabric_boost": ["plan", "hermes-framework-coding", "research-first-agent-design"],
        "inhibit": ["drive-by refactors", "unbounded scope"],
        "report_style": "structured",
    },
    "security": {
        "title": "Security",
        "bias": "Least privilege, audit, no secret leakage",
        "fabric_boost": ["requesting-code-review", "hermes-gateway-verify"],
        "inhibit": ["print secrets", "force push", "disable auth"],
        "report_style": "risks_first",
    },
    "scientist": {
        "title": "Scientist",
        "bias": "Hypothesis, measure, honesty bar; no science theater",
        "fabric_boost": ["arxiv", "evaluating-llms-harness", "spike"],
        "inhibit": ["claim unmeasured accuracy", "consciousness cosplay"],
        "report_style": "evidence",
    },
    "operator": {
        "title": "Operator",
        "bias": "Health, restarts, runbooks, verify live",
        "fabric_boost": ["hermes-agent", "hermes-gateway-channels", "software-development"],
        "inhibit": ["version-string-as-health", "silent restart"],
        "report_style": "status_table",
    },
    "signal": {
        "title": "Signal",
        "bias": "Compression, X/social clarity, public-safe copy",
        "fabric_boost": ["x-presence", "professional-messaging", "humanizer"],
        "inhibit": ["private data in public", "wall of text"],
        "report_style": "compressed",
    },
    "partner": {
        "title": "Partner",
        "bias": "Monotropism, finish reports, high-load short say",
        "fabric_boost": ["professional-messaging", "ilo-finish-report", "hermes-agent"],
        "inhibit": ["option menus under high load", "leave hanging with only verify table"],
        "report_style": "closeout",
    },
    "dreamer": {
        "title": "Dreamer",
        "bias": "Consolidate, promote skills, prune noise; silent unless material",
        "fabric_boost": ["hermes-agent", "note-taking", "obsidian"],
        "inhibit": ["public posts in dream", "recursive cron loops"],
        "report_style": "silent_or_diff",
    },
}


@dataclass
class Lens:
    name: str
    title: str
    bias: str
    fabric_boost: list[str] = field(default_factory=list)
    inhibit: list[str] = field(default_factory=list)
    report_style: str = "short_ship"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_name(cls, name: str) -> "Lens":
        key = safe_name(name, default="builder")
        raw = BUILTIN.get(key) or BUILTIN["builder"]
        return cls(
            name=key if key in BUILTIN else "builder",
            title=str(raw["title"]),
            bias=str(raw["bias"]),
            fabric_boost=list(raw.get("fabric_boost") or []),
            inhibit=list(raw.get("inhibit") or []),
            report_style=str(raw.get("report_style") or "short_ship"),
        )


def _active_path(agent_id: str = "default") -> Path:
    return grid_root() / "lenses" / f"{safe_name(agent_id)}.json"


def list_lenses() -> list[str]:
    return sorted(BUILTIN.keys())


def get_active_lens(agent_id: str = "default") -> Lens:
    raw = read_json(_active_path(agent_id), {})
    name = str((raw or {}).get("active") or "builder")
    return Lens.from_name(name)


def set_active_lens(name: str, *, agent_id: str = "default") -> Lens:
    lens = Lens.from_name(name)
    atomic_write_json(
        _active_path(agent_id),
        {"active": lens.name, "title": lens.title, "bias": lens.bias},
    )
    return lens


def lens_inject_block(agent_id: str = "default") -> str:
    lens = get_active_lens(agent_id)
    lines = [
        f"**Lens:** {lens.title} (`{lens.name}`)",
        f"_Bias:_ {lens.bias}",
        f"_Style:_ {lens.report_style}",
    ]
    if lens.inhibit:
        lines.append("_Inhibit:_ " + "; ".join(lens.inhibit[:4]))
    if lens.fabric_boost:
        lines.append("_Skill priors:_ " + ", ".join(lens.fabric_boost[:5]))
    return "\n".join(lines)
