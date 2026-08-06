#!/usr/bin/env bash
# Production Hermespace → Hermes Agent installer.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
HERMES_HOME="${HERMES_HOME:-$HOME/.hermes}"
HERMESPACE_HOME="${HERMESPACE_HOME:-$HOME/.hermespace}"
INSTALL_DESKTOP=1
ENABLE_PLUGIN=1

for arg in "$@"; do
  case "$arg" in
    --no-desktop) INSTALL_DESKTOP=0 ;;
    --no-enable) ENABLE_PLUGIN=0 ;;
    -h|--help)
      echo "usage: $0 [--no-desktop] [--no-enable]"
      exit 0
      ;;
    *)
      echo "hermespace: unknown installer option: $arg" >&2
      exit 2
      ;;
  esac
done

# shellcheck source=scripts/_python.sh
source "$ROOT/scripts/_python.sh"

echo "Hermespace production install"
echo "  CHECKOUT=$ROOT"
echo "  HERMES_HOME=$HERMES_HOME"
echo "  HERMESPACE_HOME=$HERMESPACE_HOME"
echo "  PYTHON=$PYTHON"

mkdir -p "$HERMESPACE_HOME" "$HERMES_HOME/skills" "$HERMES_HOME/plugins"

echo "  installing Python package"
"$PYTHON" -m pip install -e "$ROOT" --quiet
"$PYTHON" -c \
  "import hermespace; from hermespace import AccessEngine; assert AccessEngine().status()['ready']"
echo "  package import + AccessEngine readiness OK"

replace_link() {
  local target="$1"
  local source="$2"
  if [[ -L "$target" || -f "$target" ]]; then
    rm -f "$target"
  elif [[ -d "$target" ]]; then
    rm -rf "$target"
  fi
  ln -s "$source" "$target"
}

# Link the complete repository, not only hermes_plugin/.  Current Hermes
# `plugins install owner/repo` likewise installs the repository root; keeping
# both paths identical catches source-layout regressions.
replace_link "$HERMES_HOME/plugins/hermespace" "$ROOT"
replace_link "$HERMES_HOME/skills/hermespace" "$ROOT/skills/hermespace"
echo "  plugin → $HERMES_HOME/plugins/hermespace"
echo "  skill  → $HERMES_HOME/skills/hermespace"

if [[ "$INSTALL_DESKTOP" == "1" ]]; then
  bash "$ROOT/scripts/install_desktop_plugin.sh"
else
  echo "  desktop plugin skipped"
fi

if command -v hermes >/dev/null 2>&1; then
  if [[ "$ENABLE_PLUGIN" == "1" ]]; then
    hermes plugins enable hermespace
    echo "  Hermes plugin enabled"
  else
    echo "  enable later: hermes plugins enable hermespace"
  fi
else
  echo "  Hermes CLI not on PATH — source install is ready; enable later"
fi

HERMES_HOME="$HERMES_HOME" HERMESPACE_HOME="$HERMESPACE_HOME" \
  "$PYTHON" "$ROOT/scripts/verify_hermes_integration.py"

cat <<EOF

Hermespace is operational.

Native install (Hermes v0.20+):
  hermes plugins install PabloTheThinker/hermespace --enable

Verify:
  hermes hermespace doctor
  # or inside a session:
  /hermespace status

Direct CLI:
  hermespace ops doctor
  hermespace base status

State:
  $HERMESPACE_HOME
EOF
