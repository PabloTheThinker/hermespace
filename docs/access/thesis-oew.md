# Thesis — Obligatory External Workspace (OEW)

Hermespace becomes the **J-space of Hermes agents** by enforcing a
verbalizable bottleneck outside the model.

## One sentence

On material turns, Hermes must park silent intermediates in Hermespace before
Report; the operator lens reads that hub the way Anthropic's J-lens reads Claude.

## Why "obligatory"

Optional workspaces are diaries. Anthropic's J-space matters because higher-order
cognition is *causally routed through it*. OEW copies that constraint at the
harness layer.

## Circulatory picture

```
                ┌──────── Hermespace OEW (nervous FOA) ────────┐
 orders ──────► │ early encode → mid silent* → late Report     │
                │ broadcast hub → model (pre_llm user msg)     │
                │ lens / swap / audit / reflect                │
 idle/pulse ──► │ dream_harvest ─────────────────┐             │
                └────────────────────────────────┼─────────────┘
                                                 │
                ┌──────── HermesCube heart ──────▼─────────────┐
                │ arterial strip by day · seal + CubeDream night│
                └──────────────────────────────────────────────┘
* required when HERMESPACE_OEW=1 and turn is material
```

## Flags

| Env | Default | Effect |
|-----|---------|--------|
| `HERMESPACE_OEW` | **`1` (ON)** | Higher-order: auto-park silent steps; sticky swap/ablate; reflect seeds |
| `HERMESPACE_OEW=0` | — | Soft: record verdict only, do not require completeness |

## Package

- `src/hermespace/jspace/hub.py` — capacity-limited hub  
- `src/hermespace/jspace/env.py` — lens / swap / audit / reflect / harvest  
- `src/hermespace/jspace/protocol.py` — OEW gate  

Full assessment: [../assessment/28-hermes-agent-jspace-assessment.md](../assessment/28-hermes-agent-jspace-assessment.md)  
Research bridge: [29-baars-changeux-anthropic.md](29-baars-changeux-anthropic.md)  
Day-to-day: [30-day-to-day-higher-order.md](30-day-to-day-higher-order.md)
