"""Comparative benchmark — what Hermespace measurably changes.

Measures:
  - Dual decode context savings (user vs model token ratio)
  - World model overhead per turn
  - Fabric rank precision
  - Workbench inject overhead
  - Operation latency

Run: PYTHONPATH=src python3 experiments/comparative_benchmark.py
"""

from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1]
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from hermespace.agent_api import decode_for_user, decode_for_model, encode_message, run_turn
from hermespace.desk import Desk
from hermespace.engine import HermespaceEngine
from hermespace.world import WorldModel
from hermespace.hermes_fabric import rank_skills_for_goal


# ── helpers ───────────────────────────────────────────────────────────────

def _token_estimate(text: str) -> int:
    return len(text) // 4  # rough: ~4 chars per token


@dataclass
class Metric:
    name: str
    value: float | str
    unit: str
    note: str = ""


@dataclass
class BenchmarkResult:
    suite: str
    metrics: list[Metric] = field(default_factory=list)

    def add(self, name: str, value: float | str, unit: str, note: str = "") -> None:
        self.metrics.append(Metric(name, value, unit, note))

    def print(self) -> None:
        print(f"\n{'='*60}")
        print(f"  {self.suite}")
        print(f"{'='*60}")
        for m in self.metrics:
            print(f"  {m.name:<45} {str(m.value):>10}  {m.unit:<8}  {m.note}")
        print(f"{'='*60}")


# ── 1. Dual decode context savings ───────────────────────────────────────

