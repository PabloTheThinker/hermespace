#!/usr/bin/env bash
# Fail if package tree looks operator-specific or secret-bearing.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
fail=0

# Patterns checked against tracked content (exclude this script + .git)
check() {
  local pat="$1"
  local hits
  hits="$(grep -RInE --exclude-dir=.git --exclude-dir=__pycache__ \
    --exclude='security_audit.sh' --exclude='*.pyc' \
    "$pat" . 2>/dev/null | grep -v 'scripts/security_audit.sh' || true)"
  if [[ -n "$hits" ]]; then
    echo "FAIL pattern: $pat"
    echo "$hits" | head -20
    fail=1
  fi
}

echo "Auditing $ROOT"
check '/home/ilo'
check '/home/pablo'
check 'pablothethinker'
check 'Pablo Navarro'
check 'thethinker\.pablo'
check 'Vektra'
check 'Parallax'
check '100\.64\.'
check 'Spring Hill'
check 'Founding Five'
check 'ilo-pablo-partner'
check 'SUDO_PASSWORD'
check 'xai-oauth'
# openai-style keys (avoid matching normal words: require sk- + 10 more alnum)
check 'sk-[A-Za-z0-9]{10,}'

if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  if git ls-files | grep -E 'episodes\.jsonl|seals\.jsonl|(^|/)ACTIVE\.json$' ; then
    echo "FAIL: runtime state tracked"
    fail=1
  fi
fi

if [[ "$fail" -ne 0 ]]; then
  echo "security_audit FAILED"
  exit 1
fi
echo "security_audit OK"
