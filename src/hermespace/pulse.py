"""Hermespace Pulse — pocket-native runtime (smarter than bare cron).

Design:
- Jobs live under HERMESPACE_HOME (pocket only).
- A tick is cheap, idempotent, coalescing (missed windows → run once).
- Conditions read desk load, workbench mode, autonomy, pending access.
- Actions are pocket-safe builtins (dream, idle, viewport, mission scan…).
- External clock is optional: system cron/timer only needs `hs pulse tick`.
- Daemon mode loops ticks in-process for hosts without cron.

Not a Hermes cron fork — Hermespace world rhythm.
"""

from __future__ import annotations

import json
import os
import time
import traceback
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from hermespace.grid.secure_store import atomic_write_json, grid_root, read_json, safe_name


def _utcnow() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _now() -> float:
    return time.time()


# ── Models ──────────────────────────────────────────────────────────────────


@dataclass
class PulseJob:
    id: str
    name: str
    action: str  # dream | idle_tick | viewport | mission_pulse | selftalk_hygiene | custom
    enabled: bool = True
    # schedule
    every_sec: int = 900  # interval; 0 = event-only
    coalesce: bool = True  # if overdue, run once not N times
    # conditions (all that are set must pass)
    require_idle: bool = True
    max_load: float = 0.85  # skip when desk load total above this
    require_autonomy: bool = False
    only_if_missions: bool = False
    only_if_pending_access: bool = False
    quiet_hours: str = ""  # "23-8" local-ish UTC hour skip, empty=off
    # budget
    max_per_day: int = 48
    priority: int = 50  # higher first
    # payload
    params: dict[str, Any] = field(default_factory=dict)
    agent_id: str = "default"
    # runtime state
    last_run: float = 0.0
    last_status: str = ""
    last_error: str = ""
    runs_today: int = 0
    runs_day: str = ""  # YYYY-MM-DD
    next_due: float = 0.0
    created: str = field(default_factory=_utcnow)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "PulseJob":
        return cls(
            id=str(d.get("id") or uuid.uuid4().hex[:10]),
            name=str(d.get("name") or "job"),
            action=str(d.get("action") or "idle_tick"),
            enabled=bool(d.get("enabled", True)),
            every_sec=int(d.get("every_sec") or 900),
            coalesce=bool(d.get("coalesce", True)),
            require_idle=bool(d.get("require_idle", True)),
            max_load=float(d["max_load"]) if d.get("max_load") is not None else 0.85,
            require_autonomy=bool(d.get("require_autonomy", False)),
            only_if_missions=bool(d.get("only_if_missions", False)),
            only_if_pending_access=bool(d.get("only_if_pending_access", False)),
            quiet_hours=str(d.get("quiet_hours") or ""),
            max_per_day=int(d.get("max_per_day") or 48),
            priority=int(d.get("priority") or 50),
            params=dict(d.get("params") or {}),
            agent_id=safe_name(str(d.get("agent_id") or "default")),
            last_run=float(d.get("last_run") or 0),
            last_status=str(d.get("last_status") or ""),
            last_error=str(d.get("last_error") or ""),
            runs_today=int(d.get("runs_today") or 0),
            runs_day=str(d.get("runs_day") or ""),
            next_due=float(d.get("next_due") or 0),
            created=str(d.get("created") or _utcnow()),
        )


def _jobs_path() -> Path:
    return grid_root() / "pulse_jobs.json"


def _log_path() -> Path:
    return grid_root() / "pulse_log.jsonl"


def load_jobs() -> list[PulseJob]:
    raw = read_json(_jobs_path(), {"jobs": []})
    jobs = [PulseJob.from_dict(x) for x in (raw.get("jobs") or []) if isinstance(x, dict)]
    return jobs


def save_jobs(jobs: list[PulseJob]) -> None:
    atomic_write_json(
        _jobs_path(),
        {"jobs": [j.to_dict() for j in jobs], "updated": _utcnow()},
    )


