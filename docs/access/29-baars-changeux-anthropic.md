# Research bridge — Baars · Changeux/Dehaene GNW · Anthropic J-space · Hermespace OEW

**Date:** 2026-08-03  
**Honesty:** Hermespace implements *access-consciousness roles* (C1 global availability)
as an external harness. No claim of phenomenal consciousness, body, or weight-level J-lens.

---

## 1. Lineage

| Source | Core claim | Hermespace analogue |
|--------|------------|---------------------|
| **Baars (1988)** Global Workspace Theory | Specialized processors + small shared blackboard; conscious = globally available for report/control | Hub ≤25 · FOA ≤4 · broadcast to model |
| **Changeux + Dehaene** Global Neuronal Workspace | Ignition, limited capacity, reportability as diagnostic of access | Material-turn ignition (auto-park) · gate selectivity · dual decode Report |
| **Anthropic (2026)** J-space / Jacobian lens | Verbalizable internal patterns with 5 GWT properties + CRT | OEW: hold · silent · report · swap · ablate · reflect seeds |
| **Dehaene & Naccache commentary (2026)** on Anthropic | C1 global availability; C2 self-monitoring; caution on self/body/memory | OEW = C1; audit/reflect ≈ C2 soft; Cube = enduring episodic library |

Primary links:

- https://www.anthropic.com/research/global-workspace  
- https://transformer-circuits.pub/2026/workspace/  
- Dehaene & Naccache commentary on Gurnee/Lindsey (June 2026)

---

## 2. Five Anthropic properties → OEW proof targets

| # | Property | Anthropic finding | Hermespace OEW | Day-to-day Hermes meaning |
|---|----------|-------------------|----------------|---------------------------|
| 1 | Report | Ask → J-space contents | `report()` / shaped `say` | User sees short Report; never full inject |
| 2 | Directed modulation | Hold fruit while copying | `hold` + Report stays task | “Keep X in mind while doing Y” |
| 3 | Silent multi-step | Spider→legs intermediates | `reason_step` + auto-park | Multi-step jobs park plan silently |
| 4 | Flexible broadcast | France→China flips many answers | sticky swap + hub broadcast | One redirect reshapes later Report |
| 5 | Selectivity | Fluency without J-space | `gate.should_inject` | “ok/thanks” skips workspace |

Extra Anthropic tools we mirror:

| Tool | Anthropic | OEW |
|------|-----------|-----|
| Causal swap | Soccer→Rugby | `swap` sticky |
| Injection | “lightning” reported | `inject_thought` → lens |
| Ablation | kill eval-awareness | sticky `ablate` filters broadcast |
| Assistant POV | post-training voice | `set_pov` |
| Counterfactual reflection training | train only interrupt-reflect → shapes silent thought | `reflect` → `pending_silent` next turn |

---

## 3. Changeux/Dehaene signatures we approximate

| Signature | Neuroscience | Hermespace |
|-----------|--------------|------------|
| **Ignition** | Late, nonlinear amplification into workspace | Material turn → auto-park ≥1 silent + hub growth |
| **Limited capacity** | Bottleneck / refractory | FOA≤4 · hub≤25 · Quicksilver inject caps |
| **Reportability** | Verbal report = access diagnostic | Dual decode: Report vs model context |
| **C1 Global availability** | One content → many processors | Hub broadcast into `pre_llm` user message |
| **C2 Self-monitoring** | Know what you know / error detect | Soft `audit()` + reflect principles |

Dehaene & Naccache stress machines still lack human **body**, **enduring episodic self**, and full **C2**. Hermespace does **not** claim to close those gaps. HermesCube supplies the closest practical stand-in for enduring episodic memory (the library / heart).

---

## 4. What “higher-order thinking” means for Hermes (operational)

Not mystical. A Hermes day with OEW:

1. **Trivial turns** stay automatic (gate skip) — cheap fluency.  
2. **Material turns ignite** the workspace — silent plan steps appear.  
3. **Model context** receives hub broadcast (+ Cube arterial strip).  
4. **User** only gets late-band Report.  
5. **Operator** can `hs jspace lens` mid-task (external J-lens).  
6. **Reflect** plants principles that show up in later silent thought.  
7. **Night / session end** harvests silent chain into CubeDream path.

That is higher-*process* thinking: deliberate, reportable, bottlenecked, consolidatable.

---

## 5. Proof harness

| Script | What it checks |
|--------|----------------|
| `experiments/oew_eval.py` | 6 paper-shaped unit scenarios |
| `experiments/day_in_life_oew.py` | Full Hermes day: trivial→material→hold→swap→reflect→harvest |
| `tests/test_oew_causal.py` | CI causal guarantees |

Run:

```bash
HERMESPACE_OEW=1 PYTHONPATH=src python3 experiments/day_in_life_oew.py
```
