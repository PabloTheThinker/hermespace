# Pocket security + user viewport

## Why

Hermespace is a **pocket dimension**. Two operator needs:

1. **Containment** — the agent’s internal world must not spill into user projects or destroy data without permission.  
2. **Visibility** — the human must be able to *look inside* the pocket and see desk, missions, scars, self-talk, dreams, skillbench.

## Boundary API

```python
from hermespace.grid.boundary import check_path, grant_permit, policy_markdown

check_path("/home/me/myapp", "write")   # denied by default
grant_permit("/home/me/myapp", hours=1, note="feature")
check_path("/home/me/myapp/src/x.py", "write")  # allowed until expiry
```

## Viewport API

```python
from hermespace.grid.viewport import snapshot, render_markdown, write_viewport_files

print(render_markdown("my-agent"))
write_viewport_files("my-agent")  # HERMESPACE_HOME/viewport/
```

## CLI

```bash
hs grid policy
hs grid permit --path ~/code/app --hours 2
hs grid check-path --path ~/code/app --mode write
hs view
hs view --format write
```

## Threat model (short)

| Threat | Mitigation |
|--------|------------|
| Silent project pollution | default deny external write |
| Secret theft into git | secretish path block + ship audit |
| Autonomy rampage | `HERMESPACE_AUTONOMY=0` + boundary still applies |
| Skill supply chain | promote guard + drafts namespace only |
| Operator blindness | `hs view` read-only dashboard |

## Not claimed

- OS-level sandbox / seccomp  
- Full Hermes tool mediation (Hermes tools still need Hermes config)  
- Network egress firewall  

Hermespace enforces **its own** pocket laws. Pair with Hermes tool permissions for host tools.

## Conversational regulation

User ↔ agent phrases (also `hs grid regulate -m "..."`):

| Say | Effect |
|-----|--------|
| `show boundary` / `what's allowed` | Explain pocket rules |
| `allow ~/project for 2h` | Time-limited write permit |
| `approve request <id>` | Approve pending agent request |
| `deny request <id>` | Deny pending request |
| `revoke permits` | Clear temporary permits |
| `list access requests` | Pending queue |

Agent (inside pocket):

```python
from hermespace import Grid
g = Grid("my-agent")
g.request_access("~/code/app", reason="need to patch tests", hours=2)
# then wait — do not write until approved
```

Plugin inject includes pending requests + talkable rules every material turn.

## Desktop

1. `hs view --serve --port 8764` (loopback)
2. Desktop plugin `hermespace` pane (Approve/Deny + snapshot)
3. Install: symlink `desktop_plugin/hermespace` → `$HERMES_HOME/desktop-plugins/hermespace`
4. ⌘K → Reload desktop plugins

