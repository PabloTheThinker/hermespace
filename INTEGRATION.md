# INTEGRATION — doors for any Hermes agent

## Install (once)

```bash
git clone https://github.com/PabloTheThinker/hermespace.git
cd hermespace
export HERMESPACE_ROOT="$PWD"
export HERMESPACE_HOME="${HERMESPACE_HOME:-$HOME/.hermespace}"
export HERMES_HOME="${HERMES_HOME:-$HOME/.hermes}"
export PYTHONPATH="$PWD/src${PYTHONPATH:+:$PYTHONPATH}"
# optional: pip install -e .

# Public Hermes skill (broad operator skill for any agent)
mkdir -p "$HERMES_HOME/skills/hermespace"
cp -a skills/hermespace/. "$HERMES_HOME/skills/hermespace/"
# or: ln -sfn "$HERMESPACE_ROOT/skills/hermespace" "$HERMES_HOME/skills/hermespace"

# Hermes plugin broadcast
ln -sfn "$HERMESPACE_ROOT/hermes_plugin" "$HERMES_HOME/plugins/hermespace"
hermes plugins enable hermespace
```

Agent skill SoT: [`skills/hermespace/SKILL.md`](skills/hermespace/SKILL.md).  
Recommended env: see `docs/RECOMMENDED.md`.

## Door A — Python (best for agents)

```python
from hermespace.agent_api import (
    encode_message,
    run_turn,
    decode_for_user,
    decode_for_model,
    decode_bundle,
    study_memory,
)

inp = encode_message(
    user_text,
    goal="...",              # optional
    decision="A — ...",      # optional
    plan=["step1", "step2"],
    say="What I'll tell the user.",
    session_id=session_id,
    agent_id="my-hermes-agent",
    force=True,              # multi-step jobs
)
out = run_turn(inp)

# OUTPUT channels
send_to_user(decode_for_user(out))      # human
model_context = decode_for_model(out)   # next completion / tools
meta = decode_bundle(out)               # neural, memory_id, plan, ...

# Later
study_memory("auth timeout")
```

One-shot:

```python
from hermespace.agent_api import quick_reply
bundle = quick_reply(user_text, session_id=sid, agent_id="my-agent")
send_to_user(bundle["user_reply"])
```

## Door B — CLI

```bash
./scripts/hs turn -m "$USER_TEXT" \
  --goal "..." --decision "A" --say "..." \
  --plan "1" --session-id "$SID" --agent-id my-agent \
  --force --output report          # user channel only

./scripts/hs turn ... --output context   # model channel
./scripts/hs turn ... --json             # full OUTPUT envelope
./scripts/hs history --session-id "$SID"
./scripts/hs study "keyword"
```

## Door C — Hermes plugin (broadcast)

After a turn has made the desk **ready**, `pre_llm_call` injects `context` on material messages.  
Plugin does **not** create INPUT — agents still call Door A/B first.

## Door D — Smoke / health

```bash
./scripts/smoke_test.sh
# artifacts under $HERMESPACE_HOME/smoke_results/
```

## Decode rules (do not skip)

| Output field | Goes to |
|--------------|---------|
| `report` / `decode_for_user` | Human user |
| `context` / `decode_for_model` | Model only (not raw chat dump) |
| `memory_id` | Study / audit |

## State locations

```
$HERMESPACE_HOME/memory/hermespace/
  ACTIVE.md           live desk
  hermespace.db       turn DB
  journal/*.md        human journal
  neural_attractors.json
```

## Door E — Workbench (pocket dimension)

```python
from hermespace import Workbench
wb = Workbench(agent_id="my-agent", session_id="main")
wb.enter()
wb.idle_tick()  # while waiting
result = wb.receive_order("Do the thing", goal="Do the thing", say="On it.", force=True)
send_user(result["user_reply"])
```

See docs/14-workbench-pocket-dimension.md.

## Hermes framework hooks (v0.12)

Plugin registers:
- `on_session_start` — workbench enter + env kit context
- `pre_llm_call` — desk + neural broadcast + workbench footer
- `on_session_end` — idle_tick

Why: docs/16-why-hermes-framework.md

## Skills & memory (every user)

Hermespace pulls **this install's** Hermes skills + MEMORY/USER into the workbench inject.

```python
from hermespace.agent_api import rank_skills, fabric_snapshot, remember_learning, run_turn, encode_message
rank_skills("telegram gateway")
fabric_snapshot(goal="...", message="...")
# learnings stay in Hermespace DB — Hermes MEMORY.md still via Hermes memory tool
remember_learning("Prefer plain Telegram", goal="messaging")
```

See docs/17-skills-memory-bridge.md.
