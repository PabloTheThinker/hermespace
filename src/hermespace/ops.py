"""Everyday ops — boot/doctor/tick so Hermespace is usable without ceremony."""

from __future__ import annotations

import os
import socket
import time
from pathlib import Path
from typing import Any

from hermespace import __version__
from hermespace.paths import hermespace_home, package_root, state_dir


def _port_open(host: str, port: int, timeout: float = 0.4) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def doctor(*, agent_id: str = "default", port: int = 8764, host: str = "127.0.0.1") -> dict[str, Any]:
    """Non-destructive health snapshot for operators and agents."""
    home = hermespace_home()
    checks: list[dict[str, Any]] = []

    def add(ok: bool, name: str, detail: str = "") -> None:
        checks.append({"ok": ok, "name": name, "detail": detail})

    add(True, "version", __version__)
    add(home.is_dir() or True, "hermespace_home", str(home))
    add((package_root() / "src" / "hermespace").is_dir(), "package_src", str(package_root()))

    # imports
    try:
        from hermespace import pulse
        from hermespace.grid import access, boundary, dream, skillbench, selftalk, viewport
        from hermespace.grid.missions import list_missions

        add(True, "imports", "pulse+grid")
    except Exception as exc:  # noqa: BLE001
        add(False, "imports", str(exc))
        return {"ok": False, "checks": checks, "home": str(home)}

    try:
        pulse.ensure_defaults(agent_id)
        st = pulse.status(agent_id, light=True)
        jobs = st.get("jobs") or []
        n = len(jobs) if isinstance(jobs, list) else int(jobs or 0)
        add(n >= 1, "pulse_jobs", f"jobs={n}")
    except Exception as exc:  # noqa: BLE001
        add(False, "pulse_jobs", str(exc))

    try:
        from hermespace.world import WorldModel
        wm = WorldModel(agent_id=agent_id)
        add(True, "world", "agent={} beliefs={} evolutions={}".format(wm.state.agent_id, len(wm.state.beliefs), wm.state.evolution_count))
    except Exception as exc:
        add(False, "world", str(exc))

    try:
        pol = boundary.load_policy()
        add(pol.project_write_default == "deny", "boundary_default_deny", pol.project_write_default)
        pend = access.list_requests(agent_id=agent_id, status="pending")
        add(True, "access_pending", str(len(pend)))
    except Exception as exc:  # noqa: BLE001
        add(False, "boundary_access", str(exc))

    try:
        ms = list_missions(agent_id)
        add(True, "missions", str(len(ms)))
        mods = skillbench.list_modules(agent_id)
        add(True, "skillbench_modules", str(len(mods)))
        talk = selftalk.recent(agent_id, limit=3)
        add(True, "selftalk", str(len(talk)))
        dreams = dream.last_dreams(agent_id, limit=3)
        add(True, "dreams", str(len(dreams)))
    except Exception as exc:  # noqa: BLE001
        add(False, "grid_surface", str(exc))

    try:
        paths = viewport.write_viewport_files(agent_id)
        html = Path(paths["html"]).read_text(encoding="utf-8")
        add("kpi-row" in html, "viewport_html", paths["html"])
    except Exception as exc:  # noqa: BLE001
        add(False, "viewport_html", str(exc))

    from hermespace.grid.view_server import tailscale_ipv4
    hosts_try = [host or "127.0.0.1", "127.0.0.1"]
    tip = tailscale_ipv4()
    if tip:
        hosts_try.append(tip)
    serve_up = any(_port_open(h, port) for h in dict.fromkeys(hosts_try))
    add(serve_up, "viewport_serve", f"port {port} on {', '.join(dict.fromkeys(hosts_try))}")
    if tip:
        add(True, "tailscale_ipv4", tip)
    else:
        add(False, "tailscale_ipv4", "not detected (optional — install/login tailscale)")

    # hermes plugin door
    hh = Path(os.environ.get("HERMES_HOME", Path.home() / ".hermes")).expanduser()
    plug = hh / "plugins" / "hermespace"
    desk = hh / "desktop-plugins" / "hermespace" / "plugin.js"
    add(plug.exists(), "hermes_plugin_link", str(plug))
    add(desk.is_file(), "desktop_plugin", str(desk))

    ok = all(c["ok"] for c in checks if c["name"] not in {"viewport_serve", "hermes_plugin_link", "desktop_plugin"})
    # soft: serve/desktop may be off — still "ops ready" if core ok
    core_ok = all(
        c["ok"]
        for c in checks
        if c["name"]
        in {
            "imports",
            "pulse_jobs",
            "boundary_default_deny",
            "viewport_html",
            "version",
        }
    )
    return {
        "ok": core_ok,
        "all_green": all(c["ok"] for c in checks),
        "checks": checks,
        "home": str(home),
        "state_dir": str(state_dir()),
        "version": __version__,
        "serve_up": serve_up,
        "hints": _hints(checks, port),
    }


