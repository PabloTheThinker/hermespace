# Code map — where to edit

Hermespace is one Python package (`src/hermespace/`) plus a thin Hermes plugin
(`hermes_plugin/`), skill, and optional desktop UI.

**North star:** [PURPOSE.md](../PURPOSE.md) · **Architecture:** [01-architecture.md](01-architecture.md)

## Layers (edit here first)

```
L6 operator     cli.py  ops.py  scripts/  desktop_plugin/
L5 autonomy     grid/*  pulse.py
L4 identity     world.py  episodic.py  semantic.py  memory_db.py
L3 warehouse    cube_module.py  (Cube center/heart OR standalone)
L2 J-Space      jspace.py  cognition.py  streams.py  neural_space.py
L1 turn spine   workflow.py  engine.py  desk.py  gate.py  inject.py
L0 contract     io_contract.py  paths.py  store.py  agent_api.py
```

## Turn spine (L1)

| Module | Role |
|--------|------|
| `workflow.py` | GATE→ENCODE→DESK→PLAN→DECODE→BROADCAST→SEAL + Cube/J-Space |
| `engine.py` | enter / update / seal desk |
| `desk.py` | ACTIVE.md model |
| `gate.py` | Selectivity — skip trivial |
| `inject.py` | GWT broadcast of desk |

## J-Space + cognition (L2)

| Module | Role |
|--------|------|
| `jspace.py` | Functional workspace — hold / reason / report / broadcast |
| `cognition.py` | FOA≤4, load, executive modes |
| `streams.py` | Multi-stream encode / report decode |
| `neural_space.py` | Embedding FOA field |

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

## Rules of thumb

1. Dual decode: never dump `context` into user chat.  
2. Soft-fail Cube — Space must run standalone.  
3. When Cube present: `.cube` is durable SoT; world JSONL is projection.  
4. Peel grid features; don’t inflate `cli.py` without need.  
5. J-Space silent steps stay in model context only.
