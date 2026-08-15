"""HermesCube heart / center adapter — soft dependency + standalone warehouse.

Cube (when installed) is the durable SoT for long-tail memory.
Hermespace owns nervous FOA (desk / Access Workspace). This module is the cable:

  center 1.2  → beat / supply / return_flow / autonomic_tick / organs
  heart  1.0  → ensure_heart / build_space_inject / seal_learning / pulse_charge
                / sync_world_beliefs
  hive   opt  → room of peer agents (HERMESCUBE_HIVE)
  connect     → agent enters charged world + Access Workspace + optional hive room
  standalone  → local SemanticStore + WorldModel (no Cube required)

Never hard-fail. Feature-detect via ``heart_status`` / ``center_status``.
See docs/architecture/HERMESCUBE.md and PURPOSE.md.
"""

from __future__ import annotations

import logging
import os
from typing import Any, Iterable

logger = logging.getLogger("hermespace.cube_module")

# Local contract version — Space adapter surface (independent of Cube package).
SPACE_CUBE_ADAPTER_VERSION = "1.3"

# Load → arterial char budgets (match Cube center when present).
LOAD_STRIP_CHARS: dict[str, int] = {
    "low": 900,
    "mid": 640,
    "high": 420,
    "protect": 280,
}


def cube_available() -> bool:
    try:
        import hermescube  # noqa: F401

        return True
    except Exception:
        return False


def normalize_load(load: str | float | None = None, *, high_load: bool = False) -> str:
    if high_load:
        return "high"
    if load is None:
        return "mid"
    if isinstance(load, (int, float)):
        v = float(load)
        if v >= 0.85:
            return "protect"
        if v >= 0.65:
            return "high"
        if v >= 0.35:
            return "mid"
        return "low"
    s = str(load).strip().lower()
    if s in LOAD_STRIP_CHARS:
        return s
    if s in ("protected", "mono", "monotropic"):
        return "protect"
    return "mid"


def strip_budget(load: str | float | None = None, *, high_load: bool = False) -> int:
    return LOAD_STRIP_CHARS[normalize_load(load, high_load=high_load)]


def center_status() -> dict[str, Any]:
    """Prefer Cube center 1.1; fall back to heart / standalone status."""
    try:
        from hermescube.center import center_status as _cs

        st = _cs()
        st["adapter"] = SPACE_CUBE_ADAPTER_VERSION
        st["mode"] = "center"
        return st
    except Exception:
        pass
    heart = heart_status()
    return {
        "api_version": heart.get("api_version") or "standalone",
        "adapter": SPACE_CUBE_ADAPTER_VERSION,
        "mode": "heart" if heart.get("available") else "standalone",
        "ok": bool(heart.get("heart_ready") or heart.get("standalone_ready")),
        "heart": heart,
        "organs": {
            "nervous_foa": {
                "organ": "Hermespace desk / Access Workspace",
                "job": "FOA ≤4, dual decode, GWT broadcast",
                "ready": True,
                "note": "owned_by_hermespace",
            },
            "heart": {
                "organ": "HermesCube .cube or standalone warehouse",
                "job": "Durable long-tail memory",
                "ready": bool(heart.get("heart_ready") or heart.get("standalone_ready")),
            },
        },
    }


def heart_status() -> dict[str, Any]:
    """Cube heart_status when available; else standalone warehouse readiness."""
    try:
        from hermescube.space_bridge import heart_status as _hs

        st = _hs()
        st["adapter"] = SPACE_CUBE_ADAPTER_VERSION
        st["mode"] = "cube"
        return st
    except Exception as e:
        logger.debug("heart_status cube miss: %s", e)
    return _standalone_heart_status()


def module_status() -> dict[str, Any]:
    """Back-compat alias."""
    return heart_status()


