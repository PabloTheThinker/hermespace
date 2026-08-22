# Hermes plugin hooks

## Register
```bash
hermes plugins install PabloTheThinker/hermespace --enable
hermes hermespace doctor
```

Repository `__init__.py` → `hermespace.plugin.register(ctx)`.

## Hooks
| Hook | Behavior |
|------|----------|
| on_session_start | Initialize session scope; stage first-turn context |
| pre_llm_call | Gate + bounded desk/hub inject |
| post_llm_call | Observe successful native turn |
| pre_tool_call | Observe upcoming tool; fail-open; never persist args |
| post_tool_call | Count tool name only; never persist payloads |
| on_skill_lifecycle | Park skill name+event only |
| kanban_task_claimed / completed | Park kanban id so the hub moves |
| pre_verify | Observe verify gate; fail-open |
| on_session_end | Lightweight turn boundary |
| on_session_finalize | Harvest ≤10s fail-open + idle maintenance |
| on_session_reset | Prime rotated gateway session |
| subagent_start/stop | Track specialist lifecycle |

## Implementation
Logic: `src/hermespace/hermes_bridge.py`  
Plugin package: `src/hermespace/plugin.py`.

## Env
`HERMESPACE_ROOT`, `HERMESPACE_HOME`, `HERMESPACE_AGENT_ID`,  
`HERMESPACE_AUTO_ORDER=0`, `HERMESPACE_IDLE_ON_SESSION_END=1`,  
`HERMESPACE_NEURAL_BACKEND=auto`, `HERMESPACE_OFF=0`, `HERMESPACE_FORCE=0`

## Failure modes
- Missing runtime → registration fails visibly
- Desk not ready → thin or skipped pre_llm inject (run turn/order first)  
- Use `/hermespace runtime` to inspect native lifecycle
