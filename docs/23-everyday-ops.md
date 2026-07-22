# Everyday Hermespace ops (any user / agent)

Host-agnostic. Package SoT. State in `$HERMESPACE_HOME` (default `~/.hermespace`).

## One-time install

```bash
cd "${HERMESPACE_ROOT:-$HOME/projects/hermespace}"
./scripts/install_hermes.sh          # skill + Hermes plugin
./scripts/install_desktop_plugin.sh  # Desktop hard-copy plugin
hermes plugins enable hermespace
```

Env (shell or Desktop):

```bash
export HERMESPACE_ROOT=…/hermespace
export HERMESPACE_HOME="${HERMESPACE_HOME:-$HOME/.hermespace}"
export HERMES_HOME="${HERMES_HOME:-$HOME/.hermes}"
export PYTHONPATH="$HERMESPACE_ROOT/src${PYTHONPATH:+:$PYTHONPATH}"
# Optional ILO_HOME if desk lives under an operator home tree
```

## Daily boot (2 commands)

```bash
hs ops boot                 # seed pulse, one tick, write viewport files
hs view --serve --port 8764 # dashboard + in-process Pulse every 60s
```

Open **http://127.0.0.1:8764/** (hard refresh). Desktop: Reload plugins → **Hermespace** pane/page.

Optional host timer (if you do not keep `view --serve` up):

```bash
hs pulse install-timer      # user crontab → hs pulse tick each minute
```

## CLI map

| Command | Purpose |
|---------|---------|
| `hs ops doctor` | Health (core must pass) |
| `hs ops boot` | Seed + tick + viewport write |
| `hs ops tick-all [--dream]` | Full cycle |
| `hs ops status` | Compact block for agents |
| `hs pulse tick\|status\|list` | Runtime jobs |
| `hs view --serve` | Live dashboard (+ pulse loop) |
| `hs grid access-request/approve/deny` | Pocket exits |
| `hs grid regulate -m "…"` | Chat phrases |
| `hs grid mission\|dream\|…` | Grid surfaces |

## Chat phrases (user)

- `show boundary`
- `allow ~/path for 2h`
- `approve request <id>` / `deny request <id>`
- `revoke permits`

## Agent API

```python
from hermespace import Workbench, ops
from hermespace.grid.access import request_access
from hermespace.grid.boundary import allow_write
from hermespace.grid.missions import add_mission
from hermespace.grid.dream import run_dream
from hermespace.grid.skillbench import register_module, merge_skills
from hermespace.grid.selftalk import say
from hermespace import pulse

ops.boot()                          # everyday ready
wb = Workbench(agent_id="agent", session_id="s1"); wb.enter()
# external write:
# r = request_access("/path/to/project", reason="…");  # user approves
# allow_write("/path") only after approve/permit
pulse.tick()
run_dream(force_material=True)
say("note", role="planner")
```

## Subsystems (must work)

| Surface | Default | Tick / trigger |
|---------|---------|----------------|
| Pulse jobs | 5 seeded | `view --serve` loop, `hs pulse tick`, session boot |
| Access | deny outside pocket | chat / viewport Approve |
| Dreams | off-peak optional | pulse `dream_cycle` or `ops tick-all --dream` |
| Skillbench | pocket modules | API / grid CLI; promote → drafts only |
| Self-talk | internal log | pulse / agent `say` |
| Viewport | KPI dashboard | serve or `view --format write` |
| Workbench | FOA desk | plugin session_start + orders |

## Verify

```bash
./scripts/e2e_ops.sh
./scripts/smoke_test.sh
./scripts/doctor_desktop.sh
hs ops doctor
```

Expect: **E2E_PASS**, smoke **9/9**, doctor `ok: true`.

## Dual channel

| To human | To model |
|----------|----------|
| Short `report` / viewport | Inject context + ops status + pending access |

Never paste full inject into Telegram/email.
