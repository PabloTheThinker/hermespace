"""Rank-quality eval: hash vs ollama_embed FOA for task relevance.

Proves local embeddings beat bag-of-hash on simple discrimination tasks.
"""

from __future__ import annotations

import json
from dataclasses import dataclass

from hermespace.local_model import (
    HashEmbedBackend,
    OllamaEmbedBackend,
    ollama_embeddings_available,
)
from hermespace.neural_field import NeuralField, cosine


@dataclass
class Case:
    goal: str
    relevant: list[str]
    distractors: list[str]


CASES: list[Case] = [
    Case(
        goal="fix authentication session timeout",
        relevant=["session TTL", "auth token refresh", "login cookie expiry"],
        distractors=["banana bread recipe", "orbital mechanics homework", "paint color swatches"],
    ),
    Case(
        goal="deploy hermes agent plugin to production",
        relevant=["pre_llm_call hook", "plugin.yaml register", "gateway restart"],
        distractors=["sourdough starter", "cat veterinary visit", "medieval history quiz"],
    ),
    Case(
        goal="reduce cognitive load under monotropic deep work",
        relevant=["single goal lock", "focus of attention cap", "inhibit context switches"],
        distractors=["stock ticker symbols", "pizza toppings list", "guitar chord charts"],
    ),
]


def _rank_relevant(backend_name: str, case: Case, top_k: int = 3) -> tuple[float, list[str]]:
    if backend_name == "ollama_embed":
        be = OllamaEmbedBackend()
    else:
        be = HashEmbedBackend()

    field = NeuralField(dim=256, focus_cap=top_k, embed_fn=lambda t: be.embed(t, 256))
    field.set_query(case.goal)
    for t in case.relevant:
        field.add(t, energy=0.5, source="rel")
    for t in case.distractors:
        field.add(t, energy=0.5, source="dis")
    winners = [t.text for t in field.ignite()]
    hit = sum(1 for w in winners if w in case.relevant)
    precision = hit / max(1, len(winners))
    return precision, winners


def run_eval() -> dict:
    results = {"hash": [], "ollama_embed": []}
    ollama_ok = ollama_embeddings_available()
    for case in CASES:
        p_h, w_h = _rank_relevant("hash", case)
        results["hash"].append({"goal": case.goal, "precision@3": p_h, "winners": w_h})
        if ollama_ok:
            p_o, w_o = _rank_relevant("ollama_embed", case)
            results["ollama_embed"].append(
                {"goal": case.goal, "precision@3": p_o, "winners": w_o}
            )

    def avg(rows: list) -> float:
        if not rows:
            return 0.0
        return sum(r["precision@3"] for r in rows) / len(rows)

    summary = {
        "ollama_available": ollama_ok,
        "hash_mean_precision@3": round(avg(results["hash"]), 3),
        "ollama_mean_precision@3": round(avg(results["ollama_embed"]), 3) if ollama_ok else None,
        "recommendation": (
            "use ollama_embed (auto)"
            if ollama_ok and avg(results["ollama_embed"]) >= avg(results["hash"])
            else "hash fallback"
        ),
        "cases": results,
    }
    return summary


def main() -> int:
    s = run_eval()
    print(json.dumps(s, indent=2))
    # soft assert when ollama up
    if s["ollama_available"] and s["ollama_mean_precision@3"] is not None:
        if s["ollama_mean_precision@3"] + 1e-9 < s["hash_mean_precision@3"]:
            return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
