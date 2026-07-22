# SECURITY.md

## Public ship gate

Before commit/push:

- No secrets, tokens, `.env`, auth files  
- No personal names, private emails, wages, family, clinical status  
- No host fingerprints (absolute home paths of operators, tailnet IPs, internal hostnames)  
- Desk state (`ACTIVE.md`, `episodes.jsonl`, seals) must stay **out of git**  

```bash
./scripts/security_audit.sh
```

Default state dir: `~/.hermespace` (override `HERMESPACE_HOME`).

---

## Pocket dimension boundary (runtime)

Hermespace is a **pocket dimension**. It must not silently populate or damage user projects.

### Hard rules

| Rule | Enforcement |
|------|-------------|
| All Hermespace **state** lives under `HERMESPACE_HOME` | `boundary.pocket_root()` / grid paths |
| **Default deny** writes outside the pocket | `boundary.check_path(path, "write")` |
| No auto-write into user repos/projects | project_write_default=`deny` |
| Secret-like names never writable | `.env`, keys, `.ssh`, … |
| External **delete** always denied | `check_path(..., "delete")` |
| Skill promote → `HERMES_HOME/skills/hermespace-drafts/` only | `hermes_promote_dest` |
| Autonomy does **not** bypass boundary | gates + boundary independent |
| Viewport is **read-only** observation | `hs view` |

### Operator controls

```bash
# Inspect policy
hs grid policy

# Temporary write access to a project tree (explicit permission)
hs grid permit --path /path/to/project --hours 2 --note "feature X"

# Revoke
hs grid permit-revoke
hs grid permit-revoke --path /path/to/project

# Durable allowlist (still explicit)
hs grid allowlist-add --path /path/to/project
hs grid allowlist-remove --path /path/to/project

# Probe a path
hs grid check-path --path ./src --mode write
```

### Env

| Variable | Default | Meaning |
|----------|---------|---------|
| `HERMESPACE_HOME` | `~/.hermespace` | Pocket root |
| `HERMESPACE_AUTONOMY` | `0` | Self-order budget (still cannot leave pocket without permit) |
| `HERMESPACE_ALLOW_PACKAGE_WRITE` | `0` | Dev-only: allow writes into checkout package tree |

### Agent contract

1. Prefer tools that mutate **only** pocket state (missions, desk, skillbench drafts).  
2. Before writing to a user project: check `hs grid check-path` / `boundary.check_path`.  
3. If denied: ask the human to `hs grid permit` — do not invent workarounds.  
4. Never dump inject/self-talk secrets into user git trees.  

Code: `src/hermespace/grid/boundary.py`.

---

## Conversational regulation

In chat with the agent:

- `show boundary`
- `allow ~/project for 2h`
- `approve request <id>` / `deny request <id>`
- `revoke permits`

Agent requests via `Grid.request_access` / `hs grid access-request` — never silent project writes.

## Looking into the space (user viewport)

```bash
hs view                      # markdown dashboard (stdout)
hs view --format json
hs view --format html
hs view --format write       # writes ~/.hermespace/viewport/{VIEW.md,index.html,snapshot.json}
```

Open `HERMESPACE_HOME/viewport/index.html` in a browser for a read-only live snapshot.

Details: [docs/19-pocket-security-viewport.md](docs/19-pocket-security-viewport.md).
