# From Anthropic J-space → Hermespace (functional)

Anthropic **J-space** (2026, Jacobian lens): a small privileged set of
*verbalizable* internal representations that behave like a **global workspace**
(Baars / Dehaene GWT): reportable, modulable, used for silent multi-step
reasoning, flexibly broadcast, and **selective** (most LM work is automatic).

Hermespace implements these **roles as a harness** — files + API — not neural
access, not a claim of consciousness.

| J-space property | Hermespace |
|------------------|------------|
| Limited capacity (~tens of concepts) | Hub ≤25 · activated ≤12 · FOA ≤4 |
| Verbal report | `JSpace.report()` · Report field · `hs jspace report` |
| Directed modulation | `hold` / `release` / `inhibit` · message parse |
| Internal / silent reasoning | `reason_step` — model context only |
| Flexible generalization | One hub concept → broadcast to inject |
| Selectivity | `gate.should_inject` — skip trivial acks |
| Pre-output / broadcast | Desk before speech · `pre_llm` inject |
| Not CoT scratchpad | Silent steps never auto-dumped to user chat |

## API

```python
from hermespace import JSpace

js = JSpace(agent_id="my-agent")
js.hold("France", salience=0.9)          # directed modulation
js.reason_step("capital is Paris")       # silent intermediate
print(js.report())                       # verbal report
print(js.broadcast_block())              # GWT strip for model
js.sync_from_desk(desk, user_message=msg, cube_strip=arterial)
```

## With Cube

Cube supplies **arterial blood** (dense durable strip) into the hub via
`cube_module.cube_beat` → `JSpace.sync_from_desk(..., cube_strip=...)`.
On **connect**, `connect_agent` / `HermesBase.connect` also charges WorldModel
from Cube wisdom and seeds the hub — optional hive peers appear as silent
presence (`HERMESCUBE_HIVE`). Space still owns FOA competition and dual decode.

Living map of these research memories:
[33-living-memories-cube-world.md](../assessment/33-living-memories-cube-world.md).

**Product surface (v0.23+):** [`JSpaceEngine`](34-jspace-engine.md) — one engine for
connect / turn / lens / chain / harvest. Warehouse optional.

## Sources

- https://www.anthropic.com/research/global-workspace  
- Transformer Circuits: *Verbalizable Representations Form a Global Workspace* (2026)  
- See also [10-jspace-claude.md](10-jspace-claude.md)
