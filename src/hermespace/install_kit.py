"""One-install front door — Space plus optional Cube / Insight organs.

Do not vendor hermescube or hermes-insight. Soft-import / pip-offer only.
Always UNION plugins.enabled. Never rewrite the list.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Any

from hermespace.environment import hermes_home as default_hermes_home
from hermespace.hermes_enable import (
    ensure_cube_memory_provider,
    read_plugins_enabled,
    union_plugins_enabled,
)
from hermespace.paths import package_root

ORGAN_SPECS: tuple[dict[str, str], ...] = (
    {
        "plugin": "hermescube",
        "import_name": "hermescube",
        "repo": "PabloTheThinker/hermescube",
        "pip": "git+https://github.com/PabloTheThinker/hermescube.git",
        "role": "desk + library",
    },
    {
        "plugin": "hermes-insight",
        "import_name": "hermes_insight",
        "repo": "PabloTheThinker/hermes-insight",
        "pip": "git+https://github.com/PabloTheThinker/hermes-insight.git",
        "role": "pattern card",
    },
)


def _importable(name: str) -> bool:
    try:
        __import__(name)
        return True
    except Exception:
        return False


def _plugin_present(plugin: str, home: Path) -> bool:
    plug = home / "plugins" / plugin
    alt = home / "plugins" / plugin.replace("-", "_")
    return plug.exists() or alt.exists()


def organ_status(*, home: Path | None = None) -> dict[str, Any]:
    root = home if home is not None else default_hermes_home()
    organs: list[dict[str, Any]] = []
    for spec in ORGAN_SPECS:
        present = _importable(spec["import_name"]) or _plugin_present(spec["plugin"], root)
        organs.append({**spec, "present": present})
    return {"home": str(root), "organs": organs}


def union_front_door(*, home: Path | None = None) -> dict[str, Any]:
    """Union hermespace plus any present Cube/Insight plugin names."""
    root = home if home is not None else default_hermes_home()
    actions: list[dict[str, Any]] = [union_plugins_enabled("hermespace", home=root)]
    status = organ_status(home=root)
    for organ in status["organs"]:
        if organ["present"]:
            actions.append(union_plugins_enabled(organ["plugin"], home=root))
    return {
        "ok": all(a.get("ok") for a in actions),
        "enabled": read_plugins_enabled(root / "config.yaml"),
        "actions": actions,
    }


def offer_organs(
    *,
    home: Path | None = None,
    yes: bool = False,
    no_organs: bool = False,
    python: str | None = None,
) -> dict[str, Any]:
    """Offer to pip-install Cube/Insight if missing. Never required."""
    root = home if home is not None else default_hermes_home()
    py = python or sys.executable
    offered: list[dict[str, Any]] = []
    if no_organs:
        return {"ok": True, "skipped": True, "offered": [], "reason": "no_organs"}
    for spec in ORGAN_SPECS:
        present = _importable(spec["import_name"]) or _plugin_present(spec["plugin"], root)
        rec: dict[str, Any] = {
            "plugin": spec["plugin"],
            "repo": spec["repo"],
            "role": spec["role"],
            "present": present,
            "installed": False,
        }
        if present:
            rec["action"] = "already"
            offered.append(rec)
            continue
        rec["offer"] = f"Optional organ ({spec['role']}): pip install {spec['repo']}"
        if not yes:
            rec["action"] = "offered"
            offered.append(rec)
            continue
        try:
            proc = subprocess.run(
                [py, "-m", "pip", "install", spec["pip"]],
                check=False,
                capture_output=True,
                text=True,
                timeout=180,
            )
            rec["action"] = "pip"
            rec["returncode"] = proc.returncode
            rec["installed"] = proc.returncode == 0 and _importable(spec["import_name"])
        except (OSError, subprocess.TimeoutExpired) as exc:
            rec["action"] = "error"
            rec["error"] = type(exc).__name__
        offered.append(rec)
    return {"ok": True, "skipped": False, "offered": offered}


def link_space(*, checkout: Path | None = None, home: Path | None = None) -> dict[str, Any]:
    """Copy/link Space plugin + skill into $HERMES_HOME. No Cube/Insight source."""
    root = (checkout or package_root()).resolve()
    hh = home if home is not None else default_hermes_home()
    (hh / "plugins").mkdir(parents=True, exist_ok=True)
    (hh / "skills").mkdir(parents=True, exist_ok=True)
    plug = hh / "plugins" / "hermespace"
    skill = hh / "skills" / "hermespace"
    skill_src = root / "skills" / "hermespace"
    for target, source in ((plug, root), (skill, skill_src)):
        if target.is_symlink() or target.is_file():
            target.unlink()
        elif target.is_dir() and not target.is_symlink():
            # Leave a real checkout copy alone; only replace links.
            continue
        if source.exists():
            target.symlink_to(source)
    return {
        "ok": plug.exists() and (skill / "SKILL.md").is_file(),
        "plugin": str(plug),
        "skill": str(skill),
    }


def install_front_door(
    *,
    checkout: Path | None = None,
    home: Path | None = None,
    yes: bool = False,
    no_organs: bool = False,
    enable: bool = True,
    python: str | None = None,
) -> dict[str, Any]:
    """Install Space, offer organs, union plugins.enabled, maybe set Cube memory."""
    hh = home if home is not None else default_hermes_home()
    out: dict[str, Any] = {
        "ok": False,
        "home": str(hh),
        "note": "Cube and Insight stay standalone repos — soft-import only.",
    }
    out["link"] = link_space(checkout=checkout, home=hh)
    out["organs"] = offer_organs(home=hh, yes=yes, no_organs=no_organs, python=python)
    if enable:
        out["union"] = union_front_door(home=hh)
    else:
        out["union"] = {"ok": True, "skipped": True, "enabled": read_plugins_enabled(hh / "config.yaml")}
    cube_present = any(
        o.get("present") or o.get("installed")
        for o in (out["organs"].get("offered") or [])
        if o.get("plugin") == "hermescube"
    ) or _importable("hermescube") or _plugin_present("hermescube", hh)
    if cube_present:
        out["memory"] = ensure_cube_memory_provider(home=hh)
        if out["memory"].get("action") == "kept":
            out["memory"]["note"] = (
                f"left memory.provider={out['memory'].get('provider')} "
                "(will not clobber a provider you already chose)"
            )
    else:
        out["memory"] = {
            "ok": True,
            "action": "skipped",
            "note": "Cube not installed — memory.provider left unset. "
            "When Cube is present, Space sets hermescube only if unset.",
        }
    out["ok"] = bool(out["link"].get("ok")) and bool(out["union"].get("ok"))
    return out
