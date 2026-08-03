"""Functional J-Space — harness-level global workspace for Hermespace.

Maps Anthropic J-space *roles* (GWT) onto a durable desk harness — not neural
access, not consciousness claims:

  1. Verbal report     — workspace contents are reportable
  2. Directed modulation — hold / summon / inhibit concepts on request
  3. Internal reasoning  — silent intermediate steps (not dumped to user chat)
  4. Flexible broadcast  — one hub concept feeds many downstream uses
  5. Selectivity         — automatic turns skip the workspace (gate)

Capacity: FOA ≤4 (Cowan) · activated ≤12 · verbal hub ≤25 (J-space-scale).
Honesty: files + API only — no model-weight access.
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from hermespace.cognition import (
    ACTIVATED_CAP,
    FOCUS_CAP,
    Modality,
    Slot,
    compete_for_focus,
    parse_slot,
)
from hermespace.paths import state_dir

# Anthropic J-space holds on the order of tens of concepts; we cap the hub.
HUB_CAP = 25
# Silent reasoning chain (internal steps never shown as user Report by default)
REASON_CAP = 8

_HOLD_RE = re.compile(
    r"\b(?:hold|focus(?:\s+on)?|think(?:\s+about)?|keep(?:\s+in\s+mind)?|"
    r"concentrate(?:\s+on)?|remember)\b[:\s]+(.+)$",
    re.I,
)
_SUMMON_RE = re.compile(
    r"\b(?:what(?:'s|\s+is)\s+(?:on\s+)?(?:your\s+)?(?:mind|desk|workspace)|"
    r"show\s+(?:hermespace|desk|j[\s-]?space|workspace)|report\s+workspace)\b",
    re.I,
)
_SILENT_RE = re.compile(
    r"\b(?:silently|in\s+(?:your\s+)?head|without\s+saying|"
    r"intermediate\s+step|step\s+\d+)\b",
    re.I,
)


def _utcnow() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


@dataclass
class WorkspaceConcept:
    """One verbalizable unit in the harness J-space."""

    text: str
    salience: float = 0.5
    modality: str = "verbal"
    source: str = "desk"  # desk | hold | summon | reason | world | cube | fabric
    silent: bool = False  # internal reasoning — not for user Report dump
    held: bool = False  # directed modulation — keep under competition pressure

    def label(self) -> str:
        sal = max(0.0, min(1.0, self.salience))
        prefix = f"[{self.modality}|{sal:.2f}]"
        flags = []
        if self.held:
            flags.append("hold")
        if self.silent:
            flags.append("silent")
        if flags:
            prefix = f"[{self.modality}|{sal:.2f}|{'+'.join(flags)}]"
        return f"{prefix} {self.text.strip()}"

    def to_slot(self) -> Slot:
        mod = Modality.VERBAL
        try:
            mod = Modality(self.modality)
        except ValueError:
            mod = Modality.VERBAL
        return Slot(self.text, mod, max(0.0, min(1.0, self.salience)))


@dataclass
class JSpaceState:
    """Snapshot of the functional workspace."""

    hub: list[WorkspaceConcept] = field(default_factory=list)
    focus: list[str] = field(default_factory=list)  # ≤4 labels
    silent_steps: list[str] = field(default_factory=list)
    reportable: list[str] = field(default_factory=list)
    load_level: str = "mid"
    executive: str = "update"
    mode: str = "workspace"  # workspace | automatic | protect
    updated: str = field(default_factory=_utcnow)
    meta: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "hub": [asdict(c) for c in self.hub],
            "focus": list(self.focus),
            "silent_steps": list(self.silent_steps),
            "reportable": list(self.reportable),
            "load_level": self.load_level,
            "executive": self.executive,
            "mode": self.mode,
            "updated": self.updated,
            "meta": dict(self.meta),
            "hub_n": len(self.hub),
            "focus_n": len(self.focus),
        }


class JSpace:
    """Functional global workspace — the nervous FOA Hermespace owns.

    Soft-standalone: works with desk/world/semantic alone.
    When HermesCube is present, arterial strips enrich the hub via cube_module.
    """

    def __init__(self, agent_id: str = "hermes-agent", root: Path | None = None) -> None:
        self.agent_id = (agent_id or "hermes-agent").strip()
        self.root = (root or state_dir() / "jspace").resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.path = self.root / f"{_safe(self.agent_id)}.json"
        self.state = self._load()

    def _load(self) -> JSpaceState:
        if not self.path.is_file():
            return JSpaceState()
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return JSpaceState()
        hub = []
        for item in raw.get("hub") or []:
            if not isinstance(item, dict) or not item.get("text"):
                continue
            hub.append(
                WorkspaceConcept(
                    text=str(item["text"]),
                    salience=float(item.get("salience") or 0.5),
                    modality=str(item.get("modality") or "verbal"),
                    source=str(item.get("source") or "desk"),
                    silent=bool(item.get("silent")),
                    held=bool(item.get("held")),
                )
            )
        return JSpaceState(
            hub=hub[:HUB_CAP],
            focus=list(raw.get("focus") or [])[:FOCUS_CAP],
            silent_steps=list(raw.get("silent_steps") or [])[:REASON_CAP],
            reportable=list(raw.get("reportable") or [])[:HUB_CAP],
            load_level=str(raw.get("load_level") or "mid"),
            executive=str(raw.get("executive") or "update"),
            mode=str(raw.get("mode") or "workspace"),
            updated=str(raw.get("updated") or _utcnow()),
            meta=dict(raw.get("meta") or {}),
        )

    def save(self) -> None:
        self.state.updated = _utcnow()
        self.path.write_text(
            json.dumps(self.state.to_dict(), indent=2),
            encoding="utf-8",
        )

    # --- property 2: directed modulation ---

    def hold(
        self,
        text: str,
        *,
        salience: float = 0.9,
        modality: str = "verbal",
        silent: bool = False,
    ) -> WorkspaceConcept:
        """Directed modulation — put a concept into the workspace and keep it."""
        body = (text or "").strip()
        if not body:
            raise ValueError("hold requires non-empty text")
        self._drop_body(body)
        concept = WorkspaceConcept(
            text=body,
            salience=max(0.0, min(1.0, salience)),
            modality=modality,
            source="hold",
            silent=silent,
            held=True,
        )
        self.state.hub.append(concept)
        self._recompete()
        self.save()
        return concept

    def release(self, text: str) -> bool:
        """Drop a held/hub concept by body match."""
        body = (text or "").strip().casefold()
        before = len(self.state.hub)
        self.state.hub = [c for c in self.state.hub if c.text.casefold() != body]
        self._recompete()
        self.save()
        return len(self.state.hub) < before

    def inhibit(self, text: str) -> WorkspaceConcept:
        """White-bear style: mark concept as exec-inhibit (still lights up)."""
        body = (text or "").strip()
        return self.hold(f"do not dwell: {body}", salience=0.7, modality="exec")

    # --- property 3: internal reasoning ---

    def reason_step(self, step: str, *, salience: float = 0.8) -> str:
        """Silent intermediate step — for model context, not user Report dump."""
        s = (step or "").strip()
        if not s:
            return ""
        self.state.silent_steps = (self.state.silent_steps + [s])[-REASON_CAP:]
        self.hold(s, salience=salience, silent=True)
        return s

    def clear_silent(self) -> None:
        self.state.silent_steps = []
        self.state.hub = [c for c in self.state.hub if not c.silent]
        self._recompete()
        self.save()

    # --- property 1: verbal report ---

    def report(self, *, include_silent: bool = False) -> str:
        """What the workspace would say if asked — reportable contents only."""
        lines = ["## J-Space (harness workspace)"]
        lines.append(f"- mode: {self.state.mode} · load: {self.state.load_level} · exec: {self.state.executive}")
        lines.append("### Focus of attention")
        if self.state.focus:
            for f in self.state.focus:
                lines.append(f"- {f}")
        else:
            lines.append("- (empty)")
        lines.append("### Reportable hub")
        shown = 0
        for c in sorted(self.state.hub, key=lambda x: x.salience, reverse=True):
            if c.silent and not include_silent:
                continue
            lines.append(f"- {c.label()}")
            shown += 1
            if shown >= 12:
                break
        if shown == 0:
            lines.append("- (empty)")
        if include_silent and self.state.silent_steps:
            lines.append("### Silent reasoning")
            for s in self.state.silent_steps:
                lines.append(f"- {s}")
        return "\n".join(lines)

    # --- property 4: flexible broadcast ---

    def broadcast_block(self, *, max_chars: int = 900, high_load: bool = False) -> str:
        """GWT broadcast — dense strip for model context (never user chat dump)."""
        cap = 420 if high_load else max_chars
        parts = ["### J-Space hub (broadcast)"]
        parts.append(
            f"_FOA≤{FOCUS_CAP} · hub≤{HUB_CAP} · mode={self.state.mode} · "
            f"load={self.state.load_level}_"
        )
        used = sum(len(p) + 1 for p in parts)
        # Focus first — privileged channel
        if self.state.focus:
            parts.append("**Focus:**")
            used += len(parts[-1]) + 1
            for f in self.state.focus[:FOCUS_CAP]:
                line = f"- {f[:140]}"
                if used + len(line) + 1 > cap:
                    break
                parts.append(line)
                used += len(line) + 1
        # Held + high-salience hub (flexible reuse)
        hub_sorted = sorted(
            self.state.hub,
            key=lambda c: (c.held, c.salience),
            reverse=True,
        )
        if hub_sorted and not high_load:
            parts.append("**Hub:**")
            used += len(parts[-1]) + 1
        for c in hub_sorted:
            if high_load and not (c.held or c.salience >= 0.75):
                continue
            line = f"- {c.label()[:160]}"
            if used + len(line) + 1 > cap:
                break
            if any(c.text[:40] in p for p in parts):
                continue
            parts.append(line)
            used += len(line) + 1
        if self.state.silent_steps and not high_load:
            parts.append("**Silent steps:**")
            used += len(parts[-1]) + 1
            for s in self.state.silent_steps[-4:]:
                line = f"- {s[:120]}"
                if used + len(line) + 1 > cap:
                    break
                parts.append(line)
                used += len(line) + 1
        block = "\n".join(parts)
        if len(block) > cap:
            block = block[: cap - 3] + "..."
        return block

    # --- property 5: selectivity ---

    def should_enter(self, message: str, *, desk_ready: bool = False, force: bool = False) -> tuple[bool, str]:
        """Selectivity — automatic turns skip the workspace."""
        if force:
            return True, "force"
        from hermespace.gate import should_inject

        return should_inject(message, desk_ready=desk_ready, is_first_turn=False)

    def parse_modulation(self, message: str) -> dict[str, Any]:
        """Detect hold/summon/silent intents in user text."""
        msg = (message or "").strip()
        out: dict[str, Any] = {"hold": None, "summon": False, "silent": False}
        if not msg:
            return out
        if _SUMMON_RE.search(msg):
            out["summon"] = True
        if _SILENT_RE.search(msg):
            out["silent"] = True
        m = _HOLD_RE.search(msg)
        if m:
            out["hold"] = m.group(1).strip()[:200]
        return out

    # --- sync from desk / enrich ---

    def sync_from_desk(
        self,
        desk: Any,
        *,
        user_message: str = "",
        cube_strip: str = "",
    ) -> JSpaceState:
        """Refresh hub from desk FOA + optional Cube arterial strip."""
        load_level = "mid"
        executive = "update"
        concepts: list[str] = []
        focus: list[str] = []
        if desk is not None:
            load = getattr(desk, "load", None) or {}
            if isinstance(load, dict):
                load_level = str(load.get("level") or "mid")
            executive = str(getattr(desk, "executive", None) or "update")
            concepts = list(getattr(desk, "concepts", None) or [])
            focus = list(getattr(desk, "focus", None) or [])

        # Keep held concepts across sync
        held = [c for c in self.state.hub if c.held]
        silent_keep = list(self.state.silent_steps)

        new_hub: list[WorkspaceConcept] = list(held)
        seen = {c.text.casefold() for c in new_hub}

        for raw in concepts:
            slot = parse_slot(raw)
            body = slot.text.strip()
            if not body or body.casefold() in seen:
                continue
            new_hub.append(
                WorkspaceConcept(
                    text=body,
                    salience=slot.salience,
                    modality=slot.modality.value,
                    source="desk",
                    silent=False,
                    held=False,
                )
            )
            seen.add(body.casefold())

        # Cube / standalone arterial enrichment
        for line in _strip_lines(cube_strip):
            if line.casefold() in seen:
                continue
            new_hub.append(
                WorkspaceConcept(
                    text=line[:200],
                    salience=0.72,
                    modality="verbal",
                    source="cube",
                    silent=False,
                    held=False,
                )
            )
            seen.add(line.casefold())

        # Modulation from this turn's message
        mod = self.parse_modulation(user_message)
        if mod.get("hold"):
            body = str(mod["hold"])
            if body.casefold() not in seen:
                new_hub.append(
                    WorkspaceConcept(
                        text=body,
                        salience=0.92,
                        modality="verbal",
                        source="hold",
                        silent=bool(mod.get("silent")),
                        held=True,
                    )
                )
                seen.add(body.casefold())
            if mod.get("silent"):
                silent_keep = (silent_keep + [body])[-REASON_CAP:]

        self.state.hub = new_hub[-HUB_CAP:]
        self.state.silent_steps = silent_keep[-REASON_CAP:]
        self.state.load_level = load_level
        self.state.executive = executive
        if load_level == "high" or executive == "protect":
            self.state.mode = "protect"
        else:
            self.state.mode = "workspace"

        self._recompete(preferred_focus=focus)
        self.state.reportable = [
            c.text for c in self.state.hub if not c.silent
        ][:HUB_CAP]
        self.state.meta["last_sync"] = _utcnow()
        self.state.meta["modulation"] = mod
        self.state.meta["cube_enriched"] = bool(cube_strip and cube_strip.strip())
        self.save()
        return self.state

    def enrich_from_world(self, beliefs: Iterable[str], *, limit: int = 5) -> int:
        """Standalone charge — pull world wisdom into hub when Cube absent."""
        added = 0
        seen = {c.text.casefold() for c in self.state.hub}
        for b in beliefs:
            text = str(b or "").strip()
            if not text or text.casefold() in seen:
                continue
            self.state.hub.append(
                WorkspaceConcept(
                    text=text[:200],
                    salience=0.65,
                    modality="verbal",
                    source="world",
                    silent=False,
                    held=False,
                )
            )
            seen.add(text.casefold())
            added += 1
            if added >= limit:
                break
        if added:
            self.state.hub = self.state.hub[-HUB_CAP:]
            self._recompete()
            self.save()
        return added

    def status(self) -> dict[str, Any]:
        d = self.state.to_dict()
        d["path"] = str(self.path)
        d["agent_id"] = self.agent_id
        d["caps"] = {"foa": FOCUS_CAP, "activated": ACTIVATED_CAP, "hub": HUB_CAP}
        d["properties"] = [
            "verbal_report",
            "directed_modulation",
            "internal_reasoning",
            "flexible_broadcast",
            "selectivity",
        ]
        return d

    # --- internals ---

    def _drop_body(self, body: str) -> None:
        needle = body.casefold()
        self.state.hub = [c for c in self.state.hub if c.text.casefold() != needle]

    def _recompete(self, preferred_focus: list[str] | None = None) -> None:
        slots = [c.to_slot() for c in self.state.hub]
        # Boost held
        for i, c in enumerate(self.state.hub):
            if c.held and i < len(slots):
                slots[i] = Slot(slots[i].text, slots[i].modality, min(1.0, slots[i].salience + 0.15))
        winners = compete_for_focus(slots, FOCUS_CAP)
        if preferred_focus:
            # Prefer desk focus labels that still exist
            pref: list[Slot] = []
            for label in preferred_focus:
                body = parse_slot(label).text.casefold()
                for s in slots:
                    if s.text.casefold() == body:
                        pref.append(s)
                        break
            if pref:
                rest = [s for s in winners if s.text.casefold() not in {p.text.casefold() for p in pref}]
                winners = (pref + rest)[:FOCUS_CAP]
        self.state.focus = [s.label() for s in winners][:FOCUS_CAP]


def _safe(name: str) -> str:
    return re.sub(r"[^a-zA-Z0-9._-]+", "_", name)[:80] or "default"


def _strip_lines(block: str) -> list[str]:
    out: list[str] = []
    for raw in (block or "").splitlines():
        s = raw.strip()
        if not s or s.startswith("#") or s.startswith("_"):
            continue
        if s.startswith("- "):
            s = s[2:].strip()
        if s.startswith("**") and s.endswith("**"):
            continue
        if len(s) < 3:
            continue
        out.append(s[:200])
    return out


def get_jspace(agent_id: str = "hermes-agent") -> JSpace:
    return JSpace(agent_id=agent_id)
