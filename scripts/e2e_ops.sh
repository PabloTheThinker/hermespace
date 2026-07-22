#!/usr/bin/env bash
# End-to-end everyday ops: boot → pulse → access → dream → skillbench → selftalk → viewport
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
export PYTHONPATH="${ROOT}/src${PYTHONPATH:+:$PYTHONPATH}"
export HERMESPACE_HOME="${HERMESPACE_HOME:-$(mktemp -d /tmp/hs-e2e-XXXX)}"
export HERMESPACE_AUTONOMY=0
export HERMESPACE_ROOT="$ROOT"
HS=(python3 -m hermespace.cli)
ec=0
pass() { echo "PASS  $*"; }
fail() { echo "FAIL  $*"; ec=1; }

echo "=== Hermespace E2E ops ==="
echo "HERMESPACE_HOME=$HERMESPACE_HOME"

"${HS[@]}" ops boot --agent-id default >/tmp/hs-e2e-boot.json || fail "ops boot"
python3 - <<'PY' || fail "boot json"
import json
d=json.load(open("/tmp/hs-e2e-boot.json"))
assert d.get("ok") or d.get("tick"), d
assert d.get("tick",{}).get("jobs",0)>=1
print("boot_ok", d["tick"].get("ran"), d["tick"].get("skipped"))
PY
pass "ops boot"

"${HS[@]}" ops doctor >/tmp/hs-e2e-doc.json || true
python3 - <<'PY' || fail "doctor core"
import json
d=json.load(open("/tmp/hs-e2e-doc.json"))
assert d.get("ok") or d.get("tick"), d
print("doctor_ok", d.get("version"))
PY
pass "ops doctor core"

# access flow
"${HS[@]}" grid access-request --path /tmp/hs-e2e-out --reason e2e --hours 1 --agent-id default >/tmp/hs-e2e-req.json
RID=$(python3 -c 'import json;print(json.load(open("/tmp/hs-e2e-req.json")).get("id") or json.load(open("/tmp/hs-e2e-req.json")).get("request",{}).get("id",""))')
# CLI may print differently - python API fallback
python3 - <<'PY'
import json, os, sys
sys.path.insert(0, os.environ["PYTHONPATH"].split(":")[0])
from hermespace.grid.access import request_access, approve_request, list_requests
from hermespace.grid.boundary import check_path
r = request_access("/tmp/hs-e2e-out2", reason="e2e", hours=1)
assert r.id
out = approve_request(r.id, resolver="e2e")
assert out.get("ok"), out
dec = check_path("/tmp/hs-e2e-out2", mode="write")
assert dec.allowed, dec
print("access_ok", r.id, dec)
PY
pass "access request/approve"

# missions + dream + skillbench + selftalk
python3 - <<'PY'
import sys, os
sys.path.insert(0, os.environ["PYTHONPATH"].split(":")[0])
from hermespace.grid.missions import add_mission, list_missions, update_mission
from hermespace.grid.dream import run_dream, last_dreams
from hermespace.grid.skillbench import register_module, merge_skills, list_modules
from hermespace.grid.selftalk import say, recent
from hermespace import pulse
from hermespace.grid.viewport import write_viewport_files

m = add_mission(title="e2e mission", priority=1)
update_mission(m.id, status="active")
assert m
d = run_dream("default", force_material=True)
assert d
say("e2e selftalk note", role="ops")
mod = register_module(name="e2e-mod-a", body="# e2e A\nDo A.\n", source="e2e")
mod2 = register_module(name="e2e-mod-b", body="# e2e B\nDo B.\n", source="e2e")
assert mod and mod2
prop = merge_skills("e2e-mod-a", "e2e-mod-b", new_name="e2e-merged")
assert prop
tick = pulse.tick(agent_id="default")
assert "ran" in tick
paths = write_viewport_files()
html = open(paths["html"]).read()
assert "kpi-row" in html and "<pre>" not in html
assert list_missions()
assert last_dreams()
assert recent()
assert list_modules()
print("grid_surfaces_ok", tick.get("ran"), tick.get("skipped"))
PY
pass "missions dream skillbench selftalk pulse viewport"

"${HS[@]}" ops tick-all --dream >/tmp/hs-e2e-tick.json
python3 - <<'PY' || fail "tick-all"
import json
d=json.load(open("/tmp/hs-e2e-tick.json"))
assert "pulse" in d and "viewport" in d
print("tick_all_ok", d["pulse"].get("ran"))
PY
pass "ops tick-all"

# chat regulate
"${HS[@]}" grid regulate -m "show boundary" --agent-id default >/tmp/hs-e2e-reg.json
python3 - <<'PY' || fail "regulate"
import json
d=json.load(open("/tmp/hs-e2e-reg.json"))
assert d.get("handled") is True
print("regulate_ok", d.get("action"))
PY
pass "chat regulate"

echo "=== summary: $([[ $ec -eq 0 ]] && echo E2E_PASS || echo E2E_FAIL) home=$HERMESPACE_HOME ==="
exit $ec
