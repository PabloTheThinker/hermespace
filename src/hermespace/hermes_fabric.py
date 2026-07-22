"""Bridge Hermespace ↔ Hermes skills + MEMORY/USER fabric.

Any user's Hermes agent keeps *their* skills and memories usable inside
the pocket dimension:

- Rank skills against the live goal (embeddings when available)
- Pull short MEMORY.md / USER.md excerpts into model context (bounded)
- Never commit user memory into the Hermespace git package
- Optional: record learnings into Hermespace study DB (not overwrite Hermes MEMORY)

Hermes remains source of truth for MEMORY.md / skills files.
Hermespace coordinates FOA + inject so the agent *uses* them this turn.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from hermespace.environment import hermes_home
from hermespace.local_model import select_embed_backend
from hermespace.neural_field import cosine

# Hard caps — Hermes-style token hygiene
MEMORY_EXCERPT_CHARS = 900
USER_EXCERPT_CHARS = 600
SKILL_PREVIEW_CHARS = 500
MAX_SKILL_HITS = 5

# Quicksilver-style skill index cache: scan signature → catalog
_SKILL_INDEX_CACHE: dict[str, tuple[str, list[tuple[str, Path, str]]]] = {}
_FABRIC_CACHE: dict[str, tuple[float, "FabricSnapshot"]] = {}
_FABRIC_TTL_S = float(os.environ.get("HERMESPACE_FABRIC_TTL", "45"))


def _skills_scan_sig(root: Path) -> str:
    """Cheap invalidation key — file count + newest mtime (not full content hash)."""
    newest = 0.0
    count = 0
    try:
        for p in root.rglob("SKILL.md"):
            count += 1
            try:
                newest = max(newest, p.stat().st_mtime)
            except OSError:
                pass
    except OSError:
        pass
    return f"{count}:{newest:.3f}"


@dataclass
class SkillHit:
    name: str
    path: str
    score: float
    preview: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "path": self.path,
            "score": round(self.score, 4),
            "preview": self.preview[:SKILL_PREVIEW_CHARS],
        }


@dataclass
class FabricSnapshot:
    memory_excerpt: str = ""
    user_excerpt: str = ""
    skill_hits: list[SkillHit] = field(default_factory=list)
    hermes_home: str = ""
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "hermes_home": self.hermes_home,
            "memory_excerpt": self.memory_excerpt,
            "user_excerpt": self.user_excerpt,
            "skill_hits": [h.to_dict() for h in self.skill_hits],
            "notes": self.notes,
        }

    def inject_markdown(self) -> str:
        """Block for model context — skills + memory the agent already owns."""
        parts = ["### Hermes fabric (your skills & memory — use them)"]
        if self.skill_hits:
            parts.append("**Ranked skills for this goal:**")
            for h in self.skill_hits:
                parts.append(f"- `{h.name}` (score={h.score:.2f})")
                if h.preview:
                    # first non-empty lines only
                    line = " ".join(
                        ln.strip()
                        for ln in h.preview.splitlines()
                        if ln.strip() and not ln.strip().startswith("---")
                    )[:180]
                    if line:
                        parts.append(f"  _{line}_")
        else:
            parts.append("_No skill ranking (empty skills dir or no goal)._")
        if self.user_excerpt:
            parts.append("**USER.md (excerpt):**")
            parts.append(self.user_excerpt[:USER_EXCERPT_CHARS])
        if self.memory_excerpt:
            parts.append("**MEMORY.md (excerpt):**")
            parts.append(self.memory_excerpt[:MEMORY_EXCERPT_CHARS])
        parts.append(
            "_Load full skills via Hermes `skill_view(name=...)` when a hit matches the task._"
        )
        return "\n".join(parts)


def _read_capped(path: Path, limit: int) -> str:
    if not path.is_file():
        return ""
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""
    text = text.strip()
    if len(text) <= limit:
        return text
    # head + tail for MEMORY style
    head = text[: int(limit * 0.7)]
    tail = text[-int(limit * 0.25) :]
    return head + "\n…\n" + tail


def _skill_index(hh: Path) -> list[tuple[str, Path, str]]:
    """Return (name, path, blurb) for each SKILL.md.

    Cached by directory mtime signature (Quicksilver skill-discovery pattern).
    """
    root = hh / "skills"
    if not root.is_dir():
        return []
    sig = _skills_scan_sig(root)
    cached = _SKILL_INDEX_CACHE.get(str(root))
    if cached and cached[0] == sig:
        return cached[1]
    out: list[tuple[str, Path, str]] = []
    for p in root.rglob("SKILL.md"):
        name = p.parent.name
        try:
            raw = p.read_text(encoding="utf-8", errors="replace")[:2000]
        except OSError:
            raw = ""
        # description from frontmatter if present
        desc = ""
        m = re.search(r"^description:\s*[>|]?\s*(.+)$", raw, re.M | re.I)
        if m:
            desc = m.group(1).strip()[:240]
        if not desc:
            for ln in raw.splitlines():
                s = ln.strip()
                if s.startswith("#"):
                    desc = s.lstrip("#").strip()[:240]
                    break
        blurb = f"{name} {desc}"
        out.append((name, p, blurb))
    _SKILL_INDEX_CACHE[str(root)] = (sig, out)
    return out


def rank_skills_for_goal(
    goal: str,
    *,
    message: str = "",
    limit: int = MAX_SKILL_HITS,
    hh: Path | None = None,
    include_preview: bool = True,
) -> list[SkillHit]:
    """Rank user's Hermes skills against goal+message via embeddings/hash.

    Quicksilver default: **hash** backend for fabric ranking (153 skills ×
    Ollama embed was ~3s on the pre_llm path). Opt into neural rank with
    HERMESPACE_FABRIC_EMBED=1 or HERMESPACE_FABRIC_BACKEND=ollama_embed.
    """
    home = hh or hermes_home()
    catalog = _skill_index(home)
    if not catalog:
        return []
    query = f"{goal} {message}".strip() or goal
    # Speed spine: fabric rank is hot-path; hash unless explicitly upgraded
    backend_name = os.environ.get("HERMESPACE_FABRIC_BACKEND", "").strip()
    if not backend_name:
        if os.environ.get("HERMESPACE_FABRIC_EMBED", "").strip().lower() in {
            "1",
            "true",
            "yes",
            "on",
        }:
            backend_name = os.environ.get("HERMESPACE_NEURAL_BACKEND", "auto")
        else:
            backend_name = "hash"
    backend = select_embed_backend(backend_name)
    qv = backend.embed(query, 256)
    scored: list[SkillHit] = []
    for name, path, blurb in catalog:
        sv = backend.embed(blurb, 256)
        score = max(0.0, cosine(qv, sv))
        preview = ""
        if include_preview:
            try:
                preview = path.read_text(encoding="utf-8", errors="replace")[
                    :SKILL_PREVIEW_CHARS
                ]
            except OSError:
                preview = blurb
        scored.append(SkillHit(name=name, path=str(path), score=score, preview=preview))
    scored.sort(key=lambda h: h.score, reverse=True)
    # drop near-zero noise
    scored = [h for h in scored if h.score >= 0.15][:limit]
    return scored


def load_memory_excerpts(hh: Path | None = None) -> tuple[str, str]:
    home = hh or hermes_home()
    mem = _read_capped(home / "memories" / "MEMORY.md", MEMORY_EXCERPT_CHARS)
    if not mem:
        mem = _read_capped(home / "MEMORY.md", MEMORY_EXCERPT_CHARS)
    user = _read_capped(home / "memories" / "USER.md", USER_EXCERPT_CHARS)
    if not user:
        user = _read_capped(home / "USER.md", USER_EXCERPT_CHARS)
    return mem, user


def snapshot_fabric(
    *,
    goal: str = "",
    message: str = "",
    hh: Path | None = None,
) -> FabricSnapshot:
    """Build fabric snapshot with short TTL cache (Quicksilver: leave critical path)."""
    import time

    home = hh or hermes_home()
    key = f"{home}|{(goal or '')[:120]}|{(message or '')[:80]}"
    now = time.monotonic()
    hit = _FABRIC_CACHE.get(key)
    if hit and (now - hit[0]) < _FABRIC_TTL_S:
        return hit[1]

    snap = FabricSnapshot(hermes_home=str(home))
    if not home.is_dir():
        snap.notes.append("HERMES_HOME missing — fabric empty")
        return snap
    mem, user = load_memory_excerpts(home)
    snap.memory_excerpt = mem
    snap.user_excerpt = user
    if goal or message:
        snap.skill_hits = rank_skills_for_goal(
            goal or message, message=message, hh=home
        )
        snap.notes.append(f"ranked {len(snap.skill_hits)} skills")
    else:
        snap.notes.append("no goal — skills not ranked")
    if snap.memory_excerpt:
        snap.notes.append("MEMORY.md excerpt loaded")
    if snap.user_excerpt:
        snap.notes.append("USER.md excerpt loaded")
    # cap cache size
    if len(_FABRIC_CACHE) > 32:
        oldest = min(_FABRIC_CACHE.items(), key=lambda kv: kv[1][0])[0]
        _FABRIC_CACHE.pop(oldest, None)
    _FABRIC_CACHE[key] = (now, snap)
    return snap


def skill_load_hints(hits: list[SkillHit]) -> list[str]:
    """Desk concepts pointing agent at Hermes skill_view."""
    out = []
    for h in hits[:MAX_SKILL_HITS]:
        out.append(f"[exec|0.72] skill_hint:{h.name} (use skill_view name={h.name})")
    return out