def ensure_defaults(agent_id: str = "default") -> list[PulseJob]:
    """Seed built-in rhythm if empty."""
    jobs = load_jobs()
    if jobs:
        return jobs
    seeds = [
        PulseJob(
            id="idle_maintain",
            name="Idle maintain",
            action="idle_tick",
            every_sec=900,
            require_idle=True,
            max_load=0.9,
            priority=40,
            agent_id=agent_id,
            params={"consolidate_every": 3},
        ),
        PulseJob(
            id="dream_cycle",
            name="Dream cycle",
            action="dream",
            every_sec=6 * 3600,
            require_idle=True,
            max_load=0.7,
            priority=70,
            max_per_day=4,
            agent_id=agent_id,
            quiet_hours="",  # set e.g. "9-17" to skip busy UTC hours
        ),
        PulseJob(
            id="viewport_refresh",
            name="Viewport refresh",
            action="viewport",
            every_sec=300,
            require_idle=False,
            max_load=1.0,
            priority=20,
            agent_id=agent_id,
        ),
        PulseJob(
            id="mission_pulse",
            name="Mission pulse",
            action="mission_pulse",
            every_sec=3600,
            require_idle=True,
            only_if_missions=True,
            max_load=0.8,
            priority=60,
            agent_id=agent_id,
        ),
        PulseJob(
            id="access_watch",
            name="Access request watch",
            action="access_watch",
            every_sec=120,
            require_idle=False,
            only_if_pending_access=True,
            max_load=1.0,
            priority=80,
            agent_id=agent_id,
            max_per_day=200,
        ),
        PulseJob(
            id="world_evolve",
            name="World evolution",
            action="world_evolve",
            every_sec=3600,
            require_idle=True,
            max_load=0.8,
            priority=65,
            agent_id=agent_id,
        ),
    ]
    save_jobs(seeds)
    return seeds


def get_job(job_id: str) -> PulseJob | None:
    for j in load_jobs():
        if j.id == job_id:
            return j
    return None


def upsert_job(job: PulseJob) -> PulseJob:
    jobs = load_jobs()
    out: list[PulseJob] = []
    found = False
    for j in jobs:
        if j.id == job.id:
            out.append(job)
            found = True
        else:
            out.append(j)
    if not found:
        out.append(job)
    save_jobs(out)
    return job


def delete_job(job_id: str) -> bool:
    jobs = load_jobs()
    n = len(jobs)
    jobs = [j for j in jobs if j.id != job_id]
    save_jobs(jobs)
    return len(jobs) < n


def set_enabled(job_id: str, enabled: bool) -> PulseJob | None:
    j = get_job(job_id)
    if not j:
        return None
    j.enabled = enabled
    upsert_job(j)
    return j


def append_log(entry: dict[str, Any]) -> None:
    p = _log_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(entry, default=str) + "\n"
    with p.open("a", encoding="utf-8") as f:
        f.write(line)
    # Cheap size guard: only trim when file grows large (avoid read-full every tick)
    try:
        if p.stat().st_size > 256_000:
            lines = p.read_text(encoding="utf-8").splitlines()
            if len(lines) > 500:
                p.write_text("\n".join(lines[-400:]) + "\n", encoding="utf-8")
    except OSError:
        pass


# ── World sensors ───────────────────────────────────────────────────────────


def _desk_context(agent_id: str) -> dict[str, Any]:
    ctx: dict[str, Any] = {
        "mode": "idle",
        "load_total": 0.0,
        "missions_open": 0,
        "pending_access": 0,
        "autonomy": False,
    }
    try:
        from hermespace.store import load_desk

        desk = load_desk()
        load = desk.load or {}
        # load may be dict with total or I/E/G
        tot = load.get("total")
        if tot is None:
            try:
                tot = float(load.get("I", 0) or 0) * 0.5 + float(load.get("E", 0) or 0) * 0.3
            except Exception:
                tot = 0.0
        ctx["load_total"] = float(tot or 0)
        ctx["goal"] = desk.goal
        ctx["executive"] = desk.executive
    except Exception as e:  # noqa: BLE001
        ctx["desk_error"] = type(e).__name__

    try:
        from hermespace.workbench import Workbench

        wb = Workbench(agent_id=agent_id, session_id="default")
        st = wb.status()
        ctx["mode"] = st.get("mode") or "idle"
        ctx["idle_ticks"] = st.get("idle_ticks")
    except Exception:
        pass

    try:
        from hermespace.grid.missions import list_missions

        ctx["missions_open"] = len(
            [m for m in list_missions(agent_id) if m.status in ("active", "open", "blocked")]
        )
    except Exception:
        pass

    try:
        from hermespace.grid.access import list_requests

        ctx["pending_access"] = len(list_requests(agent_id=agent_id, status="pending"))
    except Exception:
        pass

    try:
        from hermespace.grid.gates import autonomy_enabled

        ctx["autonomy"] = bool(autonomy_enabled())
    except Exception:
        ctx["autonomy"] = os.environ.get("HERMESPACE_AUTONOMY", "0") in ("1", "true", "yes")

    return ctx


