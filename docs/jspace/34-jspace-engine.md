# J-Space Engine — Hermespace as open-source GWT for Hermes Agent

**Version:** 0.23.0  
**Thesis:** Anthropic’s J-space is a *privileged verbalizable workspace* found
inside weights. Hermes Agent usually has **no weight access**. Hermespace
therefore ships a **true J-Space Engine** — the same five access roles, as an
open-source harness Hermes can actually run.

Research: [Anthropic global workspace](https://www.anthropic.com/research/global-workspace) ·
[`anthropics/jacobian-lens`](https://github.com/anthropics/jacobian-lens) (optional open-weight companion)

---

## 1. One engine

```python
from hermespace import JSpaceEngine

eng = JSpaceEngine(agent_id="my-agent")
eng.connect()                              # world + hub seed
out = eng.turn("First repro then patch then verify", goal="Fix auth")
print(eng.decode_user(out))                # short Report
print(eng.decode_model(out)[:400])         # dense context (never dump to chat)
print(eng.lens())                          # what is on the agent's mind
eng.chain("spider", "8 legs")              # silent multi-step
eng.swap("ship now", "canary first")       # causal redirect
print(eng.access_roles())                  # five GWT properties, live
eng.harvest()                              # night consolidation
```

CLI:

```bash
hs base connect
hs base roles
hs base metrics
hs base probe -m "thanks!"
hs base turn -m "First check then implement finally verify" --goal "Ship"
hs base chain -s "repro" -s "patch" -s "verify"
hs base lens
hs base harvest
```

`HermesBase` is a thin alias of `JSpaceEngine`. Desk file ops remain in
`HermespaceEngine` (desk spine only).

---

## 2. Five access roles (Anthropic → Hermespace)

| Anthropic / GWT | Engine API |
|-----------------|------------|
| Verbal report | `report()` · `decode_user()` |
| Directed modulation | `hold` · `swap` · `inject` · `ablate` |
| Internal reasoning | `chain()` · OEW auto-park · silent hub |
| Flexible broadcast | `broadcast()` → pre_llm / desk / fabric |
| Selectivity | `probe_material()` · gate skip on trivial acks |

Warehouse / HermesCube (if installed) is **optional arterial supply** — not
required for the engine to operate.

---

## 3. Fixes folded into the engine cut

| Issue | Fix |
|-------|-----|
| Double hub sync per turn | `advance_turn(already_synced=True)` |
| Workbench second cube_beat | Removed — single Workflow ignition |
| Silent inject double-hold | `inject_thought` → `reason_step` only |
| Fragmented night harvest | `grid.dream` calls `dream_harvest` |
| Plugin dual-decode honor system | `user_reply_hint` + Dual decode block in inject |
| Many facades | `JSpaceEngine` is the product surface |

---

## 4. Pushing limits (what is possible without weight access)

1. **Obligatory externalization** — material turns must park silent intermediates (OEW).
2. **Causal scalpel** — sticky swap / inject / ablate reshape later Report + broadcast.
3. **CRT / reflect** — interrupt → seed next mid-band principles.
4. **Alignment soft audit** — eval-awareness / concealment lexicon on externalized text.
5. **Capacity pressure metrics** — hub/silent fill ratios + ignition rate.
6. **Optional open-weight J-lens** — `jlens_status()` detects `anthropics/jacobian-lens`
   for local open models; Hermes Agent path stays harness-primary.
7. **Growing world room** — connect seeds hub from WorldModel; hive peers optional.

Honesty boundary: access-consciousness *roles* only. No phenomenal claims.
No Jacobian lens on closed Hermes models.

---

## 5. Architecture

```
Hermes Agent (specialists: tools · skills · fluency)
        │ material turns
        ▼
 JSpaceEngine  ←── hs base / plugin hooks
   ├── hub (≤25) · FOA (≤4) · silent chain
   ├── OEW protocol (default ON)
   ├── dual decode (Report ≠ inject)
   └── night harvest → semantic / optional warehouse
```

See also: [32-hermes-base-as-jspace.md](32-hermes-base-as-jspace.md) ·
[00-map.md](00-map.md) · [33-living-memories-cube-world.md](../assessment/33-living-memories-cube-world.md)
