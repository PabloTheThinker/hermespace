"""Local viewport HTTP API for Desktop + browser + Tailscale.

Default bind: 127.0.0.1 (loopback only).

For any user's Tailscale laptop → server machine:

  hs view --serve --tailscale
  # binds this machine's Tailscale IPv4 only (not public WAN)
  # open http://<that-ip>:8764/ from any device on the same tailnet

Or:

  hs view --serve --host 0.0.0.0 --open
  # all interfaces; rely on OS firewall + Tailscale ACLs

Optional shared secret when not on loopback:

  HERMESPACE_VIEW_TOKEN=secret
  # clients: ?token=secret  or  header X-Hermespace-Token: secret
"""

from __future__ import annotations

import ipaddress
import json
import os
import re
import socket
import subprocess
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import parse_qs, urlparse

from hermespace.grid import access
from hermespace.grid.boundary import policy_markdown
from hermespace.grid.viewport import render_html, snapshot, write_viewport_files


def _json_bytes(data: Any, code: int = 200) -> tuple[int, bytes, str]:
    body = json.dumps(data, indent=2, default=str).encode("utf-8")
    return code, body, "application/json; charset=utf-8"


def tailscale_ipv4() -> str | None:
    """Return this host's Tailscale IPv4 if `tailscale` CLI works, else None."""
    try:
        out = subprocess.check_output(
            ["tailscale", "ip", "-4"],
            stderr=subprocess.DEVNULL,
            timeout=3,
            text=True,
        ).strip()
    except (FileNotFoundError, subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError):
        out = ""
    for line in out.splitlines():
        cand = line.strip()
        if not cand:
            continue
        try:
            ip = ipaddress.ip_address(cand)
        except ValueError:
            continue
        if isinstance(ip, ipaddress.IPv4Address):
            # Tailscale CGNAT (RFC 6598) — built without host-fingerprint literals
            cgnat = ipaddress.ip_network(".".join(map(str, (100, 64, 0, 0))) + "/10")
            if ip in cgnat:
                return str(ip)
            # still accept any v4 tailscale reports
            return str(ip)
    # env override for odd installs
    env_ip = os.environ.get("HERMESPACE_TAILSCALE_IP", "").strip()
    if env_ip:
        try:
            ipaddress.ip_address(env_ip)
            return env_ip
        except ValueError:
            pass
    return None


def resolve_bind_host(host: str) -> str:
    """Normalize CLI/env host for serve().

    Accepts: 127.0.0.1 | localhost | ::1 | 0.0.0.0 | :: | tailscale | ts | auto
    """
    h = (host or "127.0.0.1").strip()
    low = h.lower()
    if low in ("tailscale", "ts", "auto-tailscale", "auto"):
        tip = tailscale_ipv4()
        if not tip:
            raise ValueError(
                "Tailscale IPv4 not found. Install/login tailscale, or set "
                "HERMESPACE_TAILSCALE_IP=<tailscale-ipv4>, or use --host 0.0.0.0 --open"
            )
        return tip
    if low in ("all", "any", "*"):
        return "0.0.0.0"
    return h


def is_loopback_host(host: str) -> bool:
    return host in ("127.0.0.1", "localhost", "::1")


def validate_bind_host(host: str, *, open_network: bool) -> None:
    if is_loopback_host(host):
        return
    # Tailscale CGNAT single address — OK without --open
    try:
        ip = ipaddress.ip_address(host)
        cgnat = ipaddress.ip_network(".".join(map(str, (100, 64, 0, 0))) + "/10")
        if ip in cgnat:
            return
    except ValueError:
        pass
    if host in ("0.0.0.0", "::", "[::]"):
        if not open_network and not _truthy("HERMESPACE_VIEW_OPEN"):
            raise ValueError(
                "Binding all interfaces requires --open or HERMESPACE_VIEW_OPEN=1 "
                "(use Tailscale ACLs / firewall; not for public WAN)"
            )
        return
    # other explicit IPs need open
    if not open_network and not _truthy("HERMESPACE_VIEW_OPEN"):
        raise ValueError(
            f"Non-loopback bind {host!r} requires --open or HERMESPACE_VIEW_OPEN=1 "
            "(or use --tailscale for CGNAT-only bind)"
        )


