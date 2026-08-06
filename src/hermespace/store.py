"""Persist Hermespace desk + JSON sidecar."""

from __future__ import annotations

import json
from pathlib import Path

from hermespace.atomic import atomic_write_text
from hermespace.desk import Desk
from hermespace.paths import desk_path, state_dir


def default_desk_path() -> Path:
    return desk_path()


def default_state_dir() -> Path:
    return state_dir()


def save_desk(desk: Desk, path: Path | None = None) -> Path:
    path = path or default_desk_path()
    atomic_write_text(path, desk.to_markdown())
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
    atomic_write_text(side, json.dumps(payload, indent=2))
    return path


def load_desk(path: Path | None = None) -> Desk:
    path = path or default_desk_path()
    if not path.exists():
        return Desk()
    desk = Desk.from_markdown(path.read_text(encoding="utf-8"))
    side = path.with_suffix(".json")
    if not side.is_file():
        return desk
    try:
        payload = json.loads(side.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, TypeError):
        return desk
    if not isinstance(payload, dict):
        return desk

    # Markdown is the human-readable source for intentional desk fields.
    # The sidecar is authoritative for structured metadata that Markdown
    # cannot round-trip (fabric cache, world cursor, OEW state, stream stats).
    if isinstance(payload.get("meta"), dict):
        desk.meta = dict(payload["meta"])
    if isinstance(payload.get("load"), dict):
        desk.load = dict(payload["load"])
    if isinstance(payload.get("focus"), list):
        desk.focus = [str(x) for x in payload["focus"]][:4]
    if isinstance(payload.get("executive"), str):
        desk.executive = payload["executive"]
    if isinstance(payload.get("updated"), str):
        desk.updated = payload["updated"]
    return desk
