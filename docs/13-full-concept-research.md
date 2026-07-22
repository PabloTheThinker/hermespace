# Hermespace — full concept research (operator feature, not a SaaS product)

**Status:** Active **feature/project** for everyday Hermes agents.  
**Package:** `PabloTheThinker/hermespace` · local state under `$HERMESPACE_HOME` (default `~/.hermespace`).

---

## 1. Problem

Hermes agents are strong at tools and chat, weak at **limited, reportable, task-bound workspace**:

- Context dumps grow without competition  
- No standard INPUT→workspace→OUTPUT contract  
- Hard to **revisit** what the agent “had on its desk” last turn  

Anthropic’s **J-space** (2026) showed Claude has an emergent limited internal workspace (Jacobian lens): reportable, modulable, selective, used for multi-step reasoning — not the same as visible CoT.

We cannot read Claude’s J-space. We **can** give every Hermes agent a **harness workspace** with the same *jobs*.

---

## 2. Concept stack

| Layer | Source idea | Hermespace implementation |
|-------|-------------|---------------------------|
| Limited FOA | Cowan / GWT | focus ≤4, activated ≤12 |
| Dual buffers | Baddeley WM | verbal / struct / bind / exec tags |
| Load | Sweller | I/E/G → executive protect |
| Encode multi-stream | Meta TRIBE *role* | text/audio/visual streams |
| Decode to speech | Brain2Qwerty *role* | Report field |
| Neural geometry | J-space geometry without weights | Ollama `nomic-embed-text` FOA |
| Verbalizable set | J-space reportability | optional local LLM verbalizer |
| Memory | Episodic + semantic | SQLite + markdown journal |
| Agent I/O | Production loop | `agent_api` encode/run/decode |

**Not a product pitch** — a **runtime feature** next to Hermes: install package, set env, call doors.

---

## 3. Everyday operate loop

```
User message
    → encode_message (INPUT)
    → run_turn (desk + neural + memory)
    → decode_for_user  → Telegram/UI reply
    → decode_for_model → next LLM step / tools
    → history/study later
```

CLI twin: `hs turn …` · `hs history` · `hs study` · `hs neural eval`

Hermes plugin: **broadcast only** when desk already ready (`pre_llm_call`).

---

## 4. Integration doors (any Hermes agent)

| Door | API | Use |
|------|-----|-----|
| **1 Encode** | `encode_message(...)` | Build INPUT |
| **2 Run** | `run_turn(inp)` | Execute workspace |
| **3 Decode user** | `decode_for_user(out)` | What to say to human |
| **4 Decode model** | `decode_for_model(out)` | Context inject |
| **5 Bundle** | `decode_bundle(out)` | Structured agent payload |
| **6 Memory** | `study_memory` / `history` | Past desks |
| **7 One-shot** | `quick_reply(message)` | Minimal path |
| **8 CLI** | `scripts/hs turn` | Shell agents / cron |
| **9 Plugin** | `hermes_plugin` | Auto context when ready |

Module: `src/hermespace/agent_api.py`  
Guide: `docs/09-agent-io-and-memory.md` · `INTEGRATION.md`

---

## 5. Local neural path (best now)

- **Live:** Ollama embeddings `nomic-embed-text` (mean FOA precision@3 ≈ **0.89** vs hash **0.67**)  
- **Opt-in:** verbalizer via local chat model  
- **Later:** open `jacobian-lens` + torch venv on 3060-class GPU  
- **Never:** claim Claude internal J-space access  

---

## 6. What “done for daily use” means

- [x] INPUT/OUTPUT contract  
- [x] Memory DB + journal  
- [x] Neural FOA with local embeds  
- [x] Hermes plugin symlink + enable  
- [x] Security audit (no operator fingerprints in git)  
- [x] Smoke test script  
- [x] Agent API doors  

---

## 7. Sources (public)

- Anthropic: A global workspace in language models (2026-07-06)  
- Paper: Verbalizable Representations Form a Global Workspace…  
- Open code: github.com/anthropics/jacobian-lens  
- Meta Brain&AI encode/decode *roles* (TRIBE / Brain2Qwerty public lines)  
- Classical: Baddeley WM, GWT (Baars/Dehaene), Sweller load, Cowan FOA  
