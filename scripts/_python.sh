#!/usr/bin/env bash
# Resolve Python executable: prefer python3 (Unix), fall back to python (Windows).
if [[ -z "${PYTHON:-}" ]]; then
  if command -v python3 >/dev/null 2>&1; then
    PYTHON=python3
  elif command -v python >/dev/null 2>&1; then
    PYTHON=python
  else
    echo "hermespace: python3 or python not found in PATH" >&2
    exit 127
  fi
fi
