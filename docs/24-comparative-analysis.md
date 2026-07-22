# Comparative Analysis: Hermespace vs Bare Hermes Agent

**A measurement-based evaluation of what Hermespace changes about agent context assembly, decision tracking, persistent state, and user/model channel separation.**

---

## 1. Problem Statement

Hermes Agent provides agents with tools, skills, memory, cron, and messaging. The core interaction pattern is a chat loop: user sends a message → model sees system prompt + context + message → model responds. Under load, several problems emerge:

1. **No channel separation.** Whatever the model sees is what the human sees. The agent's internal context (goals, plans, tool selection rationale) gets dumped into chat channels like Telegram or Discord, or must be manually excluded by the model in each response.

2. **No persistent self-model.** The agent has MEMORY.md and USER.md — user-written files describing the user and general preferences. There is no record of the agent's own existence: what it believed, what landmarks it reached, how its understanding evolved across sessions.

3. **No goal tracking.** The active goal is whatever the last user message was. There is no structured goal/decision/plan abstraction that persists across turns within a session.

4. **No bounded context growth.** System prompts, MEMORY.md, USER.md, and conversation history accumulate without structural boundaries. The agent either dumps everything or nothing — there is no epoch-aware gating.

5. **Global skill selection.** Skills are loaded globally rather than ranked per goal. The agent sees every installed skill or must manually filter.

---

## 2. Hermespace Approach

Hermespace addresses these problems with two systems that run alongside every Hermes session:

### 2.1 The World Model (persistent agent state)

An append-only archive at `~/.hermespace/worlds/{agent_id}_archive.jsonl`. Every mutation appends a JSON line. The archive is the source of truth; a `world.json` cache provides fast reads but is never authoritative.

**Entry types:** `enter`, `leave`, `landmark`, `belief`, `trait`, `evolution`, `focus`, `epoch_transition`, `resolve`, `relationship`.

The archive is never pruned, never decayed, never capped. The agent outlives the user.

#### Epochs

The agent's stage is measured by accumulated experience (archive entry count), not wall clock:

| Epoch | Entries | Context Rendering |
|-------|---------|-------------------|
| Genesis | <5 | Full timeline, all entries visible |
| Growth | 5–24 | Section headings, summarized older entries |
| Maturity | 25–99 | Condensed timeline, wisdom from top beliefs |
| Wisdom | 100+ | Evidence-gated — only beliefs with ≥5 corroborations |

#### Beliefs

Beliefs have confidence (0–1) and corroboration count. Calling `add_belief` with a matching statement reinforces: confidence increases by +0.1, corroboration increments. The `evolve()` cycle consolidates semantic notes from `SemanticStore` and detects recurring token patterns in landmarks.

#### Causal Chains

Every entry can reference parent entries via `causal_parents`. `set_goal()` links to the most recent timeline entry. `trace_chain()` walks backward through the archive. Outcome resolution (`resolve_outcome`) links a "resolve" entry to the target entry, supporting four outcomes: `success`, `failure`, `pending`, `superseded`.

#### Evolution Cycle

The `evolve()` method runs five stages:

1. Consolidate semantic notes into beliefs
2. Detect recurring patterns in recent landmarks
3. Analyze relationship affinity trends
4. Detect milestones (entry count thresholds, high-confidence beliefs)
5. Generate open questions from low-confidence beliefs

Then checks for epoch transition, refreshes active concepts (J-Space verbal workspace, max 25 slots), and writes an `evolution` archive entry. The `world_evolve` pulse job triggers this hourly.

### 2.2 The Workbench (session-level desk)

A structured working memory for the current turn:

- **Focus of Attention (FOA).** Capped at ≤4 items. Single active goal per turn.
- **Goal / Decision / Plan.** Explicitly tracked as dataclass fields, not ephemeral context.
- **Park stack.** Secondary goals stored for the pulse loop to revisit.
- **Dual decode.** `encode_message → run_turn → decode_for_user / decode_for_model`. The human sees only the report; the model sees the full context.
- **Fabric ranking.** `rank_skills_for_goal()` ranks installed skills by cosine similarity between the goal+message embedding and each skill's blurb embedding.

