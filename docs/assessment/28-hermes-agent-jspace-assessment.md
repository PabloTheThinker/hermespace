# Assessment — Making Hermespace the J-Space of Hermes Agent

**Date:** 2026-08-03  
**Hermespace:** v0.21.0 (OEW higher-order ON by default)  
**Hermes Agent surveyed:** v0.19.1 (v2026.7.30) · Quicksilver v0.19.0 · Judgment v0.18.0 · main as of 2026-08-03  
**Companion:** [HermesCube](https://github.com/PabloTheThinker/hermescube) v0.50 (heart / library)  
**Research basis:** Anthropic *Verbalizable Representations Form a Global Workspace* (2026)

---

## 0. Verdict

**Possible.** Hermespace already implements the *roles* of Anthropic's J-space as an
external harness. Hermes Agent's recent architecture (cache-safe `pre_llm_call`,
Context Engine `select_context` / `on_turn_complete`, MemoryProvider split,
background review, MoA, verification contracts, subagent transcripts, live
reasoning streams) gives us the **hooks to make that workspace obligatory and
causal** — the missing piece that turns a diary into a global workspace.

The innovation is not a Jacobian lens on Hermes weights. It is an
**Obligatory External Workspace (OEW)**: a protocol bottleneck where material
Hermes cognition must park verbalizable intermediates in Hermespace, the operator
can lens them, swaps redirect later Report/broadcast, and CubeDream consolidates
them at night.

```
Anthropic:   weights ──J-lens──► silent verbalizable concepts
Hermespace:  Hermes ──OEW protocol──► durable hub/silent chain ──lens──► operator
                                      │
                                      ▼
                               Cube heart (day strip) + CubeDream (night)
```

---

## 1. What Anthropic J-space is (target properties)

| Property | Meaning | Hermespace analogue today | Gap |
|----------|---------|---------------------------|-----|
| Report | Contents can be named on ask | `JSpace.report` / dual decode | Soft — not forced |
| Directed modulation | Hold / focus on request | `hold` / `release` / `inhibit` | Soft |
| Silent multi-step | Intermediates without speech | `reason_step` + mid band | Opt-in |
| Flexible broadcast | One concept → many tasks | `broadcast_block` on inject | Present |
| Selectivity | Fluency without workspace | `gate.should_inject` | Weak measurement |
| Causal swap/inject | Edits change answers | `swap` / `inject` / `ablate` | Not turn-binding yet |
| Alignment audit | Hidden goals visible | soft lexicon `audit()` | Externalized-only |
| Assistant POV | Post-training voice in workspace | `set_pov` | Present |
| Counterfactual reflection | Interrupt → shape later thought | `reflect()` | No next-turn seed |
| Night consolidation | Sleep / dream | `dream_harvest` + CubeDream | Wired soft |

Capacity targets already match the paper's "tens of concepts": hub ≤25, activated ≤12, FOA ≤4.

---

## 2. Recent Hermes Agent updates — what they unlock

