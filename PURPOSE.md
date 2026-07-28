# PURPOSE.md — Hermespace north star

**One line:** Hermespace is the **functional J-Space workbench** for Hermes Agent — a harness-level global workspace (FOA desk, dual decode, load protect) that runs **standalone** and is **powered by HermesCube** when present.

Public pitch: **[ABOUT.md](ABOUT.md)**. Architecture: **[docs/01-architecture.md](docs/01-architecture.md)**. Code layout: **[docs/CODEMAP.md](docs/CODEMAP.md)**. Cube contract: **[docs/HERMESCUBE.md](docs/HERMESCUBE.md)**.

---

## Problem

Agents under load lose the turn: context windows fill, FOA scatters, silent reasoning never surfaces for the *model* without dumping into *user* chat, and there is no bounded verbalizable workspace analogous to Anthropic’s J-space (reportable, modulable, selective).

A workbench alone cannot invent a lifetime archive — that is Cube’s job.  
A warehouse alone cannot focus the turn — that is Space’s job.

## Solution

```
┌─────────────────────────────────────────────────────────────────┐
│ Hermes Agent                                                    │
│  MEMORY.md · skills · tools                                     │
│                                                                 │
│  Hermespace (this package)                                      │
│    J-Space harness · FOA ≤4 · dual decode · pulse / idle        │
│    World projection · autonomy grid · viewport                  │
│         ↕ soft cable (cube_module)                              │
│  HermesCube (optional)                                          │
│    .cube SoT · center.beat · seal · autonomic charge            │
└─────────────────────────────────────────────────────────────────┘
```

| Layer | Job | Authority |
|-------|-----|-----------|
| **Hermespace J-Space** | Verbalizable workspace — hold, reason silently, broadcast | Turn FOA SoT |
| **ACTIVE desk** | Goal / decision / report / concepts | Live turn surface |
| **WorldModel JSONL** | Identity / beliefs projection | Working projection (recharged from Cube when present) |
| **HermesCube** | Durable long-tail warehouse | Durable memory SoT when installed |
| **Standalone warehouse** | SemanticStore + WorldModel | Local SoT when Cube absent |

## Functional J-Space (Anthropic-inspired roles, not neural access)

| Property | Harness implementation |
|----------|------------------------|
| Verbal report | `JSpace.report()` · Report field · `hs jspace report` |
| Directed modulation | `hold` / `release` / `inhibit` · message parse |
| Internal reasoning | `reason_step` — silent, model-context only |
| Flexible broadcast | Hub ≤25 · FOA ≤4 · `broadcast_block` on `pre_llm` |
| Selectivity | `gate.should_inject` — trivial acks skip workspace |

Honesty: files + API only. No model-weight access. No consciousness claims.

## Standalone vs Cube-powered

| Mode | When | Warehouse | Inject strip |
|------|------|-----------|--------------|
| **Standalone** | Cube not importable | Semantic + World evolve | Local wisdom strip |
| **Heart 1.0** | `hermescube.space_bridge` | `memory.cube` | `build_space_inject` |
| **Center 1.1** | `hermescube.center` | `memory.cube` | `beat` / load-tiered `supply` |

Soft-fail always. Feature-detect via `hs cube status` / `center_status()`.

## Non-goals

- Not a second LLM runtime / not J-Space neural readout  
- Not a replacement for MEMORY.md or HermesCube  
- Not auto-rewrite of Hermes MEMORY.md  
- Not consciousness / medical claims  
- Does **not** require Cube to operate as a workbench  

## Success metrics

1. **Standalone green** — full turn + jspace + doctor without Cube  
2. **Cube when present** — `ensure` → `beat` → `seal` → `pulse` wired  
3. **Dual decode** — Report ≠ context dump  
4. **Selective** — trivial acks skip ceremony  
5. **Load-aware** — high load shrinks inject (900→280 chars)  
6. **Smoke 9/9** + unit tests green  

## Version posture

Ship purpose-aligned increments. Plugin yaml + `__version__` move together.  
Deepen the Cube cable; do not fork a second durable archive when Cube is present.
