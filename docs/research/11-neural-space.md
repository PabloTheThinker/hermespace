# Neural Space — research + design (Hermespace)

## Goal

Move Hermespace from **purely symbolic desk** toward a **neural-ish continuous workspace**, without lying about Claude J-space access.

## What is actually possible (2026)

| Level | Possibility | Status in Hermespace |
|-------|-------------|----------------------|
| **A. Geometric field** | Embed concepts; cosine competition; ignition FOA | **Shipped** (`neural_field` + `neural_space`) |
| **B. Local embeddings** | Ollama `nomic-embed-text` / HF sentence models | Adapter ready; needs embed server flags |
| **C. Open J-lens** | Anthropic `jacobian-lens` on Qwen/etc. | Documented adapter; needs GPU + fitted lens.pt |
| **D. SAE features** | Sparse autoencoders on residual stream | Future experiment track |
| **E. Claude live J-space** | Read Anthropic internals | **Not possible** externally |

Open code: https://github.com/anthropics/jacobian-lens  
Paper: Verbalizable Representations Form a Global Workspace (2026-07).

## Out-of-the-box design choices we took

1. **Dual workspace** — symbolic ACTIVE.md **and** continuous field (not either/or).  
2. **Ignition** — scores = blend(energy, alignment_to_goal); top-k become FOA.  
3. **Salience rewrite** — neural scores push back into `[modality|sal]` tags.  
4. **Attractor memory** — sealed/report texts become long-lived attractors (`neural_attractors.json`).  
5. **Residual snapshot** — mean ignited vectors (+ query blend) stored in `desk.meta.neural`.  
6. **Hopfield-ish pull** — probe drifts to nearest attractor label (toy but useful for recall).  

## Why this is “neural space” without cosplay

- J-space is **geometry + causality in activation space**.  
- We implement **geometry + competition + limited broadcast** in a vector field tied to the desk.  
- When a real J-lens backend exists locally, the same `NeuralSpace.sync_from_desk` boundary can swap scoring for lens logits.

## Agent use

```bash
hs turn -m "plan multi-step refactor" --goal "Refactor auth" --force --json
# meta.neural.focus / scores in output
hs neural status
hs neural pull --text "session timeout"
```

## Roadmap (honest)

1. Optional Ollama embed backend when `--embeddings` is up  
2. Nightly attractor consolidation from memory DB reports  
3. Optional jlens backend on a small open model (GPU job)  
4. Eval: does neural FOA improve multi-step task success vs symbolic-only?

## Non-goals

- Claiming we read Claude’s J-space  
- Shipping model weights  
- Consciousness claims  
