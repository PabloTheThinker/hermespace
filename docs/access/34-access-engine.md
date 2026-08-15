# Access Engine — Hermespace's open access workspace for Hermes Agent

**Version:** 0.24.0  
**Product name:** Hermespace **Access Engine** / **Access Workspace**  
**Thesis:** Hermes Agent usually has no weight access. Hermespace therefore
ships its own privileged verbalizable workspace — an open-source harness the
operator can read, shape, and audit.

---

## 1. One engine

```python
from hermespace import AccessEngine

eng = AccessEngine(agent_id="my-agent")
eng.connect()
out = eng.turn("First repro then patch then verify", goal="Fix auth")
print(eng.decode_user(out))                # short Report
print(eng.decode_model(out)[:400])         # dense context (never dump to chat)
print(eng.lens())
eng.chain("spider", "8 legs")
eng.swap("ship now", "canary first")
print(eng.access_roles())
eng.harvest()
```

```bash
hs base connect
hs base roles
hs base metrics
hs base turn -m "First check then implement finally verify" --goal "Ship"
hs access hold -t "canary first"
hs access lens
hs base harvest
```

`HermesBase` is a thin alias of `AccessEngine`. Desk file ops remain in
`HermespaceEngine` (desk spine only).

---

## 2. Five access roles

| Role | Engine API |
|------|------------|
| Verbal report | `report()` · `decode_user()` |
| Directed modulation | `hold` · `swap` · `inject` · `ablate` |
| Internal reasoning | `chain()` · OEW auto-park · silent hub |
| Flexible broadcast | `broadcast()` → pre_llm / desk / fabric |
| Selectivity | `probe_material()` · gate skip on trivial acks |

Warehouse / HermesCube (if installed) is **optional arterial supply**.

---

## 3. Brand note

This product is **Hermespace Access Workspace** — not named after any third-party
interpretability term. Research inspiration may be cited in assessment docs;
the shipped API, CLI, and package are Hermespace's own (`hermespace.access`).

Deprecated import shim: `hermespace.jspace` → re-exports `hermespace.access`.

---

## 4. Architecture

```
Hermes Agent (tools · skills · fluency)
        │ material turns
        ▼
 AccessEngine  ←── hs base / hs access / plugin hooks
   ├── AccessHub (≤25) · FOA (≤4) · silent chain
   ├── OEW protocol (default ON)
   ├── dual decode (Report ≠ inject)
   └── night harvest → semantic / optional warehouse
```
