#!/usr/bin/env bash
# Everyday Hermespace smoke test — integration doors + neural + memory.
set -uo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
export PYTHONPATH="${ROOT}/src${PYTHONPATH:+:$PYTHONPATH}"
export HERMESPACE_HOME="${HERMESPACE_HOME:-$(mktemp -d /tmp/hermespace-smoke-XXXXXX)}"
export HERMESPACE_NEURAL_BACKEND="${HERMESPACE_NEURAL_BACKEND:-auto}"
export HERMESPACE_NEURAL_VERBALIZE="${HERMESPACE_NEURAL_VERBALIZE:-0}"
HS="${ROOT}/scripts/hs"
OUT_DIR="${HERMESPACE_HOME}/smoke_results"
mkdir -p "$OUT_DIR"
LOG="$OUT_DIR/smoke.log"
RESULTS="$OUT_DIR/results.json"
pass=0
fail=0

log() { echo "$@" | tee -a "$LOG"; }
ok() { pass=$((pass + 1)); log "PASS  $1"; }
bad() { fail=$((fail + 1)); log "FAIL  $1 — $2"; }

log "=== Hermespace smoke ==="
log "HERMESPACE_HOME=$HERMESPACE_HOME"
log "ROOT=$ROOT"

if PYTHONPATH="$ROOT/src" python3 -m unittest discover -s "$ROOT/tests" -q >>"$LOG" 2>&1; then
  ok "unit_tests"
else
  bad "unit_tests" "see smoke.log"
fi

if bash "$ROOT/scripts/security_audit.sh" >>"$LOG" 2>&1; then
  ok "security_audit"
else
  bad "security_audit" "audit failed"
fi

if PYTHONPATH="$ROOT/src" python3 -c "from hermespace.local_model import local_capabilities; import json; print(json.dumps(local_capabilities(), indent=2))" >"$OUT_DIR/caps.json" 2>>"$LOG"; then
  ok "neural_caps"
else
  bad "neural_caps" "caps failed"
fi

if PYTHONPATH="$ROOT/src" python3 >"$OUT_DIR/agent_api.json" 2>>"$LOG" <<'PY'
from hermespace.agent_api import (
    encode_message, run_turn, decode_for_user, decode_for_model,
    decode_bundle, memory_paths, study_memory, history,
)
import json
inp = encode_message(
    "Fix authentication session timeout in production",
    goal="Fix auth session timeout",
    decision="A — patch TTL",
    plan=["repro", "patch", "verify"],
    say="I'll patch session TTL and verify login stays alive.",
    session_id="smoke-sess",
    agent_id="smoke-agent",
    force=True,
)
out = run_turn(inp)
assert not out.skipped, out.reason
user = decode_for_user(out)
model = decode_for_model(out)
assert len(user) > 5
assert "Goal" in model or "Hermespace" in model or "desk" in model.lower()
bundle = decode_bundle(out)
assert bundle["memory_id"]
assert memory_paths().get("db")
# study
hits = study_memory("auth", limit=5)
assert isinstance(hits, list)
print(json.dumps({
    "user_reply": user,
    "model_context_head": model[:500],
    "neural_backend": (bundle.get("neural") or {}).get("backend"),
    "neural_focus": (bundle.get("neural") or {}).get("focus"),
    "memory_id": bundle["memory_id"],
    "memory_paths": memory_paths(),
    "ready": bundle["ready"],
    "decision": bundle["decision"],
    "study_hits": len(hits),
}, indent=2))
PY
then
  ok "agent_api_encode_decode"
else
  bad "agent_api_encode_decode" "see smoke.log"
fi

if "$HS" turn -m "deploy hermespace plugin" \
  --goal "Deploy hermespace plugin" \
  --decision "A — enable plugin" \
  --say "Enabling Hermespace plugin and verifying inject." \
  --plan "link" --plan "enable" --plan "verify" \
  --session-id smoke-cli --agent-id smoke-cli \
  --force --json >"$OUT_DIR/cli_turn.json" 2>>"$LOG"
then
  ok "cli_turn_json"
else
  bad "cli_turn_json" "hs turn failed"
fi

if "$HS" history --session-id smoke-cli --limit 5 >"$OUT_DIR/history.json" 2>>"$LOG"; then
  ok "cli_history"
else
  bad "cli_history" "history failed"
fi

if "$HS" study "plugin" --limit 5 >"$OUT_DIR/study.json" 2>>"$LOG"; then
  ok "cli_study"
else
  bad "cli_study" "study failed"
fi

if PYTHONPATH="$ROOT/src" python3 "$ROOT/experiments/neural_rank_eval.py" >"$OUT_DIR/neural_eval.json" 2>>"$LOG"; then
  ok "neural_rank_eval"
else
  bad "neural_rank_eval" "eval failed"
fi

if PYTHONPATH="$ROOT/src" python3 >>"$LOG" 2>&1 <<PY
import importlib.util
from pathlib import Path
from hermespace.hermes_bridge import on_session_start, on_pre_llm_call, on_session_end
s = on_session_start(session_id="smoke")
assert s and s.get("context")
r = on_pre_llm_call(user_message="proceed deploy hermespace plugin", session_id="smoke")
assert r is None or (isinstance(r, dict) and "context" in r)
on_session_end(session_id="smoke")
p = Path("$ROOT/hermes_plugin/__init__.py")
spec = importlib.util.spec_from_file_location("hsplug", p)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
assert hasattr(mod, "register")
print("plugin_result", bool(r), "register_ok")
PY
then
  ok "hermes_plugin_pre_llm"
else
  bad "hermes_plugin_pre_llm" "plugin failed"
fi

python3 - <<PY
import json
from pathlib import Path
out = {
    "pass": int("$pass"),
    "fail": int("$fail"),
    "total": int("$pass") + int("$fail"),
    "ok": int("$fail") == 0,
    "hermespace_home": """$HERMESPACE_HOME""",
    "artifacts": sorted(p.name for p in Path("""$OUT_DIR""").iterdir()),
}
# attach neural eval summary if present
ne = Path("""$OUT_DIR""") / "neural_eval.json"
if ne.is_file():
    try:
        d = json.loads(ne.read_text())
        out["neural_eval"] = {
            "hash_mean_precision@3": d.get("hash_mean_precision@3"),
            "ollama_mean_precision@3": d.get("ollama_mean_precision@3"),
            "recommendation": d.get("recommendation"),
        }
    except Exception:
        pass
api = Path("""$OUT_DIR""") / "agent_api.json"
if api.is_file():
    try:
        out["agent_api"] = json.loads(api.read_text())
    except Exception:
        pass
Path("""$RESULTS""").write_text(json.dumps(out, indent=2))
print(json.dumps(out, indent=2))
PY

log "=== summary: pass=$pass fail=$fail ==="
log "results: $RESULTS"
# exit 0 only if all passed
[[ "$fail" -eq 0 ]]
