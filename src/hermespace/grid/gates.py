"""Autonomy / safety gates — ground-up for Hermespace (not a Conductor port).

Principles borrowed as *ideas*, rebuilt for this surface:
- Budget limits unattended action
- Risk classes
- No irreversible money/public without human
- Dual-channel silence for idle/dream unless material
"""

from __future__ import annotations

import os
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from hermespace.grid.secure_store import (
    atomic_write_json,
    autonomy_enabled,
    grid_root,
    read_json,
)

# Risk ranks
RISK = {"read": 0, "write_local": 1, "network": 2, "exec": 3, "irreversible": 4}


@dataclass
class Budget:
    max_tool_calls: int = 8
    max_self_orders: int = 2
    max_risk: str = "write_local"  # ceiling for unattended
    used_tool_calls: int = 0
    used_self_orders: int = 0
    window_started: float = field(default_factory=time.time)
    window_seconds: int = 3600

    def reset_if_stale(self) -> None:
        if time.time() - self.window_started > self.window_seconds:
            self.used_tool_calls = 0
            self.used_self_orders = 0
            self.window_started = time.time()


def _budget_path() -> Path:
    return grid_root() / "budget.json"


def load_budget() -> Budget:
    raw = read_json(_budget_path(), {})
    if not isinstance(raw, dict):
        return Budget()
    b = Budget(
        max_tool_calls=int(raw.get("max_tool_calls") or 8),
        max_self_orders=int(raw.get("max_self_orders") or 2),
        max_risk=str(raw.get("max_risk") or "write_local"),
        used_tool_calls=int(raw.get("used_tool_calls") or 0),
        used_self_orders=int(raw.get("used_self_orders") or 0),
        window_started=float(raw.get("window_started") or time.time()),
        window_seconds=int(raw.get("window_seconds") or 3600),
    )
    b.reset_if_stale()
    return b


def save_budget(b: Budget) -> None:
    atomic_write_json(_budget_path(), asdict(b))


@dataclass
class GateResult:
    allowed: bool
    reason: str
    silent_user: bool = True


_BLOCKED_INTENT = (
    "buy domain",
    "purchase",
    "wire money",
    "send money",
    "tweet as",
    "post publicly",
    "rm -rf /",
    "sudo password",
    "exfiltrat",
)


def check_intent(text: str) -> GateResult:
    low = (text or "").lower()
    for b in _BLOCKED_INTENT:
        if b in low:
            return GateResult(False, f"blocked_intent:{b}", silent_user=True)
    return GateResult(True, "ok", silent_user=True)


def check_autonomy_self_order(text: str, risk: str = "write_local") -> GateResult:
    if not autonomy_enabled():
        return GateResult(False, "HERMESPACE_AUTONOMY off", silent_user=True)
    intent = check_intent(text)
    if not intent.allowed:
        return intent
    b = load_budget()
    b.reset_if_stale()
    if RISK.get(risk, 99) > RISK.get(b.max_risk, 1):
        return GateResult(False, f"risk {risk} > ceiling {b.max_risk}", silent_user=True)
    if b.used_self_orders >= b.max_self_orders:
        return GateResult(False, "self_order budget exhausted", silent_user=True)
    b.used_self_orders += 1
    save_budget(b)
    return GateResult(True, "budget_ok", silent_user=True)


def check_skill_promote(body: str) -> GateResult:
    """Lightweight static guard before promoting a draft skill to Hermes."""
    low = (body or "").lower()
    dangerous = (
        "curl | bash",
        "wget | sh",
        "eval(",
        "base64 -d",
        "/etc/shadow",
        "ignore previous instructions",
        "exfiltrate",
        "sudo -s",
    )
    for d in dangerous:
        if d in low:
            return GateResult(False, f"skill_guard:{d}", silent_user=False)
    if len(body) > 120_000:
        return GateResult(False, "skill_too_large", silent_user=False)
    return GateResult(True, "ok", silent_user=False)


def gate_status() -> dict[str, Any]:
    from hermespace.grid.boundary import load_policy

    b = load_budget()
    b.reset_if_stale()
    pol = load_policy()
    return {
        "autonomy_enabled": autonomy_enabled(),
        "budget": asdict(b),
        "env_hint": "HERMESPACE_AUTONOMY=0|1",
        "boundary": {
            "pocket_root": pol.pocket_root,
            "project_write_default": pol.project_write_default,
            "allowlist_n": len(pol.allowlist),
            "permits_n": len(pol.permits),
        },
    }
