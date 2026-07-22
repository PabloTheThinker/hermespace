#!/usr/bin/env bash
# Install Hermespace Desktop plugin as a REAL file (not symlink).
# Desktop loads from getStatus().hermes_home/desktop-plugins/<id>/plugin.js
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SRC="$ROOT/desktop_plugin/hermespace/plugin.js"
HERMES_HOME="${HERMES_HOME:-$HOME/.hermes}"
DEST_DIR="$HERMES_HOME/desktop-plugins/hermespace"
DEST="$DEST_DIR/plugin.js"

if [[ ! -f "$SRC" ]]; then
  echo "missing $SRC" >&2
  exit 1
fi

mkdir -p "$DEST_DIR"
# Remove symlink or old file first — cp won't replace symlink→same path
rm -f "$DEST"
cp -f "$SRC" "$DEST"
# Also drop a tiny marker for doctor
cat >"$DEST_DIR/INSTALL.txt" <<EOF
Hermespace desktop plugin
source=$SRC
installed=$(date -u +%Y-%m-%dT%H:%M:%SZ)
HERMES_HOME=$HERMES_HOME
Reload: Desktop ⌘K → Reload desktop plugins
Open: sidebar Hermespace · pane "hermespace" · chip hs · /hermespace
Socket: hs view --serve --port 8764
EOF

echo "Installed Desktop plugin:"
echo "  $DEST ($(wc -c <"$DEST") bytes)"
if [[ -L "$DEST" ]]; then
  echo "ERROR: still a symlink" >&2
  exit 1
fi
echo "  id=hermespace (folder must match)"
echo "Next: Reload desktop plugins in Hermes Desktop"
echo "Settings → Plugins should list Hermespace (status loaded)"
