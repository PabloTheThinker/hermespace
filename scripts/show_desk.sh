#!/usr/bin/env bash
set -euo pipefail
HOME_ROOT="${HERMESPACE_HOME:-${ILO_HOME:-$HOME/.hermespace}}"
DEST="$HOME_ROOT/memory/hermespace/ACTIVE.md"
if [[ ! -f "$DEST" ]]; then
  echo "no active desk at $DEST"
  exit 1
fi
cat "$DEST"
