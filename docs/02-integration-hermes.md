# Hermes integration

## Plugin

`hermes_plugin/` → `$HERMES_HOME/plugins/hermespace`  
Hook: `pre_llm_call` returns `{"context": "..."}` into the **user message** (Hermes contract; preserves system-prompt cache).

```bash
export HERMESPACE_ROOT=/path/to/hermespace
export HERMESPACE_HOME=$HOME/.hermespace
ln -sfn "$HERMESPACE_ROOT/hermes_plugin" "$HERMES_HOME/plugins/hermespace"
hermes plugins enable hermespace
```

## Skill (optional)

Agent skill: install `skills/hermespace/` into `$HERMES_HOME/skills/hermespace`.  
Load skill `hermespace` on material turns; prefer `hs turn` / Workbench `receive_order`.

## State

Live desk is **not** committed to git. It lives under `HERMESPACE_HOME`.
