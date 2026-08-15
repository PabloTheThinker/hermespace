"""Union ``plugins.enabled`` the grokbot way — append, never replace.

Stolen from hermes-grokbot enable.py (standalone repo): read the existing
list, append this plugin if missing, write only that addition. Cube,
Insight, and grokbot may already be there.

Do not vendor grokbot. Do not dump-rewrite the YAML document. Public
reference: https://github.com/PabloTheThinker/hermes-grokbot
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from hermespace.environment import hermes_home as default_hermes_home


def config_path(home: Path | None = None) -> Path:
    return (home or default_hermes_home()) / "config.yaml"


def read_plugins_enabled(config: Path | None = None) -> list[str]:
    """Best-effort parse of plugins.enabled. Empty if missing/unreadable."""
    path = Path(config) if config else config_path()
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return []
    enabled: list[str] = []
    in_plugins = False
    in_enabled = False
    enabled_indent: int | None = None
    for line in text.splitlines():
        raw = line.split("#", 1)[0]
        if not raw.strip():
            continue
        indent = len(raw) - len(raw.lstrip(" \t"))
        stripped = raw.strip()
        if stripped == "plugins:" or stripped.startswith("plugins:"):
            in_plugins = True
            in_enabled = False
            continue
        if in_plugins and indent == 0 and not stripped.startswith("-"):
            in_plugins = False
            in_enabled = False
        if not in_plugins:
            continue
        if stripped == "enabled:" or stripped.startswith("enabled:"):
            in_enabled = True
            enabled_indent = indent
            inline = stripped.split(":", 1)[1].strip()
            if inline.startswith("[") and inline.endswith("]"):
                inner = inline[1:-1].strip()
                if inner:
                    enabled.extend(
                        p.strip().strip("\"'") for p in inner.split(",") if p.strip()
                    )
            continue
        if in_enabled:
            if enabled_indent is not None and indent <= enabled_indent and not stripped.startswith("-"):
                in_enabled = False
                continue
            if stripped.startswith("-"):
                item = stripped[1:].strip().strip("\"'")
                if item:
                    enabled.append(item)
    return enabled


def _split_inline_list(inline: str) -> list[str]:
    inner = inline.strip()
    if inner.startswith("[") and inner.endswith("]"):
        inner = inner[1:-1].strip()
    if not inner:
        return []
    return [p.strip().strip("\"'") for p in inner.split(",") if p.strip()]


def _append_enabled_item(text: str, name: str) -> str:
    lines = text.splitlines()
    in_plugins = False
    in_enabled = False
    enabled_indent: int | None = None
    last_item_idx: int | None = None
    plugins_idx: int | None = None
    enabled_idx: int | None = None
    for i, line in enumerate(lines):
        raw = line.split("#", 1)[0]
        if not raw.strip():
            continue
        indent = len(raw) - len(raw.lstrip(" \t"))
        stripped = raw.strip()
        if stripped == "plugins:" or stripped.startswith("plugins:"):
            in_plugins = True
            in_enabled = False
            plugins_idx = i
            continue
        if in_plugins and indent == 0 and not stripped.startswith("-"):
            in_plugins = False
            in_enabled = False
        if not in_plugins:
            continue
        if stripped == "enabled:" or stripped.startswith("enabled:"):
            in_enabled = True
            enabled_indent = indent
            enabled_idx = i
            inline = stripped.split(":", 1)[1].strip()
            if inline.startswith("[") and inline.endswith("]"):
                items = _split_inline_list(inline)
                if name not in items:
                    items.append(name)
                pad = line[: len(line) - len(line.lstrip(" \t"))]
                comment = ""
                if "#" in line[line.find(stripped) + len(stripped.split(":")[0]) :]:
                    hash_at = line.find("#", indent)
                    if hash_at != -1:
                        comment = line[hash_at:]
                        if comment and not comment.startswith(" "):
                            comment = " " + comment
                lines[i] = f"{pad}enabled: [{', '.join(items)}]{comment}"
                return "\n".join(lines) + ("\n" if text.endswith("\n") else "")
            continue
        if in_enabled:
            if enabled_indent is not None and indent <= enabled_indent and not stripped.startswith("-"):
                in_enabled = False
                continue
            if stripped.startswith("-"):
                last_item_idx = i
    if last_item_idx is not None:
        pad = lines[last_item_idx][: len(lines[last_item_idx]) - len(lines[last_item_idx].lstrip(" \t"))]
        lines.insert(last_item_idx + 1, f"{pad}- {name}")
        return "\n".join(lines) + ("\n" if text.endswith("\n") else "")
    if enabled_idx is not None:
        pad = "    "
        if enabled_indent is not None:
            pad = " " * (enabled_indent + 2)
        lines.insert(enabled_idx + 1, f"{pad}- {name}")
        return "\n".join(lines) + ("\n" if text.endswith("\n") else "")
    if plugins_idx is not None:
        lines.insert(plugins_idx + 1, "  enabled:")
        lines.insert(plugins_idx + 2, f"    - {name}")
        return "\n".join(lines) + ("\n" if text.endswith("\n") else "")
    block = f"plugins:\n  enabled:\n    - {name}\n"
    if text and not text.endswith("\n"):
        text += "\n"
    return text + block


def union_plugins_enabled(
    name: str = "hermespace",
    *,
    home: Path | None = None,
) -> dict[str, Any]:
    """APPEND ``name`` to plugins.enabled. Never replace the existing list."""
    root = home if home is not None else default_hermes_home()
    path = config_path(root)
    if not path.is_file():
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(f"plugins:\n  enabled:\n    - {name}\n", encoding="utf-8")
        except OSError as exc:
            return {"ok": False, "action": "error", "error": type(exc).__name__, "enabled": []}
        return {"ok": True, "action": "created", "enabled": [name], "path": str(path)}
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        return {"ok": False, "action": "unreadable", "error": type(exc).__name__, "enabled": []}
    current = read_plugins_enabled(path)
    if name in current:
        return {"ok": True, "action": "already", "enabled": current, "path": str(path)}
    new_text = _append_enabled_item(text, name)
    after: list[str] = []
    try:
        path.write_text(new_text, encoding="utf-8")
        after = read_plugins_enabled(path)
    except OSError as exc:
        return {"ok": False, "action": "error", "error": type(exc).__name__, "enabled": current}
    if any(item not in after for item in current) or name not in after:
        try:
            path.write_text(text, encoding="utf-8")
        except OSError:
            pass
        return {
            "ok": False,
            "action": "refused_rewrite",
            "enabled": current,
            "path": str(path),
        }
    return {"ok": True, "action": "appended", "enabled": after, "path": str(path)}
