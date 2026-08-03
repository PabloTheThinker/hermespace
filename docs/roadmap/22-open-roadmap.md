# Hermespace open roadmap (research + backlog)

Snapshot after v0.17 desktop-detach + pulse API. Host-agnostic.

## Done recently

| Desktop hard-copy install + dual pane/page + StatusDot contract | v0.17.1 |


| Item | Where |
|------|--------|
| Autonomy grid (missions, lenses, dream, skillbench, selftalk, title) | `grid/` |
| Pocket boundary + talkable access | `boundary`, `access`, `converse` |
| Operator viewport + loopback API | `viewport`, `view_server` |
| Pulse runtime (smarter than cron) | `pulse.py` |
| Perf harden viewport/pulse | v0.16.1 |
| Desktop **own page** (not right rail) | `desktop_plugin` routes + sidebar.nav |
| Pulse on Desktop page + `/api/pulse` | v0.17 |
| User crontab helper | `scripts/install_pulse_timer.sh` |

## Open — high value

| # | Item | Why | Effort |
|---|------|-----|--------|
| 1 | **Event-driven pulse** (access_approved → immediate tick) | Faster than 1m wake | M |
| 2 | **Propose-order path** (gated self-order when autonomy on) | True unattended loop | M |
| 3 | **AgentDrive bridge** (optional experience write/read) | Long terrain without fork | L |
| 4 | **Conductor adapter** (optional ethics/scar when present) | Unattended law | M |
| 5 | **Fudoshin eval note** with/without grid under load | Research capital | M |
| 6 | Desktop **start socket** helper from palette (spawn serve) | UX when offline | S |
| 7 | Pulse job enable/disable toggles in Desktop UI | Operator control | S |
| 8 | Multi-agent pulse boards in one page | Multi-agent hosts | M |

## Open — polish

- Docs version stamps (18 still says 0.14)
- Plugin auto-start of `hs view --serve` via Desktop host.request if ever exposed
- Screenshot in README for Teknium dogfood
- Windows/mac crontab alternatives in install_pulse_timer

## Not doing (by design)

- Porting AgentDrive/Conductor trees into Hermespace
- Character kits as lenses
- Unbounded autonomy / money / public post
- Right-rail-only HS panel (removed — page is SoT)

## Recommended next monotropic cut

1. Event bus on access approve → pulse tick  
2. Desktop enable/disable pulse job  
3. Gated `propose_order` behind `HERMESPACE_AUTONOMY=1`  
