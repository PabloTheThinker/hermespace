# Hermespace as workbench / pocket dimension

## The idea

Hermespace is not a cloud J-space microscope.  
It is the **internal room** a Hermes agent works in:

- While **idle** — maintain memory, neural attractors, park secondary goals  
- When an **order** arrives — run encode → desk/neural → decode user + model  
- Between jobs — monotropic FOA; park the rest instead of thrashing  

Same spirit as Conductor’s old “pocket dimension,” named and built as **Hermespace**.

```
              ┌──────────────── Hermespace ────────────────┐
 orders ──►   │  Workbench (per agent_id + session)         │
              │    park stack · mode idle/working           │
              │    desk FOA · neural field · memory DB      │
 idle tick ─► │    consolidate · attractors · no user spam  │
              │                                             │
              │  OUT: user_reply | model_context            │
              └─────────────────────────────────────────────┘
```

## API

```python
from hermespace.workbench import Workbench

wb = Workbench(agent_id="ilo", session_id="main")
wb.enter()                          # into the pocket dimension
wb.park_goal("Later: write docs")   # monotropic park
wb.idle_tick()                      # while waiting

result = wb.receive_order(
    "Fix auth timeout now",
    goal="Fix auth timeout",
    decision="A — patch TTL",
    plan=["repro", "patch", "verify"],
    say="Patching session TTL.",
)
send_user(result["user_reply"])
model_ctx = result["model_context"]
```

CLI:

```bash
hs workbench enter --agent-id ilo
hs workbench park --goal "Later: docs"
hs workbench idle
hs workbench order -m "Fix auth" --goal "Fix auth" --say "On it." --force
hs workbench status --agent-id ilo
```

## Idle vs order

| Phase | Behavior |
|-------|----------|
| **Idle tick** | No user message. Consolidate memory, refresh neural attractors, hold park stack. Log-only. |
| **Order** | User/system command. Full Hermespace turn. Dual decode. Then back to idle. |

## Why this fits Hermes

- Hermes agents already live between messages (gateway, cron, tools).  
- Hermespace gives that gap a **place to work** without inventing chat noise.  
- Plugin still only **broadcasts** a ready desk on the next LLM call.  
- J-space remains “inside Claude”; Hermespace remains “workbench outside the model.”

## Non-goals

- Simulated consciousness theater  
- Replacing Hermes session DB entirely  
- Running heavy GPU jobs every idle tick  
