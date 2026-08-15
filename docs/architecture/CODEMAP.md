# Code map — where to edit

Hermespace is one Python package (`src/hermespace/`) plus a thin Hermes plugin
(`hermes_plugin/`), skill, and optional desktop UI.

**North star:** [PURPOSE.md](../../PURPOSE.md) · **Layout:** [LAYOUT.md](../../LAYOUT.md) ·
**Engine:** [../access/34-jspace-engine.md](../access/34-jspace-engine.md)

## Layers (edit here first)

```
L6 operator     cli.py  ops.py  scripts/  desktop_plugin/
L5 autonomy     grid/*  pulse.py
L4 identity     world.py  episodic.py  semantic.py  memory_db.py
L3 warehouse    cube_module.py  (optional Cube OR standalone)
L2 Access Workspace ★    access/engine.py  hub  env  protocol  oew
L1 desk spine   workflow.py  engine.py  desk.py  gate.py  inject.py
L0 contract     io_contract.py  paths.py  store.py  agent_api.py
```

## Access Workspace package (`access/`) — L2 product

| Module | Role |
|--------|------|
| **`access/engine.py`** | **`AccessEngine`** — connect · turn · lens · chain · harvest |
| `access/hub.py` | Hub · hold · reason · report · broadcast |
| `access/env.py` | Lens · swap · audit · reflect · harvest |
| `access/protocol.py` | OEW gate (`HERMESPACE_OEW`) |
| `access/oew.py` | Causal beat · sticky redirect · reflect seeds |
| `jspace_env.py` | Compat shim → `jspace.env` |
| `hermes_base.py` | Thin alias of `AccessEngine` |

## Desk spine (L1)

| Module | Role |
|--------|------|
| `workflow.py` | Single material ignition (used by `AccessEngine.turn`) |
| `engine.py` | DeskEngine — ACTIVE.md enter / update / seal |
| `desk.py` | ACTIVE.md model |
| `gate.py` | Selectivity — skip trivial |
| `inject.py` | Desk GWT strip |

## Warehouse cable (L3 — optional)

| Module | Role |
|--------|------|
| `cube_module.py` | Soft arterial strip / seal / pulse / room |

## Integration

| Path | Role |
|------|------|
| `hermes_bridge.py` | Plugin hooks — session / pre_llm / end |
| `hermes_plugin/` | Thin `register(ctx)` |
| `workbench.py` | Session pocket — enter / order / idle |
| `agent_api.py` | Dual-decode doors |

## Rules of thumb

1. Prefer `from hermespace import AccessEngine` — one operating surface.  
2. Dual decode: never dump `context` into user chat.  
3. Soft-fail warehouse — engine must run standalone.  
4. Single ignition path: no second beat after `Workflow.run`.  
5. Silent steps stay in model context only.  
6. Prefer `from hermespace.jspace import …` over deep/compat paths.
