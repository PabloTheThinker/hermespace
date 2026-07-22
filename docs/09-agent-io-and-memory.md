# Agent I/O — how any Hermes agent uses Hermespace

## Picture

```
┌──────────────┐     INPUT      ┌─────────────┐     OUTPUT      ┌──────────────┐
│ Hermes agent │ ─────────────► │ Hermespace  │ ─────────────► │ Reply to user│
│ (+ user msg) │  message/goal  │  workflow   │  report+context│              │
└──────────────┘                └──────┬──────┘                └──────────────┘
                                       │
                                       ▼
                               Memory DB + journal
                          (study previous turns later)
```

## INPUT (`HermespaceInput`)

| Field | Required | Meaning |
|-------|----------|---------|
| `message` | yes | What the user said / task text |
| `goal` | recommended | Workspace goal (defaults to message head) |
| `decision` | optional | Chosen path (default `A — proceed`) |
| `plan` | optional | Steps |
| `say` / report draft | optional | If empty, decode may draft |
| `session_id` | optional | Groups memory |
| `agent_id` | optional | Which agent |
| `force` | optional | Enter even if message looks trivial |
| `seal` | optional | Seal after turn |

### CLI input example

```bash
./scripts/hs input --example
./scripts/hs turn -m "Fix login timeout" \
  --goal "Fix login timeout" \
  --decision "A — patch session TTL" \
  --say "I'll extend session TTL and retest login." \
  --plan "repro" --plan "patch" --plan "test" \
  --session-id "sess-42" \
  --agent-id "my-hermes" \
  --json
```

### Python input

```python
from hermespace import Workflow, HermespaceInput

out = Workflow().run(HermespaceInput(
    message="Fix login timeout",
    goal="Fix login timeout",
    decision="A — patch session TTL",
    plan=["repro", "patch", "test"],
    say="I'll extend session TTL and retest login.",
    session_id="sess-42",
    agent_id="my-hermes",
    force=True,
))
```

## OUTPUT (`HermespaceOutput`)

| Field | Use |
|-------|-----|
| **`report`** | **Say this to the user** (primary) |
| **`context`** | Inject into model context / pre_llm (do not dump raw to user) |
| `decision` / `plan` | What the desk committed to |
| `ready` | Desk complete enough to act |
| `memory_id` | Row id in study DB |
| `memory_path` | Path to `hermespace.db` |
| `skipped` | Gate skipped turn |

### Agent reply rule

```text
if not output.skipped:
    send_to_user(output.report)      # OUTPUT → user
    keep_in_context(output.context)  # for next tool/LLM step
```

CLI:

```bash
./scripts/hs turn -m "..." --goal "..." --output report   # user text only
./scripts/hs turn -m "..." --goal "..." --output context  # inject only
./scripts/hs turn -m "..." --goal "..." --json            # full envelope
```

## Memory database (study previous Hermespace)

Created automatically under `$HERMESPACE_HOME/memory/hermespace/`:

| Path | What |
|------|------|
| `hermespace.db` | SQLite turns (input + output) |
| `journal/YYYY-MM-DD.md` | Human-readable daily log |
| `ACTIVE.md` | Live desk |

```bash
./scripts/hs memory-paths
./scripts/hs history --session-id sess-42 --limit 20
./scripts/hs study "login" --limit 10
./scripts/hs output --session-id sess-42 --field report
```

Python:

```python
wf = Workflow()
wf.history(session_id="sess-42", limit=20)
wf.study("login")
```

## Hermes plugin role

`pre_llm_call` **broadcasts** `context` when a desk is already ready.  
It does **not** replace INPUT. Agents should still `turn`/`run` to create INPUT and memory rows.

## Minimal agent loop

1. Build **INPUT** from user message  
2. `out = Workflow().run(input)`  
3. Reply with **`out.report`**  
4. Use tools guided by **`out.plan`** / desk  
5. Later: `study` / `history` to recall prior Hermespace work  
