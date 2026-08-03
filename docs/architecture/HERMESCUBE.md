# HermesCube × Hermespace — heart / generator contract

**HermesCube is the heart** (when installed). **Hermespace is the nervous FOA** —
and a **standalone workbench** when Cube is absent.

Companion: [PabloTheThinker/hermescube](https://github.com/PabloTheThinker/hermescube)  
North star: [PURPOSE.md](../PURPOSE.md) · Anatomy (Cube): Cube `docs/ANATOMY.md`

```
Hermes Agent
  ├── Hermespace     J-Space · FOA desk · dual decode · pulse/idle
  │     ↑ powered by heart (or standalone warehouse)
  └── HermesCube     .cube SoT · Cuboasis · CubeDream · growth
           │
           └─ space_bridge / center  ←── soft-imported by cube_module
```

## Authority

| Surface | With Cube | Standalone |
|---------|-----------|------------|
| `$HERMES_HOME/memories/memory.cube` | **Durable SoT** | n/a |
| Hermespace world JSONL | Projection — recharge via `pulse_charge` | Local warehouse |
| ACTIVE desk / J-Space hub | Turn FOA | Turn FOA |
| SemanticStore | Mirror / study | Local seal target |

## Space adapter (`hermespace.cube_module`)

```python
from hermespace.cube_module import (
    ensure_heart,
    center_status,
    cube_beat,      # center 1.1 → heart 1.0 → standalone
    cube_pulse,     # autonomic_tick → pulse_charge → standalone evolve
    seal_learning,
    cube_inject,
    strip_budget,
)
```

| Call | Use |
|------|-----|
| `ensure_heart()` | `Workbench.enter` / session start / pulse |
| `cube_beat(query, seals=, load=)` | Turn / `pre_llm_call` |
| `cube_pulse(agent_id=)` | `idle_tick` / `world_evolve` |
| `seal_learning(text)` | `remember_learning` / turn seal |
| `center_status()` | Doctor / desktop |

Load tiers → strip chars: low 900 · mid 640 · high 420 · protect 280.

## Functional J-Space

See [00-jspace-to-hermespace.md](00-jspace-to-hermespace.md) and `hermespace.jspace`.

```bash
hs jspace hold -t "deploy pipeline"
hs jspace report
hs jspace broadcast
hs cube status
hs cube beat -q "what do we believe about deploys?"
```

## Install both

```bash
hermes plugins install PabloTheThinker/hermescube
# … then Hermespace install
./scripts/install_hermes.sh
```

Soft dependency: if Cube is missing, Space inject/seal/pulse use the standalone warehouse.
