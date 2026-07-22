#!/usr/bin/env bash
# Doctor: Hermespace ↔ Hermes Desktop integration checks
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
HERMES_HOME="${HERMES_HOME:-$HOME/.hermes}"
SRC="$ROOT/desktop_plugin/hermespace/plugin.js"
DEST="$HERMES_HOME/desktop-plugins/hermespace/plugin.js"
ec=0
ok() { echo "OK  $*"; }
bad() { echo "FAIL $*"; ec=1; }

echo "=== Hermespace Desktop doctor ==="
echo "HERMES_HOME=$HERMES_HOME"

if [[ -f "$SRC" ]]; then ok "package plugin.js ($(wc -c <"$SRC") bytes)"; else bad "missing $SRC"; fi

if [[ -f "$DEST" ]]; then
  ok "installed $DEST ($(wc -c <"$DEST") bytes)"
  if [[ -L "$DEST" ]]; then
    bad "DEST is symlink → $(readlink "$DEST") (use install_desktop_plugin.sh hard copy)"
  else
    ok "DEST is real file (not symlink)"
  fi
  if cmp -s "$SRC" "$DEST" 2>/dev/null; then ok "DEST matches package source"
  else bad "DEST differs from package — re-run install_desktop_plugin.sh"; fi
else
  bad "not installed at $DEST — run: ./scripts/install_desktop_plugin.sh"
fi

# contract greps
if [[ -f "$DEST" ]]; then
  P="$DEST"
else
  P="$SRC"
fi
rg -q "id: PLUGIN_ID|id: 'hermespace'" "$P" && ok "plugin.id hermespace" || bad "plugin.id"
rg -q "area: 'panes'" "$P" && ok "registers panes tile" || bad "no panes tile"
rg -q "ROUTES_AREA" "$P" && ok "registers ROUTES_AREA" || bad "no ROUTES_AREA"
rg -q "SIDEBAR_NAV_AREA" "$P" && ok "registers SIDEBAR_NAV" || bad "no SIDEBAR_NAV"
rg -q "PALETTE_AREA" "$P" && ok "palette" || bad "no palette"
# StatusDot contract
if rg -n "tone: '(success|warning|danger|neutral)'" "$P" >/dev/null; then
  bad "StatusDot uses invalid tones (need good|muted|warn|bad)"
else
  ok "StatusDot tones look valid"
fi
if rg -n "Badge[^\n]{0,40}secondary" "$P" >/dev/null 2>&1; then
  bad "Badge may use secondary (forbidden)"
else
  ok "no Badge secondary"
fi
# unsupported imports
python3 - <<'PY' "$P" || true
import re,sys
src=open(sys.argv[1]).read()
imp=re.compile(r"(from\s*|import\s*\(\s*|import\s+)(['\"])([^'\"]+)\2")
ok={"@hermes/plugin-sdk","react","react/jsx-runtime","react/jsx-dev-runtime"}
bare=[]
for m in imp.finditer(src):
  s=m.group(3)
  if s and not re.match(r'^[./]',s) and not re.match(r'^[a-z][a-z0-9+.-]*:',s,re.I) and s not in ok:
    bare.append(s)
if bare:
  print("FAIL unsupported imports:", bare); raise SystemExit(1)
print("OK  imports only sdk+react")
PY

# socket
if curl -sf -o /dev/null --max-time 2 http://127.0.0.1:8764/api/health   || curl -sf -o /dev/null --max-time 2 http://127.0.0.1:8764/api/snapshot; then
  ok "viewport loopback :8764 up"
else
  echo "WARN viewport :8764 down — run: PYTHONPATH=src ./scripts/hs view --serve --port 8764"
fi
# portable Tailscale check (any user's IP)
if command -v tailscale >/dev/null 2>&1; then
  TSIP=$(tailscale ip -4 2>/dev/null | head -1 | tr -d '[:space:]')
  if [ -n "$TSIP" ]; then
    if curl -sf -o /dev/null --max-time 2 "http://${TSIP}:8764/api/health"; then
      ok "viewport tailscale http://${TSIP}:8764"
    else
      echo "INFO tailscale IP ${TSIP} — serve with: hs view --serve --tailscale"
    fi
  fi
fi

echo "---"
if [[ $ec -eq 0 ]]; then echo "DOCTOR_PASS"; else echo "DOCTOR_FAIL"; fi
exit $ec
