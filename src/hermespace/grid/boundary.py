"""Pocket-dimension boundary — Hermespace must not spill into user projects.

Rules (hard):
1. All Hermespace *state* lives under HERMESPACE_HOME only.
2. Writes outside the pocket require explicit allowlist or session permit.
3. User project trees are never auto-populated (no silent project files).
4. Destructive paths blocked even with autonomy on.
5. Hermes skill promote only to hermespace-drafts/ unless permit.

This is the security spine for the pocket dimension.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Literal

from hermespace.grid.secure_store import atomic_write_json, grid_root, read_json
from hermespace.paths import hermespace_home, package_root

Mode = Literal["read", "write", "exec", "delete"]

# Paths that must never be written by Hermespace grid code
_NEVER_WRITE_SUFFIXES = (
    ".env",
    ".pem",
    ".key",
    "id_rsa",
    "id_ed25519",
    "credentials.json",
    "auth.json",
    "secrets.yaml",
    "secrets.yml",
)

_NEVER_WRITE_NAMES = {
    ".git",
    ".ssh",
    ".gnupg",
    "sudoers",
    "shadow",
    "passwd",
}


@dataclass
class BoundaryDecision:
    allowed: bool
    reason: str
    path: str = ""
    mode: str = ""
    in_pocket: bool = False


@dataclass
class Policy:
    """Operator-visible security policy snapshot."""

    pocket_root: str
    package_root: str
    project_write_default: str = "deny"  # deny | allowlist
    autonomy: bool = False
    allowlist: list[str] = field(default_factory=list)
    permits: list[dict[str, Any]] = field(default_factory=list)
    rules: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def pocket_root() -> Path:
    return hermespace_home().resolve()


def _policy_path() -> Path:
    return grid_root() / "boundary_policy.json"


def _default_rules() -> list[str]:
    return [
        "State only under HERMESPACE_HOME (the pocket).",
        "Never auto-write into user project trees.",
        "External write requires allowlist entry or time-limited permit.",
        "Secrets-like filenames are never writable.",
        "Hermes promote defaults to skills/hermespace-drafts/ only.",
        "Autonomy does not bypass boundary (only budgets inside pocket).",
        "Delete outside pocket is always denied.",
        "User viewport is read-only observation of pocket state.",
    ]


def load_policy() -> Policy:
    raw = read_json(_policy_path(), {})
    if not isinstance(raw, dict):
        raw = {}
    allow = [str(x) for x in (raw.get("allowlist") or []) if str(x).strip()]
    permits = [x for x in (raw.get("permits") or []) if isinstance(x, dict)]
    # drop expired permits
    now = time.time()
    permits = [p for p in permits if float(p.get("expires_at") or 0) > now]
    return Policy(
        pocket_root=str(pocket_root()),
        package_root=str(package_root()),
        project_write_default=str(raw.get("project_write_default") or "deny"),
        autonomy=os.environ.get("HERMESPACE_AUTONOMY", "0").strip()
        in ("1", "true", "yes", "on"),
        allowlist=allow,
        permits=permits,
        rules=_default_rules(),
    )


def save_policy(policy: Policy) -> None:
    data = policy.to_dict()
    # don't persist computed roots as sole source — keep allowlist/permits
    atomic_write_json(
        _policy_path(),
        {
            "project_write_default": policy.project_write_default,
            "allowlist": policy.allowlist,
            "permits": policy.permits,
            "updated": time.time(),
        },
    )


def is_in_pocket(path: Path | str) -> bool:
    try:
        p = Path(path).expanduser().resolve()
        root = pocket_root()
        return p == root or root in p.parents
    except OSError:
        return False


def is_in_package(path: Path | str) -> bool:
    try:
        p = Path(path).expanduser().resolve()
        root = package_root().resolve()
        return p == root or root in p.parents
    except OSError:
        return False


def _is_secretish(path: Path) -> bool:
    name = path.name.lower()
    if name in _NEVER_WRITE_NAMES:
        return True
    for suf in _NEVER_WRITE_SUFFIXES:
        if name.endswith(suf) or name == suf.lstrip("."):
            return True
    parts = {p.lower() for p in path.parts}
    if ".ssh" in parts or ".gnupg" in parts:
        return True
    return False


def _has_permit(path: Path, mode: Mode, policy: Policy) -> bool:
    now = time.time()
    try:
        target = path.resolve()
    except OSError:
        return False
    for p in policy.permits:
        if float(p.get("expires_at") or 0) <= now:
            continue
        if mode == "write" and p.get("mode") not in ("write", "write_delete"):
            continue
        if mode == "delete" and p.get("mode") != "write_delete":
            continue
        base = Path(str(p.get("path") or "")).expanduser()
        try:
            base_r = base.resolve()
        except OSError:
            continue
        if target == base_r or base_r in target.parents or target in base_r.parents:
            # permit covers the tree
            if target == base_r or base_r in target.parents:
                return True
    for a in policy.allowlist:
        try:
            base_r = Path(a).expanduser().resolve()
        except OSError:
            continue
        if target == base_r or base_r in target.parents:
            return True
    return False


def check_path(path: str | Path, mode: Mode = "read") -> BoundaryDecision:
    """Primary boundary check for any path Hermespace might touch outside pure pocket APIs."""
    try:
        p = Path(path).expanduser().resolve()
    except OSError as e:
        return BoundaryDecision(False, f"unresolvable:{e}", str(path), mode)

    in_pocket = is_in_pocket(p)
    # reads: pocket + package always OK; elsewhere OK for observation (viewport may read desk only)
    if mode == "read":
        if _is_secretish(p) and not in_pocket:
            return BoundaryDecision(False, "secretish_read_blocked", str(p), mode, in_pocket)
        return BoundaryDecision(True, "read_ok", str(p), mode, in_pocket)

    # writes/deletes: secretish always blocked (pocket or not)
    if _is_secretish(p) and mode in ("write", "delete", "exec"):
        return BoundaryDecision(False, "secretish_write_blocked", str(p), mode, in_pocket)

    # writes/deletes inside pocket always OK (except we still block weirdness)
    if in_pocket:
        if mode == "delete" and p == pocket_root():
            return BoundaryDecision(False, "cannot_delete_pocket_root", str(p), mode, True)
        return BoundaryDecision(True, "pocket_write_ok", str(p), mode, True)

    # package tree: allow writes only if HERMESPACE_ALLOW_PACKAGE_WRITE=1 (dev)
    if is_in_package(p):
        if os.environ.get("HERMESPACE_ALLOW_PACKAGE_WRITE", "0").strip() in (
            "1",
            "true",
            "yes",
        ):
            return BoundaryDecision(True, "package_dev_write", str(p), mode, False)
        return BoundaryDecision(False, "package_write_denied_use_pocket", str(p), mode, False)

    if mode == "delete":
        return BoundaryDecision(False, "external_delete_denied", str(p), mode, False)

    policy = load_policy()
    if policy.project_write_default == "deny":
        if _has_permit(p, mode, policy):
            return BoundaryDecision(True, "permit_or_allowlist", str(p), mode, False)
        return BoundaryDecision(
            False,
            "external_write_denied — grant permit: hs grid permit --path DIR --hours 1",
            str(p),
            mode,
            False,
        )

    # allowlist mode still requires match
    if _has_permit(p, mode, policy):
        return BoundaryDecision(True, "allowlist_ok", str(p), mode, False)
    return BoundaryDecision(False, "not_on_allowlist", str(p), mode, False)


def assert_writable(path: str | Path) -> Path:
    d = check_path(path, "write")
    if not d.allowed:
        raise PermissionError(d.reason)
    return Path(d.path)


def grant_permit(
    path: str | Path,
    *,
    hours: float = 1.0,
    mode: str = "write",
    note: str = "",
) -> dict[str, Any]:
    """Time-limited permission for agent/operator to write under a user path."""
    p = Path(path).expanduser().resolve()
    if _is_secretish(p):
        raise PermissionError("cannot permit secretish path")
    if hours <= 0 or hours > 72:
        raise ValueError("hours must be in (0, 72]")
    if mode not in ("write", "write_delete", "read"):
        raise ValueError("mode must be write|write_delete|read")
    policy = load_policy()
    exp = time.time() + hours * 3600
    entry = {
        "path": str(p),
        "mode": mode,
        "expires_at": exp,
        "note": (note or "")[:200],
        "granted_at": time.time(),
    }
    policy.permits.append(entry)
    save_policy(policy)
    return entry


def revoke_permits(*, path: str | None = None) -> int:
    policy = load_policy()
    before = len(policy.permits)
    if path:
        target = str(Path(path).expanduser().resolve())
        policy.permits = [p for p in policy.permits if p.get("path") != target]
    else:
        policy.permits = []
    save_policy(policy)
    return before - len(policy.permits)


def add_allowlist(path: str | Path) -> list[str]:
    p = str(Path(path).expanduser().resolve())
    policy = load_policy()
    if p not in policy.allowlist:
        policy.allowlist.append(p)
    save_policy(policy)
    return policy.allowlist


def remove_allowlist(path: str | Path) -> list[str]:
    p = str(Path(path).expanduser().resolve())
    policy = load_policy()
    policy.allowlist = [x for x in policy.allowlist if x != p]
    save_policy(policy)
    return policy.allowlist


def hermes_promote_dest(skill_name: str, hermes_home: Path) -> Path:
    """Only allowed default destination for skill promotion into Hermes."""
    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in skill_name)[:64]
    dest = (hermes_home / "skills" / "hermespace-drafts" / safe / "SKILL.md").resolve()
    # must stay under hermes skills/hermespace-drafts
    base = (hermes_home / "skills" / "hermespace-drafts").resolve()
    if base not in dest.parents:
        raise PermissionError("promote dest escaped hermespace-drafts")
    return dest


def policy_markdown() -> str:
    pol = load_policy()
    lines = [
        "# Hermespace pocket boundary",
        "",
        f"**Pocket root:** `{pol.pocket_root}`",
        f"**Project write default:** `{pol.project_write_default}`",
        f"**Autonomy:** {'on' if pol.autonomy else 'off'}",
        "",
        "## Rules",
    ]
    for r in pol.rules:
        lines.append(f"- {r}")
    lines.append("")
    lines.append("## Allowlist")
    if pol.allowlist:
        for a in pol.allowlist:
            lines.append(f"- `{a}`")
    else:
        lines.append("- _(empty — external writes denied)_")
    lines.append("")
    lines.append("## Active permits")
    if pol.permits:
        for p in pol.permits:
            exp = time.strftime("%Y-%m-%dT%H:%MZ", time.gmtime(float(p["expires_at"])))
            lines.append(f"- `{p.get('path')}` mode={p.get('mode')} expires={exp}")
    else:
        lines.append("- _(none)_")
    lines.append("")
    lines.append("## Operator commands")
    lines.append("```bash")
    lines.append("hs grid policy")
    lines.append("hs grid permit --path /path/to/project --hours 2 --note \"feature work\"")
    lines.append("hs grid permit-revoke [--path DIR]")
    lines.append("hs view                 # look inside the pocket")
    lines.append("```")
    return "\n".join(lines) + "\n"
