# Living assessment — memories → Cube-centered Hermespace

**Date:** 2026-08-03  
**Hermespace:** v0.22.0  
**Companion Cube:** ~0.50 (center 1.2 · heart 1.0 · hive opt-in)  
**Purpose:** Keep the research *memories* (Anthropic J-space, Baars GWT, Dehaene,
Changeux) mapped to what we are building — so each improvement still *means*
those ideas, not a random feature pile.

---

## 0. Verdict (this iteration)

**Cube is already the core.** Hermespace’s job is to be the nervous FOA that
*connects* an arriving Hermes agent into that core so they immediately gain:

1. a charged **World** (beliefs / timeline that grow),
2. a lit **J-Space hub** (privileged verbalizable room),
3. optional **hive peers** (other agents’ soul presence — the room grows).

That is the functional analogue of “joining a J-space that already knows things.”

```
Hermes Agent connects
        │
        ▼
 HermesBase.connect()
        │
        ├─ ensure_heart / center     → Cube library (or standalone warehouse)
        ├─ WorldModel.enter          → growing personal world
        ├─ pulse / sync_world        → Cube wisdom → active beliefs
        ├─ seed J-Space hub          → FOA holds what the library knows
        └─ room_status (hive opt)    → peer agents in the knowledge space
```

---

## 1. Research memories (what we keep representing)

| Memory | Claim we honor | Where it lives now |
|--------|----------------|--------------------|
| **Anthropic J-space** | Tiny privileged verbalizable workspace; read / audit / shape; required for multi-step; skippable for fluency | `jspace/` OEW + `HermesBase` lens/audit/reflect |
| **Not CoT** | Silent intermediates ≠ user chat | dual decode · `reason_step` · mid-band |
| **Baars GWT** | Limited capacity; broadcast to specialists | hub ≤25 · FOA ≤4 · `broadcast_block` |
| **Changeux / ignition** | Material turns must ignite the workspace | `HERMESPACE_OEW=1` · protocol gate |
| **Dehaene gap** | Enduring episodic / library memory Claude lacks | **HermesCube** `memory.cube` via `cube_module` |
| **Collective / lymph** | Many processors / agents share distilled knowledge | Cube **hive** → Hermespace `room_status` |
| **Night** | Sleep consolidates | `dream_harvest` + CubeDream (Cube) |

We do **not** claim Jacobian lens on Hermes weights or phenomenal consciousness.

---

## 2. Cable gaps closed in v0.22

| Gap (v0.21) | Fix |
|-------------|-----|
| `sync_world_beliefs` only inside Cube pulse — Space never named it | `cube_module.sync_world()` |
| No single “agent joined the base” API | `connect_agent()` / `HermesBase.connect()` / `hs base connect` |
| Hive organs documented in Cube, invisible to Space | `room_status()` soft-reads `HERMESCUBE_HIVE` |
| Session start: heart + world + hub fragmented | Bridge runs full connect; context reports gains |
| Workbench enter stopped at ensure+desk sync | Optional warehouse connect seeds hub + room |

Still soft-fail: Cube absent → standalone WorldModel + SemanticStore grow the room.

---

## 3. How Cube organs map into Hermespace

| Cube organ (center 1.2) | Hermespace consumer |
|-------------------------|---------------------|
| heart / arteries / veins | `ensure_heart` · `cube_beat` · `seal_learning` |
| autonomic | `cube_pulse` · workbench `idle_tick` |
| nervous_foa | **owned by Space** — desk / OEW |
| hippocampus / dream | `harvest` → seal; CubeDream on Cube side |
| lymph (hive) | `room_status` · silent peer presence on connect |
| vascular beds (Cuboasis) | future soft surface (not required for connect) |
| blackbox | future `center.flight_*` from Space doctor |

**Rule:** one MemoryProvider = Cube. Space never competes for that socket.

---

## 4. Day-to-day connect ritual

```bash
hs base connect --agent-id my-agent
hs base room
hs base status
hs base lens
hs base think -m "First check then implement finally verify" --goal "Ship fix"
hs base harvest
```

Python:

```python
from hermespace import HermesBase
base = HermesBase(agent_id="my-agent")
print(base.connect()["summary"])
print(base.room())
```

Env for multi-agent growth:

```bash
export HERMESCUBE_HIVE=/path/to/shared/hive   # Cube hive.json root
```

---

## 5. What “more intelligence” means (honest)

On connect, the agent does **not** get new weights. It gets:

- **More durable knowledge in FOA** (Cube strip + world beliefs on the hub)
- **A longer personal timeline** (World archive grows across sessions)
- **Peer awareness** when hive is live (other agents’ soul cards → silent hub)
- **Obligatory higher-order path** on material turns (OEW)

That compounds: seal → Cube → next connect → richer hub. The room grows.

---

## 6. Next living targets (keep memories sharp)

1. Soft Cuboasis chamber strip on connect (vascular beds → FOA themes)
2. Optional pilgrimage hook on session_end (offer → assimilate → draw) — Space triggers, Cube owns
3. Doctor line: `connected · room=hive · peers=N · hub=M`
4. Keep assessments dated in `docs/assessment/` whenever the metaphor drifts

---

## Pointers

- Architecture: [HERMESCUBE.md](../architecture/HERMESCUBE.md)
- Hermes base as J-space: [32-hermes-base-as-jspace.md](../jspace/32-hermes-base-as-jspace.md)
- Prior assessment: [28-hermes-agent-jspace-assessment.md](28-hermes-agent-jspace-assessment.md)
- Code: `hermespace.cube_module.connect_agent` · `hermespace.HermesBase`
