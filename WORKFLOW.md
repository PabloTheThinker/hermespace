# Hermespace WORKFLOW — how everything works together

## Agent I/O

See **docs/09-agent-io-and-memory.md**.

- **INPUT** = `HermespaceInput` / `hs turn -m ...`
- **OUTPUT** = `report` (to user) + `context` (to model)
- **Memory** = `hermespace.db` + `journal/*.md` under `$HERMESPACE_HOME/memory/hermespace/`

## One system

```
User message
    │
    ▼
┌─────────────┐
│ 1 GATE      │  trivial? skip · material? continue
└──────┬──────┘
       ▼
┌─────────────┐
│ 2 ENCODE    │  multi-stream features + optional continuity cues
└──────┬──────┘
       ▼
┌─────────────┐
│ 3 DESK      │  FOA≤4 · load · executive · bind · capacity 12
└──────┬──────┘
       ▼
┌─────────────┐
│ 4 PLAN      │  choices → decision → plan steps
└──────┬──────┘
       ▼
┌─────────────┐
│ 5 DECODE    │  workspace → Report (say)
└──────┬──────┘
       ▼
┌─────────────┐
│ 6 BROADCAST │  inject block → Hermes pre_llm / agent context
└──────┬──────┘
       ▼
┌─────────────┐
│ 7 ACT       │  tools / code / ship (outside desk)
└──────┬──────┘
       ▼
┌─────────────┐
│ 8 SEAL      │  optional episodic + semantic promote
└─────────────┘
```

## Module map

| Piece | Role | Path |
|-------|------|------|
| Workflow | Turn spine | `src/hermespace/workflow.py` · `hs turn` |
| Engine | enter/update/seal | `engine.py` |
| Desk | limited WM state | `desk.py` + `$HERMESPACE_HOME/memory/hermespace/ACTIVE.md` |
| Cognition | Baddeley/GWT/load | `cognition.py` |
| Streams | multi-stream encode/decode | `streams.py` |
| Gate | selectivity | `gate.py` |
| Inject | broadcast text | `inject.py` |
| Memory | episodic + semantic | `episodic.py` `semantic.py` |
| Hermes plugin | auto step 6 | `hermes_plugin/` |

## Operator turn

1. Match user compression / hold context (your agent persona).  
2. `hs turn -m "..." --goal ... --decision ... --say ... --plan ...`  
3. Use inject in context (plugin may already broadcast).  
4. Speak from **Report**.  
5. Execute tools.  
6. `hs seal` when the decision is durable.  

## CLI

```bash
./scripts/hs turn -m "build X" --goal "Build X" --decision "A" --say "Building X." --plan "1"
./scripts/hs status
./scripts/hs show
./scripts/hs inject
./scripts/hs seal --note "shipped"
./scripts/hs consolidate
./scripts/hs eval
```

## Hermes

```bash
# from checkout
ln -sfn "$PWD/hermes_plugin" "${HERMES_HOME:-$HOME/.hermes}/plugins/hermespace"
export HERMESPACE_ROOT="$PWD"
hermes plugins enable hermespace
```

Plugin only **broadcasts** a ready desk; it does not invent goals.

## Done checklist

- [ ] Desk ready before multi-step work  
- [ ] Inject non-empty on material turns  
- [ ] Report matches load  
- [ ] Seal real decisions  
- [ ] `hs eval` passes  

## Anti-patterns

- Docs-only process with no `hs turn`  
- Entering desk on every “ok”  
- Claiming brain-scan capabilities  
