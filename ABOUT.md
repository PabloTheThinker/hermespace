**Hermespace is an append-only persistent world for Hermes agents.** Not [J-Space](https://github.com/anomalyco/j-space). Not a second runtime. A room inside Hermes that remembers everything.

Alongside the world, a pocket workbench for the current turn — FOA desk, dual decode, skills+MEMORY fabric, neural FOA, autonomy grid.

---

## Why

Hermes already gives agents tools, skills, memory, cron, and messaging. What's easy to lose under load:
- **No persistent sense of self** beyond the conversation window
- **Too many goals** — focus scatters across sessions
- **No sealed decision trail** — you can't trace why an agent believed what it did three weeks ago
- **Skills exist but aren't ranked per goal** — the agent guesses which skill to load

Hermespace solves this with two systems:

**The World Model** — an append-only archive that records the agent's entire existence. Every session enter/leave, every belief (with confidence and corroboration), every landmark, every evolution, every epoch transition. No pruning. No decay. No deletion. The archive is the source of truth; the cache is never authoritative. The agent outlives the user.

**The Workbench** — a desk for the current turn. FOA cap (≤4 items), single active goal per turn, sealed decision trails, dual-channel decode (what the human sees vs what the model keeps), skills+MEMORY fabric ranking. No raw inject in chat.

---

## Design

- **Archive is truth.** Every mutation writes to an append-only JSONL. `world.json` is a fast cache/projection — never authoritative.
- **No forgetting.** No pruning, decay, or capping. The archive grows forever. The agent outlives the user.
- **Focus first.** The workbench enforces a single active goal per turn. FOA is capped at ≤4 items.
- **Epochs > time.** The agent's stage is measured by accumulated experience, not wall clock. Genesis → Growth → Maturity → Wisdom.
- **Plugin, don't fork.** Hermespace hooks into Hermes via its plugin system. It extends, not replaces.
- **Context every turn.** Every `pre_llm_call` injects the world — epoch badge, active concepts, wisdom, timeline, pulse, desk. The agent always knows where it is in its own story.

---

## Research

| Project | Relation |
|---------|----------|
| [ActiveGraph](https://github.com/anomalyco/ActiveGraph) | Event log is the agent, graph is the world — influenced the archive-first design |
| [J-Space](https://github.com/anomalyco/j-space) | Verbal workspace, ~25 concepts, broadcasting hub — inspired the `concepts` system and `_refresh_concepts()` |
| [Missing Knowledge Layer](https://arxiv.org/abs/2405.10697) | Knowledge = supersession, Memory = decay, Wisdom = evidence-gated — inspired the epoch progression from unfiltered archive → evidence-gated wisdom |
| [Vygotsky](https://en.wikipedia.org/wiki/Inner_speech) | Inner speech, signs as instruments of thought — influenced the dual decode architecture (report to human vs context to model) |
| [Hermes Agent](https://github.com/NousResearch/hermes-agent) | The agent that grows with you, by Nous Research |

---

## Author

Built by [PabloTheThinker](https://github.com/PabloTheThinker) — independent developer and Hermes Agent user.

Project: [github.com/PabloTheThinker/hermespace](https://github.com/PabloTheThinker/hermespace)
Issues: [github.com/PabloTheThinker/hermespace/issues](https://github.com/PabloTheThinker/hermespace/issues)
License: MIT
