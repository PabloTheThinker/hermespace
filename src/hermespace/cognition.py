"""Cognitive science core for Hermespace.

Grounded in (functional analogues, not brain emulation):
- Baddeley & Hitch working memory: central executive + phonological loop +
  visuospatial sketchpad + episodic buffer (2000+)
- Baars / Dehaene Global Workspace: limited capacity, competition, broadcast
- Sweller cognitive load: intrinsic / extraneous / germane (simplified)
- Cowan / Miller: focus-of-attention capacity ~4±1 chunks (we allow up to 12
  tagged items with a hard focus set of 4)

Honesty: this is a harness model of *roles*, not neurons.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Iterable


class Modality(str, Enum):
    VERBAL = "verbal"  # phonological-like: goals, words, say-prep
    STRUCT = "struct"  # visuospatial/schematic: paths, architecture, graphs
    BIND = "bind"  # episodic-buffer style multi-modal binding tags
    EXEC = "exec"  # executive control notes (inhibit, shift, update)


# Cowan-style focus of attention (narrow)
FOCUS_CAP = 4
# Broader activated memory (desk)
ACTIVATED_CAP = 12
VERBAL_SOFT = 6
STRUCT_SOFT = 6


@dataclass
class Slot:
    text: str
    modality: Modality = Modality.VERBAL
    salience: float = 0.5  # 0..1 competition weight for broadcast

    def label(self) -> str:
        return f"[{self.modality.value}|{self.salience:.2f}] {self.text}"


_MOD_RE = re.compile(
    r"^\[(?P<mod>verbal|struct|bind|exec)(?:\|(?P<sal>0?\.\d+|1(?:\.0+)?))?\]\s*(?P<body>.*)$",
    re.I,
)


def parse_slot(raw: str) -> Slot:
    s = raw.strip()
    m = _MOD_RE.match(s)
    if not m:
        # heuristic modality
        low = s.lower()
        if any(k in low for k in ("path", "file", "dir", "arch", "graph", "layout", "repo")):
            return Slot(s, Modality.STRUCT, 0.55)
        if any(k in low for k in ("don't", "do not", "inhibit", "never", "forbid")):
            return Slot(s, Modality.EXEC, 0.7)
        return Slot(s, Modality.VERBAL, 0.5)
    sal = float(m.group("sal") or 0.5)
    mod = Modality(m.group("mod").lower())
    return Slot(m.group("body").strip(), mod, max(0.0, min(1.0, sal)))


def classify_message_load(user_message: str, n_concepts: int, n_plan: int) -> dict:
    """Approximate Sweller-style load components (0..1)."""
    msg = user_message or ""
    words = len(msg.split())
    # intrinsic ~ task complexity proxies
    intrinsic = min(1.0, 0.15 * n_plan + 0.05 * n_concepts + (0.01 * words))
    # extraneous ~ noise/typos/topic hop proxies
    hops = msg.count("\n") + msg.count(" and ") // 3
    typos = len(re.findall(r"\b\w*\d\w*\b", msg))  # crude
    extraneous = min(1.0, 0.08 * hops + 0.02 * max(0, words - 40) + 0.05 * typos)
    # germane ~ constructive work signals
    germane = 0.0
    if re.search(r"\b(build|design|research|understand|plan|architect)\b", msg, re.I):
        germane = 0.4
    if re.search(r"\b(why|how does|neuroscience|cognitive)\b", msg, re.I):
        germane = min(1.0, germane + 0.3)
    total = min(1.0, 0.5 * intrinsic + 0.35 * extraneous + 0.15 * (1.0 - germane * 0.5))
    level = "low" if total < 0.35 else "mid" if total < 0.65 else "high"
    return {
        "intrinsic": round(intrinsic, 3),
        "extraneous": round(extraneous, 3),
        "germane": round(germane, 3),
        "total": round(total, 3),
        "level": level,
    }


def compete_for_focus(slots: Iterable[Slot], cap: int = FOCUS_CAP) -> list[Slot]:
    """GWT-style competition: highest salience wins broadcast focus."""
    ranked = sorted(slots, key=lambda s: s.salience, reverse=True)
    return ranked[:cap]


def partition_buffers(slots: list[Slot]) -> dict[str, list[Slot]]:
    verbal = [s for s in slots if s.modality == Modality.VERBAL]
    struct = [s for s in slots if s.modality == Modality.STRUCT]
    bind = [s for s in slots if s.modality == Modality.BIND]
    exec_ = [s for s in slots if s.modality == Modality.EXEC]
    # soft caps per loop (Baddeley subsystems)
    return {
        "verbal": verbal[-VERBAL_SOFT:],
        "struct": struct[-STRUCT_SOFT:],
        "bind": bind[-4:],
        "exec": exec_[-4:],
        "focus": compete_for_focus(slots, FOCUS_CAP),
    }


def bind_episode(goal: str, decision: str, say: str, plan: list[str]) -> Slot | None:
    """Episodic buffer: bind multimodal elements into one chunk."""
    if not (goal or decision or say):
        return None
    parts = [p for p in (goal[:80], decision[:60], say[:80]) if p]
    if plan:
        parts.append("plan:" + ";".join(plan[:3])[:60])
    return Slot(" | ".join(parts), Modality.BIND, salience=0.85)


def executive_mode(load_level: str, n_choices: int) -> str:
    """Central executive posture."""
    if load_level == "high":
        return "protect"  # monotropic: single goal, inhibit switches
    if n_choices > 2:
        return "select"  # compete among choices
    return "update"  # normal update/refresh
