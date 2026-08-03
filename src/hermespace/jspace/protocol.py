"""Obligatory External Workspace (OEW) protocol — scaffold.

Anthropic's J-space is *causally necessary* for higher-order thought.
Hermespace becomes Hermes's J-space when material turns cannot complete
without parking verbalizable intermediates in the external hub.

This module is the gate: it does not yet block turns by default
(``HERMESPACE_OEW=0``). Enable with ``HERMESPACE_OEW=1`` once workflow
wiring lands. See assessment doc for the full thesis.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any


def oew_enabled() -> bool:
    return os.environ.get("HERMESPACE_OEW", "0").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


@dataclass
class ProtocolVerdict:
    """Result of evaluating whether a turn satisfies the OEW protocol."""

    ok: bool
    material: bool
    reason: str
    required: list[str] = field(default_factory=list)
    present: list[str] = field(default_factory=list)
    missing: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "material": self.material,
            "reason": self.reason,
            "required": list(self.required),
            "present": list(self.present),
            "missing": list(self.missing),
            "oew_enabled": oew_enabled(),
        }


@dataclass
class ProtocolGate:
    """Checks that a material turn externalized silent intermediates."""

    min_silent_steps: int = 1
    require_report: bool = True
    require_hub_hold: bool = False

    def evaluate(
        self,
        *,
        material: bool,
        silent_steps: int = 0,
        has_report: bool = False,
        hub_holds: int = 0,
        gated_skip: bool = False,
    ) -> ProtocolVerdict:
        if gated_skip or not material:
            return ProtocolVerdict(
                ok=True,
                material=False,
                reason="non-material or gated — protocol not required",
            )

        required: list[str] = []
        present: list[str] = []
        missing: list[str] = []

        if self.min_silent_steps > 0:
            required.append(f"silent_steps>={self.min_silent_steps}")
            if silent_steps >= self.min_silent_steps:
                present.append(f"silent_steps={silent_steps}")
            else:
                missing.append(
                    f"silent_steps={silent_steps} (need >={self.min_silent_steps})"
                )

        if self.require_report:
            required.append("report")
            if has_report:
                present.append("report")
            else:
                missing.append("report")

        if self.require_hub_hold:
            required.append("hub_hold")
            if hub_holds > 0:
                present.append(f"hub_holds={hub_holds}")
            else:
                missing.append("hub_hold")

        ok = not missing
        # Soft mode: always ok unless OEW enabled
        if not oew_enabled():
            return ProtocolVerdict(
                ok=True,
                material=True,
                reason="OEW soft — missing items noted but not blocking",
                required=required,
                present=present,
                missing=missing,
            )

        return ProtocolVerdict(
            ok=ok,
            material=True,
            reason="OEW satisfied" if ok else "OEW incomplete — park silent intermediates",
            required=required,
            present=present,
            missing=missing,
        )


def evaluate_material_turn(
    *,
    material: bool,
    silent_steps: int = 0,
    has_report: bool = False,
    hub_holds: int = 0,
    gated_skip: bool = False,
) -> ProtocolVerdict:
    """Convenience entry for workflow / bridge."""
    return ProtocolGate().evaluate(
        material=material,
        silent_steps=silent_steps,
        has_report=has_report,
        hub_holds=hub_holds,
        gated_skip=gated_skip,
    )
