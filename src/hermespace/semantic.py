"""Semantic notes — Conductor SemanticStore pattern, file-backed."""

from __future__ import annotations

import json
import re
import uuid
from collections import Counter
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from hermespace.episodic import EpisodicLog
from hermespace.paths import state_dir as default_state_dir

_STOP = frozenset(
    "the a an and or to of for in on at is was with from that this into via set goal enter sealed".split()
)


def _utcnow() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _tokens(text: str) -> list[str]:
    return [
        t
        for t in re.findall(r"[a-z0-9][a-z0-9_\-]{2,}", text.lower())
        if t not in _STOP
    ]


@dataclass
class SemanticNote:
    note_id: str
    statement: str
    tags: list[str] = field(default_factory=list)
    confidence: float = 0.7
    created_at: str = field(default_factory=_utcnow)
    source_ids: list[str] = field(default_factory=list)


class SemanticStore:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or (default_state_dir() / "semantic.json")
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def _load(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            return list(data.get("items") or [])
        except (json.JSONDecodeError, OSError):
            return []

    def _save(self, items: list[dict[str, Any]]) -> None:
        self.path.write_text(
            json.dumps({"items": items[-200:]}, indent=2), encoding="utf-8"
        )

    def list_notes(self, limit: int = 20) -> list[SemanticNote]:
        items = self._load()
        notes = [SemanticNote(**{k: v for k, v in i.items() if k in SemanticNote.__dataclass_fields__}) for i in items if isinstance(i, dict)]
        return notes[:limit]

    def add(self, statement: str, *, tags: list[str] | None = None, confidence: float = 0.7, source_ids: list[str] | None = None) -> SemanticNote:
        statement = statement.strip()
        items = self._load()
        needle = statement.casefold()
        for raw in items:
            if isinstance(raw, dict) and str(raw.get("statement", "")).casefold() == needle:
                return SemanticNote(**{k: raw[k] for k in SemanticNote.__dataclass_fields__ if k in raw})
        note = SemanticNote(
            note_id=str(uuid.uuid4()),
            statement=statement,
            tags=list(tags or []),
            confidence=max(0.0, min(1.0, confidence)),
            source_ids=list(source_ids or []),
        )
        items.append(asdict(note))
        self._save(items)
        return note


def consolidate(limit: int = 40) -> dict[str, Any]:
    """Deterministic consolidation from episodic → semantic (Conductor pattern)."""
    eps = EpisodicLog().recent(limit=limit)
    # recent() returns newest first; reverse for chrono
    entries = list(reversed(eps))
    if not entries:
        return {"scanned": 0, "created": 0, "notes": []}

    tag_c: Counter[str] = Counter()
    outcome_c: Counter[str] = Counter()
    token_c: Counter[str] = Counter()
    store = SemanticStore()
    created: list[str] = []

    for e in entries:
        outcome_c[str(e.get("outcome") or "info")] += 1
        for t in e.get("tags") or []:
            tag_c[str(t)] += 1
        for tok in _tokens(str(e.get("content") or "")):
            token_c[tok] += 1

    for tag, count in tag_c.most_common(10):
        if count < 2:
            continue
        n = store.add(
            f"Recurring Hermespace pattern: '{tag}' x{count}",
            tags=["consolidated", "tag", tag],
            confidence=min(0.95, 0.55 + 0.05 * count),
        )
        created.append(n.statement)

    for outcome, count in outcome_c.items():
        if count < 1:
            continue
        n = store.add(
            f"Outcome mix: {count} event(s) as '{outcome}'",
            tags=["consolidated", "outcome", outcome],
            confidence=min(0.9, 0.5 + 0.05 * count),
        )
        created.append(n.statement)

    for tok, count in token_c.most_common(8):
        if count < 2:
            continue
        n = store.add(
            f"Compounded term '{tok}' recurred {count}x in desk episodes",
            tags=["consolidated", "term", tok],
            confidence=min(0.88, 0.5 + 0.04 * count),
        )
        created.append(n.statement)

    return {"scanned": len(entries), "created": len(created), "notes": created}