def _in_quiet_hours(spec: str) -> bool:
    """spec '23-8' means skip from hour 23 inclusive to 8 exclusive (UTC)."""
    if not spec or "-" not in spec:
        return False
    try:
        a, b = spec.split("-", 1)
        start, end = int(a), int(b)
        h = datetime.now(timezone.utc).hour
        if start == end:
            return False
        if start < end:
            return start <= h < end
        # wraps midnight
        return h >= start or h < end
    except Exception:
        return False


def job_due(job: PulseJob, now: float | None = None) -> tuple[bool, str]:
    now = now if now is not None else _now()
    if not job.enabled:
        return False, "disabled"
    if job.every_sec <= 0:
        return False, "event_only"
    # daily budget
    day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    if job.runs_day != day:
        # reset happens on run; treat as 0
        runs = 0
    else:
        runs = job.runs_today
    if runs >= job.max_per_day:
        return False, "daily_budget"
    if _in_quiet_hours(job.quiet_hours):
        return False, "quiet_hours"
    if job.last_run <= 0:
        return True, "never_run"
    elapsed = now - job.last_run
    if elapsed >= job.every_sec:
        return True, "interval_elapsed"
    return False, f"wait_{int(job.every_sec - elapsed)}s"


def conditions_ok(job: PulseJob, world: dict[str, Any]) -> tuple[bool, str]:
    if job.require_idle and (world.get("mode") or "idle") not in ("idle", "paused"):
        return False, f"mode={world.get('mode')}"
    if float(world.get("load_total") or 0) > float(job.max_load):
        return False, f"load={world.get('load_total')}>{job.max_load}"
    if job.require_autonomy and not world.get("autonomy"):
        return False, "autonomy_off"
    if job.only_if_missions and int(world.get("missions_open") or 0) <= 0:
        return False, "no_missions"
    if job.only_if_pending_access and int(world.get("pending_access") or 0) <= 0:
        return False, "no_pending_access"
    return True, "ok"


# ── Actions ─────────────────────────────────────────────────────────────────


def _action_idle_tick(job: PulseJob, world: dict[str, Any]) -> dict[str, Any]:
    from hermespace.workbench import Workbench

    wb = Workbench(agent_id=job.agent_id, session_id="pulse")
    every = int((job.params or {}).get("consolidate_every") or 3)
    return wb.idle_tick(consolidate_every=every)


def _action_dream(job: PulseJob, world: dict[str, Any]) -> dict[str, Any]:
    from hermespace.grid.dream import run_dream

    return run_dream(job.agent_id).to_dict()


def _action_viewport(job: PulseJob, world: dict[str, Any]) -> dict[str, Any]:
    from hermespace.grid.viewport import write_viewport_files

    return write_viewport_files(job.agent_id)


def _action_mission_pulse(job: PulseJob, world: dict[str, Any]) -> dict[str, Any]:
    from hermespace.grid.missions import list_missions
    from hermespace.grid.selftalk import say

    ms = [m for m in list_missions(job.agent_id) if m.status in ("active", "open", "blocked")]
    if not ms:
        return {"ok": True, "skipped": "no_missions"}
    top = sorted(ms, key=lambda m: -int(m.priority or 0))[:3]
    note = "Mission pulse: " + "; ".join(f"{m.title}[{m.status}]" for m in top)
    say(note, agent_id=job.agent_id, role="planner")
    return {"ok": True, "missions": [m.to_dict() for m in top], "note": note}