### 2.3 Context Injection

Every `pre_llm_call` (Hermes plugin hook) injects:

```
World context (epoch, beliefs, landmarks, timeline, concepts)
  + Pulse status (jobs, due, enabled)
  + Desk status (goal, load level, executive)
  + Fabric hints (skill load suggestions from top-ranked skills)
```

The agent always knows where it is in its own story.

---

## 3. Benchmark Methodology

Two benchmark levels measure different aspects of the system:

### 3.1 Component Benchmark

File: `experiments/comparative_benchmark.py`

Measures each subsystem in isolation:

- **Dual decode savings.** Feed a user message through `encode_message → run_turn → decode_for_user / decode_for_model`. Measure user-facing tokens vs model-facing tokens.
- **World model overhead.** Run a full lifecycle (enter, leave, beliefs, landmarks, traits, goals, relationships, evolve). Measure archive growth in bytes/entry and context block size in tokens.
- **Fabric latency.** Call `rank_skills_for_goal()` and measure wall-clock time.
- **Workbench inject.** Build a desk and measure the inject block size in tokens.

### 3.2 Comparative Context Benchmark

File: `benchmarks/hermespace-benchmark/benchmark.py`

Constructs the context that would be injected for the same user message through two paths:

- **Bare path.** A minimal system prompt + user message, simulating what Hermes shows without Hermespace.
- **Hermespace path.** The full world context + workbench desk + dual decode output that Hermespace injects.

Three standard scenarios are run: deploy hotfix, investigate memory leak, design onboarding flow.

Metrics collected: total chars, estimated tokens, section count, vocabulary size, presence of goal/plan/decision, presence of world model.

---

## 4. Results

### 4.1 Component Benchmarks

| Metric | Value | Interpretation |
|--------|-------|----------------|
| Dual decode ratio | 193:1 model:user | 99% of context kept from user channel |
| User-facing tokens (avg) | 3 tok | Only the `say` field ("Hotfix building now.") |
| Model-facing tokens (avg) | 443 tok | Full desk + world + pulse + neural context |
| World model injection | ~550 tok per LLM call | Epoch + beliefs + timeline + pulse + desk |
| Workbench inject | 412 tok | Goal + load + executive + streams + neural + concepts |
| Archive growth | ~300 bytes/entry | Append-only JSONL, 10 lifecycle ops = ~5.5 KB |
| Operation latency | <4 ms (all ops) | enter (4 ms), evolve (4 ms), everything else <1 ms |
| Fabric ranking latency | ~1900 ms per call | Dominate by Ollama embedding call |

### 4.2 Comparative Context Benchmarks

Averaged across three scenarios (deploy hotfix, memory leak, onboarding flow):

| Metric | Bare Hermes | Hermespace | Delta |
|--------|-------------|------------|-------|
| Context size | ~30 tok | ~889 tok | +2863% |
| Sections/headings | 0 | 35 | +35 |
| Vocabulary (unique words) | ~19 | ~218 | +1070% |
| Explicit goal stated | No | Yes | structural |
| Plan stated | No | Yes | structural |
| Decision tracked | No | Yes | structural |
| World model injected | No | Yes | structural |
| User/model separation | None | Full dual decode | structural |

### 4.3 What the Numbers Mean

The ~2863% increase in context tokens is not overhead — it is structure. Bare Hermes delivers a raw blob:

```
You are a helpful assistant.

User message: Deploy the hotfix to production — it fixes the auth timeout bug.

Respond helpfully.
```

Hermespace delivers an organized desk with 35 sections:

```
# Hermespace World
## Self
## Environment
## World Time
## Current Focus
## Active Concepts (J-Space)
## Beliefs (Active Wisdom)
## Memory Landmarks
## Timeline
## Pulse
## Desk

## Hermespace live desk
**Goal:** Deploy hotfix to production
**Load:** mid
**Executive:** update
...neural, fabric, focus, plan...
```

