# Pre-update hardening (v0.16.1)

Notes from pre-update test pass — fixed:

| Note | Fix |
|------|-----|
| Plugin lacked `__version__` | `hermes_plugin.__version__` + log on register |
| Viewport write ~3× snapshot cost | Single snap shared by md/html/json |
| Pulse tick N× atomic fsync | Batch `save_jobs` once per tick |
| Pulse log full-read trim every event | Size-gated trim (~256KB) |
| Dream default quiet_hours 9–17 UTC | Default empty (opt-in) |
| Fat pulse results in jsonl | Log keys / small payloads only |

Follow-ups shipped in **0.17**: Desktop pulse job table + `/api/pulse`; `install_pulse_timer.sh`.
