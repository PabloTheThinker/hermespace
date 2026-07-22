"""Desk model — Baddeley/GWT-aligned limited workspace."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from hermespace.cognition import (
    ACTIVATED_CAP,
    FOCUS_CAP,
    Modality,
    Slot,
    bind_episode,
    classify_message_load,
    executive_mode,
    parse_slot,
    partition_buffers,
)

MAX_CONCEPTS = ACTIVATED_CAP
MAX_CHOICES = 4


def _utcnow() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


@dataclass
class Desk:
    """Active Hermespace desk — intentional working set + cognitive metadata."""

    goal: str = ""
    concepts: list[str] = field(default_factory=list)
    choices: list[str] = field(default_factory=list)
    decision: str = ""
    plan: list[str] = field(default_factory=list)
    say: str = ""
    do_not_say: list[str] = field(default_factory=list)
    updated: str = field(default_factory=_utcnow)
    meta: dict[str, Any] = field(default_factory=dict)
    # cognitive extensions (also mirrored in meta for JSON)
    load: dict[str, Any] = field(default_factory=dict)
    executive: str = "update"
    focus: list[str] = field(default_factory=list)

    def slots(self) -> list[Slot]:
        return [parse_slot(c) for c in self.concepts if c and c.strip()]

    def recompute_cognition(self, user_message: str = "") -> Desk:
        """Update load, focus, executive, Meta streams, episodic bind."""
        # Meta TRIBE reverse: encode stimulus into multi-stream slots
        if user_message.strip():
            from hermespace.streams import encode_stimulus, merge_streams_into_concepts, production_stages

            bundle = encode_stimulus(user_message, goal_hint=self.goal)
            self.concepts = merge_streams_into_concepts(self.concepts, bundle)
            self.meta["streams"] = {
                "text": len(bundle.text),
                "audio": len(bundle.audio),
                "visual": len(bundle.visual),
                "production": len(bundle.production),
            }
            self.meta["production"] = production_stages(self.goal, self.concepts, self.say)

        slots = self.slots()
        for d in self.do_not_say:
            slots.append(Slot(d, Modality.EXEC, 0.75))
        parts = partition_buffers(slots)
        self.focus = [s.label() for s in parts["focus"]]
        self.load = classify_message_load(
            user_message or self.goal, len(self.concepts), len(self.plan)
        )
        self.executive = executive_mode(str(self.load.get("level", "mid")), len(self.choices))
        bound = bind_episode(self.goal, self.decision, self.say, self.plan)
        if bound:
            label = bound.label()
            self.concepts = [c for c in self.concepts if not c.strip().lower().startswith("[bind")]
            self.concepts.append(label)
        self.meta["load"] = self.load
        self.meta["executive"] = self.executive
        self.meta["focus"] = self.focus
        self.meta["buffers"] = {
            k: [s.text for s in v] for k, v in parts.items() if k != "focus"
        }
        return self.clamp()

    def clamp(self) -> Desk:
        self.concepts = [c.strip() for c in self.concepts if c and c.strip()][-MAX_CONCEPTS:]
        self.choices = [c.strip() for c in self.choices if c and c.strip()][:MAX_CHOICES]
        self.plan = [p.strip() for p in self.plan if p and p.strip()]
        self.do_not_say = [d.strip() for d in self.do_not_say if d and d.strip()]
        self.focus = self.focus[:FOCUS_CAP]
        self.updated = _utcnow()
        return self

    def add_concept(self, text: str, *, modality: str | None = None, salience: float | None = None) -> None:
        t = text.strip()
        if not t:
            return
        if modality:
            sal = 0.5 if salience is None else salience
            t = f"[{modality}|{sal:.2f}] {t}"
        elif salience is not None and not t.startswith("["):
            slot = parse_slot(t)
            t = Slot(slot.text, slot.modality, salience).label()
        # dedupe by body text
        body = parse_slot(t).text
        self.concepts = [c for c in self.concepts if parse_slot(c).text != body]
        self.concepts.append(t)
        if len(self.concepts) > MAX_CONCEPTS:
            self.concepts = self.concepts[-MAX_CONCEPTS:]

    def is_ready(self) -> bool:
        return bool(self.goal.strip() and self.say.strip() and self.decision.strip())

    def to_markdown(self) -> str:
        self.clamp()
        lines = [
            "# HERMESPACE ACTIVE",
            f"updated: {self.updated}",
            "",
            "## Goal",
            self.goal.strip() or "(empty)",
            "",
            "## Active concepts (desk)",
        ]
        if self.concepts:
            lines.extend(f"- {c}" for c in self.concepts)
        else:
            lines.append("- (none)")
        lines += ["", "## Focus of attention"]
        if self.focus:
            lines.extend(f"- {f}" for f in self.focus)
        else:
            lines.append("- (auto on recompute)")
        lines += [
            "",
            "## Cognitive load",
            f"level={self.load.get('level', 'n/a')} total={self.load.get('total', 'n/a')} intrinsic={self.load.get('intrinsic', 'n/a')} extraneous={self.load.get('extraneous', 'n/a')} germane={self.load.get('germane', 'n/a')}",
            "",
            f"## Executive mode",
            self.executive or "update",
            "",
            "## Choices",
        ]
        if self.choices:
            lines.extend(f"- {c}" for c in self.choices)
        else:
            lines.append("- (none)")
        lines += [
            "",
            "## Decision",
            self.decision.strip() or "(none)",
            "",
            "## Plan",
        ]
        if self.plan:
            for i, step in enumerate(self.plan, 1):
                lines.append(f"{i}. {step}")
        else:
            lines.append("1. (none)")
        lines += [
            "",
            "## Report",
            self.say.strip() or "(empty)",
            "",
            "## Do not say",
        ]
        if self.do_not_say:
            lines.extend(f"- {d}" for d in self.do_not_say)
        else:
            lines.append("- (none)")
        lines.append("")
        return "\n".join(lines)

    @classmethod
    def from_markdown(cls, text: str) -> Desk:
        desk = cls()
        section = ""
        plan_buf: list[str] = []
        concept_buf: list[str] = []
        choice_buf: list[str] = []
        donot_buf: list[str] = []
        focus_buf: list[str] = []
        goal_lines: list[str] = []
        decision_lines: list[str] = []
        say_lines: list[str] = []
        exec_lines: list[str] = []
        load: dict[str, Any] = {}

        for raw in text.splitlines():
            line = raw.rstrip()
            if line.startswith("updated:"):
                desk.updated = line.split(":", 1)[1].strip()
                continue
            if line.startswith("## "):
                section = line[3:].strip().lower()
                continue
            if line.startswith("# "):
                continue
            if not section:
                continue
            if section.startswith("goal"):
                if line.strip() and line.strip() != "(empty)":
                    goal_lines.append(line.strip())
            elif section.startswith("active concepts"):
                if line.strip().startswith("- "):
                    item = line.strip()[2:].strip()
                    if item and item != "(none)":
                        concept_buf.append(item)
            elif section.startswith("focus"):
                if line.strip().startswith("- "):
                    item = line.strip()[2:].strip()
                    if item and not item.startswith("(auto"):
                        focus_buf.append(item)
            elif section.startswith("cognitive load"):
                if "=" in line:
                    for tok in line.split():
                        if "=" not in tok:
                            continue
                        k, v = tok.split("=", 1)
                        k = k.strip().lower().rstrip(":")
                        if k == "level":
                            load["level"] = v
                        else:
                            try:
                                load[k] = float(v)
                            except ValueError:
                                load[k] = v
            elif section.startswith("executive"):
                if line.strip() and line.strip() != "(none)":
                    exec_lines.append(line.strip())
            elif section.startswith("choices"):
                if line.strip().startswith("- "):
                    item = line.strip()[2:].strip()
                    if item and item != "(none)":
                        choice_buf.append(item)
            elif section.startswith("decision"):
                if line.strip() and line.strip() != "(none)":
                    decision_lines.append(line.strip())
            elif section.startswith("plan"):
                s = line.strip()
                if s and s[0].isdigit() and "." in s[:4]:
                    plan_buf.append(s.split(".", 1)[1].strip())
                elif s.startswith("- "):
                    plan_buf.append(s[2:].strip())
            elif section.startswith("say") or section.startswith("report"):
                if line.strip() and line.strip() != "(empty)":
                    say_lines.append(line.strip())
            elif section.startswith("do not"):
                if line.strip().startswith("- "):
                    item = line.strip()[2:].strip()
                    if item and item != "(none)":
                        donot_buf.append(item)

        desk.goal = "\n".join(goal_lines).strip()
        desk.concepts = concept_buf
        desk.choices = choice_buf
        desk.decision = "\n".join(decision_lines).strip()
        desk.plan = [p for p in plan_buf if p and p != "(none)"]
        desk.say = "\n".join(say_lines).strip()
        desk.do_not_say = donot_buf
        desk.focus = focus_buf
        desk.load = load
        desk.executive = (exec_lines[0] if exec_lines else "update")
        return desk.clamp()
