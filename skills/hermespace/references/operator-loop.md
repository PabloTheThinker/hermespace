# Operator loop cheat sheet

Env: `HERMESPACE_ROOT`, `HERMESPACE_HOME`, `HERMES_HOME`, `PYTHONPATH=$HERMESPACE_ROOT/src`.  
`hs` = `./scripts/hs` from checkout.

## Status / health
```bash
hs status | show | ready | inject | say
hs neural caps
./scripts/smoke_test.sh    # 9/9
```

## Material turn
```bash
hs turn -m "$USER" --goal "G" --decision "A — …" --say "…" \
  --plan "p1" --plan "p2" --force --json
```

```python
from hermespace.agent_api import (
    encode_message, run_turn, decode_for_user, decode_for_model, decode_bundle,
)
out = run_turn(encode_message(
    text, goal="G", decision="A", plan=["p1"], say="…",
    session_id=sid, agent_id="my-agent", force=True,
))
user = decode_for_user(out)
ctx = decode_for_model(out)
meta = decode_bundle(out)  # includes fabric
```

## Workbench
```python
from hermespace import Workbench
wb = Workbench(agent_id="my-agent", session_id="main")
wb.enter(); wb.idle_tick(); wb.park_goal("later")
r = wb.receive_order(text, goal="G", say="…", force=True)
# r["user_reply"], r["model_context"], r["bundle"]
```

```bash
hs workbench enter|status|idle|env|park|order|pop
```

## Fabric / study
```bash
hs fabric --goal "…"
hs skills --goal "…"
hs history --session-id main
hs study "keyword"
hs seal --note "…"
hs consolidate
```

## Plugin
```bash
ln -sfn "$HERMESPACE_ROOT/hermes_plugin" "$HERMES_HOME/plugins/hermespace"
hermes plugins enable hermespace
```

## Dual decode
- report → human  
- context → model only  
- fabric in bundle → agent meta  
- never dump full inject to user channels  
