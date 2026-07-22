# HermesCube × Hermespace

**Goal:** Hermespace is the live desk / FOA / high-load workspace.  
**HermesCube** is the deep-memory **module** Space opens so large archives don’t blow context.

```
Hermes Agent
  ├── Hermespace  — desk, load, FOA, inject budget
  └── HermesCube  — warehouse .cube, hyper recall, WAL turns
         ↑
    space_bridge (optional import)
```

## High load

Space already caps inject (~900 chars) and drops world prose.  
Cube adds a **dense strip** of the most relevant durable facts for the FOA query — so monotropic turns still have *memory*, not bulk.

## APIs

**Cube package**
- `hermescube.space_bridge.build_space_inject(query, high_load=…)`
- `hermescube.space_bridge.seal_to_cube(content)`
- `hermescube.space_bridge.module_status()`

**Space package**
- `hermespace.cube_module.cube_inject` / `cube_seal` / `cube_status`
- Wired in `hermes_bridge.on_pre_llm_call` after world block
- `remember_learning` also seals into Cube when present

## Install both

```bash
# Cube (user Hermes home)
hermes plugins install PabloTheThinker/hermescube
./scripts/install_hermes.sh --from-git
# Space — existing Hermespace install
# Ensure both importable on Hermes PYTHONPATH
```

Soft dependency: if Cube is missing, Space inject is unchanged.
