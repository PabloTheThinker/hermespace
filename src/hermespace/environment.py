"""Pocket-dimension environment kit for Hermes agents.

Maps the Hermes runtime surfaces Nous documents into a single inventory
the agent can see while *inside* Hermespace:

- tools / toolsets (categories, not host secrets)
- skills directory presence
- memory files (MEMORY/USER) if present under HERMES_HOME
- cron/automation awareness
- MCP placeholder
- messaging platforms (declared, not credentials)

This does not re-implement Hermes — it **mirrors** what's available so the
workbench feels like a full room, not an empty desk.
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


# Canonical Hermes-shaped capability surfaces (from public Nous docs)
HERMES_TOOL_SURFACES: list[dict[str, str]] = [
    {"id": "terminal", "label": "Terminal / backends", "why": "local, docker, ssh, serverless"},
    {"id": "web", "label": "Web search & browse", "why": "Tool Gateway / browser"},
    {"id": "files", "label": "File read/write/patch", "why": "workspace code and docs"},
    {"id": "memory", "label": "Persistent memory", "why": "MEMORY.md + USER.md + providers"},
    {"id": "skills", "label": "Skills system", "why": "procedural memory, agentskills.io"},
    {"id": "cron", "label": "Cron / automation", "why": "unattended jobs while idle"},
    {"id": "messaging", "label": "Messaging gateway", "why": "Telegram/Discord/Slack/…"},
    {"id": "mcp", "label": "MCP servers", "why": "external tool servers"},
    {"id": "voice", "label": "Voice / media", "why": "TTS/STT, images"},
    {"id": "delegate", "label": "Delegation", "why": "subagents / mixture of agents"},
    {"id": "plugins", "label": "Plugins", "why": "pre_llm hooks, integrations"},
    {"id": "session_search", "label": "Session search", "why": "FTS past conversations"},
]


def hermes_home() -> Path:
    raw = os.environ.get("HERMES_HOME", "").strip()
    if raw:
        return Path(raw).expanduser().resolve()
    return (Path.home() / ".hermes").resolve()


@dataclass
class EnvironmentReport:
    hermes_home: str
    surfaces: list[dict[str, Any]] = field(default_factory=list)
    skills_count: int = 0
    skills_sample: list[str] = field(default_factory=list)
    memory_files: list[str] = field(default_factory=list)
    cron_present: bool = False
    plugins_sample: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def desk_concepts(self) -> list[str]:
        """Short concepts to drop onto Hermespace desk as environment awareness."""
        out = [
            f"[struct|0.7] hermes_home:{Path(self.hermes_home).name}",
            f"[struct|0.65] skills_available:{self.skills_count}",
        ]
        if self.memory_files:
            out.append(f"[exec|0.7] memory_files:{','.join(self.memory_files[:3])}")
        if self.cron_present:
            out.append("[exec|0.6] cron_automation:present")
        live = [s["id"] for s in self.surfaces if s.get("present")]
        if live:
            out.append(f"[struct|0.75] tool_surfaces:{','.join(live[:8])}")
        return out


def probe_environment(home: Path | None = None) -> EnvironmentReport:
    hh = home or hermes_home()
    report = EnvironmentReport(hermes_home=str(hh))

    # surfaces presence heuristics (no secrets)
    checks = {
        "terminal": True,  # always conceptually available to Hermes
        "web": (hh / "config.yaml").is_file() or True,
        "files": True,
        "memory": (hh / "memories").is_dir() or (hh / "memories" / "MEMORY.md").is_file(),
        "skills": (hh / "skills").is_dir(),
        "cron": (hh / "cron").is_dir() or (hh / "cron" / "jobs.json").is_file(),
        "messaging": (hh / "gateway.pid").is_file() or (hh / "gateway.reloader.pid").is_file() or True,
        "mcp": (hh / "mcp").is_dir() or False,
        "voice": False,
        "delegate": True,
        "plugins": (hh / "plugins").is_dir(),
        "session_search": (hh / "state.db").is_file() or True,
    }
    for spec in HERMES_TOOL_SURFACES:
        sid = spec["id"]
        report.surfaces.append(
            {
                **spec,
                "present": bool(checks.get(sid, False)),
            }
        )

    skills_dir = hh / "skills"
    if skills_dir.is_dir():
        names: list[str] = []
        for p in sorted(skills_dir.rglob("SKILL.md"))[:200]:
            # skill name ≈ parent folder
            names.append(p.parent.name)
        report.skills_count = len(names)
        report.skills_sample = names[:15]

    mem_dir = hh / "memories"
    for name in ("MEMORY.md", "USER.md", "SOUL.md"):
        if (mem_dir / name).is_file() or (hh / name).is_file():
            report.memory_files.append(name)

    report.cron_present = bool(checks.get("cron"))

    plug = hh / "plugins"
    if plug.is_dir():
        report.plugins_sample = sorted(
            [p.name for p in plug.iterdir() if p.is_dir() or p.is_symlink()]
        )[:20]

    if not hh.is_dir():
        report.notes.append("HERMES_HOME not found — inventory is conceptual only")
    else:
        report.notes.append("inventory probed from HERMES_HOME (no secrets read)")

    return report


def environment_markdown(report: EnvironmentReport | None = None) -> str:
    rep = report or probe_environment()
    lines = [
        "# Hermespace environment kit",
        "",
        f"HERMES_HOME: `{rep.hermes_home}`",
        "",
        "## Tool surfaces",
    ]
    for s in rep.surfaces:
        mark = "yes" if s.get("present") else "—"
        lines.append(f"- [{mark}] **{s['id']}** — {s['label']} ({s['why']})")
    lines += [
        "",
        f"## Skills: {rep.skills_count}",
        *(f"- {n}" for n in rep.skills_sample),
        "",
        f"## Memory files: {', '.join(rep.memory_files) or '(none spotted)'}",
        f"## Cron: {'present' if rep.cron_present else 'not spotted'}",
        f"## Plugins: {', '.join(rep.plugins_sample) or '(none)'}",
        "",
        "## Notes",
        *(f"- {n}" for n in rep.notes),
        "",
    ]
    return "\n".join(lines)
