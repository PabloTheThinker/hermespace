<p align="center">
  <img src="assets/banner.svg" width="800" alt="Hermespace">
</p>

<p align="center">
  <em>A persistent agent world that grows forever. Pocket workbench for the current turn.</em>
</p>

<p align="center">
  <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python"></a>
  <a href="https://hermes-agent.nousresearch.com/"><img src="https://img.shields.io/badge/Hermes_Agent-compatible-7C3AED?style=for-the-badge" alt="Hermes Agent"></a>
  <a href="https://github.com/PabloTheThinker/hermespace/releases"><img src="https://img.shields.io/badge/Version-0.18.4-0EA5E9?style=for-the-badge" alt="Version"></a>
  <a href="tests/"><img src="https://img.shields.io/badge/Smoke-9%2F9-16A34A?style=for-the-badge" alt="Smoke 9/9"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge" alt="MIT"></a>
</p>

<p align="center">
  <a href="#the-world-model">World Model</a> ·
  <a href="#the-workbench">Workbench</a> ·
  <a href="#quick-start">Quick Start</a> ·
  <a href="#cli">CLI</a> ·
  <a href="#docs">Docs</a> ·
  <a href="#about">About</a>
</p>

<br>

**Hermespace is an append-only persistent world for Hermes agents.** Every session, every belief, every landmark, every evolution is recorded in an archive that never prunes, never decays, never caps. The agent builds a deepening model of itself and its environment across sessions — and it outlives the user.

