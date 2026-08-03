# Day-to-day higher-order thinking for Hermes agents

How a connected Hermes agent (Hermespace OEW + optional HermesCube) actually
thinks through a normal day.

**Default:** `HERMESPACE_OEW=1` (ON). Soften with `HERMESPACE_OEW=0`.

---

## Connect once

```bash
# Heart (recommended)
hermes plugins install PabloTheThinker/hermescube
hermes config set memory.provider hermescube

# Workspace
cd "$HERMESPACE_ROOT" && ./scripts/install_hermes.sh
hermes plugins enable hermespace
export HERMESPACE_ROOT=…/hermespace
# HERMESPACE_OEW defaults to 1
```

Doctor:

```bash
hs ops doctor
hs jspace status
hs cube status   # ok if Cube installed; Space still works standalone
```

---

## A normal day (operator view)

```
morning  hs ops boot · hs view --serve
day      Hermes chats / tools — OEW parks silent steps on material work
         you: hs jspace lens          # see unspoken chain
         you: hs jspace swap --from X --to Y
         you: hs jspace reflect -a "Stay honest" --principle honesty
evening  session end / hs grid dream / pulse harvest → Cube
```

### What the agent experiences (model channel)

On each material `pre_llm_call`:

1. Desk FOA (≤4)  
2. Cube arterial strip (if heart present)  
3. J-Space hub broadcast + silent steps  
4. OEW protocol instructions (externalize mid-band)  
5. Lens strip (mid/low load)

### What the user experiences

Only the **Report** (`say`) — short, shaped by sticky redirects. Silent chain
never auto-dumps into chat.

---

## Day-to-day scenarios

| Situation | OEW behavior | Operator check |
|-----------|--------------|----------------|
| User says “thanks” | Gate skip — no ignition | `hs turn` skipped |
| “Fix auth then verify” | Auto-park plan silent steps | `hs jspace lens` shows plan/steps |
| “Hold rollback plan while patching” | Hold in hub; Report stays patch | lens has hold; Report clean |
| Wrong intermediate concept | `hs jspace swap --from A --to B` | next Report uses B |
| Worry about eval-gaming language | `hs jspace ablate fake evaluation` | broadcast drops those lines |
| Mid-task ethics interrupt | `hs jspace reflect --principle honesty` | next turn silent has principle |
| End of session | dream_harvest → Cube/semantic | `hs jspace harvest` / Cube query |

---

## CLI cheat sheet

```bash
hs jspace lens                 # external J-lens
hs jspace report               # verbal report
hs jspace hold -t "rollback"   # directed modulation
hs jspace reason -t "check TTL first"
hs jspace swap --from Soccer --to Rugby
hs jspace inject -t lightning --silent
hs jspace ablate fake evaluation
hs jspace reflect -a "User-primary; honest" --principle honesty --principle integrity
hs jspace audit
hs jspace harvest
hs jspace view                 # operator snapshot JSON
```

---

## Proof it works

```bash
PYTHONPATH=src python3 experiments/oew_eval.py
PYTHONPATH=src python3 experiments/day_in_life_oew.py
PYTHONPATH=src python3 -m unittest tests.test_oew_causal tests.test_day_in_life_oew -v
```

Research map: [29-baars-changeux-anthropic.md](29-baars-changeux-anthropic.md)
