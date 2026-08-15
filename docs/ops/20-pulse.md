# Pulse runtime (pocket rhythm)

Hermespace **Pulse** is a desk-aware job runtime that lives *inside* the pocket.
It is **not** Hermes cron and not system cron — those can only *wake* it.

## Why smarter than bare cron

| Bare cron | Pulse |
|-----------|--------|
| Fires on wall clock only | Wall clock **or** conditions |
| Blind to agent state | Reads desk load, workbench mode, missions, access queue |
| Stacks missed runs | **Coalesce** — overdue → run once |
| No FOA | Skips when load high / not idle (per job) |
| Host-global | State under `$HERMESPACE_HOME` only |

## Drive it

```bash
# one cycle (put this on system timer every minute)
hs pulse tick

# in-process loop
hs pulse daemon --interval 60

# inspect
hs pulse status
hs pulse list
hs pulse run --id dream_cycle
hs pulse disable --id dream_cycle
```

Systemd timer / crontab example (host-agnostic):

```cron
* * * * * cd /path/to/hermespace && HERMESPACE_HOME=$HOME/.hermespace PYTHONPATH=src ./scripts/hs pulse tick >>$HOME/.hermespace/pulse-cron.log 2>&1
```

## Default jobs

| id | action | every | notes |
|----|--------|-------|--------|
| idle_maintain | idle_tick | 15m | consolidate while idle |
| dream_cycle | dream | 6h | quiet_hours default 9–17 UTC |
| viewport_refresh | viewport | 5m | Desktop snapshot files |
| mission_pulse | mission_pulse | 1h | only if open missions |
| access_watch | access_watch | 2m | only if pending access |

## Add a job

```bash
hs pulse add --name "Night dream" --id night_dream --action dream --every-sec 28800 --max-load 0.6
```

## Safety

- Actions are pocket builtins (no silent project writes).
- `require_autonomy` jobs stay off until `HERMESPACE_AUTONOMY=1`.
- Boundary + access rules still apply for anything outside the pocket.

## Performance

- `hs pulse tick` batches job state into **one** write (not per-job fsync).
- Pulse log trims only after ~256KB (no full-read every minute).
- Viewport write uses a **single** snapshot (no triple rescan).
- `pulse.compact_summary()` / `status(light=True)` for cheap desk injects.
