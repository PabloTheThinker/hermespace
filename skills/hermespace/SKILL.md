---
name: hermespace
description: >-
  Full Hermespace pocket workbench for Hermes Agent (v0.18+): concept, dual
  decode, workbench I/O, fabric skills+MEMORY, FOA desk, Pulse, viewport
  app-shell, Tailscale serve, pocket boundary, autonomy grid, Desktop plugin,
  ops boot/doctor/smoke. Use for hermespace, pocket, workbench, FOA, pulse,
  viewport, access approve, fabric, neural FOA, Desktop Hermespace missing.
---

# Hermespace — complete agent guide

**What it is:** A **limited working-memory desk outside the model** for Hermes agents.  
**What it is not:** A second LLM runtime · Claude J-space weights · a SaaS brand · a replacement for Hermes skills/MEMORY.

**Package SoT:** `$HERMESPACE_ROOT` (git checkout) · https://github.com/PabloTheThinker/hermespace  
**State:** `$HERMESPACE_HOME` default `~/.hermespace` (optional `ILO_HOME`)  
**Hermes:** `$HERMES_HOME` default `~/.hermes`  
**Version:** align `src/hermespace/__init__.py` · `pyproject.toml` · `hermes_plugin/plugin.yaml`

---

## 1. Core concept (read this first)

Hermes already has tools, skills, memory, cron, messaging. Under load, agents lose **focus**: too many goals, dumping model context into chat, wrong skill, no sealed decision.

Hermespace is the **room inside Hermes** where multi-step work stays:

| Property | Meaning |
|----------|---------|
| **Limited FOA** | Focus of attention ≤ ~4; desk capacity ~12 |
| **Monotropic** | One active goal; park the rest |
| **Dual decode** | `report` → human · `context` → model only |
| **Legible** | Plan, decision, fabric, seal trail |
| **Harness-level** | No model-weight access; no consciousness claims |

### Mental model

```
User / order
    → GATE (skip trivial acks)
    → ENCODE (streams, load)
    → DESK (FOA, decision, plan)
    → DECODE (report + context)
    → BROADCAST (plugin inject when desk ready)
    → ACT (Hermes tools — real work happens here)
    → SEAL (optional episodic / study DB)
```

**Idle vs order**

| Phase | Behavior |
|-------|----------|
| **Idle** | `idle_tick` — consolidate, attractors, env inventory; **no user spam** |
| **Order** | `receive_order` / `run_turn` — full turn → dual decode → back to idle |

Inspired by WM / GWT *roles* (Baddeley, Cowan FOA, load) — **metaphor only**, not medical or brain-reading.

Deep design: package `docs/13-full-concept-research.md`, `WORKFLOW.md`, `docs/14-workbench-pocket-dimension.md`, `docs/16-why-hermes-framework.md`.

---

## 2. When to load this skill

- User says Hermespace / pocket / workbench / FOA desk / pulse / viewport  
- Multi-step job needs monotropic focus + dual channel  
- Rank Hermes skills / inject MEMORY for this goal  
- Desktop Hermespace missing or right-rail only  
- Access approve/deny, autonomy toggles, ops boot  
- Public ship / smoke / security_audit  
- After material ship: always full **REVIEW** (never ADHOC_PASS alone)

**Companions (depth only):** `hermespace-ops` · `hermespace-grid` · `hermespace-everyday` · `hermespace-runtime-ops` · `pocket-dimension-security`  
This skill is the **whole-concept + how-to-use** entry point.

---

## 3. Install once (any machine)

```bash
git clone https://github.com/PabloTheThinker/hermespace.git
cd hermespace
export HERMESPACE_ROOT="$PWD"
export HERMESPACE_HOME="${HERMESPACE_HOME:-$HOME/.hermespace}"
export HERMES_HOME="${HERMES_HOME:-$HOME/.hermes}"
export PYTHONPATH="$HERMESPACE_ROOT/src${PYTHONPATH:+:$PYTHONPATH}"
./scripts/install_hermes.sh              # skill + plugin into HERMES_HOME
./scripts/install_desktop_plugin.sh      # HARD COPY desktop plugin (not symlink)
hermes plugins enable hermespace
./scripts/smoke_test.sh                  # expect 9/9
./scripts/doctor_desktop.sh              # expect DOCTOR_PASS when Desktop used
```