Not [J-Space](https://github.com/anomalyco/j-space). Not a second agent runtime. A room inside Hermes that remembers everything.

---

## The World Model

A persistent agent world that grows forever. The archive is the source of truth; the cache is never authoritative.

### Archive

```python
from hermespace import WorldModel

wm = WorldModel(agent_id="my-agent")
wm.enter()                                  # agent enters the world
wm.add_belief("Fast deploys reduce risk", 0.85, source="observation")
wm.add_belief("Fast deploys reduce risk", 0.85, source="observation")  # reinforces
wm.add_landmark("Zero-downtime deploy v2")
wm.set_trait("operations-minded")
wm.set_goal("Improve deploy pipeline", decision="A — automate", plan=["audit", "implement", "verify"])
wm.add_relationship("dev-team", "team", 0.8)
print(wm.render_markdown())                 # epoch-aware markdown
wm.evolve()                                 # consolidate, detect patterns, check epoch
```

Every mutation appends to `~/.hermespace/worlds/{agent_id}_archive.jsonl` — an append-only JSONL that grows forever. No pruning. No decay. No deletion.

Entry types: `enter`, `leave`, `landmark`, `belief`, `trait`, `evolution`, `focus`, `epoch_transition`, `resolve`, `relationship`.

### Epochs

The agent's stage is measured by accumulated experience, not wall clock:

| Epoch | Entries | Behavior |
|-------|---------|----------|
| **Genesis** ✨ | <5 | Brief timeline, all entries visible |
| **Growth** 🌱 | 5–24 | Section headings, summarized older entries |
| **Maturity** 🎓 | 25–99 | Condensed timeline, wisdom from top beliefs |
| **Wisdom** 🧠 | 100+ | Evidence-gated wisdom, deeply held beliefs only |

Epoch transitions are recorded as `epoch_transition` archive entries and change how the world is rendered in the agent's context block.

### Beliefs

Beliefs have confidence (0–1) and corroboration count. Calling `add_belief` with the same statement reinforces — confidence increases by +0.1, corroboration increments. The `evolve()` cycle consolidates semantic notes from `SemanticStore` and detects recurring patterns in landmarks.

### Causal Chains

Every entry can reference parent entries via `causal_parents`. `set_goal()` links to the most recent timeline entry. `trace_chain()` walks backward through the archive.

```python
# Walk the chain
focus_entries = wm.archive.query("focus")
chain = wm.trace_chain(focus_entries[-1].id)

# Resolve an outcome
wm.resolve_outcome(lm_entry.id, "success")
```

### Evolution

The `evolve()` cycle runs five stages:

1. Consolidate semantic notes into beliefs
2. Detect recurring patterns in recent landmarks
3. Analyze relationship affinity trends
4. Detect milestones (entry count thresholds, high-confidence beliefs)
5. Generate open questions from low-confidence beliefs

Then checks for epoch transition, refreshes active concepts (J-Space hub, max 25), and writes an `evolution` archive entry.

The `world_evolve` pulse job runs this hourly. Manual: `hs world evolve` or `WorldModel.evolve()`.

### Context Injection

Every `pre_llm_call` injects the world context: epoch badge, active concepts, wisdom (top beliefs), timeline, pulse summary, and desk status. The agent always knows where it is in its own story.

### CLI

```bash
hs world show               # render world.md
hs world enter              # agent enters the world
hs world leave              # agent leaves (session end)
hs world evolve             # run evolution cycle
hs world add-belief --statement "..."
hs world add-landmark --event "..."
hs world set-trait --trait "..."
hs world set-goal --goal "..."
hs world search --query "deploy"
hs world archive-stats      # count by entry type
hs world timeline --limit 10
hs world resolve --entry-id <id> --outcome success
hs world trace --entry-id <id>
```

---

## The Workbench

Alongside the world, Hermespace provides a desk for the current turn — FOA, dual decode, skills+MEMORY fabric, neural FOA, and an autonomy grid.

| Feature | What it does |
|---|---|
| **Focus of Attention** | ≤4 items, single active goal per turn |
| **Dual Decode** | Human gets a short report; the model gets dense context. Never dump raw inject into chat channels. |
| **Skills + Memory Fabric** | Ranks Hermes skills per goal; injects MEMORY.md / USER.md excerpts |
| **Neural FOA** | `HERMESPACE_NEURAL_BACKEND=auto` — Ollama embeddings when live, hash fallback |
| **Autonomy Grid** | Missions, lenses, dream, self-talk, skillbench, title/tree, access gates. Ground-up design. |
| **Pulse Runtime** | Desk-aware pocket rhythm — idle tick, dream, world evolve, mission pulse |
| **Desktop View** | Sidebar + full page plugin for Hermes Desktop, with Tailscale viewport and socket API |

### Quick start

```bash
git clone https://github.com/PabloTheThinker/hermespace.git
cd hermespace
./scripts/install_hermes.sh     # link skill + plugin
./scripts/smoke_test.sh         # expect 9/9
```

```python
from hermespace import Workbench

wb = Workbench(agent_id="my-agent", session_id="main")
wb.enter()
r = wb.receive_order("Ship the patch", goal="Ship", decision="A — ship", plan=["implement","test"], say="Shipping.", force=True)
print(r["user_reply"])       # → human
ctx = r["model_context"]     # → model (includes world context)
```

### Hermes plugin hooks

| Hook | What happens |
|---|---|
| `on_session_start` | `WorldModel.enter()` + workbench enter + env probe + world stats injected |
| `pre_llm_call` | World context block (epoch + concepts + wisdom + timeline + pulse + desk) injected |
| `on_session_end` | `WorldModel.leave()` + workbench idle tick |

---

## How it works

```text
User message
    │
    ▼
 GATE  ── trivial? skip ── material? continue
    │
    ▼
 ENCODE → DESK → PLAN     FOA, load, decision, steps
    │
    ▼
 DECODE                   report (human) + context (model)
    │
    ▼
 BROADCAST                plugin inject + world context
    │
    ▼
 ACT                      Hermes tools / code / ship
    │
    ▼
 SEAL                     episodic + semantic promote + world evolve
```

State (local, never committed):

```text
$HERMESPACE_HOME/memory/hermespace/
  ACTIVE.md              live desk
  hermespace.db          turn database
  journal/               human-readable logs
  workbenches/           per-agent workbench JSON
  worlds/                world archive (JSONL) + cache (JSON)
```

---

## CLI

| Command | Purpose |
|---------|---------|
| `hs world show\|enter\|leave\|evolve\|search\|archive-stats` | Persistent world |
| `hs turn` | Full INPUT → OUTPUT turn |
| `hs workbench enter\|order\|idle\|park\|status` | Session workbench |
| `hs fabric` / `hs skills` | MEMORY + ranked skills |
| `hs grid mission-add\|lens-set\|think\|dream\|skill-register` | Autonomy grid |
| `hs pulse tick\|daemon\|status` | Pulse runtime |
| `hs neural caps\|eval` | Neural FOA |
| `hs view --serve --port 8764` | Desktop viewport |
| `./scripts/smoke_test.sh` | Health (9/9) |

---

## Docs

| Doc | Contents |
|-----|----------|
| [`ABOUT.md`](ABOUT.md) | Philosophy, design principles, author |
| [`INTEGRATION.md`](INTEGRATION.md) | Python · CLI · plugin · workbench doors |
| [`skills/hermespace/SKILL.md`](skills/hermespace/SKILL.md) | **Agent skill** (load in Hermes) |
| [`FOR_HERMES.md`](FOR_HERMES.md) | Maintainer / dogfood brief |
| [`CONTRIBUTING.md`](CONTRIBUTING.md) | How to contribute |
| [`WORKFLOW.md`](WORKFLOW.md) | GATE → SEAL stages |
| [`SECURITY.md`](SECURITY.md) | What never ships in git |
| [`docs/14-workbench-pocket-dimension.md`](docs/14-workbench-pocket-dimension.md) | Workbench reference (legacy) |
| [`docs/16-why-hermes-framework.md`](docs/16-why-hermes-framework.md) | Why this belongs in Hermes |
| [`docs/18-autonomy-grid.md`](docs/18-autonomy-grid.md) | Grid design |
| [`docs/20-pulse-runtime.md`](docs/20-pulse-runtime.md) | Pulse runtime |
| [`docs/22-open-roadmap.md`](docs/22-open-roadmap.md) | Roadmap |
| [`spec/DESK.md`](spec/DESK.md) | Desk schema |
| [`spec/PROTOCOL.md`](spec/PROTOCOL.md) | Protocol spec |

---

## Repository Layout

```text
assets/                  media (banners, diagrams)
src/hermespace/          runtime package
hermes_plugin/           Hermes session / pre_llm / end hooks
skills/hermespace/       public Hermes agent skill
scripts/                 CLI, install, smoke test, security audit
docs/                    design notes (20+ docs)
spec/                    desk schema + protocol
tests/                   unit tests
experiments/             eval harness, neural benchmarks
desktop_plugin/          Hermes Desktop sidebar + full page
```

---

## Verify

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
./scripts/smoke_test.sh              # expect pass=9 fail=0
./scripts/security_audit.sh          # before any public push
```

---

## About

Built by [PabloTheThinker](https://github.com/PabloTheThinker). Hermespace is an independent companion for Hermes Agent, not an official Nous Research product.

[`ABOUT.md`](ABOUT.md) — philosophy, design principles, related projects.

---

## License

[MIT](LICENSE)
