# Code map — where to edit

Hermespace is one Python package (`src/hermespace/`) plus a thin Hermes plugin
(`hermes_plugin/`), skill, and optional desktop UI.

**North star:** [PURPOSE.md](../../PURPOSE.md) · **Layout:** [LAYOUT.md](../../LAYOUT.md) ·
**Assessment:** [../assessment/28-hermes-agent-jspace-assessment.md](../assessment/28-hermes-agent-jspace-assessment.md)

## Layers (edit here first)

```
L6 operator     cli.py  ops.py  scripts/  desktop_plugin/
L5 autonomy     grid/*  pulse.py
L4 identity     world.py  episodic.py  semantic.py  memory_db.py
L3 warehouse    cube_module.py  (Cube center/heart OR standalone)
L2 J-Space OEW  jspace/  cognition.py  streams.py  neural_space.py
L1 turn spine   workflow.py  engine.py  desk.py  gate.py  inject.py
L0 contract     io_contract.py  paths.py  store.py  agent_api.py
```

## J-Space package (`jspace/`) — L2

| Module | Role |
|--------|------|
| `jspace/hub.py` | Hub · hold · reason · report · broadcast |
| `jspace/env.py` | Lens · swap · audit · reflect · harvest |
| `jspace/protocol.py` | OEW gate (`HERMESPACE_OEW`) |
| `jspace_env.py` | Compat shim → `jspace.env` |

## Turn spine (L1)

| Module | Role |
|--------|------|
| `workflow.py` | GATE→ENCODE→DESK→PLAN→DECODE→BROADCAST→SEAL + Cube/J-Space |
| `engine.py` | enter / update / seal desk |
| `desk.py` | ACTIVE.md model |
| `gate.py` | Selectivity — skip trivial |
| `inject.py` | GWT broadcast of desk |

## Warehouse cable (L3)

| Module | Role |
|--------|------|
| `cube_module.py` | `cube_beat` / `cube_pulse` / `seal_learning` / standalone |

## Integration

| Path | Role |
|------|------|
| `hermes_bridge.py` | Plugin hooks — session / pre_llm / end |
| `hermes_plugin/` | Thin `register(ctx)` |
| `workbench.py` | Session pocket — enter / order / idle |
| `agent_api.py` | Public doors for agents |

## Planned packages (README only)

`turn/` · `memory/` · `warehouse/` — move modules after OEW Phase B is green.

## Rules of thumb

1. Dual decode: never dump `context` into user chat.  
2. Soft-fail Cube — Space must run standalone.  
3. When Cube present: `.cube` is durable SoT; world JSONL is projection.  
4. Peel grid features; don’t inflate `cli.py` without need.  
5. J-Space silent steps stay in model context only.  
6. Prefer `from hermespace.jspace import …` over deep/compat paths.
