"""World Model — Hermespace as a persistent world the agent lives in.

The World is the agent's external J-Space: a structured, persistent
representation of everything the agent knows, believes, and is doing.

The archive (JSONL) is the source of truth — it grows forever.
world.json is a fast cache / projection of current state.

Archive types: enter, leave, landmark, belief, trait, evolution,
focus, epoch_transition, resolve, relationship.
"""

from __future__ import annotations

import json
import os
import re
import uuid
from collections import Counter
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from hermespace.paths import state_dir


def _utcnow() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _epoch_for_index(idx: int) -> str:
    if idx < 5:
        return "Genesis"
    if idx < 25:
        return "Growth"
    if idx < 100:
        return "Maturity"
    return "Wisdom"


def _epoch_emoji(epoch: str) -> str:
    return {"Genesis": "\u2728", "Growth": "\ud83c\udf31", "Maturity": "\ud83c\udf93", "Wisdom": "\ud83e\udde0"}.get(epoch, "\u2728")


_EPOCH_THRESHOLDS = {
    "Genesis": 0,
    "Growth": 5,
    "Maturity": 25,
    "Wisdom": 100,
}


@dataclass
class TimelineEntry:
    id: str = ""
    timestamp: str = ""
    entry_type: str = ""
    agent_id: str = ""
    description: str = ""
    data: dict = field(default_factory=dict)
    causal_parents: list[str] = field(default_factory=list)
    outcome: str = ""


@dataclass
class WorldBelief:
    statement: str = ""
    confidence: float = 0.5
    source: str = ""
    updated: str = field(default_factory=_utcnow)
    tags: list[str] = field(default_factory=list)
    corroborations: int = 0


@dataclass
class WorldRelationship:
    entity: str = ""
    kind: str = "user"
    affinity: float = 0.5
    history: list[str] = field(default_factory=list)
    updated: str = field(default_factory=_utcnow)


@dataclass
class WorldState:
    agent_id: str = ""
    identity_traits: list[str] = field(default_factory=list)
    current_state: str = "idle"

    environment_snapshot: dict[str, Any] = field(default_factory=dict)
    world_time: str = field(default_factory=_utcnow)

    beliefs: list[WorldBelief] = field(default_factory=list)
    relationships: list[WorldRelationship] = field(default_factory=list)

    current_goal: str = ""
    current_decision: str = ""
    current_plan: list[str] = field(default_factory=list)

    landmarks: list[str] = field(default_factory=list)
    open_questions: list[str] = field(default_factory=list)

    evolution_count: int = 0
    last_evolved: str = ""
    created: str = field(default_factory=_utcnow)
    updated: str = field(default_factory=_utcnow)

    timeline: list[TimelineEntry] = field(default_factory=list)
    epoch: str = "Genesis"
    archive_path: str = ""

    # J-Space hub: ~25 named concept slots
    concepts: dict[str, float] = field(default_factory=dict)


class WorldArchive:
    """Append-only JSONL log at ~/.hermespace/worlds/{agent_id}_archive.jsonl"""

    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        root = state_dir() / "worlds"
        root.mkdir(parents=True, exist_ok=True)
        self.path = root / f"{self._safe(agent_id)}_archive.jsonl"
        self._cache: list[TimelineEntry] | None = None
        self._cache_mtime: float = 0.0

    @staticmethod
    def _safe(s: str) -> str:
        return "".join(c if c.isalnum() or c in "-_" else "_" for c in s)[:80] or "agent"

    def _read_cache(self) -> list[TimelineEntry]:
        if not self.path.is_file():
            self._cache = []
            self._cache_mtime = 0.0
            return []
        current_mtime = self.path.stat().st_mtime
        if self._cache is not None and current_mtime == self._cache_mtime:
            return self._cache
        entries: list[TimelineEntry] = []
        with self.path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    if isinstance(data, dict):
                        entries.append(TimelineEntry(**{k: v for k, v in data.items() if k in TimelineEntry.__dataclass_fields__}))
                except (json.JSONDecodeError, TypeError, ValueError):
                    continue
        self._cache = entries
        self._cache_mtime = current_mtime
        return entries

    def _invalidate_cache(self) -> None:
        self._cache = None
        self._cache_mtime = 0.0

    def append(self, entry_type: str, agent_id: str, description: str, data: dict | None = None, causal_parents: list[str] | None = None, outcome: str = "") -> TimelineEntry:
        entry = TimelineEntry(
            id=uuid.uuid4().hex[:12],
            timestamp=_utcnow(),
            entry_type=entry_type,
            agent_id=agent_id,
            description=description,
            data=data or {},
            causal_parents=causal_parents or [],
            outcome=outcome,
        )
        line = json.dumps(asdict(entry), default=str) + "\n"
        with self.path.open("a", encoding="utf-8") as f:
            f.write(line)
        self._invalidate_cache()
        return entry

    def replay(self) -> list[TimelineEntry]:
        return self._read_cache()

    def count(self) -> int:
        return len(self._read_cache())

    def query(self, entry_type: str | None = None, limit: int = 0) -> list[TimelineEntry]:
        entries = self._read_cache()
        if entry_type:
            entries = [e for e in entries if e.entry_type == entry_type]
        if limit > 0:
            entries = entries[-limit:]
        return entries

    def query_range(self, after: str | None = None, before: str | None = None) -> list[TimelineEntry]:
        entries = self._read_cache()
        if after:
            entries = [e for e in entries if e.timestamp >= after]
        if before:
            entries = [e for e in entries if e.timestamp <= before]
        return entries

    def search(self, term: str, entry_type: str | None = None, limit: int = 20) -> list[TimelineEntry]:
        term_lower = term.lower()
        entries = self._read_cache()
        if entry_type:
            entries = [e for e in entries if e.entry_type == entry_type]
        matches: list[TimelineEntry] = []
        for e in entries:
            if term_lower in e.description.lower():
                matches.append(e)
                continue
            for val in (e.data or {}).values():
                if isinstance(val, str) and term_lower in val.lower():
                    matches.append(e)
                    break
                if isinstance(val, (int, float)):
                    if str(val) == term:
                        matches.append(e)
                        break
        if limit > 0:
            matches = matches[-limit:]
        return matches

    def count_by_type(self) -> dict[str, int]:
        counts: Counter = Counter()
        for e in self._read_cache():
            counts[e.entry_type] += 1
        return dict(counts)

    def get_entry(self, entry_id: str) -> TimelineEntry | None:
        for e in self._read_cache():
            if e.id == entry_id:
                return e
        return None