def _action_access_watch(job: PulseJob, world: dict[str, Any]) -> dict[str, Any]:
    from hermespace.grid.access import list_requests, pending_inject_block
    from hermespace.grid.selftalk import say

    pending = list_requests(agent_id=job.agent_id, status="pending")
    if not pending:
        return {"ok": True, "pending": 0}
    say(
        f"Access watch: {len(pending)} pending — user can approve in chat/Desktop.",
        agent_id=job.agent_id,
        role="system",
    )
    # refresh viewport so Desktop sees them
    try:
        from hermespace.grid.viewport import write_viewport_files

        write_viewport_files(job.agent_id)
    except Exception:
        pass
    return {
        "ok": True,
        "pending": len(pending),
        "ids": [r.id for r in pending],
        "inject_hint": pending_inject_block(job.agent_id)[:400],
    }


def _action_selftalk_hygiene(job: PulseJob, world: dict[str, Any]) -> dict[str, Any]:
    from hermespace.grid.selftalk import recent

    rows = recent(job.agent_id, limit=5)
    return {"ok": True, "recent": len(rows)}


def _action_world_evolve(job: PulseJob, world: dict[str, Any]) -> dict[str, Any]:
    from hermespace.world import WorldModel

    wm = WorldModel(agent_id=job.agent_id)
    result = wm.evolve()
    return result



ACTIONS: dict[str, Callable[[PulseJob, dict[str, Any]], dict[str, Any]]] = {
    "idle_tick": _action_idle_tick,
    "dream": _action_dream,
    "viewport": _action_viewport,
    "mission_pulse": _action_mission_pulse,
    "access_watch": _action_access_watch,
    "selftalk_hygiene": _action_selftalk_hygiene,
    "world_evolve": _action_world_evolve,
}


def run_job(
    job: PulseJob,
    *,
    force: bool = False,
    world: dict[str, Any] | None = None,
    persist: bool = True,
) -> dict[str, Any]:
    world = world or _desk_context(job.agent_id)
    now = _now()
    day = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    if not force:
        due, why = job_due(job, now)
        if not due:
            return {"ok": False, "skipped": True, "reason": why, "job": job.id}
        ok, why = conditions_ok(job, world)
        if not ok:
            return {"ok": False, "skipped": True, "reason": why, "job": job.id}

    fn = ACTIONS.get(job.action)
    if not fn:
        job.last_status = "error"
        job.last_error = f"unknown_action:{job.action}"
        if persist:
            upsert_job(job)
        return {"ok": False, "error": job.last_error, "job": job.id}

    try:
        result = fn(job, world)
        if job.runs_day != day:
            job.runs_today = 0
            job.runs_day = day
        job.runs_today += 1
        job.last_run = now
        job.next_due = now + max(0, job.every_sec)
        job.last_status = "ok"
        job.last_error = ""
        if persist:
            upsert_job(job)
        entry = {
            "ts": _utcnow(),
            "job": job.id,
            "action": job.action,
            "status": "ok",
            "result_keys": list(result.keys()) if isinstance(result, dict) else [],
        }
        # Don't dump huge result payloads into the log every tick
        if isinstance(result, dict) and len(json.dumps(result, default=str)) < 800:
            entry["result"] = result
        append_log(entry)
        return {"ok": True, "job": job.id, "action": job.action, "result": result}
    except Exception as e:  # noqa: BLE001
        job.last_status = "error"
        job.last_error = f"{type(e).__name__}: {e}"[:300]
        job.last_run = now  # backoff even on error if coalesce
        if persist:
            upsert_job(job)
        append_log(
            {
                "ts": _utcnow(),
                "job": job.id,
                "action": job.action,
                "status": "error",
                "error": job.last_error,
                "trace": traceback.format_exc()[-500:],
            }
        )
        return {"ok": False, "job": job.id, "error": job.last_error}


