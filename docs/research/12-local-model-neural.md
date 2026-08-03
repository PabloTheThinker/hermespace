# Local models ↔ Hermespace Neural Space

## What this machine can do (survey)

| Resource | Role for neural space |
|----------|------------------------|
| **Ollama + nomic-embed-text** | Real multi-dim embeddings for FOA competition | **Live** |
| **Ollama chat (llama3.1:8b, etc.)** | Verbalizer: pick reportable workspace concepts | **Live** |
| **RTX 3060 12GB** | Enough for 7B–8B HF + light lens fit later |
| **torch / transformers** | Required for Anthropic `jacobian-lens` | Not in base python |
| **jacobian-lens repo** | Open J-lens fit/apply on Qwen-class models | Cloneable; not default |
| **Claude J-space** | Anthropic-only internals | Not accessible |

## Three tiers of “neural”

### Tier 1 — Geometric + local embeds (default when Ollama embeds work)
- Embed goal + concepts with **nomic-embed-text**
- Cosine competition + ignition → FOA
- Backend name: `ollama_embed`
- Env: `HERMESPACE_NEURAL_BACKEND=auto` (default)

### Tier 2 — Local LLM verbalizer (J-space *role*, not Jacobian)
- Small local chat model lists 3–6 **reportable** concepts for this turn
- Mirrors Anthropic “verbalizable workspace” *behaviorally*
- Env: `HERMESPACE_NEURAL_VERBALIZE=1` (default on), `HERMESPACE_VERBAL_MODEL=llama3.1:8b`

### Tier 3 — True J-lens on open weights (optional upgrade)
```bash
# sketch — GPU job
python -m venv .venv-jlens && source .venv-jlens/bin/activate
pip install torch transformers accelerate
pip install -e /path/to/jacobian-lens
# fit lens on e.g. Qwen2.5-1.5B or 7B if VRAM allows
# export HERMESPACE_NEURAL_BACKEND=jlens
# export HERMESPACE_JLENS_PATH=./lens.pt
```
Hermespace adapter remains a thin boundary; fitting is a separate research job.

## Agent path (Hermes)

```bash
export HERMESPACE_HOME=$HOME/.hermespace
export HERMESPACE_NEURAL_BACKEND=auto
export HERMESPACE_NEURAL_VERBALIZE=1

hs neural status          # shows embeddings_ok, models
hs turn -m "multi-step plan..." --goal "..." --force --json
# meta.neural.backend == ollama_embed when live
# meta.neural.verbalized == concepts from local LLM
```

## Why this helps the *AI model* (not just humans)

1. **Better FOA** — embedding similarity ranks what belongs on the desk for *this* goal.  
2. **Reportable set** — verbalizer proposes what should be “sayable,” aligning inject with what the agent can actually use.  
3. **Memory attractors** — past reports live as vectors; pull/recall without re-reading whole journal.  
4. **No cloud neural lock-in** — runs on local Ollama; degrades to hash if down.

## Non-goals

- Reading Claude’s private J-space  
- Shipping torch weights in this repo  
- Claiming biological consciousness  