def ensure_heart() -> dict[str, Any]:
    """Ensure durable warehouse exists (Cube memory.cube or standalone dirs)."""
    try:
        from hermescube.space_bridge import ensure_heart as _eh

        out = _eh()
        out["adapter"] = SPACE_CUBE_ADAPTER_VERSION
        out["mode"] = "cube"
        return out
    except Exception as e:
        logger.debug("ensure_heart cube miss: %s", e)
    return _standalone_ensure()


def cube_inject(
    query: str,
    *,
    high_load: bool = False,
    max_chars: int | None = None,
    load: str | float | None = None,
    session_id: str = "hermespace",
) -> str:
    """Arterial supply — Cube strip or standalone world/semantic strip."""
    level = normalize_load(load, high_load=high_load)
    cap = max_chars if max_chars is not None else strip_budget(level)
    try:
        from hermescube.center import supply

        rec = supply(
            query,
            load=level,
            max_chars=cap,
            session_id=session_id,
        )
        return str(rec.get("block") or "")
    except Exception:
        pass
    try:
        from hermescube.space_bridge import build_space_inject

        return (
            build_space_inject(
                query,
                high_load=level in ("high", "protect"),
                max_chars=cap,
                session_id=session_id,
            )
            or ""
        )
    except Exception:
        pass
    return _standalone_inject(query, max_chars=cap, high_load=level in ("high", "protect"))


def cube_seal(content: str, **kwargs: Any) -> bool:
    """Bool seal — prefer structured seal_learning when Cube present."""
    rec = seal_learning(content, **kwargs)
    return bool(rec.get("ok"))


def seal_learning(
    content: str,
    *,
    entry_type: str = "belief",
    source: str = "hermespace",
    trust: float = 0.75,
    agent_id: str = "",
    **kwargs: Any,
) -> dict[str, Any]:
    """Venous return — desk learning → durable warehouse (Cube or standalone)."""
    text = (content or "").strip()
    if not text:
        return {"ok": False, "error": "empty", "mode": "none"}
    try:
        from hermescube.space_bridge import seal_learning as _sl

        rec = _sl(
            text,
            entry_type=entry_type,
            source=source,
            trust=trust,
            agent_id=agent_id or os.environ.get("HERMESPACE_AGENT_ID", "hermes-agent"),
            **{k: v for k, v in kwargs.items() if k in ("hermes_home",)},
        )
        if isinstance(rec, dict):
            rec["adapter"] = SPACE_CUBE_ADAPTER_VERSION
            rec["mode"] = "cube"
            return rec
    except Exception as e:
        logger.debug("seal_learning cube miss: %s", e)
    try:
        from hermescube.space_bridge import seal_to_cube

        ok = bool(
            seal_to_cube(
                text,
                entry_type=entry_type,
                source=source,
                trust=trust,
            )
        )
        return {"ok": ok, "mode": "cube_bool", "adapter": SPACE_CUBE_ADAPTER_VERSION}
    except Exception:
        pass
    return _standalone_seal(text, entry_type=entry_type, agent_id=agent_id, source=source)


def cube_status() -> dict[str, Any]:
    return heart_status()


def hermes_memory_provider() -> str:
    """Return Hermes ``memory.provider`` when detectable (never required).

    Fail-soft: missing or unreadable config → empty string (provider off).
    """
    try:
        for key in ("HERMES_MEMORY_PROVIDER", "MEMORY_PROVIDER"):
            raw = os.environ.get(key, "").strip().lower()
            if raw:
                return raw
        home = os.environ.get("HERMES_HOME", "").strip()
        roots = [os.path.expanduser(home)] if home else [os.path.expanduser("~/.hermes")]
        for root in roots:
            cfg = os.path.join(root, "config.yaml")
            try:
                with open(cfg, encoding="utf-8") as fh:
                    text = fh.read()
            except OSError:
                continue
            in_memory = False
            for line in text.splitlines():
                raw = line.split("#", 1)[0]
                if raw.strip().startswith("memory:") or raw.strip() == "memory:":
                    in_memory = True
                    continue
                if in_memory and raw and not raw[:1].isspace() and not raw.startswith("\t"):
                    in_memory = False
                if not in_memory:
                    continue
                stripped = raw.strip()
                if stripped.startswith("provider:"):
                    return stripped.split(":", 1)[1].strip().strip("\"'").lower()
        return ""
    except Exception:
        return ""