def _hints(checks: list[dict[str, Any]], port: int) -> list[str]:
    by = {c["name"]: c for c in checks}
    out: list[str] = []
    if not by.get("viewport_serve", {}).get("ok"):
        out.append(f"Start viewport: hs view --serve --port {port}")
    if not by.get("desktop_plugin", {}).get("ok"):
        out.append("Install Desktop plugin: ./scripts/install_desktop_plugin.sh then Reload desktop plugins")
    if not by.get("hermes_plugin_link", {}).get("ok"):
        out.append("Install Hermes plugin: ./scripts/install_hermes.sh && hermes plugins enable hermespace")
    if not by.get("pulse_jobs", {}).get("ok"):
        out.append("Seed pulse: hs pulse status")
    return out


def boot(
    *,
    agent_id: str = "default",
    tick: bool = True,
    write_viewport: bool = True,
    seed_pulse: bool = True,
) -> dict[str, Any]:
    """Bring pocket subsystems to a known-good everyday state."""
    from hermespace import pulse
    from hermespace.grid.viewport import write_viewport_files
    from hermespace.workbench import Workbench

    out: dict[str, Any] = {"agent_id": agent_id, "version": __version__, "home": str(hermespace_home())}

    wb = Workbench(agent_id=agent_id, session_id="ops-boot")
    out["workbench"] = wb.enter()

    try:
        from hermespace.world import WorldModel
        wm = WorldModel(agent_id=agent_id)
        wm.enter()
        out["world"] = {"agent_id": agent_id, "beliefs": len(wm.state.beliefs), "landmarks": len(wm.state.landmarks)}
    except Exception as exc:
        out["world"] = {"error": str(exc)}

    if seed_pulse:
        jobs = pulse.ensure_defaults(agent_id)
        out["pulse_jobs"] = len(jobs)

    if tick:
        out["tick"] = pulse.tick(agent_id=agent_id, seed_defaults=True)

    if write_viewport:
        out["viewport"] = write_viewport_files(agent_id)

    out["doctor"] = doctor(agent_id=agent_id)
    out["ok"] = bool(out["doctor"].get("ok"))
    return out


def tick_all(*, agent_id: str = "default", force_dream: bool = False) -> dict[str, Any]:
    """One operational cycle: pulse tick (+ optional forced dream)."""
    from hermespace import pulse
    from hermespace.grid import dream
    from hermespace.grid.viewport import write_viewport_files
    from hermespace.grid.selftalk import say

    result: dict[str, Any] = {"ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    result["pulse"] = pulse.tick(agent_id=agent_id, seed_defaults=True)
    if force_dream:
        result["dream"] = dream.run_dream(agent_id, force_material=True).__dict__
    say(f"tick_all ran={result['pulse'].get('ran')} skip={result['pulse'].get('skipped')}", agent_id=agent_id, role="ops")
    result["viewport"] = write_viewport_files(agent_id)
    return result


def compact_status(*, agent_id: str = "default") -> str:
    """Short inject block for agents."""
    d = doctor(agent_id=agent_id)
    lines = [
        "### Hermespace ops",
        f"- version: {d.get('version')} · core_ok: {d.get('ok')} · serve: {d.get('serve_up')}",
        f"- home: `{d.get('home')}`",
    ]
    for c in d.get("checks") or []:
        mark = "ok" if c.get("ok") else "FAIL"
        if c["name"] in {"imports", "pulse_jobs", "access_pending", "missions", "viewport_html", "viewport_serve"}:
            lines.append(f"- [{mark}] {c['name']}: {c.get('detail')}")
    for h in d.get("hints") or []:
        lines.append(f"- hint: {h}")
    return "\n".join(lines) + "\n"
