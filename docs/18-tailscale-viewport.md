# Viewport + Tailscale (any user)

Hermespace viewport works on **your** machine and **your** tailnet — no hard-coded operator IPs.

## Local only (default)

```bash
export HERMESPACE_HOME="${HERMESPACE_HOME:-$HOME/.hermespace}"
export PYTHONPATH="$PWD/src${PYTHONPATH:+:$PYTHONPATH}"
./scripts/hs view --serve --port 8764
# → http://127.0.0.1:8764/
```

## Same tailnet (laptop → server)

On the **machine running Hermespace** (must be on Tailscale):

```bash
# Preferred: bind ONLY this host's Tailscale IPv4 (CGNAT (Tailscale))
./scripts/hs view --serve --tailscale --port 8764
```

Printed line:

```text
tailscale: http://<tailscale-ipv4>:8764/
```

On your **laptop** (same tailnet): open that URL, or MagicDNS:

```text
http://<machine-name>.tailnet-xxxx.ts.net:8764/
```

### Fallback: all interfaces

```bash
./scripts/hs view --serve --bind-all --allow-remote --port 8764
```

Use OS firewall / Tailscale ACLs so port **8764** is not open on the public WAN.

### Optional shared secret (non-loopback)

```bash
export HERMESPACE_VIEW_TOKEN='long-random'
export HERMESPACE_VIEW_TOKEN_REQUIRED=1   # force even on loopback if you want
./scripts/hs view --serve --tailscale
# clients: http://<tailscale-ipv4>:8764/?token=long-random
# or header: X-Hermespace-Token: long-random
```

### If `tailscale` CLI is missing

```bash
export HERMESPACE_TAILSCALE_IP=<tailscale-ipv4>   # from `tailscale ip -4` on that host
./scripts/hs view --serve --host "$HERMESPACE_TAILSCALE_IP" --port 8764
```

## Desktop / Hermes plugin

- Plugin and CLI use `$HERMESPACE_HOME` only — no `/home/someone` paths.
- Doctor checks loopback **and** detected Tailscale IP:

```bash
./scripts/hs ops doctor
./scripts/doctor_desktop.sh
```

## Env reference

| Variable | Meaning |
|----------|---------|
| `HERMESPACE_HOME` | State root (default `~/.hermespace`) |
| `HERMESPACE_VIEW_TOKEN` | Optional auth token |
| `HERMESPACE_VIEW_TOKEN_REQUIRED` | `1` = require token always |
| `HERMESPACE_VIEW_OPEN` | `1` = allow `0.0.0.0` without `--allow-remote` |
| `HERMESPACE_TAILSCALE_IP` | Override detected Tailscale IPv4 |

## Security notes

- Default remains **loopback-only**.
- `--tailscale` binds the CGNAT address Tailscale assigns **this** host — works for every user on every tailnet.
- Never commit real Tailscale IPs, tokens, or home paths into the public repo.
