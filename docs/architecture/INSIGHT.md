# Hermes Insight × Hermespace — optional perceive cable

**Hermes Insight stays a standalone package.** Hermespace does not vendor it.
When `hermes_insight` is importable, Access Engine appends a **bounded perceive
card** (~400 chars) on material `pre_llm_call` / `AccessEngine.turn`.

```
from hermespace.insight_module import insight_card, insight_status

rec = insight_card("two workers share one token", goal=desk.goal, plan=desk.plan)
# rec["card"] → lever / top rule / usable / action_hint
```

| Rule | Behavior |
|------|----------|
| Missing package | Soft-fail (`mode=missing`) — engine still runs |
| High load | Skip (`skipped=high_load`) |
| Card | lever, top rule, usable, action_hint — never the lattice |
| `insight_plan` | Hot path only when `usable` **and** the goal is multi-step |
| Required? | Never |

Companion: [PabloTheThinker/hermes-insight](https://github.com/PabloTheThinker/hermes-insight)