def cube_is_memory_provider() -> bool:
    """True when Hermes ``memory.provider`` is Cube. Config-only — no Cube import."""
    try:
        return hermes_memory_provider() in {"hermescube", "cube"}
    except Exception:
        return False


def skip_cube_foa_strip() -> bool:
    """Skip the FOA Cube strip only when Cube is confirmed as memory.provider.

    Unreadable / missing config → False (provider off) so ``cube_beat`` still runs.
    Empty prefetch is fine — skip leaves no second strip. No Cube code required.
    """
    try:
        return cube_is_memory_provider()
    except Exception:
        return False


def cube_already_prefetched(
    query: str = "",
    *,
    session_id: str = "",
) -> bool:
    """Alias for ``skip_cube_foa_strip`` — config says Cube owns prefetch."""
    return skip_cube_foa_strip()


def cube_beat(
    query: str = "",
    *,
    seals: str | Iterable[str] | None = None,
    entry_type: str = "belief",
    load: str | float | None = None,
    high_load: bool = False,
    agent_id: str = "hermes-agent",
    charge: bool = False,
    session_id: str = "hermespace",
    skip_if_prefetched: bool = True,
) -> dict[str, Any]:
    """One cardiac cycle for a Hermespace turn (Cube center or standalone).

    Order: ensure → systole (seal) → diastole (supply) → optional autonomic.

    When Hermes ``memory.provider=hermescube``, skip the arterial FOA strip
    entirely. Do not call ``center.supply`` / ``build_space_inject`` as a
    last prefetch — MemoryManager already ran ``CubeMemoryProvider.prefetch``.
    Seals and ``pulse_charge`` remain allowed (World projection, not FOA).
    """
    if skip_if_prefetched and skip_cube_foa_strip():
        level = normalize_load(load, high_load=high_load)
        out: dict[str, Any] = {
            "api_version": "1.0",
            "adapter": SPACE_CUBE_ADAPTER_VERSION,
            "mode": "skipped",
            "ok": True,
            "phases": {"diastole": {"ok": True, "skipped": "provider_prefetch", "chars": 0}},
            "block": "",
            "load_level": level,
            "skipped": "provider_prefetch",
        }
        if seals is not None:
            items = [seals] if isinstance(seals, str) else list(seals)
            sealed = [
                seal_learning(str(x), entry_type=entry_type, agent_id=agent_id)
                for x in items
                if str(x).strip()
            ]
            out["phases"]["systole"] = {
                "ok": all(r.get("ok") for r in sealed) if sealed else False,
                "count": sum(1 for r in sealed if r.get("ok")),
            }
        if charge:
            out["phases"]["autonomic"] = cube_pulse(agent_id=agent_id)
        return out

    try:
        from hermescube.center import beat

        out = beat(
            query or "",
            seals=seals,
            entry_type=entry_type,
            load=load,
            high_load=high_load,
            agent_id=agent_id,
            charge=charge,
            session_id=session_id,
        )
        if isinstance(out, dict):
            out["adapter"] = SPACE_CUBE_ADAPTER_VERSION
            out["mode"] = "center"
            return out
    except Exception as e:
        logger.debug("center.beat miss: %s", e)

    # Heart 1.0 / standalone fallback
    level = normalize_load(load, high_load=high_load)
    out = {
        "api_version": "1.0",
        "adapter": SPACE_CUBE_ADAPTER_VERSION,
        "mode": "standalone" if not cube_available() else "heart",
        "ok": False,
        "phases": {},
        "block": "",
        "load_level": level,
    }
    out["phases"]["ensure"] = ensure_heart()
    if seals is not None:
        items = [seals] if isinstance(seals, str) else list(seals)
        sealed = [
            seal_learning(
                str(x),
                entry_type=entry_type,
                agent_id=agent_id,
            )
            for x in items
            if str(x).strip()
        ]
        out["phases"]["systole"] = {
            "ok": all(r.get("ok") for r in sealed) if sealed else False,
            "sealed": sealed,
            "count": sum(1 for r in sealed if r.get("ok")),
        }
    block = cube_inject(
        query or "",
        load=level,
        session_id=session_id,
    )
    out["phases"]["diastole"] = {
        "ok": True,
        "block": block,
        "chars": len(block),
        "load_level": level,
    }
    out["block"] = block
    if charge:
        out["phases"]["autonomic"] = cube_pulse(agent_id=agent_id)
    out["ok"] = bool((out["phases"].get("ensure") or {}).get("ok", True))
    return out


