#!/usr/bin/env bash
set -euo pipefail
HOME_ROOT="${HERMESPACE_HOME:-${ILO_HOME:-$HOME/.hermespace}}"
DEST="$HOME_ROOT/memory/hermespace/ACTIVE.md"
TEMPLATE="$(cd "$(dirname "$0")/.." && pwd)/runtime/ACTIVE.template.md"
mkdir -p "$(dirname "$DEST")"
if [[ -f "$TEMPLATE" ]]; then
  cp "$TEMPLATE" "$DEST"
else
  cat > "$DEST" <<'EOF'
# HERMESPACE ACTIVE
updated: (template)

## Goal

## Active concepts (desk)

## Choices

## Decision

## Plan

## Report

## Do not say
EOF
fi
date -Iseconds >> "$DEST"
echo "desk ready: $DEST"