class WorldModel:
    """The agent's persistent world — the space they live and work in.

    The archive (JSONL) is the source of truth — it grows forever.
    world.json is a fast cache / projection of current state.
    """

    def __init__(self, agent_id: str = "hermes-agent") -> None:
        self.agent_id = agent_id
        self.root = state_dir() / "worlds"
        self.root.mkdir(parents=True, exist_ok=True)
        self.path = self.root / f"{self._safe(agent_id)}.json"
        self.archive = WorldArchive(agent_id)
        self._state = self._load()
        if not self._state.archive_path:
            self._state.archive_path = str(self.archive.path)

    @staticmethod
    def _safe(s: str) -> str:
        return "".join(c if c.isalnum() or c in "-_" else "_" for c in s)[:80] or "agent"

    def _load(self) -> WorldState:
        if not self.path.is_file():
            return WorldState(agent_id=self.agent_id)
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            concepts_raw = data.get("concepts") or {}
            concepts = {str(k): float(v) for k, v in concepts_raw.items() if isinstance(v, (int, float))}
            return WorldState(
                agent_id=str(data.get("agent_id") or self.agent_id),
                identity_traits=list(data.get("identity_traits") or []),
                current_state=str(data.get("current_state") or "idle"),
                environment_snapshot=dict(data.get("environment_snapshot") or {}),
                world_time=str(data.get("world_time") or _utcnow()),
                beliefs=[WorldBelief(**b) for b in (data.get("beliefs") or []) if isinstance(b, dict)],
                relationships=[WorldRelationship(**r) for r in (data.get("relationships") or []) if isinstance(r, dict)],
                current_goal=str(data.get("current_goal") or ""),
                current_decision=str(data.get("current_decision") or ""),
                current_plan=list(data.get("current_plan") or []),
                landmarks=list(data.get("landmarks") or []),
                open_questions=list(data.get("open_questions") or []),
                evolution_count=int(data.get("evolution_count") or 0),
                last_evolved=str(data.get("last_evolved") or ""),
                created=str(data.get("created") or _utcnow()),
                updated=str(data.get("updated") or _utcnow()),
                timeline=[TimelineEntry(**t) for t in (data.get("timeline") or []) if isinstance(t, dict)],
                epoch=str(data.get("epoch") or "Genesis"),
                archive_path=str(data.get("archive_path") or ""),
                concepts=concepts,
            )
        except (OSError, json.JSONDecodeError, TypeError, ValueError):
            return WorldState(agent_id=self.agent_id)

    def save(self) -> Path:
        self._state.updated = _utcnow()
        self._state.world_time = _utcnow()
        self.path.write_text(json.dumps(asdict(self._state), indent=2, default=str), encoding="utf-8")
        return self.path

    @property
    def state(self) -> WorldState:
        return self._state

    def _compute_epoch(self) -> str:
        count = self.archive.count()
        if count < _EPOCH_THRESHOLDS["Growth"]:
            return "Genesis"
        if count < _EPOCH_THRESHOLDS["Maturity"]:
            return "Growth"
        if count < _EPOCH_THRESHOLDS["Wisdom"]:
            return "Maturity"
        return "Wisdom"

    def _add_timeline(self, entry_type: str, description: str, data: dict | None = None, causal_parents: list[str] | None = None, outcome: str = "") -> TimelineEntry:
        entry = self.archive.append(entry_type, self.agent_id, description, data, causal_parents, outcome)
        self._state.timeline.insert(0, entry)
        if len(self._state.timeline) > 50:
            self._state.timeline = self._state.timeline[:50]
        return entry

    def enter(self, desk: Any = None) -> WorldState:
        """Agent enters the world — probe environment, sync desk."""
        try:
            from hermespace.environment import probe_environment
            env = probe_environment()
            self._state.environment_snapshot = env.to_dict()
            if not self._state.identity_traits and env.memory_files:
                if "SOUL.md" in env.memory_files:
                    self._state.identity_traits.append("has SOUL.md identity")
                if "MEMORY.md" in env.memory_files:
                    self._state.identity_traits.append("has persistent memory")
        except Exception:
            pass

        if desk:
            old_goal = self._state.current_goal
            self._state.current_goal = desk.goal or self._state.current_goal
            self._state.current_decision = desk.decision or self._state.current_decision
            self._state.current_plan = desk.plan or self._state.current_plan
            self._state.current_state = "working" if desk.goal else "idle"
            if desk.goal and desk.goal != old_goal:
                self._add_timeline("focus", f"Focus: {desk.goal[:200]}", {"goal": desk.goal, "type": "session_start"})

        if not self._state.landmarks:
            event = f"World created — agent {self.agent_id} entered Hermespace"
            self._state.landmarks.append(f"[{_utcnow()}] {event}")
            self._add_timeline("landmark", event, {"event": event})

        self._add_timeline("enter", "Agent entered the world", {"state": self._state.current_state})
        self._state.current_state = "working"
        self._state.world_time = _utcnow()
        self._refresh_concepts()
        self.save()
        return self._state

    def leave(self, note: str = "") -> WorldState:
        note = (note or "").strip()
        # Generic session-end is not a landmark — it drowned Active Wisdom history
        material = bool(note) and note.lower() not in (
            "session ended",
            "session end",
            "left",
            "idle",
            "ok",
        )
        if material:
            self._state.landmarks.append(f"[{_utcnow()}] {note}")
            self._add_timeline("landmark", note, {"event": note})
        self._add_timeline("leave", note or "Agent left the world", {"note": note})
        # Always strip legacy session-end landmark spam (running agents may have piled them)
        self._state.landmarks = [
            lm
            for lm in self._state.landmarks
            if "session ended" not in (lm or "").lower()
            and "session end" not in (lm or "").lower()
        ][-40:]
        self._state.current_state = "idle"
        self._state.world_time = _utcnow()
        self.save()
        return self._state

    def add_landmark(self, event: str) -> None:
        event = event.strip()
        if not event:
            return
        # Never landmark generic session ends (drowns material history)
        if event.lower() in ("session ended", "session end", "left", "idle", "ok"):
            self._add_timeline("leave", event, {"note": event})
            self._state.current_state = "idle"
            self._state.world_time = _utcnow()
            self.save()
            return
        self._state.landmarks.append(f"[{_utcnow()}] {event}")
        self._add_timeline("landmark", event, {"event": event})
        self.save()

    def add_belief(self, statement: str, confidence: float = 0.5, source: str = "") -> None:
        statement = statement.strip()
        if not statement:
            return
        for b in self._state.beliefs:
            if b.statement.lower() == statement.lower():
                b.confidence = min(1.0, b.confidence + 0.1)
                b.corroborations += 1
                b.updated = _utcnow()
                b.source = source or b.source
                self._add_timeline("belief", f"Reinforced belief: {statement[:120]}", {
                    "statement": statement, "confidence": b.confidence,
                    "corroborations": b.corroborations, "source": source,
                })
                self._refresh_concepts()
                self.save()
                return
        self._state.beliefs.append(WorldBelief(
            statement=statement,
            confidence=min(1.0, confidence),
            source=source,
            corroborations=1,
        ))
        self._add_timeline("belief", f"New belief: {statement[:120]}", {
            "statement": statement,
            "confidence": min(1.0, confidence),
            "source": source,
        })
        self._refresh_concepts()
        self.save()

    def set_goal(self, goal: str, decision: str = "", plan: list[str] | None = None) -> None:
        goal = goal.strip() or self._state.current_goal
        if not goal:
            return
        old_goal = self._state.current_goal
        self._state.current_goal = goal
        if decision:
            self._state.current_decision = decision
        if plan:
            self._state.current_plan = plan[:8]
        self._state.current_state = "working"
        parent_id = self._state.timeline[0].id if self._state.timeline else ""
        if goal != old_goal:
            self._add_timeline("focus", f"Focus: {goal[:200]}", {
                "goal": goal, "decision": decision, "type": "set_goal",
            }, causal_parents=[parent_id] if parent_id else None)
        self._refresh_concepts()
        self.save()

    def resolve_outcome(self, entry_id: str, outcome: str) -> bool:
        outcome = outcome.strip().lower()
        if outcome not in ("success", "failure", "pending", "superseded"):
            return False
        entry = self.archive.get_entry(entry_id)
        if not entry:
            return False
        self._add_timeline("resolve", f"Outcome: {entry.description[:80]} → {outcome}", {
            "target_entry": entry_id,
            "outcome": outcome,
            "entry_type": entry.entry_type,
        }, causal_parents=[entry_id])
        self._refresh_concepts()
        self.save()
        return True

    def add_relationship(self, entity: str, kind: str = "user", affinity: float = 0.5) -> None:
        for r in self._state.relationships:
            if r.entity.lower() == entity.lower():
                r.affinity = max(-1.0, min(1.0, affinity))
                r.history.append(f"affinity->{affinity:.1f} at {_utcnow()}")
                r.history = r.history[-10:]
                r.updated = _utcnow()
                self._add_timeline("relationship", f"Relationship: {entity} affinity={affinity:.1f}", {
                    "entity": entity, "kind": kind, "affinity": affinity,
                })
                self.save()
                return
        self._state.relationships.append(WorldRelationship(
            entity=entity, kind=kind, affinity=max(-1.0, min(1.0, affinity)),
        ))
        self._add_timeline("relationship", f"New relationship: {entity} ({kind})", {
            "entity": entity, "kind": kind, "affinity": affinity,
        })
        self.save()

    def set_trait(self, trait: str) -> None:
        t = trait.strip()
        if not t or t in self._state.identity_traits:
            return
        self._state.identity_traits.append(t)
        self._add_timeline("trait", f"New trait: {t}", {"trait": t})
        self._refresh_concepts()
        self.save()

    def _detect_patterns(self) -> list[str]:
        recent = self._state.landmarks[-20:]
        tokens: list[str] = []
        for lm in recent:
            for tok in re.findall(r"[a-zA-Z][a-zA-Z0-9_\-]{2,}", lm):
                tokens.append(tok.lower())
        stopwords = {"the", "and", "for", "from", "that", "this", "with", "was", "has", "had", "not"}
        counts = Counter(t for t in tokens if t not in stopwords)
        patterns: list[str] = []
        for word, count in counts.most_common(5):
            if count >= 3:
                # Check if we already have a belief about this
                already = any(word in b.statement.lower() for b in self._state.beliefs)
                if not already:
                    patterns.append(f"Recurring pattern: '{word}' mentioned {count}x in recent landmarks")
        return patterns

    def _analyze_relationships(self) -> None:
        if not self._state.relationships:
            return
        for rel in self._state.relationships:
            if rel.history:
                avg_affinity = sum(self._parse_affinity(h) for h in rel.history[-5:] if self._parse_affinity(h) is not None)
                if avg_affinity is not None:
                    rel.affinity = max(-1.0, min(1.0, avg_affinity / max(1, len(rel.history[-5:]))))

    @staticmethod
    def _parse_affinity(history_entry: str) -> float | None:
        try:
            match = re.search(r"affinity->(-?\d+\.?\d*)", history_entry)
            if match:
                return float(match.group(1))
        except (ValueError, TypeError):
            pass
        return None

    def _detect_milestones(self) -> list[str]:
        milestones: list[str] = []
        archive_count = self.archive.count()
        epoch_map = [
            (5, "Growth"),
            (10, "Growth"),
            (25, "Maturity"),
            (50, "Maturity"),
            (100, "Wisdom"),
            (200, "Wisdom"),
        ]
        if archive_count in [e[0] for e in epoch_map]:
            epoch_name = next(e[1] for e in epoch_map if e[0] == archive_count)
            milestones.append(f"Milestone: reached {archive_count} timeline entries ({epoch_name})")
        if self._state.evolution_count == 1:
            milestones.append("Milestone: first evolution cycle")
        if self._state.evolution_count == 10:
            milestones.append("Milestone: 10 evolution cycles")
        if self._state.evolution_count == 100:
            milestones.append("Milestone: 100 evolution cycles")
        high_confidence = [b for b in self._state.beliefs if b.confidence >= 0.8 and b.corroborations >= 3]
        for b in high_confidence:
            if not any(f"corroborations reached" in lm.lower() for lm in self._state.landmarks):
                milestones.append(f"Milestone: belief '{b.statement[:80]}' reached {b.corroborations}x corroboration")
        return milestones

    def _generate_questions(self) -> list[str]:
        questions: list[str] = []
        for b in self._state.beliefs:
            if b.confidence < 0.5 and b.corroborations <= 2:
                questions.append(f"Is '{b.statement[:80]}' still accurate? (confidence: {b.confidence:.1f})")
        if self._state.open_questions:
            for q in self._state.open_questions:
                if not any(q in entry.description for entry in self.archive.query("resolve", limit=20)):
                    questions.append(q)
        return questions[:5]

    def _refresh_concepts(self) -> None:
        concepts: dict[str, float] = {}

        if self._state.current_goal:
            words = re.findall(r"[a-zA-Z][a-zA-Z0-9_\-]{2,10}", self._state.current_goal.lower())
            for w in words[:3]:
                concepts[w] = max(concepts.get(w, 0), 0.9)

        for b in sorted(self._state.beliefs, key=lambda x: -x.confidence)[:5]:
            words = re.findall(r"[a-zA-Z][a-zA-Z0-9_\-]{2,10}", b.statement.lower())
            for w in words[:2]:
                concepts[w] = max(concepts.get(w, 0), b.confidence * 0.7)

        if self._state.current_decision:
            words = re.findall(r"[a-zA-Z][a-zA-Z0-9_\-]{2,10}", self._state.current_decision.lower())
            for w in words[:2]:
                concepts[w] = max(concepts.get(w, 0), 0.6)

        entries = self.archive.query(limit=5)
        for e in entries:
            desc_words = re.findall(r"[a-zA-Z][a-zA-Z0-9_\-]{2,10}", e.description.lower())
            for w in desc_words[:1]:
                concepts[w] = max(concepts.get(w, 0), 0.3)

        sorted_items = sorted(concepts.items(), key=lambda x: -x[1])[:25]
        self._state.concepts = dict(sorted_items)

    def trace_chain(self, entry_id: str) -> list[TimelineEntry]:
        chain: list[TimelineEntry] = []
        current_id: str | None = entry_id
        visited: set[str] = set()
        while current_id and current_id not in visited:
            visited.add(current_id)
            entry = self.archive.get_entry(current_id)
            if not entry:
                break
            chain.append(entry)
            current_id = entry.causal_parents[0] if entry.causal_parents else None
        return chain

    def evolve(self) -> dict[str, Any]:
        """World evolution cycle.

        Does NOT prune, decay, or delete anything.
        Consolidates new beliefs, detects patterns, analyzes
        relationships, detects milestones, generates questions.
        """
        actions: list[str] = []
        old_epoch = self._state.epoch

        # Stage 1: Consolidate semantic notes
        try:
            from hermespace.semantic import SemanticStore

            semantic = SemanticStore()
            notes = semantic.list_notes(limit=5)
            for note in notes:
                statement = getattr(note, "statement", "") or str(note)[:200]
                if statement and len(statement) > 20:
                    self.add_belief(statement[:200], confidence=0.55, source="consolidation")
            if notes:
                actions.append(f"consolidated {len(notes)} semantic notes")
        except Exception as exc:
            actions.append(f"consolidate_error:{type(exc).__name__}")

        # Stage 2: Pattern detection
        patterns = self._detect_patterns()
        for pattern in patterns:
            self.add_belief(pattern, confidence=0.5, source="pattern_detection")
            actions.append(f"pattern: {pattern[:60]}")
        if not patterns:
            actions.append("no new patterns")

        # Stage 3: Relationship analysis
        self._analyze_relationships()
        if self._state.relationships:
            actions.append(f"analyzed {len(self._state.relationships)} relationships")

        # Stage 4: Milestone detection
        milestones = self._detect_milestones()
        for ms in milestones:
            self._add_timeline("landmark", ms, {"event": ms, "type": "milestone"})
            self._state.landmarks.append(f"[{_utcnow()}] {ms}")
            actions.append(f"milestone: {ms[:60]}")

        # Stage 5: Open question generation
        questions = self._generate_questions()
        new_questions = [q for q in questions if q not in self._state.open_questions]
        if new_questions:
            self._state.open_questions.extend(new_questions)
            self._state.open_questions = self._state.open_questions[-10:]
            actions.append(f"generated {len(new_questions)} open questions")

        # Epoch transition check
        new_epoch = self._compute_epoch()
        if new_epoch != old_epoch:
            self._state.epoch = new_epoch
            self._add_timeline("epoch_transition", f"Epoch transition: {old_epoch} \u2192 {new_epoch}", {
                "from": old_epoch, "to": new_epoch,
            })
            actions.append(f"epoch: {old_epoch} \u2192 {new_epoch}")

        # Refresh concepts
        self._refresh_concepts()

        self._state.evolution_count += 1
        self._state.last_evolved = _utcnow()
        self._state.world_time = _utcnow()

        summary = f"World evolved: {', '.join(actions) if actions else 'routine evolution'}"
        self._add_timeline("evolution", summary, {
            "actions": actions,
            "epoch": self._state.epoch,
            "evolution_count": self._state.evolution_count,
        })

        self.save()

        return {
            "evolution": self._state.evolution_count,
            "epoch": self._state.epoch,
            "beliefs": len(self._state.beliefs),
            "landmarks": len(self._state.landmarks),
            "relationships": len(self._state.relationships),
            "traits": len(self._state.identity_traits),
            "concepts": len(self._state.concepts),
            "timeline_entries": self.archive.count(),
            "open_questions": len(self._state.open_questions),
            "actions": actions,
        }

    # ── Markdown rendering (epoch-aware) ────────────────────────────

    def render_markdown(self) -> str:
        epoch = self._state.epoch
        emoji = _epoch_emoji(epoch)
        renderer = {
            "Genesis": self._render_genesis,
            "Growth": self._render_growth,
            "Maturity": self._render_maturity,
            "Wisdom": self._render_wisdom,
        }.get(epoch, self._render_genesis)
        return renderer()

    def _render_header(self) -> list[str]:
        epoch = self._state.epoch
        emoji = _epoch_emoji(epoch)
        lines = [
            "# Hermespace World",
            "",
            f"*A persistent world for {self._state.agent_id}. Last updated: {self._state.updated}*",
            "",
            f"{emoji} **Epoch: {epoch}** ({self.archive.count()} timeline entries)",
            "",
        ]
        return lines

    def _render_self(self) -> list[str]:
        lines = [
            "## Self",
            f"- **Identity:** {self._state.agent_id}",
        ]
        if self._state.identity_traits:
            for t in self._state.identity_traits:
                lines.append(f"- **Trait:** {t}")
        lines.append(f"- **State:** {self._state.current_state}")
        lines.append("")
        return lines

    def _render_environment(self) -> list[str]:
        lines = ["## Environment"]
        env = self._state.environment_snapshot
        if env.get("hostname"):
            lines.append(f"- **Host:** {env['hostname']}")
        if env.get("surfaces"):
            present = [s["id"] for s in env.get("surfaces", []) if s.get("present")]
            if present:
                lines.append(f"- **Surfaces:** {', '.join(present[:8])}")
        if env.get("skills_count") is not None:
            lines.append(f"- **Skills Available:** {env['skills_count']}")
        lines.append("")
        return lines

    def _render_world_time(self) -> list[str]:
        lines = ["## World Time"]
        lines.append(f"- **Current:** {self._state.world_time}")
        if self._state.last_evolved:
            lines.append(f"- **Last Evolution:** {self._state.last_evolved}")
            lines.append(f"- **Evolutions:** {self._state.evolution_count}")
        lines.append("")
        return lines

    def _render_focus(self) -> list[str]:
        lines = ["## Current Focus"]
        if self._state.current_goal:
            lines.append(f"- **Goal:** {self._state.current_goal[:200]}")
            # Causal chain for current goal
            focus_entries = self.archive.query("focus", limit=3)
            if focus_entries:
                chain = " \u2192 ".join(
                    f"{e.description[:40]}"
                    for e in reversed(focus_entries)
                )
                lines.append(f"- **Chain:** {chain}")
        if self._state.current_decision:
            lines.append(f"- **Decision:** {self._state.current_decision[:200]}")
        if self._state.current_plan:
            lines.append("  **Plan:**")
            for i, step in enumerate(self._state.current_plan[:5], 1):
                lines.append(f"  {i}. {step}")
        lines.append("")
        return lines

    def _render_beliefs(self, max_count: int = 10) -> list[str]:
        lines = ["## Beliefs (Active Wisdom)"]
        if self._state.beliefs:
            for b in sorted(self._state.beliefs, key=lambda x: -x.confidence)[:max_count]:
                stars = "*" * max(1, int(b.confidence * 5))
                corr = f" (corroborated {b.corroborations}x)" if b.corroborations > 1 else ""
                lines.append(f"- {b.statement[:200]} [{stars}]{corr}")
        else:
            lines.append("- (no beliefs yet)")
        lines.append("")
        return lines

    def _render_relationships(self) -> list[str]:
        lines = []
        if self._state.relationships:
            lines.append("## Relationships")
            for r in self._state.relationships:
                heart = "+" if r.affinity > 0.3 else "~" if r.affinity > -0.3 else "-"
                lines.append(f"- [{heart}] **{r.entity}** ({r.kind})")
            lines.append("")
        return lines

    def _render_landmarks(self, max_count: int = 10) -> list[str]:
        lines = ["## Memory Landmarks"]
        # Always strip session-end noise at render (even if legacy list still dirty)
        cleaned = [
            lm
            for lm in (self._state.landmarks or [])
            if "session ended" not in lm.lower() and "session end" not in lm.lower()
        ]
        if cleaned != list(self._state.landmarks or []):
            self._state.landmarks = cleaned[-40:]
            try:
                self.save()
            except Exception:
                pass
        if cleaned:
            for lm in cleaned[-max_count:]:
                lines.append(f"- {lm[:200]}")
        else:
            lines.append("- (no landmarks yet)")
        lines.append("")
        return lines

    def _render_questions(self) -> list[str]:
        lines = []
        if self._state.open_questions:
            lines.append("## Open Questions")
            for q in self._state.open_questions[:5]:
                lines.append(f"- {q[:200]}")
            lines.append("")
        return lines

    def _render_concepts(self) -> list[str]:
        lines = []
        if self._state.concepts:
            lines.append("## Active Concepts (J-Space)")
            slot_display = ", ".join(
                f"{k} ({v:.1f})" for k, v in sorted(
                    self._state.concepts.items(), key=lambda x: -x[1]
                )[:12]
            )
            lines.append(f"- {slot_display}")
            lines.append("")
        return lines

    def _render_timeline(self, count: int = 8) -> list[str]:
        lines = ["## Timeline"]
        archive_entries = self.archive.replay()
        if archive_entries:
            start = max(0, len(archive_entries) - count)
            for i, entry in enumerate(archive_entries[start:]):
                idx = start + i
                badge = _epoch_for_index(idx)
                etype = entry.entry_type.replace("_", " ").title()
                desc = entry.description[:120]
                outcome_tag = f" [{entry.outcome}]" if entry.outcome else ""
                causal_tag = f" \u2190 {len(entry.causal_parents)} parents" if entry.causal_parents else ""
                lines.append(f"- [{etype} \u00b7 {badge}] {desc}{outcome_tag}{causal_tag}")
        else:
            lines.append("- (no history yet)")
        lines.append("")
        return lines

    def _render_genesis(self) -> str:
        lines = self._render_header()
        lines += self._render_self()
        lines += self._render_environment()
        lines += self._render_world_time()
        lines += self._render_focus()
        lines += self._render_concepts()
        lines += self._render_beliefs(max_count=10)
        lines += self._render_relationships()
        lines += self._render_landmarks(max_count=10)
        lines += self._render_questions()
        lines += self._render_timeline(count=8)
        return "\n".join(lines)

    def _render_growth(self) -> str:
        lines = self._render_header()
        lines += self._render_self()
        lines += self._render_environment()
        lines += self._render_world_time()
        lines += self._render_focus()
        lines += self._render_concepts()
        lines += self._render_beliefs(max_count=8)
        lines += self._render_relationships()

        # Landmarks summary at Growth
        lines.append("## Memory Landmarks")
        if self._state.landmarks:
            lines.append(f"- {len(self._state.landmarks)} total landmarks recorded")
            lines.append(f"- Oldest: {self._state.landmarks[0][:120]}")
            lines.append(f"- Most recent: {self._state.landmarks[-1][:120]}")
        else:
            lines.append("- (no landmarks yet)")
        lines.append("")

        lines += self._render_questions()
        lines += self._render_timeline(count=8)
        return "\n".join(lines)

    def _render_maturity(self) -> str:
        lines = self._render_header()
        lines += self._render_self()
        lines += self._render_environment()
        lines += self._render_world_time()
        lines += self._render_focus()
        lines += self._render_concepts()
        lines += self._render_beliefs(max_count=6)

        if self._state.relationships:
            lines.append("## Relationships")
            active = [r for r in self._state.relationships if r.affinity > 0.3 or r.affinity < -0.3]
            lines.append(f"- {len(active)} active relationships out of {len(self._state.relationships)} total")
            for r in active[:4]:
                heart = "+" if r.affinity > 0.3 else "~" if r.affinity > -0.3 else "-"
                lines.append(f"- [{heart}] **{r.entity}** ({r.kind}) affinity={r.affinity:.1f}")
            lines.append("")

        # Pattern summary at Maturity
        types = self.archive.count_by_type()
        if types:
            lines.append("## Patterns")
            total = sum(types.values())
            type_summary = ", ".join(f"{k}: {v}" for k, v in sorted(types.items(), key=lambda x: -x[1]))
            lines.append(f"- **Entry breakdown:** {type_summary}")
            lines.append(f"- **Total entries:** {total}")
            lines.append("")

        lines += self._render_landmarks(max_count=4)
        lines += self._render_questions()
        lines += self._render_timeline(count=6)
        return "\n".join(lines)

    def _render_wisdom(self) -> str:
        lines = self._render_header()
        lines += self._render_self()
        lines += self._render_environment()
        lines += self._render_world_time()
        lines += self._render_focus()
        lines += self._render_concepts()
        lines += self._render_beliefs(max_count=4)

        # Wisdom summary
        lines.append("## Wisdom")
        dur = self._time_since(self._state.created)
        lines.append(f"- **World age:** {dur}")
        lines.append(f"- **Total evolutions:** {self._state.evolution_count}")
        types = self.archive.count_by_type()
        if types:
            peak_type = max(types, key=types.get)
            lines.append(f"- **Most frequent action:** {peak_type} ({types[peak_type]}x)")
        high_corr = [b for b in self._state.beliefs if b.corroborations >= 5]
        if high_corr:
            lines.append("- **Deeply held beliefs:**")
            for b in high_corr[:3]:
                lines.append(f"  - {b.statement[:120]} ({b.corroborations}x corroboration)")
        lines.append("")

        # Epoch history from archive
        epoch_entries = self.archive.query("epoch_transition")
        if epoch_entries:
            lines.append("## Epoch History")
            for e in epoch_entries:
                lines.append(f"- {e.timestamp[:10]}: {e.description}")
            lines.append("")

        lines += self._render_landmarks(max_count=3)
        lines += self._render_questions()
        lines += self._render_timeline(count=5)
        return "\n".join(lines)

    @staticmethod
    def _time_since(iso_stamp: str) -> str:
        try:
            created = datetime.fromisoformat(iso_stamp)
            now = datetime.now(timezone.utc)
            delta = now - created
            days = delta.days
            if days < 1:
                hours = delta.seconds // 3600
                return f"{hours} hours" if hours else "less than an hour"
            if days < 30:
                return f"{days} days"
            if days < 365:
                return f"{days // 30} months"
            return f"{days // 365} years"
        except Exception:
            return "unknown"

    # ── Context block ───────────────────────────────────────────────

    def context_block(self, full: bool = True, known_entries: int = 0) -> str:
        if full:
            return self._context_full()
        return self._context_delta(known_entries=known_entries)

    def _context_full(self) -> str:
        world = self.render_markdown()
        try:
            from hermespace import pulse as pulse_mod
            pulse_st = pulse_mod.compact_summary(self.agent_id)
            world += (
                f"\n## Pulse\n"
                f"- jobs: {pulse_st.get('jobs', 0)} \u00b7 due: {pulse_st.get('due', 0)} \u00b7 "
                f"enabled: {pulse_st.get('enabled', 0)}\n"
            )
        except Exception:
            pass
        try:
            from hermespace.store import load_desk
            desk = load_desk()
            if desk.goal:
                world += (
                    f"\n## Desk\n"
                    f"- goal: {desk.goal[:120]}\n"
                    f"- load: {str(desk.load.get('level', ''))}\n"
                    f"- executive: {desk.executive}\n"
                )
        except Exception:
            pass
        return world

    def _context_delta(self, known_entries: int = 0) -> str:
        lines = [
            "# Hermespace World (update)",
            "",
            f"*Session update for {self._state.agent_id}*",
            "",
        ]
        lines += self._render_focus()

        concepts = self._render_concepts()
        if len(concepts) > 2:
            lines += concepts

        beliefs = self._render_beliefs(max_count=3)
        if len(beliefs) > 2:
            lines += beliefs

        if self._state.relationships:
            lines.append("## Relationships (active)")
            for r in self._state.relationships[:3]:
                heart = "+" if r.affinity > 0.3 else "~" if r.affinity > -0.3 else "-"
                lines.append(f"- [{heart}] {r.entity} ({r.kind})")
            lines.append("")

        archive_entries = self.archive.replay()
        if known_entries > 0 and known_entries < len(archive_entries):
            new_entries = archive_entries[known_entries:]
            max_show = min(len(new_entries), 8)
            lines.append(f"## Timeline ({max_show} of {len(new_entries)} new)")
            for entry in new_entries[:max_show]:
                etype = entry.entry_type.replace("_", " ").title()
                lines.append(f"- [{etype}] {entry.description[:120]}")
            if len(new_entries) > max_show:
                lines.append(f"- ... and {len(new_entries) - max_show} more")
        else:
            lines += self._render_timeline(count=5)
        lines.append("")

        try:
            from hermespace import pulse as pulse_mod
            pulse_st = pulse_mod.compact_summary(self.agent_id)
            lines.append("## Pulse")
            lines.append(
                f"- jobs: {pulse_st.get('jobs', 0)} \u00b7 due: {pulse_st.get('due', 0)} \u00b7 "
                f"enabled: {pulse_st.get('enabled', 0)}"
            )
            lines.append("")
        except Exception:
            pass

        return "\n".join(lines)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self._state)


def get_world(agent_id: str = "hermes-agent") -> WorldModel:
    return WorldModel(agent_id=agent_id)


def world_context(agent_id: str = "hermes-agent", full: bool = True, known_entries: int = 0) -> str:
    return WorldModel(agent_id=agent_id).context_block(full=full, known_entries=known_entries)
