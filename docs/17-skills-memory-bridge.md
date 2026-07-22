# Hermes skills + memory inside Hermespace

## Goal

Whoever the user is, their Hermes agent must still use:

- **Their skills** (`~/.hermes/skills/**/SKILL.md`)  
- **What they remember** (`MEMORY.md`, `USER.md`)  
- **What they learn** (Hermes memory tool + Hermespace study DB)

Hermespace does **not** replace Hermes memory/skills.  
It **pulls them into the pocket dimension** so FOA + inject make the agent *use* them.

## How it works

| Source | Hermespace action |
|--------|-------------------|
| Skills catalog | Embed-rank vs goal/message → top hits in inject + desk `skill_hint:*` |
| MEMORY.md | Bounded excerpt into model context |
| USER.md | Bounded excerpt (prefs/style) into model context |
| New learning | `remember_learning(...)` → Hermespace DB/journal (opt-in seal); Hermes MEMORY still via Hermes `memory` tool |

## Agent guidance (in inject)

```
### Hermes fabric (your skills & memory — use them)
**Ranked skills for this goal:**
- `some-skill` (score=0.72)
  _description blurb_
**USER.md (excerpt):** ...
**MEMORY.md (excerpt):** ...
_Load full skills via Hermes skill_view(name=...) when a hit matches._
```

## API

```python
from hermespace.agent_api import (
    encode_message, run_turn, decode_for_user, decode_for_model,
    rank_skills, fabric_snapshot, remember_learning,
)

# automatic on every run_turn:
out = run_turn(encode_message(user_text, goal="...", force=True))
# out.meta["fabric"] has skill_hits + memory excerpts
# out.context includes fabric block

# explicit:
rank_skills("fix telegram gateway")
fabric_snapshot(goal="...", message="...")
remember_learning("Prefer plain Telegram formatting", goal="messaging")
```

CLI:

```bash
hs fabric --goal "fix auth" --message "session timeout"
hs skills --goal "telegram email"
```

## Privacy

- Runtime only — **never commit** user MEMORY/USER into the Hermespace git repo  
- Excerpts are capped (token hygiene, Hermes-style)  
- Secrets in MEMORY stay the operator’s responsibility (same as Hermes)

## Division of labor

| System | Owns |
|--------|------|
| Hermes `memory` tool / MEMORY.md | Durable operator facts (char budget) |
| Hermes skills / skill_manage | Procedures |
| Hermespace fabric bridge | Rank + inject into this turn’s workbench |
| Hermespace memory DB | Studyable turn history + optional learnings |
