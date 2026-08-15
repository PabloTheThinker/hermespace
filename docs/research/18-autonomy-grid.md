# Hermespace autonomy grid (v0.14)

Ground-up grid inside the pocket dimension — **not** a port of AgentDrive or Conductor.
Roles inspired by those systems; security and data models rebuilt for Hermespace.

## Thesis

Hermes = body. Hermespace = world. The **grid** is where the agent:

- holds **missions** and **scars**
- switches **cognitive lenses** (modes, not character kits)
- **dreams** (bounded consolidation)
- **self-talks** (internal dual-channel dialogue)
- runs a **skillbench** (hot-swap modules, merge/mutate → gated promote)
- grows a **title + skill tree** self-model

## Modules (`src/hermespace/grid/`)

| Module | Role |
|--------|------|
| `secure_store` | Atomic JSON, path sandbox |
| `gates` | Autonomy budget, intent blocks, skill promote guard |
| `missions` | Durable goals |
| `scars` | Typed failure memory |
| `lenses` | builder/architect/security/scientist/operator/signal/partner/dreamer |
| `dream` | Night/idle consolidation report |
| `skillbench` | Modules + fusion + mutation drafts |
| `selftalk` | Internal dialogue log |
| `title_tree` | Title history + tree from bench |
| `api.Grid` | Facade |

## CLI

```bash
hs grid status|context|gates
hs grid mission-add --title "…" --priority 90
hs grid mission-list
hs grid lens-set --name architect
hs grid dream [--force]
hs grid think -t "internal note" --role planner
hs grid skill-register --name foo --file ./SKILL.md
hs grid skill-merge --a foo --b bar
hs grid skill-mutate --name foo --delta "add verify step"
hs grid skill-promote --id <proposal> [--to-hermes]
hs grid title-adopt
hs grid tree-rebuild
```

Python:

```python
from hermespace import Grid
g = Grid("my-agent")
g.add_mission("Ship feature")
g.set_lens("builder")
g.think("Focus one path", role="planner")
g.dream()
print(g.context_block())  # also folded into inject when load not high
```

## Security (default-safe)

- `HERMESPACE_AUTONOMY=0` default — self-order blocked  
- Skill promote static guard (no curl|bash, injection strings, huge bodies)  
- Hermes write only under `skills/hermespace-drafts/` with `--to-hermes`  
- Path escape blocked on all grid file ops  
- Dream/selftalk do not spam user channel  

## Hermes mapping (extension, not fork)

| Hermes surface | Grid counterpart |
|----------------|------------------|
| skills + skill_manage | skillbench drafts → optional promote |
| MEMORY.md | fabric + dream promote suggestions |
| cron / idle | `hs grid dream` + workbench idle |
| plugins hooks | inject includes grid context |
| skills_guard idea | `gates.check_skill_promote` |
| learning loop | merge/mutate + title tree |

## AgentDrive / Conductor

**Not vendored.** Principles remade:

| Foreign idea | Hermespace rebuild |
|--------------|-------------------|
| Experience graph | missions + scars + dream log + study DB |
| Growth merge / fused skills | `skill-merge` proposals |
| Learned skills | `skill-mutate` proposals |
| DNA/title | `title_tree` |
| Overseer gates | `gates` budget + intent |
| Pillars/scars | grid scars (typed), not Conductor plugin dual-load |

## Meta-brain

Self-talk + dual decode = agent can reason *to itself* inside the room; user still only sees `report`. Streams/TRIBE encode remain stimulus → desk; selftalk is internal production stream.

## Version

Grid since **0.14**; current package see pyproject. Pulse **0.16+**. Desktop page **0.17** (no right-rail).
