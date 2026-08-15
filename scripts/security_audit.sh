#!/usr/bin/env bash
# Fail if package tree looks operator-specific or secret-bearing.
# Needles are GENERIC only — never bake a specific home user, mesh IP,
# tailnet, or house brand into this script (that would re-pollute the
# public tree). See oss-memory-isolation / audit-needles-are-leaks.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
fail=0

echo "Auditing $ROOT"

# git grep when available (tracked only — house-local untracked notes stay out).
# Non-git fallback walks the tree but skips ARCHIVED.md and caches.
if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  _raw_hits() {
    local pat="$1"
    shift
    git grep -nIE "$pat" -- \
      ':(exclude)scripts/security_audit.sh' \
      ':(exclude)**/*.png' \
      ':(exclude)**/*.jpg' \
      ':(exclude)**/*.svg' \
      "$@" \
      2>/dev/null || true
  }
else
  _raw_hits() {
    local pat="$1"
    shift
    grep -RInE --exclude-dir=.git --exclude-dir=__pycache__ \
      --exclude-dir=.pytest_cache --exclude='security_audit.sh' \
      --exclude='ARCHIVED.md' --exclude='*.pyc' --exclude='*.png' \
      --exclude='*.jpg' --exclude='*.svg' \
      "$pat" . 2>/dev/null || true
  }
fi

# Report FAIL if any hits remain after optional grep -vE filter.
check() {
  local pat="$1"
  local filter="${2:-}"
  local hits
  hits="$(_raw_hits "$pat")"
  if [[ -n "$filter" && -n "$hits" ]]; then
    hits="$(printf '%s\n' "$hits" | grep -Ev "$filter" || true)"
  fi
  if [[ -n "$hits" ]]; then
    echo "FAIL pattern: $pat"
    echo "$hits" | head -20
    fail=1
  fi
}

# Code-only scan (docs may show pedagogical /home/me examples).
check_code() {
  local pat="$1"
  local hits
  if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    hits="$(git grep -nIE "$pat" -- \
      '*.py' '*.sh' '*.yaml' '*.yml' '*.toml' '*.json' \
      ':(exclude)scripts/security_audit.sh' \
      2>/dev/null || true)"
  else
    hits="$(grep -RInE --include='*.py' --include='*.sh' --include='*.yaml' \
      --include='*.yml' --include='*.toml' --include='*.json' \
      --exclude-dir=.git --exclude-dir=__pycache__ --exclude='security_audit.sh' \
      "$pat" . 2>/dev/null || true)"
  fi
  if [[ -n "$hits" ]]; then
    echo "FAIL code pattern: $pat"
    echo "$hits" | head -20
    fail=1
  fi
}

# Absolute operator home paths in code (POSIX + macOS) — generic class only.
# Docs may illustrate with /home/me|/home/someone|/home/user placeholders.
check_code '/home/[a-zA-Z0-9._-]+'
check_code '/Users/[a-zA-Z0-9._-]+'

# Whole-tree: private agent-home style paths (generic)
check '(^|[^A-Za-z0-9_])~/?\.ilo/'
check '(^|[^A-Za-z0-9_])\.ilo/brain'

# CGNAT dotted quads in code (class only). Docs may show 100.x examples.
check_code '100\.(6[4-9]|[7-9][0-9]|1[01][0-9]|12[0-7])\.[0-9]+\.[0-9]+'

# Real-looking ts.net hosts in code — allow docs placeholders (*-xxxx.ts.net)
check '[a-z0-9-]+\.ts\.net' 'xxxx\.ts\.net|example\.ts\.net|tailnet-xxxx'

# Common secret markers (whole tree)
check 'SUDO_PASSWORD'
check 'xai-oauth'
# openai-style keys (avoid matching normal words: require sk- + 10 more alnum)
check 'sk-[A-Za-z0-9]{10,}'

if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  if git ls-files | grep -E 'episodes\.jsonl|seals\.jsonl|(^|/)ACTIVE\.json$' ; then
    echo "FAIL: runtime state tracked"
    fail=1
  fi
  if git ls-files --others --exclude-standard | grep -E '(^|/)ARCHIVED\.md$' >/dev/null; then
    echo "WARN: untracked ARCHIVED.md present (house-local; keep untracked / gitignored)"
  fi
fi

if [[ "$fail" -ne 0 ]]; then
  echo "security_audit FAILED"
  exit 1
fi
echo "security_audit OK"
