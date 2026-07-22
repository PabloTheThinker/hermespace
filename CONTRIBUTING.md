# Contributing to Hermespace

Thanks for helping. Hermespace is a **companion workbench for [Hermes Agent](https://github.com/NousResearch/hermes-agent)** — keep that scope.

## Ground rules

1. **Host-agnostic public tree** — no operator home paths, secrets, personal data, or private host names in git. Run `./scripts/security_audit.sh` before every push.
2. **Honesty** — harness-level cognition only. No claims of model-weight access, medical use, or consciousness.
3. **Does not replace Hermes** — skills, MEMORY.md, gateway, and tools stay Hermes-owned; we rank/inject/broadcast.
4. **Smoke stays green** — `./scripts/smoke_test.sh` expect **9/9** after behavioral changes.
5. **Versions move together** — `src/hermespace/__init__.py` `__version__` and `hermes_plugin/plugin.yaml` `version`.

## Dev setup

```bash
git clone https://github.com/PabloTheThinker/hermespace.git
cd hermespace
export PYTHONPATH="$PWD/src"
./scripts/install_hermes.sh   # optional local Hermes link
./scripts/smoke_test.sh
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

## Where to change what

| Area | Path |
|------|------|
| Core runtime | `src/hermespace/` |
| Hermes hooks | `src/hermespace/hermes_bridge.py` + thin `hermes_plugin/` |
| Agent skill | `skills/hermespace/` |
| CLI | `src/hermespace/cli.py`, `scripts/hs` |
| Tests | `tests/` |
| Maintainer note | `FOR_HERMES.md` |
| Integration doors | `INTEGRATION.md`, `WORKFLOW.md` |

## PR checklist

- [ ] `security_audit` OK  
- [ ] unittest + smoke 9/9  
- [ ] Skill/docs updated if operator procedure changed  
- [ ] No runtime state (`ACTIVE.md`, `*.db`, journal) committed  
- [ ] Dual-decode rules preserved (report ≠ context dump)  

## Code of conduct

Be kind. Assume good intent. Prefer short, evidence-backed discussion (logs, smoke output, API shapes).
