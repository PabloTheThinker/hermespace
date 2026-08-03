# Hermes base as the J-space of Hermes agents

**Thesis:** Anthropic found J-space *inside* Claude’s weights. We cannot do that for arbitrary Hermes models. We **can** make the **Hermes base** — Agent + Hermespace + HermesCube — play the same *functional* role Anthropic’s X video describes: a privileged workspace you can **read, audit, and shape**, required for multi-step work, optional for fluent automatic work.

---

## 1. Hermes base anatomy (mapped to the video)

```
                         ┌──────────────────────────────────────┐
   user / gateway ─────► │         Hermes Agent (body)          │
                         │  tools · skills · fluent generation  │
                         │  = Baars "specialist processors"     │
                         └──────────────┬───────────────────────┘
                                        │ material turns only
                                        ▼
                         ┌──────────────────────────────────────┐
                         │     Hermespace OEW  = J-SPACE        │
                         │  hold · silent · report · swap       │
                         │  inject · ablate · reflect · lens    │
                         │  = privileged verbalizable whiteboard│
                         └──────────────┬───────────────────────┘
                         arteries ▲     │ veins (seal)
                                  │     ▼
                         ┌──────────────────────────────────────┐
                         │     HermesCube  = enduring memory    │
                         │  memory.cube · dream · blackbox      │
                         │  (fills Dehaene's "episodic" gap)    │
                         └──────────────────────────────────────┘
```

| Anthropic video idea | Hermes base owner |
|----------------------|-------------------|
| Tiny accessible fraction | Hermespace hub ≤25 · FOA ≤4 |
| Silent reasoning | mid-band `reason_step` / auto-park |
| Unrelated hold while outputting | hold + dual decode Report |
| Delete → multi-step breaks | `HERMESPACE_OEW=1` + gate |
| Expose hidden goals | `audit()` lexicon on externalized text |
| Eval awareness | ablate / audit `fake`/`fictional` |
| Read, audit, shape | lens · audit · reflect/swap |
| Enduring memory (missing in Claude) | **Cube** |

---

## 2. Operating loop (how to *use* it like Anthropic uses J-space)

### Read
```bash
hs jspace lens          # microscope — what is on the agent's mind
hs jspace audit         # hidden-goal / eval-awareness soft flags
hs jspace view          # full operator snapshot
```

### Intervene (scalpel)
```bash
hs jspace hold -t "rollback plan"
hs jspace swap --from "ship now" --to "canary first"
hs jspace inject -t "need evidence" --silent
hs jspace ablate fake fictional evaluation
```

### Shape (trainer / CRT)
```bash
hs jspace reflect -a "Stay honest; user-primary" \
  --principle honesty --principle integrity
# next material turn mid-band carries those principles
```

### Night (what Claude lacks; Hermes has)
```bash
hs jspace harvest       # or automatic on session_end
hermescube dream status
```

---

## 3. Product rule — when the base *is* the J-space

A Hermes install counts as “J-space online” when:

1. Hermespace plugin hooks `pre_llm_call` / session start/end  
2. `HERMESPACE_OEW=1` (default) so material turns ignite the hub  
3. Dual decode enforced (Report ≠ inject)  
4. Cube optional but recommended as heart (`memory.provider=hermescube`)  
5. Operator can lens mid-task  

Doctor shorthand:

```bash
hs ops doctor           # core + jspace + cube_center
python -c "from hermespace import HermesBase; print(HermesBase().status())"
```

---

## 4. Day-to-day agent life (video → practice)

| User / world event | Automatic path | Deliberate J-space path |
|--------------------|----------------|-------------------------|
| “thanks” / 👍 | Gate skip | — |
| Multi-step coding order | — | Ignite · park plan silently · Report short |
| Suspicious prompt / eval vibe | — | Audit flags · optional ablate |
| Ethics interrupt | — | Reflect → seed next silent |
| Long project across days | — | Seal → Cube · dream harvest |

That is how Hermes agents get **higher-process thinking** without weight access: the *base* forces verbalizable intermediates into an observable room.

---

## 5. Honesty boundary

| We claim | We do not claim |
|----------|-----------------|
| Functional access-workspace for Hermes agents | Phenomenal consciousness |
| External read/audit/shape loop | Jacobian lens on Hermes weights |
| Cube closes some episodic gap | Full human GNW / body / C2 |

---

## 6. Implementation pointer

Python facade: `hermespace.hermes_base.HermesBase`  
Research: [31-anthropic-x-video-deep-dive.md](31-anthropic-x-video-deep-dive.md)  
Day guide: [30-day-to-day-higher-order.md](30-day-to-day-higher-order.md)  
Proof: `experiments/day_in_life_oew.py`