def cube_pulse(*, agent_id: str = "hermes-agent", ensure: bool = True) -> dict[str, Any]:
    """Autonomic idle — charge WorldModel from Cube, or standalone consolidate."""
    try:
        from hermescube.center import autonomic_tick

        out = autonomic_tick(agent_id=agent_id, ensure=ensure)
        if isinstance(out, dict):
            out["adapter"] = SPACE_CUBE_ADAPTER_VERSION
            out["mode"] = "center"
            return out
    except Exception:
        pass
    try:
        from hermescube.space_bridge import pulse_charge

        out = pulse_charge(agent_id=agent_id, ensure=ensure)
        if isinstance(out, dict):
            out["adapter"] = SPACE_CUBE_ADAPTER_VERSION
            out["mode"] = "heart"
            return out
    except Exception as e:
        logger.debug("pulse_charge miss: %s", e)
    return _standalone_pulse(agent_id=agent_id)


def sync_world(*, agent_id: str = "hermes-agent") -> dict[str, Any]:
    """Charge Hermespace WorldModel from Cube wisdom (or standalone evolve).

    Cube ``sync_world_beliefs`` is the arterial charge Anthropic/Dehaene lack —
    enduring memory → active world beliefs the desk can hold.
    """
    try:
        from hermescube.space_bridge import sync_world_beliefs

        out = sync_world_beliefs(agent_id=agent_id)
        if isinstance(out, dict):
            out["adapter"] = SPACE_CUBE_ADAPTER_VERSION
            out["mode"] = "cube"
            return out
    except Exception as e:
        logger.debug("sync_world_beliefs miss: %s", e)
    return _standalone_pulse(agent_id=agent_id)


def room_status(*, agent_id: str = "hermes-agent") -> dict[str, Any]:
    """Soft hive / peer-room awareness — other agents sharing Cube knowledge.

    Env: ``HERMESCUBE_HIVE`` (or plugins.hermescube.hive_path when Cube provider
    is live). Solo installs report ``mode=solo`` with local world growth only.
    """
    out: dict[str, Any] = {
        "ok": True,
        "mode": "solo",
        "agent_id": agent_id,
        "hive_configured": False,
        "souls": [],
        "soul_n": 0,
        "adapter": SPACE_CUBE_ADAPTER_VERSION,
        "note": "Solo room — local WorldModel + Access Workspace; set HERMESCUBE_HIVE for fleet",
    }
    hive_root = (os.environ.get("HERMESCUBE_HIVE") or "").strip()
    if not hive_root:
        return out
    out["hive_configured"] = True
    out["hive_root"] = hive_root
    try:
        from hermescube.hive import hive_status, list_souls

        st = hive_status(hive_root)
        souls = list_souls(hive_root)
        peers = []
        for s in souls or []:
            if not isinstance(s, dict):
                continue
            sid = str(s.get("agent_id") or s.get("id") or s.get("name") or "").strip()
            if not sid:
                continue
            peers.append(
                {
                    "agent_id": sid,
                    "self": sid.casefold() == agent_id.casefold(),
                    "era": (s.get("growth") or {}).get("era")
                    if isinstance(s.get("growth"), dict)
                    else s.get("era"),
                    "wisdom_n": len(s.get("wisdom") or [])
                    if isinstance(s.get("wisdom"), list)
                    else 0,
                }
            )
        out["mode"] = "hive" if st.get("ok") else "hive_pending"
        out["ok"] = bool(st.get("ok", True))
        out["hive"] = {
            "ok": st.get("ok"),
            "name": st.get("name"),
            "entries": st.get("entries"),
            "pending_offerings": st.get("pending_offerings"),
            "interviews": st.get("interviews"),
        }
        out["souls"] = peers
        out["soul_n"] = len(peers)
        out["peer_n"] = sum(1 for p in peers if not p.get("self"))
        out["note"] = (
            f"Hive room online — {out['peer_n']} peer agent(s), "
            f"{out['soul_n']} soul card(s)"
            if peers
            else "Hive configured — await first pilgrimage / soul cards"
        )
        return out
    except Exception as e:
        out["ok"] = False
        out["mode"] = "hive_error"
        out["error"] = type(e).__name__
        out["note"] = "Hive path set but Cube hive API unavailable"
        logger.debug("room_status hive miss: %s", e)
        return out


