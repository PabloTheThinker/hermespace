# Hermespace Desktop plugin

## Why it failed before
1. **Symlink install** — Desktop loads from `getStatus().hermes_home/desktop-plugins/…`. Symlinks into other trees often fail remote/profile FS reads.
2. **StatusDot tones** — host only accepts `good|muted|warn|bad` (not success/warning/danger).
3. **Right-rail only** — removed earlier left users with nowhere visible if routes didn’t register.

## Surfaces (v0.17.1)
| Surface | How |
|---------|-----|
| **Pane** `hermespace` | `area: panes` — dockable like ilo-ops |
| **Page** `/hermespace` | `ROUTES_AREA` |
| **Sidebar** Hermespace | `SIDEBAR_NAV_AREA` → openRouteTile |
| **Chip** `hs` | statusBar → navigate page |
| **Palette** | Open + socket hint |

## Install
```bash
./scripts/install_desktop_plugin.sh   # hard copy into $HERMES_HOME
./scripts/doctor_desktop.sh
```
Then Desktop: **⌘K → Reload desktop plugins**.  
Settings → Plugins → Hermespace should be **loaded**.

## Socket
```bash
PYTHONPATH=src ./scripts/hs view --serve --port 8764
```
