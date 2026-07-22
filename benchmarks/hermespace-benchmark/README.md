# Hermespace Benchmark

Comparative benchmark — **Bare Hermes** vs **Hermespace-enhanced**.

## Structure

```
benchmarks/hermespace-benchmark/
  benchmark.py          Main comparative benchmark (context assembly)
  hermes/               Fresh Hermes Agent clone (for reference)
  README.md             This file
```

## Run

```bash
cd benchmarks/hermespace-benchmark
PYTHONPATH=../../src python3 benchmark.py
```

## Metrics measured

| Category | What it compares |
|----------|-----------------|
| **Context size** | Total chars and estimated tokens (Bare vs Hermespace) |
| **Structure** | Number of sections/headings in each context |
| **Vocabulary** | Unique words — information density |
| **Goal tracking** | Is there an explicit goal, plan, and decision? |
| **World model** | Is the persistent world injected (epoch, beliefs)? |
| **Dual decode** | Is user context separated from model context? |

## Hermes Agent clone

The `hermes/` directory is a shallow clone of
[github.com/NousResearch/hermes-agent](https://github.com/NousResearch/hermes-agent)
for reference during benchmarking. Not used at runtime — the benchmark simulates
context assembly from both paths.

## Results (2026-07-19)

| Metric | Bare | Hermespace | Delta |
|--------|------|------------|-------|
| Avg tokens | ~30 tok | ~889 tok | +2863% |
| Sections | 0 | 35 | +35 |
| Goal stated | No | Yes | — |
| Plan stated | No | Yes | — |
| Decision tracked | No | Yes | — |
| World model | No | Yes | — |

The token increase is not overhead — it is structure. Hermespace replaces a raw
blob with an organized desk: explicit goal, plan, decision trajectory, world
model (epoch, beliefs, landmarks, timeline), pulse health, and dual-channel
decode that separates user context from model context.