No operator home paths required. Portable env only.

---

## 4. How an agent uses Hermespace (primary loops)

### 4.1 Python — preferred for agents

```python
from hermespace import Workbench
from hermespace.agent_api import (
    encode_message, run_turn, decode_for_user, decode_for_model, decode_bundle,
    rank_skills, fabric_snapshot, remember_learning,
)

# --- Pocket dimension (idle / order) ---
wb = Workbench(agent_id="my-agent", session_id="main")
wb.enter()                          # env kit onto desk
wb.park_goal("Later: docs")         # monotropic park
wb.idle_tick()                      # while waiting — no user message

r = wb.receive_order(
    user_text,
    goal="…",
    decision="A — …",
    plan=["step1", "step2"],
    say="Short human report.",
    force=True,
)
send_to_user(r["user_reply"])       # HUMAN channel only
model_ctx = r["model_context"]      # MODEL / tools only
fabric = (r.get("bundle") or {}).get("fabric") or {}
# fabric["skill_hits"] → load full bodies with skill_view(name="…")
# fabric MEMORY/USER excerpts already in model_context

# --- Explicit turn API ---
inp = encode_message(user_text, goal="…", decision="A", plan=["…"], say="…",
                     session_id="main", agent_id="my-agent", force=True)
out = run_turn(inp)
send_to_user(decode_for_user(out))
ctx = decode_for_model(out)
meta = decode_bundle(out)           # includes fabric when present

rank_skills("telegram formatting", limit=5)
fabric_snapshot(goal="…", message=user_text)
remember_learning("Prefer plain TG", goal="messaging")  # study DB only — not Hermes MEMORY.md
```

### 4.2 Dual decode (hard rule)

| Field | Goes to | Never |
|-------|---------|--------|
| `report` / `user_reply` | **Human** (TG/email/UI) | Full inject dump |
| `context` / `model_context` | **Model** next step / tools | User-facing chat |
| `bundle["fabric"]` | Agent meta | Public logs with secrets |

High load → short report, monotropic, no option menus.

### 4.3 CLI

```bash
hs turn -m "…" --goal "…" --decision "A" --say "…" --plan "1" --force --json
hs workbench enter|idle|park|order|status|env --agent-id X
hs fabric --goal "…" -m "…"
hs skills --goal "…"
hs status | show | inject | say
hs seal --note "…"
hs study "keyword" | history --session-id …
hs neural caps|eval
hs ops boot | doctor | tick-all
hs controls show|set|job
hs pulse tick|status
hs grid status|mission-add|lens-set|dream|think
hs view --serve --port 8764
hs view --serve --tailscale --port 8764    # any user's tailnet
```

### 4.4 Hermes plugin (automatic)

Hooks: `on_session_start` · `pre_llm_call` · `on_session_end`  
- Broadcasts **ready** desk into model context  
- Does **not** invent goals — agents still call Workbench / turn  
- Optional: `HERMESPACE_AUTO_ORDER=0` (default), `HERMESPACE_IDLE_ON_SESSION_END=1`

### 4.5 Skills + MEMORY fabric

Every material turn can:

1. Rank `$HERMES_HOME/skills/**/SKILL.md` vs goal (embeddings if Ollama, else hash)  
2. Inject capped **MEMORY.md** + **USER.md** excerpts  
3. Put `skill_hint:name` on desk → agent should `skill_view(name="exact-name")`  

Hermes remains SoT for MEMORY writes (`memory` tool) and skill files.  
Hermespace **coordinates** FOA + inject so you *use* them this turn.

Docs: `docs/17-skills-memory-bridge.md`.

