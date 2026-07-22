# For Hermes Agent maintainers & dogfooders

**Repo:** https://github.com/PabloTheThinker/hermespace  
**Companion to:** [NousResearch/hermes-agent](https://github.com/NousResearch/hermes-agent)  
**Not** an official Nous product — independent open companion workspace.

## What this is (30 seconds)

Hermespace adds a **limited working-memory desk** beside Hermes:

1. **Workbench** — FOA, park stack, load-aware `receive_order`
2. **Dual decode** — short human `report` vs dense model `context` (never dump inject to chat)
3. **Fabric** — rank *this* `$HERMES_HOME/skills` + inject MEMORY/USER excerpts
4. **Plugin** — `on_session_start` / `pre_llm_call` / `on_session_end` broadcast when desk ready
5. **Study DB** — turns under `~/.hermespace` (local; not Hermes session DB)

It does **not** replace Hermes tools, skills, memory, gateway, or the agent loop.

## Fast path

```bash
git clone https://github.com/PabloTheThinker/hermespace.git
cd hermespace
./scripts/install_hermes.sh
./scripts/smoke_test.sh    # expect 9/9
```

Then in any agent session:

```python
from hermespace import Workbench
wb = Workbench(agent_id="hermes", session_id="main")
wb.enter()
r = wb.receive_order("…", goal="…", say="…", force=True)
# r["user_reply"] → user   r["model_context"] → model
```

Or CLI: `./scripts/hs turn -m "…" --goal "…" --say "…" --force`

## Design honesty

| Claim | Reality |
|-------|---------|
| “Like Claude J-space” | **Role** only — limited workspace *outside* weights. No activation access. |
| Consciousness / brain scan | **No.** Harness cognition + optional local embeddings. |
| Replaces Hermes skills/memory | **No.** Ranks and injects them. |
| Official Nous module | **No.** Community companion; feedback welcome. |

Inspired by working-memory limits (Baddeley-style capacity, load, GWT broadcast as *metaphors* for agent UX) and Anthropic’s public J-space *research framing* — implemented as open Hermes integration, not a closed-model probe.

## Integration surface

| Door | Entry |
|------|--------|
| Plugin | `hermes_plugin/` → `$HERMES_HOME/plugins/hermespace` |
| Skill | `skills/hermespace/` → `$HERMES_HOME/skills/hermespace` |
| Python | `hermespace.agent_api`, `hermespace.Workbench` |
| CLI | `scripts/hs` |
| Smoke | `scripts/smoke_test.sh` |

Hook implementation lives in `src/hermespace/hermes_bridge.py` (plugin is thin `register`).

When the plugin directory is a **symlink into this checkout**, import auto-resolves `../src` so dogfooders often need no `HERMESPACE_ROOT`.

## Autonomy grid (v0.14)

Missions, lenses, dream, self-talk, skillbench (hot-swap / merge / mutate), title tree.  
Ground-up for Hermespace — not a port of AgentDrive or Conductor.

```bash
hs grid status
hs grid dream --force
```

See docs/18-autonomy-grid.md. Autonomy self-order stays **off** unless `HERMESPACE_AUTONOMY=1`.

## What we want from Hermes dogfood

- Does plugin register cleanly on current Hermes?
- Is dual-decode useful on Telegram/gateway, or noisy?
- Fabric skill ranking quality on real skill trees?
- Gaps vs native Hermes memory / Honcho / skills loop?
- Would you want any of this upstream-shaped (skill only, plugin only, or neither)?

Open issues/PRs on the repo. Thanks for looking.

## License

MIT — see `LICENSE`. Hermes Agent remains Nous Research’s project under its own license.