def tick(
    *,
    agent_id: str | None = None,
    force: bool = False,
    seed_defaults: bool = True,
) -> dict[str, Any]:
    """Evaluate due jobs. Missed windows coalesce (run once)."""
    # Master switch from pocket controls
    if not force:
        try:
            from hermespace.grid.controls import get_flag

            if not get_flag("pulse_runtime", True):
                return {
                    "ts": _utcnow(),
                    "ran": 0,
                    "skipped": 0,
                    "errors": 0,
                    "jobs": 0,
                    "results": [{"ok": False, "skipped": True, "reason": "pulse_runtime_off"}],
                    "worlds": {},
                }
        except Exception:
            pass
    if seed_defaults:
        ensure_defaults(agent_id or "default")
    all_jobs = load_jobs()
    by_id = {j.id: j for j in all_jobs}
    jobs = all_jobs
    if agent_id:
        aid = safe_name(agent_id)
        jobs = [j for j in all_jobs if j.agent_id in (aid, "default")]
    # shared world per agent
    worlds: dict[str, dict[str, Any]] = {}
    results: list[dict[str, Any]] = []
    jobs_sorted = sorted(jobs, key=lambda j: (-int(j.priority), j.id))
    ran = 0
    skipped = 0
    errors = 0
    dirty = False
    for job in jobs_sorted:
        w = worlds.get(job.agent_id)
        if w is None:
            w = _desk_context(job.agent_id)
            worlds[job.agent_id] = w
        out = run_job(job, force=force, world=w, persist=False)
        results.append(out)
        if out.get("skipped"):
            skipped += 1
        elif out.get("ok"):
            ran += 1
            dirty = True
            by_id[job.id] = job
        else:
            errors += 1
            dirty = True
            by_id[job.id] = job
    if dirty:
        # one atomic write for all job state (not N fsyncs per job)
        save_jobs(list(by_id.values()))
    summary = {
        "ts": _utcnow(),
        "ran": ran,
        "skipped": skipped,
        "errors": errors,
        "jobs": len(jobs_sorted),
        "results": results,
        "worlds": worlds,
    }
    append_log({"ts": summary["ts"], "event": "tick", "ran": ran, "skipped": skipped, "errors": errors})
    return summary


def status(agent_id: str = "default", *, light: bool = False) -> dict[str, Any]:
    """Job board + world sensors. light=True skips ensure_defaults thrash if empty file ok."""
    if not light:
        ensure_defaults(agent_id)
    elif not _jobs_path().is_file():
        ensure_defaults(agent_id)
    jobs = load_jobs()
    world = _desk_context(agent_id)
    now = _now()
    rows = []
    for j in sorted(jobs, key=lambda x: (-x.priority, x.name)):
        due, why = job_due(j, now)
        ok, cwhy = (
            conditions_ok(j, world)
            if j.agent_id in (agent_id, "default", safe_name(agent_id))
            else (True, "other_agent")
        )
        if light:
            rows.append(
                {
                    "id": j.id,
                    "name": j.name,
                    "action": j.action,
                    "enabled": j.enabled,
                    "every_sec": j.every_sec,
                    "due": due,
                    "due_reason": why,
                    "conditions_ok": ok,
                    "conditions_reason": cwhy,
                    "last_status": j.last_status,
                    "last_run": j.last_run,
                }
            )
        else:
            rows.append(
                {
                    **j.to_dict(),
                    "due": due,
                    "due_reason": why,
                    "conditions_ok": ok,
                    "conditions_reason": cwhy,
                    "seconds_since_run": (now - j.last_run) if j.last_run else None,
                }
            )
    return {
        "ts": _utcnow(),
        "world": world,
        "jobs": rows,
        "actions": sorted(ACTIONS.keys()),
        "hint": "Drive with: hs pulse tick  (cron */1)  or  hs pulse daemon",
    }


def compact_summary(agent_id: str = "default") -> dict[str, Any]:
    """Cheap pulse blurb for viewport snapshots."""
    st = status(agent_id, light=True)
    jobs = st.get("jobs") or []
    return {
        "jobs": len(jobs),
        "due": sum(1 for j in jobs if j.get("due") and j.get("conditions_ok")),
        "enabled": sum(1 for j in jobs if j.get("enabled")),
        "hint": st.get("hint"),
    }


def daemon_loop(interval_sec: int = 60, *, agent_id: str | None = None, max_ticks: int = 0) -> None:
    """In-process loop. max_ticks=0 means forever."""
    n = 0
    interval_sec = max(5, int(interval_sec))
    print(f"pulse daemon interval={interval_sec}s agent={agent_id or '*'}", flush=True)
    while True:
        summary = tick(agent_id=agent_id, seed_defaults=True)
        print(
            f"[{summary['ts']}] ran={summary['ran']} skipped={summary['skipped']} err={summary['errors']}",
            flush=True,
        )
        n += 1
        if max_ticks and n >= max_ticks:
            break
        time.sleep(interval_sec)
