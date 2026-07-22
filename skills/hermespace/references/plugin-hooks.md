# Hermes plugin hooks

## Register
```bash
ln -sfn "$HERMESPACE_ROOT/hermes_plugin" "${HERMES_HOME:-$HOME/.hermes}/plugins/hermespace"
hermes plugins enable hermespace
```

`hermes_plugin/__init__.py` → `register(ctx)`.  
Keep `plugin.yaml` `version` == package `__version__`.

## Hooks
| Hook | Behavior |
|------|----------|
| on_session_start | Workbench.enter + env kit; seed desk; return context |
| pre_llm_call | Gate + neural FOA + desk inject; optional AUTO_ORDER |
| on_session_end | idle_tick if HERMESPACE_IDLE_ON_SESSION_END=1 |

## Implementation
Logic: `src/hermespace/hermes_bridge.py`  
Plugin package: thin register only.

## Env
`HERMESPACE_ROOT`, `HERMESPACE_HOME`, `HERMESPACE_AGENT_ID`,  
`HERMESPACE_AUTO_ORDER=0`, `HERMESPACE_IDLE_ON_SESSION_END=1`,  
`HERMESPACE_NEURAL_BACKEND=auto`, `HERMESPACE_OFF=0`, `HERMESPACE_FORCE=0`

## Failure modes
- Wrong `HERMESPACE_ROOT` → import fail / empty inject  
- Desk not ready → thin or skipped pre_llm inject (run turn/order first)  
- Plugin alone never creates goals — agent must call turn/order  
