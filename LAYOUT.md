# Hermespace codespace layout

North star: [PURPOSE.md](PURPOSE.md) · Assessment:
[docs/assessment/28-hermes-agent-jspace-assessment.md](docs/assessment/28-hermes-agent-jspace-assessment.md)

## Repository map

```
hermespace/
├── PURPOSE.md / ABOUT.md / README.md / LAYOUT.md
├── src/hermespace/          # Python package
│   ├── jspace/              # ★ External J-Space (hub · env · protocol)
│   ├── turn/                # planned — workflow/desk/gate (README only)
│   ├── memory/              # planned — world/episodic/semantic (README only)
│   ├── warehouse/           # planned — cube cable (README only)
│   ├── grid/                # autonomy grid (missions · dream · skillbench)
│   ├── hermes_bridge.py     # Hermes plugin hooks
│   └── …                    # turn spine still at package root (stable imports)
├── hermes_plugin/           # thin Hermes register()
├── desktop_plugin/          # Hermes Desktop page/pane
├── skills/hermespace/       # agent skill
├── docs/
│   ├── jspace/              # J-Space map · thesis · environment
│   ├── assessment/          # deep assessments
│   ├── architecture/        # CODEMAP · Cube contract
│   ├── integration/         # Hermes fit · FOR_HERMES
│   ├── ops/                 # pulse · everyday · recommended
│   ├── research/            # numbered research archive
│   └── roadmap/             # open backlog · OEW phases
├── tests/ · scripts/ · experiments/ · benchmarks/
├── runtime/ · spec/         # templates / protocol specs
└── assets/
```

## Layer authority

| Layer | Path | Authority |
|-------|------|-----------|
| OEW / J-Space | `src/hermespace/jspace/` | Turn FOA + audit SoT |
| Turn spine | package root (`workflow`, `desk`, …) | Live turn |
| Autonomy | `grid/` | Missions / dream / skillbench |
| Identity projection | `world.py` … | Recharged from Cube |
| Warehouse cable | `cube_module.py` | Soft-fail Cube heart |
| Hermes surface | `hermes_plugin/` + bridge | Hooks only |

## Import rules

Prefer:

```python
from hermespace.jspace import JSpace, JSpaceEnv, evaluate_material_turn
```

Compat: `hermespace.jspace_env` still re-exports `JSpaceEnv`.

## Moving code later

Planned packages under `turn/`, `memory/`, `warehouse/` hold READMEs only until
OEW Phase B is green — avoid churning imports while the protocol lands.
