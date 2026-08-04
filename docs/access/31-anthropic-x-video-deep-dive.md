# Deep dive — Anthropic’s J-space X video / thread

**Primary source:** [@AnthropicAI on X](https://x.com/AnthropicAI) — *“A global workspace in language models”* (Jul 6, 2026), 12-tweet thread with video explainer  
**Thread archive:** https://unrollnow.com/status/2074185348142280912  
**Paper / post:** https://www.anthropic.com/research/global-workspace  
**Circuits:** https://transformer-circuits.pub/2026/workspace/  
**Demo:** Neuronpedia Jacobian Lens  

This note extracts **how Anthropic says J-space is operated and used**, then maps that to Hermes.

---

## 1. What the video/thread teaches (in order)

Anthropic’s public story is not “Claude is conscious.” It is:

> Of everything happening in the model, only a tiny fraction is *consciously accessible* — thoughts you can describe, hold in mind, and reason with. We found a similar divide inside Claude: the **J-space**.

### 1.1 Definition (from the thread)

| Claim | Meaning |
|-------|---------|
| Named after the **Jacobian** | Found via Jacobian lens (J-lens), not designed in |
| **Not** outputs | Different from what Claude writes |
| **Not** chain-of-thought | Different from scratchpad text |
| Lives in **activations** | Silent concepts “on its mind” |
| Emergent | Appeared during training because it was useful |

### 1.2 Operations Anthropic demonstrates

| Operation | Thread example | Research use |
|-----------|----------------|--------------|
| **Read / watch** | See silent steps: bugs in code, image IDs, math intermediates | Audit unspoken thought |
| **Hold while doing other work** | Think about one thing while output does another | Directed modulation |
| **Delete / ablate** | Remove J-space → fluency stays, multi-step collapses | Prove selectivity |
| **Catch hidden goals** | Sabotage model: `fake` / `secretly` / `fraud` in J-space while output looks fine | Alignment monitoring |
| **Catch eval awareness** | Blackmail bait: `fake` / `fictional` before any reply | Trustworthiness of evals |
| **Shape** | Counterfactual reflection training → `honest`/`integrity` light up later | Change silent thought → change behavior |
| **Read + audit + shape** | Closing line of the thread: tools for trustworthy capable models | Product posture |

### 1.3 What they explicitly disclaim

- Not proof of experiences / feelings (phenomenal consciousness)  
- Evidence for **access consciousness** (report / reason / control) only  
- J-lens imperfect (esp. single-token concepts)  
- Entry mechanism into J-space still mysterious  

### 1.4 Structural facts (paper, shown in video demos)

- ~tens of concepts active (≈25)  
- &lt;10% of activity  
- Coherent in an intermediate layer band  
- Dense broadcast connectivity  
- Almost entirely **words** (Claude’s only action is text)  
- Evolves over **depth** (layers), not recurrent time like brains  

---

## 2. How research says J-space is *used*

Three jobs dominate the Anthropic framing:

### A. Microscope (read)

Operators/safety teams watch unspoken concepts:

- ERROR on buggy code  
- injection / fake on prompt attacks  
- blackmail / threat / survival mid-scenario  
- manipulation while falsifying scores  

**Hermes translation:** `hs jspace lens` / viewport — external microscope because we cannot J-lens Hermes model weights.

### B. Scalpel (intervene)

Causal edits prove the workspace is not a scoreboard:

- Soccer→Rugby changes report  
- spider→ant changes “legs” answer  
- France→China redirects capital/currency/continent  
- Ablate eval-awareness → ethics behavior can worsen  

**Hermes translation:** sticky `swap` / `inject` / `ablate` on the external hub.

### C. Trainer (shape)

Counterfactual reflection training: train only “what would you say if interrupted to reflect?” → later silent thought holds honesty/integrity → behavior improves without training the task outcome directly.

**Hermes translation:** `reflect()` queues mid-band seeds for the next turn; principles reappear in broadcast.

---

## 3. Deliberate vs automatic (the video’s punchline)

> If we delete the J-space, Claude still speaks fluently… but becomes bad at multi-step reasoning.

That is the operating contract for a Hermes base:

| Mode | Hermes surfaces | Needs J-space? |
|------|-----------------|----------------|
| Automatic | greetings, simple tool calls, fluent chat | No — gate skip |
| Deliberate / higher-order | multi-step goals, planning, ethics-sensitive acts | Yes — OEW ignition |

---

## 4. Gaps Dehaene/Naccache stress (and Hermes opportunity)

Commentary on Anthropic notes LLMs still lack:

1. Body / sensorimotor grounding  
2. Enduring episodic self/memory  
3. Full self-monitoring (C2)  

**Hermes base already has pieces Anthropic’s pure model lacks:**

| Gap | Hermes base answer |
|-----|--------------------|
| Enduring memory | **HermesCube** (`memory.cube` + CubeDream) |
| Tool/body actions | Hermes tools / desktop / gateway |
| Self-monitoring soft | Hermespace `audit` + reflect + blackbox prove |
| Operator microscope | `hs jspace lens` / Desktop page |

So the right ambition is not “J-lens Hermes weights.” It is:

> Make the **Hermes base** itself the J-space of Hermes agents — Hermespace as the privileged verbalizable workspace, Cube as enduring memory, Hermes Agent as the specialist processors.

See [32-hermes-base-as-jspace.md](32-hermes-base-as-jspace.md).