---

## 5. Subsystems (map)

| Subsystem | Role | Entry |
|-----------|------|--------|
| **Desk** | Live FOA / goal / plan / report | `ACTIVE.md`, `hs show` |
| **Workbench** | Per-agent pocket idle/order/park | `Workbench`, `hs workbench` |
| **Workflow** | GATE→SEAL spine | `Workflow.run`, `hs turn` |
| **Fabric** | Skills rank + MEMORY/USER | `hermes_fabric`, `hs fabric` |
| **Neural FOA** | Optional embedding competition | `HERMESPACE_NEURAL_BACKEND=auto` |
| **Pulse** | Desk-aware ticks (better than blind cron) | `hs pulse`, in-process on `view --serve` |
| **Viewport** | App-shell UI (sidebar) | `hs view --serve` → Overview/Desk/Access/Pulse/Controls/Missions/Grid |
| **Boundary** | External writes **deny** by default | `request_access` → user approve |
| **Grid** | Missions, lenses, dream, skillbench, self-talk | `hs grid`, `from hermespace import Grid` |
| **Desktop plugin** | Full page `/hermespace` + sidebar | hard-copy install |

Autonomy default **off**. Resolution: `HERMESPACE_AUTONOMY_FORCE` > controls.json > `HERMESPACE_AUTONOMY`.

---

## 6. Viewport + Tailscale (any user)

```bash
# local only
hs view --serve --port 8764
# → http://127.0.0.1:8764/

# this machine's Tailscale IPv4 only (portable — every user's own tailnet)
hs view --serve --tailscale --port 8764
# → http://<that-host-ts-ip>:8764/ from any device on same tailnet

# all interfaces (needs explicit allow)
hs view --serve --bind-all --allow-remote --port 8764
```

Optional: `HERMESPACE_VIEW_TOKEN` · `HERMESPACE_TAILSCALE_IP`  
Docs: `docs/18-tailscale-viewport.md`.  
No hard-coded operator Tailscale IPs in the package.

**Stale UI after upgrade:** kill old `view --serve`, restart, browser hard-refresh.

---

## 7. Pocket boundary (security)

- Default: **cannot** write outside `$HERMESPACE_HOME` without user OK  
- Agent: `request_access(path, reason=…)` — never silent open-world writes  
- User (chat/viewport): `allow <path> for 2h` · `approve request <id>` · `deny` · `revoke permits` · `show boundary`  
- Do **not** add an “open world write” toggle  

Docs: `docs/19-pocket-security-viewport.md` · skill `pocket-dimension-security`.

---

## 8. Daily boot (operator or agent host)

```bash
cd "$HERMESPACE_ROOT"
export PYTHONPATH="$HERMESPACE_ROOT/src${PYTHONPATH:+:$PYTHONPATH}"
export HERMESPACE_HOME="${HERMESPACE_HOME:-$HOME/.hermespace}"
hs ops boot
hs view --serve --port 8764          # or --tailscale
# Desktop: Reload desktop plugins → Hermespace
```

Without leave-on serve: `hs pulse install-timer` or `hs ops tick-all`.

---

## 9. Desktop plugin contract

| Rule | Detail |
|------|--------|
| Install | **Real files** under `$HERMES_HOME/desktop-plugins/hermespace/` — **not** symlink |
| Surfaces | Full page `/hermespace` + sidebar (not right-rail only) |
| StatusDot | only `good \| muted \| warn \| bad` |
| After code change | reinstall hard-copy + Reload desktop plugins |
| Doctor | `./scripts/doctor_desktop.sh` |

See `references/desktop-integration.md` if present in package skill folder.

---

## 10. State layout (never commit)

```
$HERMESPACE_HOME/memory/hermespace/
  ACTIVE.md           live desk
  hermespace.db       turn / study DB
  journal/            human log
  workbenches/        per-agent JSON
  grid/               controls, scars, missions, …
  viewport/           HTML snapshot files
```

---

## 11. Recommended env