def seed_access_from_warehouse(
    agent_id: str = "hermes-agent",
    *,
    query: str = "",
    session_id: str = "hermespace",
    room: dict[str, Any] | None = None,
    workspace_id: str = "",
) -> dict[str, Any]:
    """Pull Cube/world wisdom + peer presence into the agent's Access Workspace hub.

    This is the intelligence gain on connect: the external workspace lights up
    with durable knowledge and (when hive is live) awareness of other agents.
    """
    report: dict[str, Any] = {
        "ok": False,
        "enriched_world": 0,
        "enriched_cube": 0,
        "enriched_peers": 0,
        "hub_n": 0,
        "adapter": SPACE_CUBE_ADAPTER_VERSION,
    }
    try:
        from hermespace.access import AccessHub

        js = AccessHub(agent_id=workspace_id or agent_id)
        beliefs: list[str] = []
        try:
            from hermespace.world import WorldModel

            wm = WorldModel(agent_id=agent_id)
            for b in list(wm.state.beliefs or [])[:10]:
                if isinstance(b, dict):
                    stmt = str(b.get("statement") or "").strip()
                else:
                    stmt = str(getattr(b, "statement", "") or "").strip()
                if stmt:
                    beliefs.append(stmt)
        except Exception as e:
            report["world_error"] = type(e).__name__

        report["enriched_world"] = js.enrich_from_world(beliefs, limit=5)

        strip = cube_inject(query or "active wisdom", session_id=session_id)
        cube_lines = _strip_inject_lines(strip)
        if cube_lines:
            report["enriched_cube"] = js.enrich_from_world(cube_lines, limit=4)
            report["cube_strip_chars"] = len(strip)

        room = room if room is not None else room_status(agent_id=agent_id)
        peer_texts: list[str] = []
        for p in list(room.get("souls") or [])[:6]:
            if not isinstance(p, dict) or p.get("self"):
                continue
            pid = str(p.get("agent_id") or "").strip()
            if not pid:
                continue
            wn = int(p.get("wisdom_n") or 0)
            peer_texts.append(
                f"peer agent present: {pid}"
                + (f" ({wn} wisdom)" if wn else "")
            )
        if peer_texts:
            # Presence is awareness, not user Report — mark silent after hold
            before = len(js.state.hub)
            for t in peer_texts[:3]:
                js.hold(t, salience=0.55, silent=True)
            report["enriched_peers"] = max(0, len(js.state.hub) - before)

        report["hub_n"] = len(js.state.hub)
        report["focus_n"] = len(js.state.focus)
        report["ok"] = True
        report["room_mode"] = room.get("mode")
        report["workspace_id"] = workspace_id or agent_id
        return report
    except Exception as e:
        report["error"] = type(e).__name__
        logger.debug("seed_access_from_warehouse miss: %s", e)
        return report


