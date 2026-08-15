# Hermespace Access Workspace (GWT harness)

Hermespace implements **access-workspace roles** as an open harness for Hermes
Agent — reportable hub, directed modulation, silent multi-step reasoning,
flexible broadcast, and selectivity. This is Hermespace's own product surface
(`AccessEngine` / `AccessHub`), not a third-party brand.

| Access role | Hermespace |
|-------------|------------|
| Limited capacity (~tens of concepts) | Hub ≤25 · activated ≤12 · FOA ≤4 |
| Verbal report | `AccessHub.report()` · Report field · `hs access report` |
| Directed modulation | `hold` / `release` / `inhibit` · message parse |
| Internal / silent reasoning | `reason_step` / `chain` — model context only |
| Flexible generalization | One hub concept → broadcast to inject |
| Selectivity | `gate.should_inject` — skip trivial acks |
| Pre-output / broadcast | Desk before speech · `pre_llm` inject |
| Not a chat scratchpad | Silent steps never auto-dumped to user chat |

## API

```python
from hermespace import AccessHub, AccessEngine

js = AccessHub(agent_id="my-agent")
js.hold("France", salience=0.9)
js.reason_step("capital is Paris")
print(js.report())
print(js.broadcast_block())

eng = AccessEngine(agent_id="my-agent")
eng.connect()
```

## With optional warehouse

Optional Cube/standalone warehouse supplies dense arterial strips via
`cube_module.cube_beat` → `AccessHub.sync_from_desk(..., cube_strip=...)`.
On **connect**, `AccessEngine.connect` charges WorldModel and seeds the hub.

Product guide: [34-access-engine.md](34-access-engine.md).

## Research context

Global-workspace and verbalizable-workspace research (including third-party
interpretability work) informs the *roles*. Hermespace's shipped name and API
are **Access Workspace** / **Access Engine**.
