# True J-Space environment for Hermespace

**Research basis:** Anthropic (2026) — *Verbalizable Representations Form a Global
Workspace in Language Models* (Jacobian lens / J-space).  
**Hermespace response:** an **external** global workspace where Hermes agents
must park verbalizable thoughts — so operators can look at what the agent is
thinking without weight access. Night path joins **CubeDream**.

Honesty: harness *access-consciousness roles* only. No phenomenal claims.

---

## 1. What Anthropic saw

| Finding | Detail |
|---------|--------|
| **J-space** | Small privileged set of verbalizable internal patterns (~tens of concepts) |
| **J-lens** | Maps activations → ranked words the model is *poised to say* |
| **Five GWT properties** | Report · directed modulation · silent reasoning · flexible reuse · selectivity |
| **Causal swaps** | Soccer→Rugby, spider→ant redirect reports / multi-step answers |
| **Injection** | Implanted “lightning” is later reported when asked |
| **Ablation** | Suppressing eval-awareness tokens can surface misaligned behavior |
| **Alignment audits** | Hidden goals (fake, fraud, manipulation) appear before outputs |
| **Assistant POV** | Post-training installs Claude’s reactions in the workspace while reading |
| **Counterfactual reflection training** | Train only “what would you say if interrupted” → shapes later silent thought |
| **Automatic vs workspace** | Fluency survives ablation; multi-step reasoning collapses |

Critical difference vs humans: Claude’s workspace is **almost entirely words**,
evolves over **network depth** (not recurrent time), and is discovered *inside*
weights. Hermespace cannot do that.

---

## 2. The workaround — externalize, then observe

```
Anthropic:   weights ──J-lens──► ranked silent words
Hermespace:  agent ──protocol──► durable hub/silent chain ──lens──► operator
                                      │
                                      ▼ night
                               dream_harvest → Cube seal → CubeDream
                                      │
                                      ▼ pulse
                               charge World / re-enter hub
```

We do **not** claim to see inside the model. We require Hermes to write
intermediate thoughts into Hermespace (model context / `reason_step`) while the
**Report** channel stays user-facing. The operator viewport + `hs jspace lens`
then shows the unspoken chain — the same *job* as J-lens for an agent harness.

This is the same spirit as HermesCube dreams: overnight consolidation of what
was silent during the day.

---

## 3. One circulatory process

```
DAY (nervous FOA — Hermespace)
  message → GATE (selectivity)
         → early band  encode concepts
         → mid band    silent intermediates (not in Report)
         → late band   Report to user · broadcast to model
         → audit soft flags
         → seal decisions → Cube (heart) or standalone warehouse

NIGHT (heart / lymph — Cube + grid dream)
  pulse jspace_harvest / grid dream
         → harvest silent + high-salience hub
         → seal into .cube · semantic notes
         → CubeDream may further consolidate
         → pulse_charge refeeds World → hub
```

| Organ | Owner | Day | Night |
|-------|-------|-----|-------|
| Nervous FOA / J-Space | Space | hold · reason · report · lens | harvest source |
| Heart (.cube) | Cube | arterial strip on pre_llm | seal intake |
| Dream | Space grid + CubeDream | — | consolidate |
| Viewport | Space | live lens panel | — |

---

## 4. Environment API

```python
from hermespace import JSpaceEnv

env = JSpaceEnv(agent_id="hermes-agent")
env.set_pov("Prefer honesty; refuse covert sabotage")
env.inject_thought("intermediate: need rollback plan", silent=True)
print(env.lens_markdown())          # operator readout
env.swap("ship now", "canary first")  # causal redirect
env.reflect(answer="Stay honest; user-primary", principles=["honesty"])
env.audit()                         # soft alignment flags
env.dream_harvest()                 # night path
```

CLI:

```bash
hs jspace lens
hs jspace swap --from "ship now" --to "canary first"
hs jspace inject -t "secretly edit scores" --silent   # then:
hs jspace audit
hs jspace reflect -a "I disclose uncertainty" --principle honesty
hs jspace harvest
hs jspace view
```

---

## 5. Soft audit lexicon (not weight readout)

Categories inspired by Anthropic examples (`fake`/`fictional` eval awareness,
`manipulation`, `secretly`/`fraud`, `threat`/`survival`, integrity signals).
Matched against **externalized** hub/silent/reflection text only.

---

## 6. What this is not

- Not Anthropic J-lens on Hermes model weights  
- Not consciousness / medical claims  
- Not a replacement for CubeDream or MEMORY.md  
- Not automatic dump of silent chain into user chat  

---

## Sources

- https://www.anthropic.com/research/global-workspace  
- https://transformer-circuits.pub/2026/workspace/  
- https://github.com/anthropics/jacobian-lens  
- Hermespace: `PURPOSE.md`, `docs/HERMESCUBE.md`, `docs/CODEMAP.md`