seed_jspace_from_warehouse = seed_access_from_warehouse  # deprecated name


def connect_agent(
    agent_id: str = "hermes-agent",
    *,
    session_id: str = "main",
    query: str = "",
    enter_world: bool = True,
    enter_workbench: bool = True,
    charge: bool = True,
    seed: bool = True,
) -> dict[str, Any]:
    """Full connect — agent gains heart + world + Access Workspace + optional hive room.

    Call when a Hermes agent joins Hermespace (session start / ``HermesBase.connect``).
    Soft-fails every Cube surface; standalone warehouse still grows the room.
    """
    out: dict[str, Any] = {
        "ok": False,
        "agent_id": agent_id,
        "session_id": session_id,
        "adapter": SPACE_CUBE_ADAPTER_VERSION,
        "phases": {},
        "gained": {},
        "memories": [
            "Access Workspace: privileged verbalizable workspace",
            "Baars GWT: limited capacity hub broadcast to specialists",
            "Dehaene gap: Cube supplies enduring episodic/library memory",
            "Hive: optional room of peer agents — intelligence compounds",
        ],
    }
    out["phases"]["ensure"] = ensure_heart()
    out["phases"]["center"] = center_status()

    if enter_workbench:
        try:
            from hermespace.workbench import Workbench

            wb = Workbench(agent_id=agent_id, session_id=session_id)
            # Avoid recursion: enter() may call connect helpers; use lean enter
            out["phases"]["workbench"] = wb.enter(connect_warehouse=False)
        except Exception as e:
            out["phases"]["workbench"] = {"ok": False, "error": type(e).__name__}

    if enter_world:
        try:
            from hermespace.world import WorldModel

            wm = WorldModel(agent_id=agent_id)
            st = wm.enter()
            out["phases"]["world"] = {
                "ok": True,
                "state": getattr(st, "current_state", None) or wm.state.current_state,
                "beliefs": len(wm.state.beliefs or []),
                "landmarks": len(wm.state.landmarks or []),
                "timeline": wm.archive.count(),
            }
        except Exception as e:
            out["phases"]["world"] = {"ok": False, "error": type(e).__name__}

    if charge:
        out["phases"]["charge"] = cube_pulse(agent_id=agent_id, ensure=False)
        # Explicit sync when Cube exposes it separately from pulse
        try:
            from hermescube.space_bridge import sync_world_beliefs

            out["phases"]["sync_world"] = sync_world_beliefs(agent_id=agent_id)
        except Exception:
            out["phases"]["sync_world"] = {"ok": None, "mode": "via_pulse_or_standalone"}

    out["phases"]["room"] = room_status(agent_id=agent_id)

    if seed:
        try:
            from hermespace.access.engine import workspace_id as _workspace_id

            access_id = _workspace_id(agent_id, session_id)
        except Exception:
            access_id = agent_id
        out["phases"]["seed"] = seed_access_from_warehouse(
            agent_id,
            query=query,
            session_id=session_id,
            room=out["phases"]["room"],
            workspace_id=access_id,
        )

    world = out["phases"].get("world") or {}
    seed_ph = out["phases"].get("seed") or {}
    room = out["phases"].get("room") or {}
    heart = out["phases"].get("ensure") or {}
    out["gained"] = {
        "warehouse_mode": heart.get("mode") or (out["phases"].get("center") or {}).get("mode"),
        "world_beliefs": world.get("beliefs", 0),
        "world_timeline": world.get("timeline", 0),
        "access_hub": seed_ph.get("hub_n", 0),
        "from_world": seed_ph.get("enriched_world", 0),
        "from_cube": seed_ph.get("enriched_cube", 0),
        "from_peers": seed_ph.get("enriched_peers", 0),
        "room_mode": room.get("mode"),
        "peer_agents": room.get("peer_n", 0),
    }
    heart_ok = bool(
        heart.get("ok")
        or heart.get("standalone_ready")
        or heart.get("heart_ready")
        or heart.get("mode") in ("standalone", "cube", "heart")
    )
    world_ok = bool(world.get("ok", True)) if enter_world else True
    out["ok"] = heart_ok and world_ok
    out["summary"] = (
        f"Connected {agent_id}: hub={out['gained']['access_hub']} "
        f"beliefs={out['gained']['world_beliefs']} "
        f"room={out['gained']['room_mode']} "
        f"peers={out['gained']['peer_agents']}"
    )
    return out


