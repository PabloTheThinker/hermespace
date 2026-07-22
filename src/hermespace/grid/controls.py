"""Operator controls — durable toggles for the pocket (viewport / API / CLI).

Stored under grid_root()/controls.json so viewport can flip autonomy without
restarting the process env. Env HERMESPACE_AUTONOMY still wins if set to force
on/off for a session (see autonomy_enabled resolution).
"""

from __future__ import annotations

from typing import Any

from hermespace.grid.secure_store import atomic_write_json, grid_root, read_json

_CONTROLS = "controls.json"

# Keys allowed from viewport/API (deny free-form injection)
_ALLOWED_BOOL = {
    "autonomy",
    "pulse_runtime",  # master: when false, pulse.tick no-ops job runs except forced
    "auto_dream",  # soft flag (pulse dream job still has own enable)
    "auto_order",  # HERMESPACE_AUTO_ORDER equivalent pocket flag
}


def _path():
    return grid_root() / _CONTROLS


def default_controls() -> dict[str, Any]:
    return {
        "autonomy": False,
        "pulse_runtime": True,
        "auto_dream": True,
        "auto_order": False,
        "updated": "",
        "source": "default",
    }


def load_controls() -> dict[str, Any]:
    raw = read_json(_path(), {})
    base = default_controls()
    if not isinstance(raw, dict):
        return base
    for k in _ALLOWED_BOOL:
        if k in raw:
            base[k] = bool(raw[k])
    if raw.get("updated"):
        base["updated"] = str(raw["updated"])[:40]
    if raw.get("source"):
        base["source"] = str(raw["source"])[:40]
    return base


def save_controls(data: dict[str, Any], *, source: str = "api") -> dict[str, Any]:
    from datetime import datetime, timezone

    cur = load_controls()
    for k in _ALLOWED_BOOL:
        if k in data:
            cur[k] = bool(data[k])
    cur["updated"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    cur["source"] = (source or "api")[:40]
    atomic_write_json(_path(), cur)
    return cur


def set_flag(name: str, enabled: bool, *, source: str = "api") -> dict[str, Any]:
    if name not in _ALLOWED_BOOL:
        raise ValueError(f"unknown control: {name}")
    return save_controls({name: bool(enabled)}, source=source)


def get_flag(name: str, default: bool = False) -> bool:
    if name not in _ALLOWED_BOOL:
        return default
    return bool(load_controls().get(name, default))


def controls_public(*, agent_id: str = "default") -> dict[str, Any]:
    """Bundle for viewport/API: flags + pulse jobs."""
    from hermespace import pulse
    from hermespace.grid.gates import gate_status

    pulse.ensure_defaults(agent_id)
    jobs = []
    for j in pulse.load_jobs():
        if j.agent_id not in (agent_id, "default"):
            continue
        jobs.append(
            {
                "id": j.id,
                "name": j.name,
                "action": j.action,
                "enabled": j.enabled,
                "every_sec": j.every_sec,
            }
        )
    flags = load_controls()
    gs = gate_status()
    return {
        "flags": flags,
        "autonomy_effective": bool(gs.get("autonomy_enabled")),
        "pulse_jobs": jobs,
        "notes": {
            "autonomy": "When on, agent may self-order within budget (still pocket-bound).",
            "pulse_runtime": "Master switch for unattended pulse ticks.",
            "auto_dream": "Prefer dream_cycle job when pulse runs.",
            "auto_order": "Plugin may auto-receive_order on user messages.",
        },
    }


def apply_control_patch(data: dict[str, Any], *, agent_id: str = "default", source: str = "viewport") -> dict[str, Any]:
    """Apply flag and/or pulse job toggles from API body."""
    from hermespace import pulse

    out: dict[str, Any] = {"ok": True, "changed": []}
    raw_flags = data.get("flags")
    if isinstance(raw_flags, dict):
        flags_in = raw_flags
    elif isinstance(data, dict):
        flags_in = data
    else:
        flags_in = {}
    patch = {k: bool(flags_in[k]) for k in _ALLOWED_BOOL if k in flags_in}
    if patch:
        out["flags"] = save_controls(patch, source=source)
        out["changed"].extend(patch.keys())
    else:
        out["flags"] = load_controls()

    # pulse jobs: { "pulse": { "job_id": true/false } } or list
    pulse_map = data.get("pulse") or data.get("jobs") or {}
    if isinstance(pulse_map, dict):
        for jid, en in pulse_map.items():
            j = pulse.set_enabled(str(jid), bool(en))
            if j:
                out["changed"].append(f"pulse:{j.id}={'on' if j.enabled else 'off'}")
    # single job convenience
    if data.get("job_id") is not None and "enabled" in data:
        j = pulse.set_enabled(str(data["job_id"]), bool(data["enabled"]))
        if j:
            out["changed"].append(f"pulse:{j.id}={'on' if j.enabled else 'off'}")

    out["controls"] = controls_public(agent_id=agent_id)
    return out
