"""HermesCube heart / center adapter — soft dependency + standalone warehouse.

Cube (when installed) is the durable SoT for long-tail memory.
Hermespace owns nervous FOA (desk / J-Space). This module is the cable:

  center 1.1  → beat / supply / return_flow / autonomic_tick
  heart  1.0  → ensure_heart / build_space_inject / seal_learning / pulse_charge
  standalone  → local SemanticStore + WorldModel (no Cube required)

Never hard-fail. Feature-detect via ``heart_status`` / ``center_status``.
See docs/HERMESCUBE.md and PURPOSE.md.
"""

from __future__ import annotations

import logging
import os
from typing import Any, Iterable

logger = logging.getLogger("hermespace.cube_module")

# Local contract version — Space adapter surface (independent of Cube package).
SPACE_CUBE_ADAPTER_VERSION = "1.1"

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
                "organ": "Hermespace desk / J-Space",
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
) -> dict[str, Any]:
    """One cardiac cycle for a Hermespace turn (Cube center or standalone).

    Order: ensure → systole (seal) → diastole (supply) → optional autonomic.
    """
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
    out: dict[str, Any] = {
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
        (sd / "jspace").mkdir(parents=True, exist_ok=True)
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
        # Enrich J-Space hub from world beliefs
        try:
            from hermespace.jspace import JSpace

            js = JSpace(agent_id=agent_id)
            beliefs: list[str] = []
            for b in list(wm.state.beliefs or [])[:8]:
                if isinstance(b, dict):
                    beliefs.append(str(b.get("statement") or ""))
                else:
                    beliefs.append(str(getattr(b, "statement", "") or ""))
            report["jspace_enriched"] = js.enrich_from_world(beliefs)
        except Exception as e:
            report["jspace_error"] = str(e)
        report["ok"] = True
    except Exception as e:
        report["error"] = str(e)
        report["ok"] = bool((report.get("ensure") or {}).get("ok"))
    return report
