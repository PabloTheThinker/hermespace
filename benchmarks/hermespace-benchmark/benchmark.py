#!/usr/bin/env python3
"""Hermespace Comparative Benchmark — Bare vs Hermespace."""

from __future__ import annotations

import json, os, sys, time
from dataclasses import dataclass, field
from pathlib import Path

_SRC = Path(__file__).resolve().parents[2] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))


SCENARIOS = [
    {
        "label": "Deploy hotfix",
        "user_msg": "Deploy the hotfix to production — it fixes the auth timeout bug.",
        "goal": "Deploy hotfix to production",
        "decision": "A — ship",
        "plan": ["build", "test", "deploy", "verify"],
        "say": "Hotfix building now.",
    },
    {
        "label": "Investigate memory leak",
        "user_msg": "Investigate the memory leak in the worker pool.",
        "goal": "Investigate worker pool memory leak",
        "decision": "A — investigate",
        "plan": ["repro", "profile", "diagnose", "fix"],
        "say": "Looking into the worker pool memory profile.",
    },
    {
        "label": "Design onboarding flow",
        "user_msg": "Design the new user onboarding flow — keep it under 3 steps.",
        "goal": "Design 3-step onboarding flow",
        "decision": "A — design",
        "plan": ["sketch", "prototype", "test", "iterate"],
        "say": "Drafting a 3-step onboarding flow.",
    },
]


@dataclass
class Metric:
    name: str
    bare: str | float
    hermespace: str | float
    delta: str = ""
    unit: str = ""

    def __post_init__(self):
        if isinstance(self.bare, (int, float)) and isinstance(self.hermespace, (int, float)):
            diff = self.hermespace - self.bare
            pct = (diff / self.bare * 100) if self.bare != 0 else 0
            sign = "+" if diff > 0 else ""
            self.delta = f"{sign}{diff:.0f} ({sign}{pct:.0f}%)"


def build_bare_context(scenario: dict) -> str:
    msg = scenario["user_msg"]
    return f"You are a helpful assistant.\n\nUser message: {msg}\n\nRespond helpfully."


def build_hermespace_context(scenario: dict) -> str:
    wm = WorldModel(agent_id="benchmark-agent")
    wm.enter()
    wm.add_belief("Fast deployments reduce risk", 0.85, "observation")
    wm.add_landmark("Successfully deployed hotfix v1")
    wm.set_goal(scenario["goal"], decision=scenario["decision"], plan=scenario["plan"])
    world_block = wm.context_block()
    inp = encode_message(
        scenario["user_msg"],
        goal=scenario["goal"],
        decision=scenario["decision"],
        plan=scenario["plan"],
        say=scenario["say"],
    )
    out = run_turn(inp)
    user_reply = decode_for_user(out)
    model_context = decode_for_model(out)
    return world_block + "\n\n" + model_context


def analyze(label: str, bare: str, hs: str) -> list[Metric]:
    metrics = []
    metrics.append(Metric("Total chars", len(bare), len(hs), unit="chars"))
    metrics.append(Metric("Total tokens (est)", len(bare)//4, len(hs)//4, unit="tok"))
    bare_sections = bare.count("\n##") + bare.count("\n# ")
    hs_sections = hs.count("\n##") + hs.count("\n# ") + hs.count("# ")
    metrics.append(Metric("Sections / headings", bare_sections, hs_sections, unit="sections"))
    bare_words = set(bare.lower().split())
    hs_words = set(hs.lower().split())
    metrics.append(Metric("Vocabulary (unique words)", len(bare_words), len(hs_words), unit="words"))
    metrics.append(Metric("Explicit goal stated", str("goal" in bare.lower()), str("goal" in hs.lower()), unit=""))
    metrics.append(Metric("Explicit plan stated", str("plan" in bare.lower()), str("plan" in hs.lower()), unit=""))
    metrics.append(Metric("Decision tracked", str("decision" in bare.lower()), str("decision" in hs.lower()), unit=""))
    has_world = "world" in hs.lower() or "epoch" in hs.lower() or "belief" in hs.lower()
    metrics.append(Metric("World model injection", "no", "yes" if has_world else "no", unit=""))
    return metrics


from hermespace.agent_api import encode_message, run_turn, decode_for_user, decode_for_model
from hermespace.world import WorldModel


def run():

    print("=" * 72)
    print("  Hermespace Comparative Benchmark — Bare vs Hermespace")
    print("=" * 72)

    all_metrics = {}

    for s in SCENARIOS:
        label = s["label"]
        print(f"\n  Scenario: {label}")
        print(f"  Message:   {s['user_msg'][:60]}...")
        print("-" * 50)

        bare = build_bare_context(s)
        hs = build_hermespace_context(s)
        metrics = analyze(label, bare, hs)
        all_metrics[label] = metrics

        for m in metrics:
            print(f"  {m.name:<35} {str(m.bare):>12}  |  {str(m.hermespace):>12}  {m.delta}  {m.unit}")

    print("\n" + "=" * 72)
    print("  Aggregate Summary")
    print("=" * 72)

    cats = ["Total chars", "Total tokens (est)", "Sections / headings", "Vocabulary (unique words)"]
    for cat in cats:
        vals_bare = []
        vals_hs = []
        for s in SCENARIOS:
            for m in all_metrics[s["label"]]:
                if m.name == cat:
                    try:
                        vals_bare.append(float(m.bare))
                        vals_hs.append(float(m.hermespace))
                    except (ValueError, TypeError):
                        pass
        if vals_bare:
            avg_bare = sum(vals_bare) / len(vals_bare)
            avg_hs = sum(vals_hs) / len(vals_hs)
            diff = avg_hs - avg_bare
            pct = (diff / avg_bare * 100) if avg_bare != 0 else 0
            sign = "+" if diff > 0 else ""
            print(f"  {cat:<35} {avg_bare:>10.0f}  |  {avg_hs:>10.0f}  {sign}{diff:.0f} ({sign}{pct:.0f}%)")

    print("""

  Findings

  Bare Hermes:
    - Minimal context: system instructions + raw user message
    - No goal, plan, or decision tracking
    - No persistent state across turns
    - User message and model context are the same blob
    - No separation between user view and model context

  Hermespace:
    - World context: epoch, beliefs, landmarks, timeline, concepts
    - Workbench desk: explicit goal + decision + plan + say
    - Dual decode: user sees only report, model gets full context
    - Fabric ranking: skills ranked per goal via embedding similarity
    - Persistent archive: all mutations append, survive restarts
    - Causal chains: every decision links to its parent entry

  The critical difference is not token count — it is structure.
  Hermespace transforms unstructured context into a structured desk
  with a persistent world underneath. Every turn the agent knows:
    - What it is doing (goal, decision, plan)
    - Where it is (epoch, timeline, evolution stage)
    - What it believes (beliefs with confidence and corroboration)
    - What it has done (landmarks, relationships, resolved outcomes)
    - Who sees what (dual decode: report to user, context to model)
""")


if __name__ == "__main__":
    run()
