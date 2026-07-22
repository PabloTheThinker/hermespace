#!/usr/bin/env bash
# One-shot Hermespace → Hermes Agent install (skill + plugin + env hints).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
HERMES_HOME="${HERMES_HOME:-$HOME/.hermes}"
HERMESPACE_HOME="${HERMESPACE_HOME:-$HOME/.hermespace}"

echo "Hermespace install"
echo "  CHECKOUT=$ROOT"
echo "  HERMES_HOME=$HERMES_HOME"
echo "  HERMESPACE_HOME=$HERMESPACE_HOME"

mkdir -p "$HERMESPACE_HOME"
mkdir -p "$HERMES_HOME/skills" "$HERMES_HOME/plugins"

# Skill
rm -rf "$HERMES_HOME/skills/hermespace"
ln -sfn "$ROOT/skills/hermespace" "$HERMES_HOME/skills/hermespace"
echo "  skill → $HERMES_HOME/skills/hermespace"

# Plugin (symlink so package auto-discovers ../src)
rm -rf "$HERMES_HOME/plugins/hermespace"
ln -sfn "$ROOT/hermes_plugin" "$HERMES_HOME/plugins/hermespace"
echo "  hermes plugin → $HERMES_HOME/plugins/hermespace"

# Desktop plugin — REAL file copy (not symlink; Desktop/remote hermes_home)
bash "$ROOT/scripts/install_desktop_plugin.sh" || {
  mkdir -p "$HERMES_HOME/desktop-plugins/hermespace"
  cp -f "$ROOT/desktop_plugin/hermespace/plugin.js" "$HERMES_HOME/desktop-plugins/hermespace/plugin.js"
  echo "  desktop plugin (fallback cp) → $HERMES_HOME/desktop-plugins/hermespace"
}

# Optional editable install when pip available
if command -v pip >/dev/null 2>&1 || command -v pip3 >/dev/null 2>&1; then
  PIP="$(command -v pip3 || command -v pip)"
  if "$PIP" install -e "$ROOT" -q 2>/dev/null; then
    echo "  pip install -e . OK"
  else
    echo "  pip install -e . skipped (optional; PYTHONPATH=src works)"
  fi
fi

if command -v hermes >/dev/null 2>&1; then
  hermes plugins enable hermespace 2>/dev/null || true
  echo "  hermes plugins enable hermespace (attempted)"
else
  echo "  hermes CLI not on PATH — enable later: hermes plugins enable hermespace"
fi

cat <<EOF

Done. Add to your shell profile (optional):

  export HERMESPACE_ROOT="$ROOT"
  export HERMESPACE_HOME="$HERMESPACE_HOME"
  export HERMES_HOME="$HERMES_HOME"
  export PYTHONPATH="$ROOT/src\${PYTHONPATH:+:\$PYTHONPATH}"
  export HERMESPACE_NEURAL_BACKEND=auto
  export HERMESPACE_NEURAL_VERBALIZE=0

Verify:

  PYTHONPATH="$ROOT/src" "$ROOT/scripts/smoke_test.sh"
  hermes plugins list   # hermespace enabled
  # Desktop pocket UI:
  PYTHONPATH="$ROOT/src" "$ROOT/scripts/hs" view --serve --port 8764
  # then in Desktop: sidebar → Hermespace  (or palette “Hermespace: Open pocket”)

Docs: $ROOT/README.md · $ROOT/FOR_HERMES.md · $ROOT/desktop_plugin/hermespace/README.md
EOF

echo "  Everyday: hs ops boot && hs view --serve --port 8764"
echo "  E2E: ./scripts/e2e_ops.sh"

