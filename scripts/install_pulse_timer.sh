#!/usr/bin/env bash
# Install a user crontab line that wakes Hermespace Pulse every minute.
# Does NOT require root. Idempotent (removes prior Hermespace Pulse markers).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
HERMESPACE_HOME="${HERMESPACE_HOME:-$HOME/.hermespace}"
MARKER="# hermespace-pulse"
LINE="$MARKER every-minute"
JOB="* * * * * cd $(printf %q "$ROOT") && HERMESPACE_HOME=$(printf %q "$HERMESPACE_HOME") PYTHONPATH=src ./scripts/hs pulse tick >>$(printf %q "$HERMESPACE_HOME/pulse-cron.log") 2>&1 $MARKER"

mkdir -p "$HERMESPACE_HOME"

if ! command -v crontab >/dev/null 2>&1; then
  echo "crontab not available — run manually:"
  echo "  $JOB"
  exit 1
fi

EXISTING="$(crontab -l 2>/dev/null || true)"
# drop old marker lines
FILTERED="$(printf '%s\n' "$EXISTING" | grep -v 'hermespace-pulse' || true)"
{
  printf '%s\n' "$FILTERED"
  # ensure trailing newline before append
  printf '%s\n' "$JOB"
} | crontab -

echo "Installed user crontab pulse wake:"
echo "  $JOB"
echo "Verify: crontab -l | grep hermespace-pulse"
echo "Log:    $HERMESPACE_HOME/pulse-cron.log"
echo "Remove: crontab -l | grep -v hermespace-pulse | crontab -"
