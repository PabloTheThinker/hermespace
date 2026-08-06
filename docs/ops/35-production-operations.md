# Production operations — Hermes Agent v0.20+

Hermespace 0.25 targets the current Hermes plugin host, including CLI,
gateways, A2A sessions, tools, subagents, and finalization.

## Install

Preferred:

```bash
hermes plugins install PabloTheThinker/hermespace --enable
hermes hermespace doctor
```

Checkout development:

```bash
./scripts/install_hermes.sh
python scripts/verify_hermes_integration.py
```

The repository root contains `plugin.yaml` and `__init__.py`, which is the
layout expected by `hermes plugins install owner/repo`. A pip install also
publishes the `hermes_agent.plugins` entry point.

## Native lifecycle

| Hermes v0.20 hook | Hermespace behavior |
|-------------------|----------------------|
| `on_session_start` | Initialize and stage first-turn context |
| `pre_llm_call` | Inject bounded ephemeral user-message context |
| `post_llm_call` | Observe successful response |
| `post_tool_call` | Count tool name only; no args/results |
| `on_session_end` | End one `run_conversation` turn; no harvest |
| `on_session_finalize` | Idempotent final harvest and idle maintenance |
| `on_session_reset` | Prime a rotated gateway session |
| `subagent_start/stop` | Count specialist lifecycle |

The distinction between `on_session_end` and `on_session_finalize` is
important: current Hermes fires `on_session_end` after every turn.

## Session isolation

Hermes session IDs are hashed before entering a path. Active desks and hubs are
stored under separate session scopes:

```text
$HERMESPACE_HOME/memory/hermespace/
  sessions/<agent>--<hash>/ACTIVE.md
  access/<agent>--<hash>.json
  runtime/<session-hash>.json
```

Runtime snapshots contain counts, lengths, model/platform labels, and tool
names. They never contain prompts, tool arguments, or tool results.

## Health

Terminal:

```bash
hermes hermespace status
hermes hermespace runtime
hermes hermespace doctor
hermespace ops doctor
```

Inside Hermes:

```text
/hermespace status
/hermespace metrics
/hermespace runtime
/hermespace lens
```

`ops doctor` reports `ok` for local engine health and `integration_ok` for the
native Hermes plugin door.

## Latency posture

The native `pre_llm_call` path defaults to cached/hash-only enrichment and
does not run the full doctor or viewport generator. Set
`HERMESPACE_SKIP_NEURAL=0` only when synchronous neural enrichment is known to
meet your platform latency budget.

## Failure behavior

- Plugin registration fails visibly if the runtime cannot import.
- Optional hooks are skipped only on older Hermes hosts; the required
  start/pre-LLM/end hooks must register.
- State writes use atomic same-filesystem replacement.
- Corrupt desk JSON sidecars fall back to human-readable `ACTIVE.md`.
- Finalization is idempotent when CLI and gateway teardown paths converge.

## Release verification

```bash
python -m pip install .
python -m unittest discover -s tests -v
python scripts/verify_hermes_integration.py
./scripts/security_audit.sh
./scripts/smoke_test.sh
./scripts/e2e_ops.sh
python -m build
```