```bash
export HERMESPACE_ROOT=…              # checkout
export HERMESPACE_HOME=$HOME/.hermespace
export HERMES_HOME=$HOME/.hermes
export PYTHONPATH=$HERMESPACE_ROOT/src
export HERMESPACE_NEURAL_BACKEND=auto
export HERMESPACE_NEURAL_VERBALIZE=0
export HERMESPACE_AUTONOMY=0
export HERMESPACE_AUTO_ORDER=0
# optional non-loopback viewport:
# export HERMESPACE_VIEW_TOKEN=…
```

`docs/hermes-env.example.sh` · `docs/RECOMMENDED.md`

---

## 12. Verify

```bash
./scripts/smoke_test.sh       # 9/9
./scripts/e2e_ops.sh          # E2E_PASS when present
./scripts/security_audit.sh   # before public push
./scripts/doctor_desktop.sh   # Desktop
hs ops doctor
PYTHONPATH=src python3 -m unittest discover -s tests -q
```

Ad-hoc script ≠ suite green — label honestly.

---

## 13. Finish REVIEW (when shipping for a human operator)

After material Hermespace work, post:

**Goal · Shipped · Why · Verify · Open · Where**

Never end on only a verify table / `ADHOC_PASS`.

---

## 14. Pitfalls

1. Dumping **inject/context** to the human channel  
2. Ending ship on ADHOC_PASS without REVIEW  
3. Desktop **symlink** install → invisible plugin  
4. Stale `view --serve` after UI change  
5. Bare `skill_view()` — always `name="…"`  
6. skill_manage patch without skill_view same turn → refused  
7. External open-world writes without request/approve  
8. Version drift package / plugin.yaml / pyproject  
9. Committing desk/DB/journal or personal paths  
10. Foreground long serve without background → tool timeout  
11. **Buying domains** or other paid registrar actions without explicit user OK  
12. Treating Hermespace as Claude J-space or a second agent brain  

---

## 15. Doc map (package)

| Doc | Use |
|-----|-----|
| `INTEGRATION.md` | All doors (Python/CLI/plugin) |
| `WORKFLOW.md` | GATE→SEAL |
| `FOR_HERMES.md` | Maintainer brief |
| `docs/09` | I/O + memory DB |
| `docs/14` | Workbench pocket |
| `docs/16` | Why Hermes framework |
| `docs/17` | Fabric skills+MEMORY |
| `docs/18-tailscale-viewport.md` | Portable Tailscale |
| `docs/18-autonomy-grid.md` | Grid / missions / dream |
| `docs/19` | Pocket security |
| `docs/20` | Pulse runtime |
| `docs/23-everyday-ops.md` | Day-to-day |
| `docs/INDEX.md` | Full index |
| `SECURITY.md` | Public ship gate |

---

## 16. Related skills

- `hermespace-ops` · `hermespace-grid` · `hermespace-everyday` · `hermespace-runtime-ops`  
- `pocket-dimension-security`  
- `hermes-agent` · `hermes-desktop-surface` · `hermes-local-ops`  
- Finish: `ilo-finish-report` / `material-finish-review` / `session-closeout` when those exist  

**Package skill path:** `$HERMESPACE_ROOT/skills/hermespace/SKILL.md`  
**Profile install:** `$HERMES_HOME/skills/.../hermespace/SKILL.md` (via `install_hermes.sh`)

---

## 17. One-screen checklist for agents

```
[ ] Material multi-step? → enter workbench / run_turn (force if needed)
[ ] Dual decode? → user gets report only; model gets context
[ ] Skills? → read fabric skill_hits → skill_view(name=…)
[ ] MEMORY? → already in fabric inject; durable prefs → Hermes memory tool
[ ] Idle wait? → idle_tick / park_goal — no spam
[ ] Leave pocket filesystem? → request_access + wait for approve
[ ] Viewport? → hs view --serve [--tailscale]
[ ] Done shipping? → smoke/doctor + human REVIEW
```