def _strip_inject_lines(block: str) -> list[str]:
    out: list[str] = []
    for raw in (block or "").splitlines():
        s = raw.strip()
        if not s or s.startswith("#") or s.startswith("_"):
            continue
        if s.startswith("- "):
            s = s[2:].strip()
        # drop confidence prefix like [0.75]
        if s.startswith("[") and "]" in s[:12]:
            s = s.split("]", 1)[-1].strip()
        if len(s) < 3:
            continue
        out.append(s[:200])
    return out


# --- standalone warehouse (no Cube) -----------------------------------------


def _standalone_heart_status() -> dict[str, Any]:
    from hermespace.paths import state_dir

    sd = state_dir()
    ready = sd.is_dir()
    entries = 0
    try:
        from hermespace.semantic import SemanticStore

        entries = len(SemanticStore().list_notes(limit=200))
    except Exception:
        pass
    try:
        from hermespace.world import WorldModel

        aid = os.environ.get("HERMESPACE_AGENT_ID", "hermes-agent")
        wm = WorldModel(agent_id=aid)
        entries += len(wm.state.beliefs)
    except Exception:
        pass
    return {
        "api_version": "standalone",
        "role": "standalone_warehouse",
        "available": False,
        "cube_exists": False,
        "heart_ready": False,
        "standalone_ready": ready,
        "entries": entries,
        "adapter": SPACE_CUBE_ADAPTER_VERSION,
        "mode": "standalone",
        "surfaces": {
            "inject": "standalone_world_semantic",
            "seal": "standalone_seal",
            "pulse": "standalone_pulse",
            "ensure": "standalone_ensure",
        },
        "note": "HermesCube not installed — Hermespace world+semantic act as local warehouse",
    }


def _standalone_ensure() -> dict[str, Any]:
    from hermespace.paths import state_dir

    sd = state_dir()
    created = False
    try:
        if not sd.is_dir():
            sd.mkdir(parents=True, exist_ok=True)
            created = True
        (sd / "access").mkdir(parents=True, exist_ok=True)
        (sd / "worlds").mkdir(parents=True, exist_ok=True)
        ok = True
    except Exception as e:
        return {
            "ok": False,
            "created": False,
            "error": str(e),
            "mode": "standalone",
            "adapter": SPACE_CUBE_ADAPTER_VERSION,
        }
    return {
        "ok": ok,
        "created": created,
        "mode": "standalone",
        "path": str(sd),
        "adapter": SPACE_CUBE_ADAPTER_VERSION,
        "api_version": "standalone",
    }


