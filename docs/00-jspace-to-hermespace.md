# From Anthropic J-space → Hermespace

Anthropic **J-space** (2026 interpretability): limited, reportable, modulable internal workspace supporting deliberate reasoning — not the same as written chain-of-thought.

| J-space property | Hermespace design |
|------------------|-------------------|
| Limited capacity | FOA≤4 + activated ≤12 |
| Reportable | Required **Report** field |
| Modulable | `enter` / recompute from user message |
| Pre-output | Desk before speech; `pre_llm` inject |
| Selective | `gate.should_inject` |
| Not neural access | Files + API — honest harness layer |

Offline-capable. No vendor API required for the workspace itself.
