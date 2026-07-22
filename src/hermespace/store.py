"""Persist Hermespace desk + JSON sidecar."""

from __future__ import annotations

import json
from pathlib import Path

from hermespace.desk import Desk
from hermespace.paths import desk_path, state_dir


def default_desk_path() -> Path:
    return desk_path()


def default_state_dir() -> Path:
    return state_dir()


def save_desk(desk: Desk, path: Path | None = None) -> Path:
    path = path or default_desk_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(desk.to_markdown(), encoding="utf-8")
    side = path.with_suffix(".json")
    payload = {
        "updated": desk.updated,
        "goal": desk.goal,
        "concepts": desk.concepts,
        "choices": desk.choices,
        "decision": desk.decision,
        "plan": desk.plan,
        "say": desk.say,
        "do_not_say": desk.do_not_say,
        "meta": desk.meta,
        "load": desk.load,
        "executive": desk.executive,
        "focus": desk.focus,
        "ready": desk.is_ready(),
    }
    side.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def load_desk(path: Path | None = None) -> Desk:
    path = path or default_desk_path()
    if not path.exists():
        return Desk()
    return Desk.from_markdown(path.read_text(encoding="utf-8"))