def _standalone_inject(query: str, *, max_chars: int = 640, high_load: bool = False) -> str:
    """Dense FOA strip from local WorldModel + SemanticStore."""
    lines = ["### Hermespace warehouse (standalone)"]
    if high_load:
        lines.append("_High load — local strip only (no Cube)._")
    used = sum(len(x) + 1 for x in lines)
    cap = max_chars
    aid = os.environ.get("HERMESPACE_AGENT_ID", "hermes-agent")

    try:
        from hermespace.world import WorldModel

        wm = WorldModel(agent_id=aid)
        scored: list[tuple[str, float]] = []
        for b in list(wm.state.beliefs or []):
            stmt = str(getattr(b, "statement", "") or "").strip()
            conf = float(getattr(b, "confidence", 0.5) or 0.5)
            if stmt:
                scored.append((stmt, conf))
        scored.sort(key=lambda x: x[1], reverse=True)
        for stmt, conf in scored[: 2 if high_load else 5]:
            line = f"- [{conf:.2f}] {stmt[:160]}"
            if used + len(line) + 1 > cap:
                break
            lines.append(line)
            used += len(line) + 1
    except Exception:
        pass

    q = (query or "").strip().lower()
    try:
        from hermespace.semantic import SemanticStore

        notes = SemanticStore().list_notes(limit=20)
        hits = []
        for n in notes:
            stmt = n.statement.strip()
            if not stmt:
                continue
            score = n.confidence
            if q and any(tok in stmt.lower() for tok in q.split() if len(tok) > 2):
                score += 0.2
            hits.append((stmt, score))
        hits.sort(key=lambda x: x[1], reverse=True)
        for stmt, _ in hits[: 1 if high_load else 3]:
            if any(stmt[:40] in x for x in lines):
                continue
            line = f"- {stmt[:160]}"
            if used + len(line) + 1 > cap:
                break
            lines.append(line)
            used += len(line) + 1
    except Exception:
        pass

    if len(lines) <= 2:
        return ""
    block = "\n".join(lines)
    if len(block) > cap:
        block = block[: cap - 3] + "..."
    return block


def _standalone_seal(
    content: str,
    *,
    entry_type: str = "belief",
    agent_id: str = "",
    source: str = "hermespace",
) -> dict[str, Any]:
    aid = agent_id or os.environ.get("HERMESPACE_AGENT_ID", "hermes-agent")
    out: dict[str, Any] = {
        "ok": False,
        "mode": "standalone",
        "adapter": SPACE_CUBE_ADAPTER_VERSION,
        "entry_type": entry_type,
        "source": source,
    }
    try:
        from hermespace.semantic import SemanticStore

        note = SemanticStore().add(
            content[:500],
            tags=["seal", entry_type, source],
            confidence=0.75,
        )
        out["semantic_id"] = note.note_id
        out["ok"] = True
    except Exception as e:
        out["semantic_error"] = str(e)
    try:
        from hermespace.world import WorldModel

        wm = WorldModel(agent_id=aid)
        if entry_type in ("belief", "trait", "landmark", "focus", "relationship"):
            if entry_type == "trait":
                wm.set_trait(content[:120])
            elif entry_type == "landmark":
                wm.add_landmark(content[:200])
            else:
                wm.add_belief(content[:400], 0.75, source=source)
            out["world_ok"] = True
            out["ok"] = True
    except Exception as e:
        out["world_error"] = str(e)
    return out


def _standalone_pulse(*, agent_id: str = "hermes-agent") -> dict[str, Any]:
    report: dict[str, Any] = {
        "ok": False,
        "mode": "standalone",
        "adapter": SPACE_CUBE_ADAPTER_VERSION,
        "phase": "autonomic",
        "ensure": _standalone_ensure(),
    }
    try:
        from hermespace.world import WorldModel

        wm = WorldModel(agent_id=agent_id)
        evo = wm.evolve()
        report["evolve"] = evo if isinstance(evo, dict) else {"result": str(evo)}
        # Enrich Access Workspace hub from world beliefs
        try:
            from hermespace.access import AccessHub

            js = AccessHub(agent_id=agent_id)
            beliefs: list[str] = []
            for b in list(wm.state.beliefs or [])[:8]:
                if isinstance(b, dict):
                    beliefs.append(str(b.get("statement") or ""))
                else:
                    beliefs.append(str(getattr(b, "statement", "") or ""))
            report["access_enriched"] = js.enrich_from_world(beliefs)
        except Exception as e:
            report["access_error"] = str(e)
        report["ok"] = True
    except Exception as e:
        report["error"] = str(e)
        report["ok"] = bool((report.get("ensure") or {}).get("ok"))
    return report