Sources: [v0.19.0 Quicksilver](https://github.com/NousResearch/hermes-agent/releases/tag/v2026.7.20),
[v0.18.0 Judgment](https://github.com/NousResearch/hermes-agent/releases/tag/v2026.7.1),
developer docs for [hooks](https://github.com/NousResearch/hermes-agent/blob/main/website/docs/user-guide/features/hooks.md),
[MemoryProvider](https://github.com/NousResearch/hermes-agent/blob/main/website/docs/developer-guide/memory-provider-plugin.md),
[Context Engine](https://github.com/NousResearch/hermes-agent/blob/main/website/docs/developer-guide/context-engine-plugin.md),
`agent/background_review.py`.

### 2.1 Quicksilver (v0.19) — speed + durability

| Hermes change | Hermespace implication |
|---------------|------------------------|
| ~80% TTFT cut; cold path ruthless | Inject must stay **tiny**; load budgets (900/640/420/280) are non-negotiable |
| Live reasoning streams default ON | Mid-band can mirror streamed reasoning **without** dumping it into user Report |
| Smart approvals default + `pre_tool_call` approve | Workspace `audit()` flags can escalate tool risk |
| Subagent live transcripts + durable ledger | Per-child `JSpace(agent_id=sub…)` hubs; parent lens aggregates |
| Delivery-obligation ledger | Seal + blackbox provenance pair with Cube heart |
| Profile-based gateway routing | `HERMESPACE_HOME` / agent_id per profile — isolate hubs |
| Sessions export (MD/HTML/HF traces) | Export hub + silent chain + audit as alignment dataset |
| Hooks spill oversized context to disk | Cap J-Space broadcast; spill full lens to viewport files |
| Byte-stable gateway system prompts | Keep Space out of system prompt; user-message inject only |

### 2.2 Judgment (v0.18) — thinking quality

| Hermes change | Hermespace implication |
|---------------|------------------------|
| MoA first-class presets | Hub holds committee intermediates; Report = aggregator only |
| Verification evidence + `/goal` completion contracts | Seal verified outcomes into hub → Cube; never claim-only |
| Background `delegate_task` fan-out | Parent hub parks mission; children write silent steps; harvest merges |
| `/learn` + `/journey` + memory graph | WorldModel + Cube journey stay projections; Space FOA stays turn-local |
| Background review fork (memory/skill) | Night sibling: `dream_harvest` after review, not competing MemoryProvider |

### 2.3 Stable platform contracts (must respect)

| Contract | Rule for Hermespace |
|----------|---------------------|
| `pre_llm_call` → **user message** only | Never touch system prompt (cache) |
| One MemoryProvider | **Cube** owns it; Space must not register a second provider |
| One Context Engine | Optional future: OEW as `context.engine` *or* stay plugin-hook |
| Soft-fail plugins | Bridge never crashes Hermes |
| Builtin MEMORY.md | Hot catalog; Cube mirrors; Space proposes only |

---

## 3. HermesCube role (do not blur)

From Cube `docs/HERMESPACE.md` / `ANATOMY.md` / `CUBEDREAM.md`:

| Organ | Owner | Day | Night |
|-------|-------|-----|-------|
| Nervous FOA / J-Space | **Hermespace** | hold · reason · report · lens | harvest source |
| Heart (`memory.cube`) | **HermesCube** | arterial strip | seal intake |
| Dream | Space grid + CubeDream | — | consolidate chapters |
| Blackbox | Cube | — | prove claims |

**Hard rule:** Hermespace must not grow a second durable archive. World JSONL is a
projection charged from Cube. OEW lives in the *turn mind*, Cube in the *years*.

---

## 4. Innovation thesis — Obligatory External Workspace (OEW)

### 4.1 The insight

Claude's J-space works because higher-order thought **cannot skip it**.
Hermespace today is optional parking. OEW flips the default:

> On material turns, Hermes may speak to the user only after at least one
> verbalizable intermediate has been written into the Hermespace mid-band,
> and Report is a late-band readout of the hub — not a free-form dump of model context.

That single constraint recreates the five GWT properties *functionally*:

1. **Report** — lens/report read the hub  
2. **Modulation** — hold/swap edit the hub before Report  
3. **Silent reasoning** — mid-band is required, not decorative  
4. **Broadcast** — pre_llm inject is hub-shaped  
5. **Selectivity** — gate skips trivial turns; fluency path bypasses OEW  

### 4.2 Causal loop (paper experiments → harness tests)

| Paper experiment | OEW harness test |
|------------------|------------------|
| Soccer→Rugby swap changes report | `swap` then `receive_order` → Report contains Rugby |
| Inject "lightning" → model reports it | `inject_thought` → next Report/audit sees it |
| Ablate eval-awareness → behavior shifts | `ablate` + re-run → audit/behavior delta |
| Hold fruit while copying text | Hub has fruit; Report is the copy only |
| France→China flexible reuse | One hold redirects capital/currency/continent prompts |

### 4.3 Day / night circulation

```
DAY  message → GATE → OEW encode (early)
                   → silent steps (mid)   [required if material]
                   → Report (late)        [user]
                   → broadcast hub        [model via pre_llm]
                   → audit soft flags
                   → Cube beat (arterial) + seal decisions

NIGHT pulse / grid dream / background_review
                   → dream_harvest silent+hub
                   → seal_learning → CubeDream
                   → autonomic_tick charges World → next-day hub
```

### 4.4 Why this is new (vs copying Anthropic or anomalyco)

- Not weight interpretability  
- Not a SaaS "J-Space" product  
- Not a second agent runtime  
- **Protocol-enforced external access-consciousness for tool-using Hermes agents**,
  with Cube as heart and operator lens as J-lens substitute  

---

## 5. What we can do — phased program

### Phase A — Foundation — **done (v0.21)**

| Item | Detail | Effort |
|------|--------|--------|
| A1 Codespace layout | `jspace/` package · docs folders · planned `turn/` `memory/` `warehouse/` | done |
| A2 Protocol scaffold | `jspace/protocol.py` + `HERMESPACE_OEW` (default ON) | done |
| A3 Assessment + thesis docs | This file + `docs/jspace/thesis-oew.md` | done |
| A4 Wire protocol into workflow | Verdict + meta on every material turn | done |

### Phase B — Causal OEW — **done (v0.21)**

| Item | Detail | Effort |
|------|--------|--------|
| B1 Mandatory silent park | `oew.auto_park_silent` from plan/goal/message | done |
| B2 Sticky swap/inject | Redirects reshape Report + silent chain; Soccer→Rugby tests | done |
| B3 Reflect → next mid-band | `queue_reflect_seeds` consumed on next `advance_turn` | done |
| B4 Ablate behavioral path | Sticky patterns filter `filtered_broadcast` | done |
| B5 Quicksilver inject hygiene | Load-tiered caps in `inject_cap_chars` | done |

### Phase C — Hermes-native depth

| Item | Detail | Effort |
|------|--------|--------|
| C1 Reasoning-stream mirror | When Hermes streams reasoning, park summaries in mid-band | M |
| C2 MoA committee hub | Per-advisor silent slots; aggregator = Report | M |
| C3 Subagent hubs | Child agent_id workspaces; parent harvest | M |
| C4 Verify → seal | Completion-contract evidence → hub seal → Cube/blackbox | M |
| C5 `pre_tool_call` audit gate | High-risk tools consult workspace audit flags | M |
| C6 Optional Context Engine | `select_context` returns hub-shaped request context (config opt-in) | L |
| C7 Session export adapter | Hub+silent+audit → Hermes export / HF trace | S |

### Phase D — Night + operator

| Item | Detail | Effort |
|------|--------|--------|
| D1 dream_harvest ↔ CubeDream | Harden seal path; diary proposals only for MEMORY.md | M |
| D2 Event-driven pulse | access_approved / session_end → immediate harvest | M |
| D3 Desktop lens SoT | Live hub panel; swap UI; audit chips | M |
| D4 Falsifiable eval suite | Paper-shaped scenarios in `experiments/` + CI | M |

### Explicit non-goals

- Weight-level J-lens / torch interpretability in default install  
- Consciousness claims  
- Competing with HermesCube as MemoryProvider  
- Dumping silent chain into user chat  
- Porting foreign product trees into Hermespace  

---

## 6. Risks

| Risk | Mitigation |
|------|------------|
| OEW adds latency / TTFT regression | Soft default off; tiny auto-park; Quicksilver budgets |
| Agents ignore protocol | Skill + inject instructions + optional hard gate |
| Context bloat | Hub caps; spill; load tiers |
| Double archive with Cube | Authority table; doctor warns |
| Cache busting | User-message inject only |
| Over-claiming "we are J-space" | Honesty headers; role language only |

---

## 7. Success metrics

1. Operator: `hs jspace lens` mid-task shows silent intermediates on material work  
2. Causal: Soccer→Rugby-style swap test green in CI  
3. Dual decode: user never sees full inject; model always gets hub broadcast  
4. Night: harvest seals into Cube when present; standalone semantic otherwise  
5. Perf: material inject ≤ protect budget under high load  
6. Hermes dogfood: plugin registers on current Hermes; TTFT impact measured  

---

## 8. Recommended next monotropic cut

1. Wire soft `ProtocolGate` into `workflow.run` / `hermes_bridge` (meta only)  
2. Auto-park one silent step from goal/plan on material turns  
3. Add causal swap unit tests  
4. Keep Cube soft-fail path green  

That is enough to *start being* Hermes's J-space — then deepen with MoA, subagents, and Context Engine options.
