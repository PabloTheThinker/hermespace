# PURPOSE.md — Hermespace north star

**One line:** Hermespace is the **true external Access Workspace environment** for Hermes
Agent — a harness where the agent’s verbalizable thoughts are forced into an
observable workspace (lens · silent chain · audit · reflect), running
**standalone** and **powered by HermesCube** at night the way CubeDream
consolidates the day.

Public pitch: **[ABOUT.md](ABOUT.md)**. Assessment:
**[docs/assessment/28-hermes-agent-jspace-assessment.md](docs/assessment/28-hermes-agent-jspace-assessment.md)**.
OEW thesis: **[docs/access/thesis-oew.md](docs/access/thesis-oew.md)**.
Hermes base as J-space: **[docs/access/32-hermes-base-as-jspace.md](docs/access/32-hermes-base-as-jspace.md)**.
Anthropic X video: **[docs/access/31-anthropic-x-video-deep-dive.md](docs/access/31-anthropic-x-video-deep-dive.md)**.
Environment: **[docs/access/27-environment.md](docs/access/27-environment.md)**.
Code layout: **[LAYOUT.md](LAYOUT.md)** · **[docs/architecture/CODEMAP.md](docs/architecture/CODEMAP.md)**.
Cube contract: **[docs/architecture/HERMESCUBE.md](docs/architecture/HERMESCUBE.md)**.

---

## Problem

Anthropic showed that Claude has an internal J-space — a small privileged set of
verbalizable representations that support report, modulation, silent reasoning,
and flexible broadcast (GWT). Operators of Hermes agents face the same opacity:
you usually only see what the agent *writes*, not what it *thinks* mid-task.

We cannot attach a Jacobian lens to Hermes model weights. We can build an
**external** workspace that plays the same functional role — and join it to
Cube’s durable heart so day-thoughts become night-memory.

## Solution

```
┌─────────────────────────────────────────────────────────────────┐
│ Hermes Agent                                                    │
│                                                                 │
│  Hermespace Access Workspace ENV (this package)                          │
│    protocol → early/mid/late bands                              │
│    silent chain (model only) · Report (user)                   │
│    lens readout · swap/inject/ablate · audit · reflect          │
│    viewport = operator window into Hermes thinking              │
│         ↕ soft cable                                            │
│  HermesCube (optional heart)                                    │
│    arterial strip by day · seal + CubeDream by night            │
└─────────────────────────────────────────────────────────────────┘
```

| Layer | Job | Authority |
|-------|-----|-----------|
| **Access Workspace environment** | Externalize + observe verbalizable thought | Turn FOA + audit SoT |
| **ACTIVE desk** | Goal / decision / report | Live turn surface |
| **WorldModel JSONL** | Identity projection | Recharged from Cube when present |
| **HermesCube** | Durable long-tail warehouse | Durable memory SoT when installed |
| **Standalone warehouse** | Semantic + World | Local SoT when Cube absent |

## Anthropic → Hermespace map

| Anthropic | Hermespace |
|-----------|------------|
| J-lens readout | `hs jspace lens` / viewport panel |
| Causal swap / inject / ablate | `swap` / `inject` / `ablate` |
| Silent multi-step intermediates | `reason_step` + mid band |
| Eval-awareness / hidden-goal audit | `audit()` soft lexicon |
| Assistant POV in workspace | `set_pov` |
| Counterfactual reflection training | `reflect()` + seal principles |
| Night / sleep consolidation | `dream_harvest` + CubeDream + pulse |

## Standalone vs Cube-powered

| Mode | Warehouse | Night path |
|------|-----------|------------|
| Standalone | Semantic + World | harvest → semantic/world |
| Heart / Center | `memory.cube` | harvest → seal_learning → CubeDream |

## Non-goals

- Not weight-level J-lens · not consciousness claims  
- Not a second LLM runtime · not MEMORY.md rewrite  
- Silent chain never auto-dumps into user chat  

## Success metrics

1. Operator can `hs jspace lens` and see silent intermediates Hermes parked  
2. Sticky swap changes subsequent Report/broadcast (Soccer→Rugby)  
3. Material turns auto-park ≥1 silent step (`HERMESPACE_OEW=1` default)  
4. Reflect seeds the next mid-band; ablate filters model inject  
5. Dual decode: user Report shaped; model gets hub + Cube strip  
6. Audit flags externalized manipulation/eval-awareness language  
7. Dream/pulse harvest feeds Cube or standalone warehouse  
8. Smoke 9/9 · unit tests green · runs without Cube  

## Version posture

Deepen the *environment* (observe + intervene + dream), not a second archive.
Plugin yaml + `__version__` move together.