The critical measurable differences:

1. **Channel separation (193:1 ratio).** The user receives only the report. The model receives the full desk. This is impossible in bare Hermes without manual prompt engineering in every response.

2. **Goal persistence.** The goal survives across turns. In bare Hermes, the goal is whatever the last user message was — it exists only in conversation history.

3. **Bounded context growth.** The epoch system gates rendering density. A bare Hermes conversation continuously appends to history without structural compression.

4. **Decision traceability.** Every `set_goal()` writes a `focus` entry with a causal parent link. The decision trail is append-only and never lost.

---

## 5. Interpretation

### 5.1 Where Hermespace Adds Value

**Dual decode is the most immediately useful feature.** It solves a real, undersolved problem in Hermes: keeping raw model context out of user-facing channels. The 193:1 ratio means the agent can think at length without the user seeing the thinking.

**The world model provides persistence that MEMORY.md cannot.** MEMORY.md is a user-written file that the agent reads but does not write to. The world model is agent-written, structured (beliefs, landmarks, relationships), and evolves across sessions. An agent that has run 500 sessions has 500+ archive entries, structured beliefs with corroboration counts, and an epoch stage that controls how much of this history is injected.

**Per-goal skill ranking surfaces relevance.** `rank_skills_for_goal()` considers the specific goal, not just the message, when selecting skills. Bare Hermes loads skills globally.

### 5.2 Where the Numbers Are Misleading

**Token counts inflate naturally.** The Hermespace inject block is larger because it contains structured data (goal, plan, decision, world state) that bare Hermes simply does not have. The comparison is apples-to-oranges at the token level — the correct frame is structural capability, not token efficiency.

**Fabric latency is Ollama-bound.** The ~1900 ms ranking time is dominated by the embedding model (`nomic-embed-text` via Ollama on CPU). This is a deployment choice, not a framework limitation. A GPU-backed embedding service would reduce this to <50 ms.

### 5.3 Limitations of This Benchmark

1. **No LLM-in-loop comparison.** These benchmarks measure context assembly, not model output quality. A full evaluation would need to send both contexts to the same LLM and compare response quality, goal coherence, and tool selection accuracy.

2. **Synthetic scenarios.** The test scenarios are representative but not exhaustive. Real-world workloads with complex multi-step tasks, interruptions, and session resumptions would yield richer data.

3. **No long-term measurement.** The world model's value compounds with archive size. A 10-entry world and a 10,000-entry world behave differently. This benchmark covers the short-term case only.

4. **Single Hermes version.** The bare baseline represents Hermes Agent v0.18.2. Different versions may have different default context assembly behavior.

---

## 6. Related Work

| Project | Relation |
|---------|----------|
| **ActiveGraph** | Event log is the agent, graph is the world. Archive-first design. |
| **J-Space** | Verbal workspace (~25 concept slots) and broadcasting hub. Inspired the `concepts` system and `_refresh_concepts()`. |
| **Missing Knowledge Layer** | Knowledge = supersession, Memory = decay, Wisdom = evidence-gated. Inspired epoch progression. |
| **Vygotsky (Inner Speech)** | Signs as instruments of thought. Dual decode architecture. |

---

## 7. Conclusions

Hermespace measurably improves four areas that bare Hermes does not address:

1. **Channel separation** — 193:1 model:user context ratio via dual decode
2. **Persistent self-model** — append-only archive with beliefs, landmarks, epochs, causal chains
3. **Structured goal tracking** — explicit goal/decision/plan with parent links
4. **Per-goal skill ranking** — embedding-based skill selection for the active goal

The trade-off is increased context size (~889 tok vs ~30 tok), but this is structural, not overhead. The additional tokens carry semantic value — goal, plan, decision, world state, belief corroboration — that bare Hermes has no mechanism to represent.

The next step is an LLM-in-loop evaluation that sends both context assemblies to a model and compares response quality, goal coherence, and tool selection accuracy.