def _truthy(name: str, default: str = "0") -> bool:
    return os.environ.get(name, default).strip().lower() in {"1", "true", "yes", "on"}


def _view_token() -> str:
    return os.environ.get("HERMESPACE_VIEW_TOKEN", "").strip()


class Handler(BaseHTTPRequestHandler):
    agent_id: str = "default"
    require_token: bool = False
    expected_token: str = ""

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A003
        return

    def _authorized(self) -> bool:
        if not self.require_token:
            return True
        # query ?token=
        u = urlparse(self.path)
        qs = parse_qs(u.query)
        tok = (qs.get("token") or [""])[0]
        if tok and tok == self.expected_token:
            return True
        hdr = self.headers.get("X-Hermespace-Token") or self.headers.get("Authorization") or ""
        if hdr.startswith("Bearer "):
            hdr = hdr[7:].strip()
        return bool(hdr) and hdr == self.expected_token

    def _send(self, code: int, body: bytes, ctype: str) -> None:
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        # local Desktop / Tailscale browser; not a public CDN product
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self) -> None:  # noqa: N802
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, X-Hermespace-Token, Authorization")
        self.end_headers()

    def do_GET(self) -> None:  # noqa: N802
        if not self._authorized():
            self._send(401, b'{"error":"unauthorized","hint":"pass ?token= or X-Hermespace-Token"}', "application/json")
            return
        u = urlparse(self.path)
        path = u.path.rstrip("/") or "/"
        qs = parse_qs(u.query)
        agent = (qs.get("agent") or [self.agent_id])[0]

        if path in ("/", "/view", "/index.html"):
            html = render_html(agent).encode("utf-8")
            self._send(200, html, "text/html; charset=utf-8")
            return
        if path == "/api/snapshot":
            code, body, ct = _json_bytes(snapshot(agent))
            self._send(code, body, ct)
            return
        if path == "/api/pending":
            pend = [r.to_dict() for r in access.list_requests(agent_id=agent, status="pending")]
            code, body, ct = _json_bytes({"pending": pend})
            self._send(code, body, ct)
            return
        if path == "/api/policy":
            code, body, ct = _json_bytes({"markdown": policy_markdown()})
            self._send(code, body, ct)
            return
        if path == "/api/write-files":
            paths = write_viewport_files(agent)
            code, body, ct = _json_bytes(paths)
            self._send(code, body, ct)
            return
        if path == "/api/pulse":
            from hermespace import pulse as pulse_mod

            st = pulse_mod.status(agent, light=True)
            code, body, ct = _json_bytes(st)
            self._send(code, body, ct)
            return
        if path == "/api/controls":
            from hermespace.grid.controls import controls_public

            code, body, ct = _json_bytes(controls_public(agent_id=agent))
            self._send(code, body, ct)
            return
        if path == "/api/health":
            code, body, ct = _json_bytes(
                {
                    "ok": True,
                    "service": "hermespace-viewport",
                    "agent_id": self.agent_id,
                    "tailscale_ipv4": tailscale_ipv4(),
                }
            )
            self._send(code, body, ct)
            return
        self._send(404, b'{"error":"not_found"}', "application/json")

    def do_POST(self) -> None:  # noqa: N802
        if not self._authorized():
            self._send(401, b'{"error":"unauthorized"}', "application/json")
            return
        u = urlparse(self.path)
        path = u.path.rstrip("/")
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length) if length else b"{}"
        try:
            data = json.loads(raw.decode("utf-8") or "{}")
        except json.JSONDecodeError:
            self._send(400, b'{"error":"bad_json"}', "application/json")
            return

        if path == "/api/approve":
            rid = str(data.get("id") or "")
            out = access.approve_request(rid, resolver="viewport", note=str(data.get("note") or ""))
            code, body, ct = _json_bytes(out, 200 if out.get("ok") else 400)
            self._send(code, body, ct)
            return
        if path == "/api/deny":
            rid = str(data.get("id") or "")
            out = access.deny_request(rid, resolver="viewport", note=str(data.get("note") or ""))
            code, body, ct = _json_bytes(out, 200 if out.get("ok") else 400)
            self._send(code, body, ct)
            return
        if path == "/api/request":
            req = access.request_access(
                str(data.get("path") or ""),
                agent_id=str(data.get("agent_id") or self.agent_id),
                mode=str(data.get("mode") or "write"),
                hours=float(data.get("hours") or 1),
                reason=str(data.get("reason") or ""),
            )
            code, body, ct = _json_bytes({"ok": True, "request": req.to_dict()})
            self._send(code, body, ct)
            return
        if path == "/api/pulse/tick":
            from hermespace import pulse as pulse_mod

            agent = str(data.get("agent_id") or self.agent_id)
            force = bool(data.get("force"))
            out = pulse_mod.tick(agent_id=agent if agent else None, force=force)
            slim = {
                "ok": True,
                "ts": out.get("ts"),
                "ran": out.get("ran"),
                "skipped": out.get("skipped"),
                "errors": out.get("errors"),
                "jobs": out.get("jobs"),
                "results": [
                    {
                        "job": r.get("job"),
                        "ok": r.get("ok"),
                        "skipped": r.get("skipped"),
                        "reason": r.get("reason"),
                        "action": r.get("action"),
                        "error": r.get("error"),
                    }
                    for r in (out.get("results") or [])
                ],
            }
            code, body, ct = _json_bytes(slim)
            self._send(code, body, ct)
            return
        if path == "/api/controls":
            from hermespace.grid.controls import apply_control_patch

            agent = str(data.get("agent_id") or self.agent_id)
            out = apply_control_patch(data, agent_id=agent, source="viewport")
            code, body, ct = _json_bytes(out, 200 if out.get("ok") else 400)
            self._send(code, body, ct)
            return
        self._send(404, b'{"error":"not_found"}', "application/json")


