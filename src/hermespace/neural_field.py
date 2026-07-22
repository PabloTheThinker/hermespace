"""Neural field primitives — continuous workspace geometry (numpy-only).

Not Claude activations. A geometric analogue of:
- limited-capacity attractor field (GWT / Hopfield-ish)
- competition by cosine similarity to a query (goal) vector
- ignition threshold for broadcast into FOA
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from typing import Callable

import numpy as np

DEFAULT_DIM = 256


def embed_text(text: str, dim: int = DEFAULT_DIM) -> np.ndarray:
    """Deterministic bag-of-features embedding (always available)."""
    v = np.zeros(dim, dtype=np.float64)
    toks = re.findall(r"[a-z0-9_]+", (text or "").lower())
    if not toks:
        toks = ["_empty"]
    for tok in toks:
        h = hashlib.sha256(tok.encode("utf-8")).digest()
        for i in range(0, min(32, len(h) - 1), 2):
            idx = int.from_bytes(h[i : i + 2], "little") % dim
            sign = 1.0 if h[(i + 2) % len(h)] % 2 == 0 else -1.0
            v[idx] += sign
    for a, b in zip(toks, toks[1:]):
        h = hashlib.sha256(f"{a}#{b}".encode()).digest()
        idx = int.from_bytes(h[:2], "little") % dim
        v[idx] += 1.0
    n = np.linalg.norm(v)
    if n > 1e-12:
        v /= n
    return v


def cosine(a: np.ndarray, b: np.ndarray) -> float:
    na = np.linalg.norm(a)
    nb = np.linalg.norm(b)
    if na < 1e-12 or nb < 1e-12:
        return 0.0
    return float(np.dot(a, b) / (na * nb))


@dataclass
class NeuralTrace:
    """One concept living in the continuous field."""

    text: str
    vector: np.ndarray
    energy: float = 0.5
    modality: str = "verbal"
    source: str = "desk"

    def to_meta(self) -> dict:
        return {
            "text": self.text[:200],
            "energy": round(self.energy, 4),
            "modality": self.modality,
            "source": self.source,
            "norm": round(float(np.linalg.norm(self.vector)), 4),
        }


@dataclass
class NeuralField:
    """Continuous workspace field with competition + ignition."""

    dim: int = DEFAULT_DIM
    ignition_threshold: float = 0.55
    focus_cap: int = 4
    traces: list[NeuralTrace] = field(default_factory=list)
    query: np.ndarray | None = None
    embed_fn: Callable[[str], np.ndarray] | None = None

    def embed(self, text: str) -> np.ndarray:
        if self.embed_fn is not None:
            return self.embed_fn(text)
        return embed_text(text, self.dim)

    def set_query(self, text: str) -> None:
        self.query = self.embed(text)

    def add(
        self,
        text: str,
        *,
        energy: float = 0.5,
        modality: str = "verbal",
        source: str = "desk",
    ) -> NeuralTrace:
        tr = NeuralTrace(
            text=text.strip(),
            vector=self.embed(text),
            energy=max(0.0, min(1.0, energy)),
            modality=modality,
            source=source,
        )
        self.traces = [t for t in self.traces if t.text != tr.text]
        self.traces.append(tr)
        return tr

    def compete(self) -> list[tuple[NeuralTrace, float]]:
        if self.query is None:
            scored = [(t, t.energy) for t in self.traces]
        else:
            scored = []
            for t in self.traces:
                align = max(0.0, cosine(t.vector, self.query))
                score = 0.45 * t.energy + 0.55 * align
                scored.append((t, score))
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored

    def ignite(self) -> list[NeuralTrace]:
        winners: list[NeuralTrace] = []
        for t, score in self.compete():
            t.energy = max(t.energy, score)
            winners.append(t)
            if len(winners) >= self.focus_cap:
                break
        # prefer ignited above threshold when enough mass
        above = [t for t, s in self.compete() if s >= self.ignition_threshold]
        if above:
            return above[: self.focus_cap]
        return winners[: self.focus_cap]

    def residual_update(self, blend: float = 0.2) -> np.ndarray:
        ignited = self.ignite()
        if not ignited and self.query is not None:
            return self.query.copy()
        acc = np.zeros(self.dim, dtype=np.float64)
        for t in ignited:
            acc += t.vector * max(t.energy, 0.1)
        if self.query is not None:
            acc = (1.0 - blend) * acc + blend * self.query
        n = np.linalg.norm(acc)
        if n > 1e-12:
            acc /= n
        return acc

    def attractor_pull(self, text: str, steps: int = 3, lr: float = 0.35) -> str:
        if not self.traces:
            return text
        probe = self.embed(text)
        nearest = self.traces[0]
        for _ in range(max(1, steps)):
            best_s = -1.0
            for t in self.traces:
                s = cosine(probe, t.vector)
                if s > best_s:
                    best_s = s
                    nearest = t
            probe = (1.0 - lr) * probe + lr * nearest.vector
            n = np.linalg.norm(probe)
            if n > 1e-12:
                probe /= n
        return nearest.text

    def snapshot(self) -> dict:
        ranked = self.compete()
        ignited = self.ignite()
        return {
            "dim": self.dim,
            "ignition_threshold": self.ignition_threshold,
            "n_traces": len(self.traces),
            "focus": [t.text[:120] for t in ignited],
            "scores": [
                {
                    "text": t.text[:100],
                    "score": round(s, 4),
                    "energy": round(t.energy, 4),
                }
                for t, s in ranked[:12]
            ],
            "residual_norm": round(float(np.linalg.norm(self.residual_update())), 4),
        }
