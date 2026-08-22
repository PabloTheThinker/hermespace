# HermesCube × Hermespace — heart / generator contract

**HermesCube is the heart** (when installed). **Hermespace is the nervous FOA** —
and a **standalone workbench** when Cube is absent.

Companion: [PabloTheThinker/hermescube](https://github.com/PabloTheThinker/hermescube)  
North star: [PURPOSE.md](../PURPOSE.md) · Living assessment:
[33-living-memories-cube-world.md](../assessment/33-living-memories-cube-world.md)

```
Hermes Agent  ──connect──►  Hermespace (J-Space · FOA · OEW)
                               │ arteries / veins / pulse
                               ▼
                            HermesCube (.cube · Cuboasis · hive · dream)
```

## Authority

| Surface | With Cube | Standalone |
|---------|-----------|------------|
| `$HERMES_HOME/memories/memory.cube` | **Durable SoT** | n/a |
| Hermespace world JSONL | Projection only — recharge via `pulse` / `sync_world`; do not grow a second archive | Local warehouse |
| ACTIVE desk / J-Space hub | Turn FOA (seeded on connect) | Turn FOA |
| Hive (`HERMESCUBE_HIVE`) | Peer room / soul cards | Solo room |
| SemanticStore | Mirror / study | Local seal target |

## Space adapter (`hermespace.cube_module` **1.3**)

```python
from hermespace.cube_module import (
    ensure_heart,
    center_status,
    cube_beat,          # center → heart → standalone
    cube_pulse,         # autonomic_tick → pulse_charge → standalone
    sync_world,         # sync_world_beliefs → standalone evolve
    room_status,        # hive peers or solo
    seed_jspace_from_warehouse,
    connect_agent,      # full join path
    seal_learning,
    cube_inject,
)
```

| Call | Use |
|------|-----|
| `connect_agent(agent_id)` | Session start / `HermesBase.connect` |
| `ensure_heart()` | Create cube or standalone dirs |
| `cube_beat(query, seals=, load=)` | FOA strip when Cube is **not** Hermes `memory.provider`. If `memory.provider=hermescube`, **skip entirely** on `pre_llm` — MemoryManager already prefetched. Empty prefetch is fine. Do not call `center.supply` / `build_space_inject` as a last prefetch. |
| `cube_pulse` / `sync_world` | Idle + connect charge |
| `room_status` | Hive awareness (`HERMESCUBE_HIVE`) |
| `seal_learning(text)` | Desk → durable archive |
| `center_status()` | Doctor / desktop |

Load tiers → strip chars: low 900 · mid 640 · high 420 · protect 280.

## Connect = intelligence gain

```bash
hs base connect --agent-id my-agent
hs base room
hs cube status
```

On connect: heart ensure → world enter → pulse/sync → seed hub from world+Cube
→ optional silent peer presence from hive soul cards.

## Functional J-Space

See [00-map.md](../jspace/00-map.md) and `hermespace.jspace`.

```bash
hs jspace hold -t "deploy pipeline"
hs jspace report
hs base lens
hs cube beat -q "what do we believe about deploys?"
```

## Install both

```bash
hermes plugins install PabloTheThinker/hermescube
# … then Hermespace install
./scripts/install_hermes.sh
```

Soft dependency: if Cube is missing, Space inject/seal/pulse/connect use the
standalone warehouse. Set `HERMESCUBE_HIVE` only when running a fleet hive.