def serve(
    host: str = "127.0.0.1",
    port: int = 8764,
    agent_id: str = "default",
    *,
    pulse_every_sec: int | None = 60,
    open_network: bool = False,
) -> None:
    """Serve viewport HTTP API. Portable across hosts and Tailscale setups."""
    host = resolve_bind_host(host)
    validate_bind_host(host, open_network=open_network)

    token = _view_token()
    # non-loopback: token optional but recommended; force if HERMESPACE_VIEW_TOKEN_REQUIRED
    require = bool(token) and (
        not is_loopback_host(host) or _truthy("HERMESPACE_VIEW_TOKEN_REQUIRED", "0")
    )
    if not is_loopback_host(host) and _truthy("HERMESPACE_VIEW_TOKEN_REQUIRED", "0") and not token:
        raise ValueError("HERMESPACE_VIEW_TOKEN_REQUIRED=1 but HERMESPACE_VIEW_TOKEN is empty")

    Handler.agent_id = agent_id
    Handler.require_token = require
    Handler.expected_token = token

    httpd = ThreadingHTTPServer((host, port), Handler)

    stop = threading.Event()

    def _pulse_loop() -> None:
        interval = max(15, int(pulse_every_sec or 60))
        time.sleep(2)
        while not stop.is_set():
            try:
                from hermespace import pulse
                from hermespace.grid.viewport import write_viewport_files

                pulse.tick(agent_id=agent_id, seed_defaults=True)
                write_viewport_files(agent_id)
            except Exception as exc:  # noqa: BLE001
                print(f"[pulse] tick error: {exc}")
            stop.wait(interval)

    thr: threading.Thread | None = None
    if pulse_every_sec and pulse_every_sec > 0:
        thr = threading.Thread(target=_pulse_loop, name="hermespace-pulse", daemon=True)
        thr.start()
        print(f"Pulse runtime: in-process tick every {pulse_every_sec}s (disable: --no-pulse)")

    # Print friendly URLs for any user
    print(f"Hermespace viewport bound {host}:{port}  agent={agent_id}")
    if is_loopback_host(host):
        print(f"  local:     http://127.0.0.1:{port}/")
    else:
        print(f"  listen:    http://{host}:{port}/")
    tip = tailscale_ipv4()
    if tip:
        q = f"?token={token}" if require and token else ""
        print(f"  tailscale: http://{tip}:{port}/{q}")
        print("  (any device on your tailnet — MagicDNS name works if enabled)")
    if require:
        print("  auth:      HERMESPACE_VIEW_TOKEN required (?token= or X-Hermespace-Token)")
    print("API: /api/health /api/snapshot /api/pending /api/pulse POST /api/approve /api/deny /api/pulse/tick")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped")
    finally:
        stop.set()
        httpd.server_close()
