#!/usr/bin/env bash
# Production Hermespace → Hermes Agent installer.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
HERMES_HOME="${HERMES_HOME:-$HOME/.hermes}"
HERMESPACE_HOME="${HERMESPACE_HOME:-$HOME/.hermespace}"
INSTALL_DESKTOP=1
ENABLE_PLUGIN=1
INSTALL_YES=0
NO_ORGANS=0

for arg in "$@"; do
  case "$arg" in
    --no-desktop) INSTALL_DESKTOP=0 ;;
    --no-enable) ENABLE_PLUGIN=0 ;;
    --yes) INSTALL_YES=1 ;;
    --no-organs) NO_ORGANS=1 ;;
    -h|--help)
      echo "usage: $0 [--no-desktop] [--no-enable] [--yes] [--no-organs]"
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
# Put this checkout first even when an older editable Hermespace is already in
# the operator's PYTHONPATH.
export PYTHONPATH="$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"

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

# Front door: offer Cube/Insight organs, then UNION plugins.enabled.
# Never rewrite the list. Never clobber a memory.provider the user chose.
HERMES_HOME="$HERMES_HOME" ENABLE_PLUGIN="$ENABLE_PLUGIN" \
  INSTALL_YES="$INSTALL_YES" NO_ORGANS="$NO_ORGANS" "$PYTHON" - <<'PY'
import os
from hermespace.install_kit import install_front_door
yes = os.environ.get("INSTALL_YES", "") == "1"
no_organs = os.environ.get("NO_ORGANS", "") == "1" or (not yes and not os.isatty(0))
out = install_front_door(
    yes=yes,
    no_organs=no_organs,
    enable=os.environ.get("ENABLE_PLUGIN", "1") == "1",
)
print("  front door", out.get("ok"), "enabled", (out.get("union") or {}).get("enabled"))
for rec in (out.get("organs") or {}).get("offered") or []:
    print("  organ", rec.get("plugin"), rec.get("action"), rec.get("offer") or rec.get("role"))
mem = out.get("memory") or {}
print("  memory.provider", mem.get("action"), mem.get("provider") or mem.get("note"))
if not out.get("ok"):
    raise SystemExit("install_front_door failed: " + str(out))
PY

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
