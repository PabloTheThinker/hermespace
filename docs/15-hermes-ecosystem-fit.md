# Hermes ecosystem fit — makers, users, what Hermespace should contain

Research snapshot for improving Hermespace as a **pocket-dimension workbench** for any Hermes agent.

## Makers (Nous Research)

| Signal | Takeaway for Hermespace |
|--------|-------------------------|
| **@NousResearch** — open-source AI, Discord-first community | Design for *open agents*, not one vendor’s cloud brain |
| **Hermes Agent product line** — “agent that grows with you” | Workbench must support **learning loop**: skills, memory, session search |
| **Funding narrative (~$1.5B talks, Hermes scale-up)** | Hermes is becoming *the* open agent runtime — Hermespace should be a **native room inside that runtime**, not a rival product |
| **Docs emphasis** | Skills, Memory, Cron, MCP, Messaging, Plugins, multi-backend terminals |

Public docs (hermes-agent.nousresearch.com):

- **Learning loop** — create/improve skills; persist knowledge; model the user  
- **MEMORY.md / USER.md** — bounded curated memory injected every turn  
- **Skills** — agentskills.io; on-demand procedural memory under `~/.hermes/skills/`  
- **Cron** — unattended work while humans are away (**idle time is first-class**)  
- **Runs anywhere / idle cost ~0** — VPS, Modal, Daytona hibernation  
- **Gateway** — Telegram etc. while agent works on a remote box  
- **MCP + 60+ tools** — environment is tool-rich  
- **Session search** — past conversations as memory substrate  

## What users actually do with Hermes (pattern)

From Nous positioning + docs (not every viral X account is Hermes-the-agent):

1. **Long-running personal operators** on a VPS/Telegram  
2. **Skill accumulation** — procedural memory over weeks  
3. **Scheduled automations** — reports, backups, audits  
4. **Multi-surface chat** — human on phone, agent on server  
5. **Self-improve loops** — skills + memory nudges  
6. **Import/migration** from other agent stacks (e.g. OpenClaw)  

(Note: @HermesAgent on X is a football game — ignore for product research.)

## Implications → Hermespace environment kit

Hermespace pocket dimension should expose **inventory**, not reimplement Hermes:

| Hermes surface | Inside Hermespace |
|----------------|-------------------|
| Tools/toolsets | `environment.surfaces[]` present/absent |
| Skills | count + sample names from `HERMES_HOME/skills` |
| Memory | MEMORY/USER/SOUL spotted under memories/ |
| Cron | cron dir presence → idle-aware |
| Plugins | list plugin folder names (e.g. hermespace) |
| Orders | `Workbench.receive_order` |
| Idle | `Workbench.idle_tick` + env refresh + consolidate |
| Dual out | user_reply + model_context |

## Design principles (from ecosystem)

1. **Idle is work** — cron/hibernate culture → idle_tick is real  
2. **Skills are the muscle** — desk should know skill inventory  
3. **Memory is bounded** — journal/DB for study; don’t dump secrets  
4. **Gateway-native** — decode_for_user is short; model context is dense  
5. **Open & portable** — no Nous-private APIs required  
6. **Grow with the agent** — attractors + seals + study over time  

## Non-goals

- Replacing Hermes memory/skills systems  
- Cloning Claude J-space  
- Scraping private user timelines into the package  
