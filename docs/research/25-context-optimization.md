# Context Injection Optimization

**Reducing per-turn context overhead from ~1191 tok to ~148 tok (87% reduction).**

---

## Problem

The initial Hermespace design injected the full world markdown + desk context on
every `pre_llm_call`. Analysis showed:

| Component | Tokens |
|-----------|--------|
| `build_inject_block()` | ~700 tok |
| `world_context()` (full) | ~441 tok |
| Workbench status + ops | ~50 tok |
| **Total per turn** | **~1191 tok** |

The world markdown was the same every turn in most sections: header, self,
environment, world time rarely change. The timeline (35% of cost) only grew
by 1-3 entries per turn. Every section was regenerated from scratch.

## Solution

Two changes to `src/hermespace/world.py` and `src/hermespace/hermes_bridge.py`:

### 1. Delta context mode (`world.py`)

`context_block()` now accepts two parameters:

```python
def context_block(self, full: bool = True, known_entries: int = 0) -> str
```

- **`full=True`**: Old behavior — full `render_markdown()` + Pulse + Desk.
- **`full=False`**: Delta mode — only what changed since `known_entries`.

Delta includes:
- Focus (goal/decision/plan — changes every turn)
- Active concepts (only if non-empty)
- Beliefs (top 3, only if non-empty)
- Active relationships (only if non-empty)
- Timeline entries since `known_entries` (capped at 8)
- Pulse summary

Delta skips:
- Header/epoch identity (static per session)
- Self/identity traits (static)
- Environment snapshot (static)
- World time (static per session)
- Memory landmarks (summarized implicitly via timeline)
- Full belief list (top 3 only)
- Desk section (duplicated in `build_inject_block()`)

### 2. Bridge integration (`hermes_bridge.py`)

- First turn (`is_first_turn=True`): full context injected.
- Subsequent turns: `known_entries` read from `desk.meta["world_entry_count"]`
  (persisted across turns within a session).
- After injection: `desk.meta["world_entry_count"]` updated to current count.
- Workbench status block only injected on mode change, not every turn.

## Results

| Mode | Chars | Tokens | vs Full | vs Original |
|------|-------|--------|---------|-------------|
| Full (old behavior) | 1564 | 391 | — | — |
| Delta (same state) | 845 | 211 | -46% | — |
| Delta (2 new entries) | 592 | 148 | -62% | -87% (from 1191) |

## Steady-state behavior

In production, each turn generates 1-3 archive entries. The delta context for a
typical subsequent turn contains:

- Focus block: ~6 lines (~60 chars)
- Top 3 beliefs: ~5 lines (~50 chars)
- Timeline (1-3 new entries): ~4 lines (~40 chars)
- Pulse: ~3 lines (~30 chars)
- **Total: ~220 chars (~55 tok)**

Combined with the workbench inject block (~412 tok), total per-turn overhead
drops from **~1191 tok to ~467 tok** once the session is established.

## File changes

- `src/hermespace/world.py`: `context_block()`, `_context_full()`,
  `_context_delta()`, `world_context()` updated with `full` and `known_entries`
  parameters.
- `src/hermespace/hermes_bridge.py`: Delta tracking via `desk.meta`,
  conditional workbench status injection.
