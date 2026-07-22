# Benchmark: What Hermespace Measurably Improves

> Measured against Hermes Agent v0.18. Bare = Hermes without Hermespace. All numbers from `benchmarks/hermespace-benchmark/benchmark.py` across 3 scenarios (deploy hotfix, investigate memory leak, design onboarding flow). Latency on Intel i7 + Docker.

---

## 1. Context Overhead

| Component | Tokens |
|-----------|--------|
| Full turn (original) | ~1191 tok |
| Full context (current) | ~889 tok |
| Delta mode per turn | ~148 tok |
| **Reduction** | **87%** |

Delta mode sends only what changed: focus block, top 3 beliefs, new timeline entries, pulse summary. Static sections (header, self, environment, world time) are skipped after the first turn.

Steady-state per-turn overhead with delta: **~467 tok** (148 world delta + 319 workbench delta).

Source: `docs/25-context-optimization.md`

---

## 2. Channel Separation (Dual Decode)

| Metric | Value |
|--------|-------|
| Model-to-user token ratio | **193:1** |
| User-facing tokens (avg) | **3 tok** (only the `say` field) |
| Model-facing tokens (avg) | **443 tok** (full desk + world + pulse + neural) |

The user sees: `"Hotfix building now."`  
The model sees: goal, decision, plan, world state, beliefs, timeline, pulse, neural state, fabric hints, active concepts.

---

## 3. Comparative Context Assembly

Averaged across 3 scenarios:

| Metric | Bare Hermes | Hermespace | Delta |
|--------|-------------|------------|-------|
| Context size (tok) | ~30 | ~889 | **+2863%** |
| Sections / headings | 0 | 35 | **+35** |
| Vocabulary (unique words) | ~19 | ~218 | **+1070%** |
| Explicit goal stated | No | Yes | structural |
| Plan stated | No | Yes | structural |
| Decision tracked | No | Yes | structural |
| World model injected | No | Yes | structural |
| User/model separation | None | Full dual decode | structural |

---

## 4. Operation Latency

| Operation | Latency |
|-----------|---------|
| `enter()` | 4 ms |
| `evolve()` | 4 ms |
| `add_belief()` | <1 ms |
| `add_landmark()` | <1 ms |
| `set_goal()` | <1 ms |
| `resolve_outcome()` | <1 ms |
| Archive growth | ~300 bytes/entry |

All archive operations finish in **<4 ms**. Fabric ranking (~1900 ms) is dominated by the embedding model (Ollama on CPU — GPU would bring this under 50 ms).

---

## 5. What the Numbers Mean

| Capability | Bare Hermes | Hermespace |
|------------|-------------|------------|
| Agent self-model across sessions | None | Append-only archive with beliefs, landmarks, epochs, relationships |
| Goal survives across turns | No (last user message only) | Yes (explicit goal + decision + plan, persists in archive) |
| Context compression | Unlimited growth | Epoch-gated: Genesis→Growth→Maturity→Wisdom |
| Decision traceability | None | Causal chains (`causal_parents`), outcome resolution |
| Skill selection | Global (all skills loaded) | Per-goal fabric ranking (cosine similarity) |
| Channel separation | None | 193:1 model:user ratio |

---

## 6. Limitations

1. **No LLM-in-loop comparison.** These are context-assembly benchmarks, not output quality. A full eval would send both contexts to the same LLM and measure response quality.
2. **Synthetic scenarios.** Real multi-step tasks with interruptions yield richer data.
3. **Short-term only.** The world model's value compounds with archive size. A 10,000-entry world behaves differently from a 10-entry one.
4. **Fabric latency is deployment-bound.** The 1900 ms ranking cost is specific to CPU-backed Ollama, not the framework.
