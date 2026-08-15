# PURPOSE.md — Hermespace north star

## One line

**Hermespace is the production Access Engine for Hermes Agent: a local,
session-safe workspace that turns goals, evidence, tool activity, and silent
intermediates into bounded context before a turn and durable continuity after
it.**

It is not another agent, model provider, or memory-provider competitor.
Hermes remains the actor. Hermespace is the room in which Hermes keeps the
current problem coherent.

**Front door.** Install Space and the agent gets a better turn: desk plus
optional Cube library and Insight pattern card as organs, one unioned
`plugins.enabled`. Cube and Insight stay standalone. Space never claims
weight access. Context is progressive: one inject, mid ≤2.8k, high/protect
≤900. After a material turn the hub keeps a bounded self-trace (last goal,
decision, `tool:name` list, sealed Report line) so the desk can improve.
Product language is self-model / self-trace / improve — never “true
self-conscious,” never a phenomenal-consciousness claim.

---

## Why it exists

An agent can be fluent while losing the thread: goals drift, tool evidence is
forgotten, several sessions overwrite one another, and the final answer exposes
less than the process needed to produce it. A durable archive alone does not
solve this; the agent needs a small, causal working set for the current turn.

Hermespace provides that working set:

- **AccessHub** — limited active concepts (hub ≤25, focus ≤4)
- **OEW** — material work must park at least one useful intermediate
- **dual decode** — dense model context stays separate from the user report
- **operator access** — lens, hold, swap, inject, ablate, reflect, audit
- **session continuity** — WorldModel, workbench, episodic receipts, runtime facts
- **native Hermes lifecycle** — CLI, gateways, A2A, tools, subagents, teardown

```
user / gateway / A2A
          │
          ▼
      Hermes Agent
   tools · skills · model
          │
          ▼
  Hermespace Access Engine
  ├─ per-session desk + AccessHub
  ├─ OEW gate + bounded broadcast
  ├─ runtime/tool/subagent receipts
  ├─ short Report / dense model context
  └─ persistent WorldModel + optional warehouse
```

---

## Operating contract

### Before a model turn

`pre_llm_call` receives the original user message. Hermespace:

1. decides whether the turn is material,
2. restores that session's desk and hub,
3. selects a bounded focus,
4. parks silent multi-step intermediates when required,
5. injects ephemeral context into the **user message only**.

The system prompt remains untouched, preserving Hermes prompt-cache behavior.

### During a turn

Hermes tools, skills, and subagents remain the specialist processors.
Hermespace records bounded operational facts (tool names and counts, never
arguments/results) and keeps the active workspace available to every downstream
step.

### After a turn

`post_llm_call` records the completed report and closes the native turn.
`on_session_end` is treated as a **turn boundary**, matching Hermes v0.20.
Only `on_session_finalize` performs final harvest and idle maintenance.

### Across concurrent sessions

Opaque Hermes session IDs are hashed into independent desk/hub paths. A gateway
user, A2A peer, or subagent cannot inherit another session's silent workspace.
World identity may remain agent-scoped; active cognition is session-scoped.

---

## Authority and boundaries

| Layer | Authority |
|-------|-----------|
| AccessHub / OEW | Active turn concepts, silent intermediates, modulation |
| Session desk | Goal, decision, plan, report, structured turn metadata |
| Workbench | Session mode, parked goals, last native turn |
| WorldModel | Agent-scoped beliefs, landmarks, timeline |
| Hermes Agent | Model calls, tools, skills, approvals, transcript |
| Optional Cube book | Durable long-tail SoT when `hermescube` is installed. If Hermes `memory.provider=hermescube`, skip the `pre_llm` FOA strip — MemoryManager already prefetched. |
| Optional Insight | `perceive_card` strip next to `cube_beat` on `pre_llm_call` when installed |

Cube and Insight stay standalone packages. Hermespace only **cables** them
via fail-soft imports (`cube_module`, `insight_module`). Neither is required.

Hermespace does **not**:

- replace Hermes's `MemoryProvider`,
- replace Hermes's context compressor,
- mutate the persisted Hermes conversation,
- inject into the system prompt,
- persist tool arguments, tool results, or secret-bearing prompt text in
  runtime telemetry,
- claim weight-level interpretability or consciousness.

---

## Hermes Agent compatibility target

Primary target: **Hermes Agent v0.20.0+**.

Hermespace uses the current public plugin contracts:

- `on_session_start`
- `pre_llm_call`
- `post_llm_call`
- `pre_tool_call` / `post_tool_call`
- `on_skill_lifecycle`
- `kanban_task_claimed` / `kanban_task_completed`
- `pre_verify`
- `on_session_end`
- `on_session_finalize` (harvest ≤10s, fail-open)
- `on_session_reset`
- `subagent_start` / `subagent_stop`
- `/hermespace` slash command
- `hermes hermespace` CLI command

New Hermes capabilities should be adopted only when they strengthen the Access
Engine without taking ownership from Hermes. In particular, Hermespace does not
register an exclusive context engine merely to observe turns; current
`pre_llm_call` and `post_llm_call` hooks already provide the correct seams.

---

## Quality bar

Hermespace should be held to the same engineering standard as Hermes Agent:

1. **Installable** — clean `pip install .` declares all runtime dependencies.
2. **Native** — `hermes plugins install PabloTheThinker/hermespace --enable`
   installs a working root plugin.
3. **Fail-visible** — a missing runtime fails registration; it never becomes an
   enabled no-op.
4. **Session-safe** — active desks and hubs are isolated by session.
5. **Crash-safe** — critical state writes use atomic replace.
6. **Bounded** — context, hub, silent chain, telemetry, and session registry have
   explicit caps.
7. **Private by default** — runtime metrics store lengths/names, not payloads.
8. **Cache-safe** — plugin context is ephemeral user-message context.
9. **Observable** — `/hermespace runtime`, `hermes hermespace doctor`, and
   `hermespace ops doctor` explain current health.
10. **Proven** — clean-wheel tests, current Hermes host-contract tests, unit
    tests, smoke, operational E2E, and security audit run in CI.

---

## Acceptance tests

The project is operational only when all of these pass:

```bash
python -m pip install .
python -m unittest discover -s tests -v
python scripts/verify_hermes_integration.py
./scripts/security_audit.sh
./scripts/smoke_test.sh
./scripts/e2e_ops.sh
python -m build
```

And on a Hermes installation:

```bash
hermes plugins install PabloTheThinker/hermespace --enable
hermes hermespace doctor
# inside a session
/hermespace status
```

---

## Product direction

Deepen the **Access Engine**, not the feature count.

Prefer changes that make the current turn more coherent, causal, bounded,
private, and observable. Reject changes that create a second agent framework,
duplicate Hermes ownership, or add ceremony without improving an executable
contract.

Architecture: [docs/architecture/CODEMAP.md](docs/architecture/CODEMAP.md)
Operations: [docs/ops/35-production-operations.md](docs/ops/35-production-operations.md)
Access Engine: [docs/access/34-access-engine.md](docs/access/34-access-engine.md)
