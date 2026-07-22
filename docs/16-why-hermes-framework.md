# Why Hermespace belongs in the Hermes framework

## One sentence

Hermes already gives agents **tools, skills, memory, cron, and messaging**.  
**Hermespace gives them a workbench** — a limited pocket dimension to wait, park goals, focus, and produce dual outputs (user + model) without turning every idle moment into chat noise.

## Gap in stock Hermes

| Hermes has | Without Hermespace |
|------------|-------------------|
| Tools | Easy to thrash many threads at once |
| MEMORY/USER | Facts, not *this-turn FOA* |
| Skills | Loaded on demand, not ranked to the live goal |
| Cron / idle hibernate | Idle is cheap, but idle has no *internal room* |
| Session search | Past chat ≠ structured desk decisions |
| pre_llm hooks | Need something worth injecting |

## What Hermespace adds (framework value)

1. **Workbench / pocket dimension** — per-agent room (`Workbench`)  
2. **INPUT → OUTPUT doors** — `encode_message` / `run_turn` / `decode_for_user` / `decode_for_model`  
3. **Neural FOA** — local embeddings rank desk concepts to the goal  
4. **Idle ticks** — consolidate + attractors + env inventory while waiting  
5. **Environment kit** — sees Hermes skills/tools/cron/plugins  
6. **Study memory** — SQLite + journal of desks (not only transcripts)  
7. **Native plugin** — `on_session_start` + `pre_llm_call` + `on_session_end`

## Mapping to Nous Hermes pillars

| Hermes pillar | Hermespace counterpart |
|---------------|------------------------|
| Learning loop / skills | Env kit lists skills; seals/attractors grow over time |
| Persistent memory | Complements MEMORY.md — turn-level desk history |
| Cron / unattended | `idle_tick` + park stack between orders |
| Messaging gateway | Dual decode: short user vs dense model context |
| Plugins | First-class file plugin under `HERMES_HOME/plugins` |
| Runs anywhere | State in `HERMESPACE_HOME` (portable) |

## Not competing with Hermes

- Does **not** replace skills, memory files, cron, or MCP  
- Does **not** claim Claude J-space access  
- **Does** give every Hermes agent a proper internal environment  

## Enable

```bash
export HERMESPACE_ROOT=/path/to/hermespace
export HERMESPACE_HOME=$HOME/.hermespace
export PYTHONPATH=$HERMESPACE_ROOT/src:$PYTHONPATH
ln -sfn $HERMESPACE_ROOT/hermes_plugin $HERMES_HOME/plugins/hermespace
hermes plugins enable hermespace
```

Optional:

```bash
export HERMESPACE_AUTO_ORDER=0          # 1 = auto workbench order on material msgs
export HERMESPACE_IDLE_ON_SESSION_END=1
export HERMESPACE_NEURAL_BACKEND=auto
export HERMESPACE_AGENT_ID=my-agent
```

## Proof

```bash
./scripts/smoke_test.sh
hs workbench enter --agent-id demo
hs workbench env --markdown
```
