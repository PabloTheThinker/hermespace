# Hermes Insight × Hermespace — optional perceive_card cable

**Hermes Insight stays a standalone package.** Hermespace does not vendor it
and does not register Insight hooks. The cable is a thin
`hermespace.insight_module` adapter hung **next to `cube_beat`** on
`pre_llm_call` (not inside `AccessEngine.turn`).

```
from hermes_insight import HermesInsight
if hasattr(HermesInsight, "perceive_card"):
    card = HermesInsight().perceive_card(goal, load=...)
```

| Rule | Behavior |
|------|----------|
| Feature-detect | `from hermes_insight import HermesInsight` and `hasattr(..., "perceive_card")` |
| Missing / no `perceive_card` | Skip — do **not** format `perceive()["card"]` (unbounded lattice) |
| High / protect load | Skip entirely (stricter than Cube) |
| Hot path | Append only the returned card, capped at 400 chars |
| `insight_plan` / `.plan` | Never on `pre_llm_call` |
| Required? | Never — `except Exception: pass` like `cube_beat` |

Companion: [PabloTheThinker/hermes-insight](https://github.com/PabloTheThinker/hermes-insight)
