"""Neural Space — continuous field ↔ symbolic desk, local-model backends."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

import numpy as np

from hermespace.cognition import parse_slot
from hermespace.desk import Desk
from hermespace.local_model import (
    local_capabilities,
    select_embed_backend,
    verbalize_workspace,
)
from hermespace.neural_field import DEFAULT_DIM, NeuralField
from hermespace.paths import state_dir

EmbedFn = Callable[[str], np.ndarray]


@dataclass
class NeuralSpaceConfig:
    dim: int = DEFAULT_DIM
    ignition_threshold: float = 0.55
    focus_cap: int = 4
    enable: bool = True
    backend: str = field(default_factory=lambda: os.environ.get("HERMESPACE_NEURAL_BACKEND", "auto"))
    verbalize: bool = field(
        default_factory=lambda: os.environ.get("HERMESPACE_NEURAL_VERBALIZE", "0").strip()
        in {"1", "true", "yes"}
    )


class NeuralSpace:
    """Operator-facing neural workspace with local model backends."""

    def __init__(self, config: NeuralSpaceConfig | None = None) -> None:
        self.config = config or NeuralSpaceConfig()
        self.embed_backend = select_embed_backend(self.config.backend)
        self.config.backend = self.embed_backend.name
        dim = self.config.dim
        # nomic embeds are 768-d; keep field at 256 projected unless hash
        self.field = NeuralField(
            dim=dim,
            ignition_threshold=self.config.ignition_threshold,
            focus_cap=self.config.focus_cap,
            embed_fn=lambda t: self.embed_backend.embed(t, dim),
        )
        self._cache_path = state_dir() / "neural_attractors.json"
        self._load_attractors()

    def _load_attractors(self) -> None:
        if not self._cache_path.is_file():
            return
        try:
            data = json.loads(self._cache_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return
        for item in data.get("attractors") or []:
            text = str(item.get("text") or "").strip()
            if text:
                self.field.add(
                    text, energy=float(item.get("energy") or 0.6), source="attractor"
                )

    def save_attractors(self, limit: int = 64) -> Path:
        self._cache_path.parent.mkdir(parents=True, exist_ok=True)
        ranked = self.field.compete()[:limit]
        payload = {
            "backend": self.config.backend,
            "attractors": [
                {"text": t.text, "energy": t.energy, "modality": t.modality}
                for t, _ in ranked
            ],
        }
        self._cache_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return self._cache_path

    def sync_from_desk(self, desk: Desk, *, user_message: str = "") -> dict[str, Any]:
        if not self.config.enable:
            return {"enabled": False}

        query = user_message or desk.goal or desk.say
        self.field.set_query(query)

        for raw in desk.concepts:
            slot = parse_slot(raw)
            self.field.add(
                slot.text,
                energy=slot.salience,
                modality=slot.modality.value,
                source="desk",
            )
        if desk.goal:
            self.field.add(desk.goal, energy=0.85, modality="verbal", source="goal")
        if desk.decision:
            self.field.add(desk.decision, energy=0.7, modality="exec", source="decision")
        if desk.say:
            self.field.add(desk.say, energy=0.65, modality="verbal", source="report")

        verbalized: list[str] = []
        if self.config.verbalize and query:
            cand = [parse_slot(c).text for c in desk.concepts]
            verbalized = verbalize_workspace(
                goal=desk.goal or query,
                message=user_message or query,
                concepts=cand,
            )
            for v in verbalized:
                self.field.add(v, energy=0.8, modality="verbal", source="local_verbalizer")

        ignited = self.field.ignite()
        ranked = self.field.compete()
        score_map = {t.text: s for t, s in ranked}

        new_concepts: list[str] = []
        for raw in desk.concepts:
            slot = parse_slot(raw)
            s = score_map.get(slot.text, slot.salience)
            new_concepts.append(
                f"[{slot.modality.value}|{min(1.0, max(0.05, s)):.2f}] {slot.text}"
            )
        bodies = {parse_slot(c).text for c in new_concepts}
        for t in ignited:
            if t.text not in bodies:
                new_concepts.append(f"[{t.modality}|{min(1.0, t.energy):.2f}] {t.text}")
                bodies.add(t.text)
        for v in verbalized:
            if v not in bodies:
                new_concepts.append(f"[verbal|0.80] {v}")
                bodies.add(v)

        desk.concepts = new_concepts[-12:]
        desk.focus = [f"[{t.modality}|{t.energy:.2f}] {t.text}" for t in ignited]

        snap = self.field.snapshot()
        snap["backend"] = self.config.backend
        snap["embed_model"] = getattr(self.embed_backend, "model", "") or self.config.backend
        snap["enabled"] = True
        snap["verbalized"] = verbalized
        snap["attractor_nearest"] = self.field.attractor_pull(query) if query else ""
        desk.meta["neural"] = snap
        return snap

    def remember_report(self, report: str, goal: str = "") -> None:
        if report.strip():
            self.field.add(report.strip(), energy=0.75, source="report_memory")
        if goal.strip():
            self.field.add(goal.strip(), energy=0.7, source="goal_memory")
        self.save_attractors()

    def status(self) -> dict[str, Any]:
        caps = local_capabilities()
        return {
            "backend": self.config.backend,
            "embed_model": getattr(self.embed_backend, "model", ""),
            "verbalize": self.config.verbalize,
            "dim": self.config.dim,
            "traces": len(self.field.traces),
            "cache": str(self._cache_path),
            "local": caps,
            "snapshot": self.field.snapshot(),
        }


class JLensAdapter:
    @staticmethod
    def available() -> bool:
        try:
            import jlens  # noqa: F401

            return True
        except ImportError:
            return False

    @staticmethod
    def howto() -> str:
        return (
            "Create venv with torch+transformers; pip install -e jacobian-lens; "
            "fit lens on open HF model; set HERMESPACE_NEURAL_BACKEND=jlens. "
            "See docs/12-local-model-neural.md"
        )
