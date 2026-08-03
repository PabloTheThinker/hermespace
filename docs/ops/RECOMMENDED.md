# Recommended production config (best path now)

## Decision (2026-07-18)

**Best path:** Ollama **nomic-embed-text** neural FOA + symbolic desk + memory DB.  
**Not yet:** Jacobian-lens (no torch in default env).  
**Verbalizer:** opt-in only (`HERMESPACE_NEURAL_VERBALIZE=1`) — adds latency.

```bash
export HERMESPACE_HOME="${HERMESPACE_HOME:-$HOME/.hermespace}"
export HERMESPACE_NEURAL_BACKEND=auto          # ollama_embed when live
export HERMESPACE_EMBED_MODEL=nomic-embed-text
export HERMESPACE_NEURAL_VERBALIZE=0          # set 1 for local LLM concept pick

hs neural caps
hs neural eval          # hash vs ollama rank quality
hs turn -m "..." --goal "..." --force --json
```

## Why this is best

1. Embeddings are **live and discriminative** on this host.  
2. No new GPU stack / multi-GB torch install required.  
3. Every `hs turn` already syncs neural FOA into desk + inject.  
4. Study memory (SQLite + journal) already records turns.  
5. J-lens remains a documented upgrade when you want a GPU research day.

## Agent reply contract (unchanged)

INPUT → Hermespace → **report** to user, **context** to model.