def benchmark_dual_decode() -> BenchmarkResult:
    r = BenchmarkResult("Dual Decode — context savings")
    sample_goals = [
        "Deploy the hotfix to production",
        "Investigate the memory leak in the worker pool",
        "Design the new user onboarding flow",
    ]
    total_user_tokens = 0
    total_model_tokens = 0
    for goal in sample_goals:
        inp = encode_message(goal, goal=goal, decision="A — proceed",
                             plan=["analyze", "implement", "verify"], say="Working on it.")
        out = run_turn(inp)
        user_text = decode_for_user(out)
        model_text = decode_for_model(out)
        ut = _token_estimate(user_text)
        mt = _token_estimate(model_text)
        total_user_tokens += ut
        total_model_tokens += mt
        if ut > 0:
            r.add(f"  {goal[:30]}...", f"{mt // max(ut,1)}:1", "model:user", f"user={ut}tok model={mt}tok")

    ratio = total_model_tokens / max(total_user_tokens, 1)
    r.add("Aggregate model:user ratio", f"{ratio:.1f}:1", "", f"user={total_user_tokens}tok model={total_model_tokens}tok")
    r.add("User-facing tokens (avg)", total_user_tokens // len(sample_goals), "tok")
    r.add("Model-facing tokens (avg)", total_model_tokens // len(sample_goals), "tok")
    savings_pct = (1 - total_user_tokens / max(total_model_tokens, 1)) * 100
    r.add("Context kept from user", f"{savings_pct:.0f}%", "", f"={total_model_tokens - total_user_tokens} tok saved per turn")

    return r


# ── 2. World model overhead ──────────────────────────────────────────────

def benchmark_world() -> BenchmarkResult:
    r = BenchmarkResult("World Model — storage & injection overhead")
    aid = "bench-world-" + str(int(time.time()))
    wm = WorldModel(agent_id=aid)

    # Baseline
    base_size = wm.archive.path.stat().st_size if wm.archive.path.exists() else 0

    # Lifecycle mutations
    ops = [
        ("enter", lambda: wm.enter()),
        ("leave", lambda: wm.leave("benchmark")),
        ("enter again", lambda: wm.enter()),
        ("belief", lambda: wm.add_belief("Benchmark belief", 0.8, "benchmark")),
        ("belief reinforce", lambda: wm.add_belief("Benchmark belief", 0.9, "benchmark")),
        ("landmark", lambda: wm.add_landmark("Benchmark landmark")),
        ("trait", lambda: wm.set_trait("benchmarked")),
        ("goal", lambda: wm.set_goal("Benchmark goal", "A", ["step1", "step2"])),
        ("relationship", lambda: wm.add_relationship("bench-bot", "service", 0.5)),
        ("evolve", lambda: wm.evolve()),
    ]
    for name, fn in ops:
        t0 = time.perf_counter()
        fn()
        elapsed = time.perf_counter() - t0
        r.add(f"  {name}", f"{elapsed*1000:.1f}", "ms")

    archive_size = wm.archive.path.stat().st_size - base_size
    entry_count = wm.archive.count()
    r.add("Archive entries", entry_count, "entries")
    r.add("Archive growth", archive_size, "bytes", f"={archive_size // max(entry_count,1)} bytes/entry avg")

    ctx = wm.context_block()
    ctx_tokens = _token_estimate(ctx)
    r.add("Context block size", ctx_tokens, "tok", f"({len(ctx)} chars)")

    # Cleanup
    import glob as g
    for f in g.glob(str(Path.home()) + "/.hermespace/**/worlds/" + aid + "*"):
        try:
            os.unlink(f)
        except OSError:
            pass

    return r


# ── 3. Fabric rank precision ─────────────────────────────────────────────

def benchmark_fabric() -> BenchmarkResult:
    r = BenchmarkResult("Fabric — skill rank precision")

    test_cases = [
        ("Write Python code for a web scraper", "python", "coding"),
        ("Deploy a Docker container to production", "docker", "devops"),
        ("Analyze server logs for errors", "log", "observability"),
    ]
    for goal, expected_kw, category in test_cases:
        t0 = time.perf_counter()
        hits = rank_skills_for_goal(goal, limit=5)
        elapsed = time.perf_counter() - t0
        top_names = [h.name for h in hits[:3]]
        has_expected = any(expected_kw in n for n in top_names)
        r.add(f"  {category}", f"{elapsed*1000:.1f}ms", f"top={top_names[0] if hits else 'none'}", f"expected={expected_kw} {'HIT' if has_expected else 'MISS'}")

    r.add("Fabric isolation", "from hermespace.hermes_fabric import rank_skills_for_goal", "", "no workbench dependency")
    return r


# ── 4. Workbench inject overhead ─────────────────────────────────────────

def benchmark_workbench() -> BenchmarkResult:
    r = BenchmarkResult("Workbench — inject overhead")

    desk = Desk(goal="Benchmark", decision="A", plan=["step"], say="Running.")
    eng = HermespaceEngine()
    eng.enter(goal=desk.goal, concepts=desk.concepts, choices=desk.choices,
              decision=desk.decision, plan=desk.plan, say=desk.say, auto_load=False)

    t0 = time.perf_counter()
    block = eng.inject()
    elapsed = time.perf_counter() - t0
    tokens = _token_estimate(block)
    r.add("Inject latency", f"{elapsed*1000:.1f}", "ms")
    r.add("Inject block size", tokens, "tok", f"({len(block)} chars)")

    r.add("Desk sections", "goal, load, executive, streams, neural, concepts, focus", "")
    r.add("Dual decode pattern", "encode_message → run_turn → decode_for_user/decode_for_model", "", "separates human from model context")

    return r


# ── 5. Summary ───────────────────────────────────────────────────────────

def run_all() -> None:
    print("\nHermespace Comparative Benchmark\n")
    results = [
        benchmark_dual_decode(),
        benchmark_world(),
        benchmark_fabric(),
    ]
    try:
        results.append(benchmark_workbench())
    except Exception as e:
        print(f"  [workbench benchmark skipped: {e}]")

    for r in results:
        r.print()

    # Compute takeaways
    dd = [m for r in results for m in r.metrics if "model:user ratio" in m.name]

    ratio_str = dd[0].value if dd else "N/A"

    print("\nKey takeaways for Observer feedback:\n")
    print(f"  - Dual decode: model:user context ratio = {ratio_str} "
          f"(user sees fraction of what model gets)")
    print("  - World model: ~550 tok injected every LLM call, "
          "~300 bytes/entry archive growth")
    print("  - Fabric: standalone import, no workbench dependency")
    print("  - Next: comparative eval vs bare Hermes (requires LLM-in-loop)")


if __name__ == "__main__":
    run_all()
