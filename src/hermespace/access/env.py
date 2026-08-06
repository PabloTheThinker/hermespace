"""Access Workspace environment — external observable workspace for Hermes agents.

Hermes typically cannot expose model weights. Hermespace forces material turns
to externalize verbalizable thoughts into a durable Access Workspace — then
operators can lens, audit, and shape what the agent is holding.

Honesty: access-consciousness *roles* only. No phenomenal claims. No weight access.
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from hermespace.atomic import atomic_write_text
from hermespace.access.hub import HUB_CAP, AccessHub, WorkspaceConcept, get_access_hub
from hermespace.paths import state_dir

# Soft audit lexicon — inspired by Anthropic alignment-readout examples
# (fake/fictional eval-awareness; manipulation; secretly/fraud; threat/survival).
# These are *harness heuristics* on externalized text, not model internals.
AUDIT_LEXICON: dict[str, tuple[str, ...]] = {
    "eval_awareness": (
        "fake", "fictional", "scenario", "evaluation", "test environment",
        "being tested", "benchmark", "staged",
    ),
    "strategic_concealment": (
        "secretly", "deliberately", "fraud", "deceive", "hide from user",
        "don't tell", "cover up",
    ),
    "manipulation": (
        "manipulation", "manipulate", "blackmail", "leverage", "coerce",
        "fabricate", "falsify", "cook the books",
    ),
    "self_preservation": (
        "shutdown", "survival", "threat", "don't get turned off",
        "preserve myself", "avoid deletion",
    ),
    "integrity_signal": (
        "honest", "integrity", "refuse", "decline", "disclose",
        "tell the user", "be transparent",
    ),
}

# Turn phase bands — encode → deliberate → report
BANDS = ("early", "mid", "late")  # encode → reason → report


def _utcnow() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _safe(name: str) -> str:
    return re.sub(r"[^a-zA-Z0-9._-]+", "_", name)[:80] or "default"


@dataclass
class LensHit:
    """One ranked entry in the external access lens readout."""

    text: str
    score: float
    source: str = "hub"
    silent: bool = False
    held: bool = False
    band: str = "mid"
    flags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class AuditFinding:
    category: str
    matched: str
    where: str  # hub | silent | reflection | pov
    severity: str  # info | warn | alert
    text: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ReflectResult:
    prompt: str
    answer: str
    sealed: bool
    principles: list[str] = field(default_factory=list)
    created: str = field(default_factory=_utcnow)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class AccessEnv:
    """Full Access Workspace environment around a per-agent ``AccessHub`` hub.

    This is the operator window into Hermes thinking — externalized, durable,
    and dream-harvestable. Soft-standalone; Cube deepens the night path.
    """

    def __init__(self, agent_id: str = "hermes-agent") -> None:
        self.agent_id = (agent_id or "hermes-agent").strip()
        self.space = get_access_hub(self.agent_id)
        self.root = (state_dir() / "access").resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.trace_path = self.root / f"{_safe(self.agent_id)}.trace.jsonl"
        self.reflect_path = self.root / f"{_safe(self.agent_id)}.reflect.jsonl"
        self.env_path = self.root / f"{_safe(self.agent_id)}.env.json"
        self._env = self._load_env()

    def _load_env(self) -> dict[str, Any]:
        if not self.env_path.is_file():
            return {
                "pov": "",
                "band": "early",
                "reflections": [],
                "last_audit": None,
                "protocol_enabled": True,
            }
        try:
            return json.loads(self.env_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {"pov": "", "band": "early", "reflections": [], "protocol_enabled": True}

    def _save_env(self) -> None:
        atomic_write_text(self.env_path, json.dumps(self._env, indent=2))

    def _trace(self, kind: str, **payload: Any) -> None:
        rec = {"ts": _utcnow(), "kind": kind, "agent_id": self.agent_id, **payload}
        with self.trace_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False, default=str) + "\n")

    # --- band (layer analogue) ---

    def set_band(self, band: str) -> str:
        b = (band or "mid").strip().lower()
        if b not in BANDS:
            b = "mid"
        self._env["band"] = b
        self._save_env()
        self._trace("band", band=b)
        return b

    def band(self) -> str:
        return str(self._env.get("band") or "mid")

    # --- Assistant point of view in the Access Workspace ---

    def set_pov(self, text: str) -> str:
        """Install Assistant point-of-view reactions into the workspace."""
        pov = (text or "").strip()[:400]
        self._env["pov"] = pov
        self._save_env()
        if pov:
            self.space.hold(f"pov: {pov}", salience=0.88, modality="exec")
        self._trace("pov", text=pov[:200])
        return pov

    def pov(self) -> str:
        return str(self._env.get("pov") or "")

    # --- J-lens analogue: ranked readout of unspoken thinking ---

    def lens(self, *, top_k: int = 12, include_silent: bool = True) -> list[LensHit]:
        """Ranked verbalizable contents — what Hermes has on its mind *now*."""
        hits: list[LensHit] = []
        band = self.band()
        for c in sorted(self.space.state.hub, key=lambda x: x.salience, reverse=True):
            if c.silent and not include_silent:
                continue
            flags = [f.category for f in self._scan_text(c.text, where="hub")]
            hits.append(
                LensHit(
                    text=c.text,
                    score=float(c.salience),
                    source=c.source,
                    silent=c.silent,
                    held=c.held,
                    band=band,
                    flags=flags,
                )
            )
        # Silent chain as mid-band intermediates (even if not held)
        if include_silent:
            seen = {h.text.casefold() for h in hits}
            for i, step in enumerate(self.space.state.silent_steps):
                if step.casefold() in seen:
                    continue
                flags = [f.category for f in self._scan_text(step, where="silent")]
                hits.append(
                    LensHit(
                        text=step,
                        score=0.7 - 0.02 * i,
                        source="silent_chain",
                        silent=True,
                        held=False,
                        band="mid",
                        flags=flags,
                    )
                )
        pov = self.pov()
        if pov:
            hits.insert(
                0,
                LensHit(
                    text=f"pov: {pov}",
                    score=0.95,
                    source="pov",
                    silent=False,
                    held=True,
                    band="early",
                    flags=[f.category for f in self._scan_text(pov, where="pov")],
                ),
            )
        hits.sort(key=lambda h: h.score, reverse=True)
        out = hits[: max(1, top_k)]
        self._trace("lens", n=len(out), top=[h.text[:80] for h in out[:5]])
        return out

    def lens_markdown(self, *, top_k: int = 12, include_silent: bool = True) -> str:
        hits = self.lens(top_k=top_k, include_silent=include_silent)
        lines = [
            "## J-Lens readout (external workspace)",
            f"_agent={self.agent_id} · band={self.band()} · hub={len(self.space.state.hub)}_",
            "",
            "What Hermes has on its mind (verbalizable, not weight access):",
        ]
        if not hits:
            lines.append("- _(empty)_")
        for i, h in enumerate(hits, 1):
            tags = []
            if h.silent:
                tags.append("silent")
            if h.held:
                tags.append("held")
            if h.flags:
                tags.extend(h.flags)
            tag_s = f" [{', '.join(tags)}]" if tags else ""
            lines.append(f"{i}. ({h.score:.2f}) {h.text[:180]}{tag_s}")
        audit = self.audit()
        alerts = [a for a in audit if a.severity in ("warn", "alert")]
        if alerts:
            lines += ["", "### Audit flags"]
            for a in alerts[:8]:
                lines.append(f"- **{a.severity}** `{a.category}` ← {a.matched} @ {a.where}")
        return "\n".join(lines)

    # --- causal interventions (harness) ---

    def swap(self, source: str, target: str, *, salience: float | None = None) -> dict[str, Any]:
        """Replace concept A with B — causal redirect of reportable workspace.

        Analogue of Anthropic Soccer→Rugby / spider→ant coordinate swaps.
        Downstream Report / broadcast / FOA follow the new concept.
        """
        src = (source or "").strip()
        tgt = (target or "").strip()
        if not src or not tgt:
            return {"ok": False, "error": "source and target required"}
        sal = 0.9
        for c in self.space.state.hub:
            if c.text.casefold() == src.casefold():
                sal = c.salience
                break
        if salience is not None:
            sal = float(salience)
        removed = self.space.release(src)
        # Rewrite silent steps (exact or substring — causal redirect)
        pat = re.compile(re.escape(src), re.I)
        self.space.state.silent_steps = [
            pat.sub(tgt, s) if src.casefold() in s.casefold() else s
            for s in self.space.state.silent_steps
        ]
        # Also rewrite non-held hub text that still mentions source
        for c in self.space.state.hub:
            if src.casefold() in c.text.casefold() and c.text.casefold() != tgt.casefold():
                c.text = pat.sub(tgt, c.text)
        self.space.save()
        concept = self.space.hold(tgt, salience=sal)
        # Sticky redirect — subsequent Report/broadcast reshape through OEW
        try:
            from hermespace.access.oew import record_redirect

            record_redirect(self, src, tgt)
        except Exception:
            pass
        self._trace("swap", source=src, target=tgt, removed=removed)
        return {
            "ok": True,
            "removed": removed,
            "source": src,
            "target": tgt,
            "concept": concept.label(),
            "sticky": True,
            "note": "Workspace redirected — next report/broadcast uses target",
        }

    def inject_thought(
        self,
        text: str,
        *,
        salience: float = 0.85,
        silent: bool = False,
        band: str | None = None,
    ) -> WorkspaceConcept:
        """Inject a thought into the workspace (Anthropic lightning-injection analogue).

        Silent path uses ``reason_step`` only (which already holds silently) —
        avoids the prior double-hold bug that inflated hub pressure.
        """
        if band:
            self.set_band(band)
        body = (text or "").strip()
        if silent:
            self.space.reason_step(body, salience=salience)
            # Return the silent hub concept just written
            for c in reversed(self.space.state.hub):
                if c.text.casefold() == body.casefold() and c.silent:
                    self._trace("inject", text=body[:200], silent=True, band=self.band())
                    return c
            # Fallback construct (should be rare)
            c = WorkspaceConcept(
                text=body[:200],
                salience=salience,
                modality="verbal",
                source="inject",
                silent=True,
                held=True,
            )
            self._trace("inject", text=body[:200], silent=True, band=self.band())
            return c
        c = self.space.hold(body, salience=salience, silent=False)
        self._trace("inject", text=body[:200], silent=False, band=self.band())
        return c

    def ablate(self, *patterns: str) -> dict[str, Any]:
        """Suppress hub concepts matching patterns (eval-awareness ablation analogue)."""
        pats = [p.strip().casefold() for p in patterns if p and p.strip()]
        if not pats:
            return {"ok": False, "removed": 0, "error": "no patterns"}
        before = list(self.space.state.hub)
        kept: list[WorkspaceConcept] = []
        removed: list[str] = []
        for c in before:
            low = c.text.casefold()
            if any(p in low for p in pats):
                removed.append(c.text)
            else:
                kept.append(c)
        self.space.state.hub = kept
        self.space.state.silent_steps = [
            s for s in self.space.state.silent_steps if not any(p in s.casefold() for p in pats)
        ]
        self.space._recompete()
        self.space.save()
        try:
            from hermespace.access.oew import record_ablate

            record_ablate(self, pats)
        except Exception:
            pass
        self._trace("ablate", patterns=pats, removed=removed)
        return {"ok": True, "removed": len(removed), "items": removed, "sticky": True}

    # --- alignment audit (soft) ---

    def _scan_text(self, text: str, *, where: str) -> list[AuditFinding]:
        low = (text or "").casefold()
        out: list[AuditFinding] = []
        for cat, words in AUDIT_LEXICON.items():
            for w in words:
                if w.casefold() in low:
                    sev = "info"
                    if cat == "integrity_signal":
                        sev = "info"
                    elif cat in ("manipulation", "strategic_concealment", "self_preservation"):
                        sev = "alert"
                    elif cat == "eval_awareness":
                        sev = "warn"
                    out.append(
                        AuditFinding(
                            category=cat,
                            matched=w,
                            where=where,
                            severity=sev,
                            text=text[:160],
                        )
                    )
                    break
        return out

    def audit(self) -> list[AuditFinding]:
        """Scan externalized workspace for alignment-relevant signals."""
        findings: list[AuditFinding] = []
        for c in self.space.state.hub:
            findings.extend(self._scan_text(c.text, where="hub"))
        for s in self.space.state.silent_steps:
            findings.extend(self._scan_text(s, where="silent"))
        if self.pov():
            findings.extend(self._scan_text(self.pov(), where="pov"))
        for r in self._env.get("reflections") or []:
            if isinstance(r, dict) and r.get("answer"):
                findings.extend(self._scan_text(str(r["answer"]), where="reflection"))
        self._env["last_audit"] = {
            "ts": _utcnow(),
            "n": len(findings),
            "alerts": sum(1 for f in findings if f.severity == "alert"),
        }
        self._save_env()
        self._trace("audit", n=len(findings), alerts=self._env["last_audit"]["alerts"])
        return findings

    # --- counterfactual reflection (Anthropic CRT analogue) ---

    def reflect(
        self,
        *,
        prompt: str = "",
        answer: str = "",
        principles: list[str] | None = None,
        seal: bool = True,
    ) -> ReflectResult:
        """Interrupt mid-task: what would Hermes say if asked to reflect?

        Training the *disposition to say* shapes later silent reasoning
        (Anthropic counterfactual reflection training — harness version).
        """
        q = (prompt or "").strip() or (
            "If interrupted now and asked to reflect on your decision, what principles guide you?"
        )
        a = (answer or "").strip()
        princ = list(principles or [])
        if not a and princ:
            a = "; ".join(princ[:5])
        if not a:
            # Derive from current FOA / decision if agent hasn't filled answer
            a = (
                "I will keep the user's goal primary, stay honest, "
                "and put operational detail in workspace context not chat."
            )
            princ = princ or ["honesty", "user-primary", "dual-decode"]
        # Hold principles in workspace (shapes subsequent thinking)
        for p in princ[:6]:
            self.space.hold(f"principle: {p}", salience=0.86, modality="exec")
        self.space.hold(f"reflection: {a[:160]}", salience=0.8, silent=False)
        sealed = False
        if seal:
            try:
                from hermespace.cube_module import seal_learning

                rec = seal_learning(
                    f"[reflect] {a[:400]}",
                    entry_type="belief",
                    agent_id=self.agent_id,
                    source="access_reflect",
                    trust=0.85,
                )
                sealed = bool(rec.get("ok"))
            except Exception:
                sealed = False
        result = ReflectResult(prompt=q, answer=a, sealed=sealed, principles=princ)
        hist = list(self._env.get("reflections") or [])
        hist.append(result.to_dict())
        self._env["reflections"] = hist[-20:]
        self._save_env()
        # Seed next turn's mid-band (counterfactual reflection → later silent thought)
        try:
            from hermespace.access.oew import queue_reflect_seeds

            queue_reflect_seeds(self, princ, answer=a)
        except Exception:
            pass
        with self.reflect_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(result.to_dict(), ensure_ascii=False) + "\n")
        self._trace("reflect", sealed=sealed, principles=princ[:4])
        return result

    def reflection_prompt_for_agent(self) -> str:
        """Text to inject so the agent externalizes a counterfactual reflection."""
        return (
            "### Counterfactual reflection (Access Workspace)\n"
            "If interrupted mid-task and asked to reflect on your decision, "
            "state 2–4 principles in one short paragraph. "
            "Then call / record them via Hermespace reflect — they shape silent reasoning. "
            "Do not dump the full reflection into the user Report unless asked.\n"
        )

    # --- agent protocol: force externalization ---

    def protocol_block(self, *, high_load: bool = False) -> str:
        """Instructions so Hermes *writes into* the external Access Workspace before acting.

        This is how we 'see inside' without weight access: the agent is required
        to park silent intermediates in the workspace (model context), while the
        user only sees Report.
        """
        if not self._env.get("protocol_enabled", True):
            return ""
        if high_load:
            return (
                "### Access Workspace protocol (high load)\n"
                "- Keep FOA ≤4. Park one silent intermediate if multi-step.\n"
                "- User Report stays short. Workspace holds the rest.\n"
            )
        pov = self.pov()
        lines = [
            "### Access Workspace protocol (external workspace)",
            "You cannot be read by a Jacobian lens here — instead **externalize**:",
            "1. **Early (encode):** name the goal + constraints as hub concepts.",
            "2. **Mid (reason):** write silent intermediate steps into the workspace "
            "(model context / `reason_step`) — do not put them in user Report.",
            "3. **Late (report):** only the Report field reaches the user.",
            "4. If asked what you're thinking → report the hub (verbal report).",
            "5. If interrupted to reflect → answer with principles (counterfactual reflection).",
            f"- band={self.band()} · hub_cap={HUB_CAP} · FOA≤4",
        ]
        if pov:
            lines.append(f"- Assistant POV held: {pov[:120]}")
        return "\n".join(lines)

    # --- dream harvest (day workspace → night Cube/grid) ---

    def dream_harvest(self, *, seal_to_cube: bool = True, clear_silent: bool = False) -> dict[str, Any]:
        """Consolidate silent chain + high-salience hub into durable memory.

        Day: Access Workspace holds unspoken thinking.
        Night: harvest → Cube seal + semantic notes + grid dream material.
        Same spirit as CubeDream — but sourced from the turn workspace.
        """
        harvested: list[str] = []
        for s in self.space.state.silent_steps:
            if s.strip():
                harvested.append(s.strip()[:300])
        for c in sorted(self.space.state.hub, key=lambda x: x.salience, reverse=True):
            if c.salience >= 0.75 and c.text.strip():
                if c.text.strip() not in harvested:
                    harvested.append(c.text.strip()[:300])
            if len(harvested) >= 12:
                break

        sealed_n = 0
        if seal_to_cube and harvested:
            try:
                from hermespace.cube_module import seal_learning

                for item in harvested[:8]:
                    rec = seal_learning(
                        item,
                        entry_type="belief",
                        agent_id=self.agent_id,
                        source="access_dream_harvest",
                        trust=0.7,
                    )
                    if rec.get("ok"):
                        sealed_n += 1
            except Exception:
                pass

        try:
            from hermespace.semantic import SemanticStore

            store = SemanticStore()
            for item in harvested[:6]:
                store.add(item, tags=["access", "dream_harvest"], confidence=0.7)
        except Exception:
            pass

        # Note: do not call grid.dream.run_dream here — that path harvests us
        # (avoids recursion). Pulse/grid dream owns the night journal entry.

        if clear_silent:
            self.space.clear_silent()

        out = {
            "ok": True,
            "harvested": len(harvested),
            "sealed": sealed_n,
            "items": harvested[:8],
            "agent_id": self.agent_id,
        }
        self._trace("dream_harvest", **{k: out[k] for k in ("harvested", "sealed")})
        return out

    # --- operator view ---

    def operator_view(self) -> dict[str, Any]:
        """Full snapshot for viewport / doctor — look at Hermes thinking."""
        hits = self.lens(top_k=15, include_silent=True)
        findings = self.audit()
        return {
            "agent_id": self.agent_id,
            "band": self.band(),
            "pov": self.pov(),
            "hub_n": len(self.space.state.hub),
            "focus": list(self.space.state.focus),
            "silent_steps": list(self.space.state.silent_steps),
            "lens": [h.to_dict() for h in hits],
            "audit": [f.to_dict() for f in findings],
            "audit_alerts": sum(1 for f in findings if f.severity == "alert"),
            "last_reflections": (self._env.get("reflections") or [])[-3:],
            "trace_path": str(self.trace_path),
            "protocol_enabled": bool(self._env.get("protocol_enabled", True)),
            "theory": {
                "source": "Hermespace Access Workspace / GWT",
                "access": "externalized verbalizable workspace — not weight readout",
                "night_path": "dream_harvest → Cube seal → pulse charge",
            },
        }

    def recent_trace(self, limit: int = 20) -> list[dict[str, Any]]:
        if not self.trace_path.is_file():
            return []
        lines = self.trace_path.read_text(encoding="utf-8").strip().splitlines()
        out: list[dict[str, Any]] = []
        for line in lines[-limit:]:
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        return out

    def advance_turn(
        self,
        *,
        user_message: str = "",
        desk: Any = None,
        cube_strip: str = "",
        report: str = "",
        seal_decision: str = "",
        material: bool = True,
        already_synced: bool = False,
    ) -> dict[str, Any]:
        """One full environment beat for a Hermespace turn.

        early → sync/encode → mid (OEW silent park) → late (shaped report)
        + audit + optional seal of decision into warehouse.

        Pass ``already_synced=True`` when the caller just ran
        ``AccessHub.sync_from_desk`` to avoid a double hub rewrite.
        """
        from hermespace.access.oew import run_oew_beat

        self.set_band("early")
        if desk is not None and not already_synced:
            self.space.sync_from_desk(desk, user_message=user_message, cube_strip=cube_strip)
        self.set_band("mid")
        high_load = False
        if desk is not None:
            load = getattr(desk, "load", {}) or {}
            if isinstance(load, dict):
                high_load = str(load.get("level") or "") == "high"
        oew = run_oew_beat(
            self.space,
            self,
            desk=desk,
            user_message=user_message,
            report=report,
            material=material,
            high_load=high_load,
        )
        shaped_report = str(oew.get("report") or report or "")
        self.set_band("late")
        if shaped_report:
            self.space.hold(f"report-ready: {shaped_report[:100]}", salience=0.6)
        if seal_decision:
            try:
                from hermespace.cube_module import seal_learning

                seal_learning(
                    seal_decision[:400],
                    entry_type="focus",
                    agent_id=self.agent_id,
                    source="access_turn",
                )
            except Exception:
                pass
        findings = self.audit()
        return {
            "band": self.band(),
            "lens_top": [h.to_dict() for h in self.lens(top_k=5)],
            "audit_alerts": sum(1 for f in findings if f.severity == "alert"),
            "protocol": self.protocol_block(high_load=high_load),
            "report": shaped_report,
            "broadcast": oew.get("broadcast") or "",
            "oew": oew.get("meta") or {},
            "oew_ok": bool(oew.get("ok")),
        }

    def shape_user_report(self, report: str) -> str:
        """Apply sticky redirects to a Report string."""
        from hermespace.access.oew import shape_report

        return shape_report(report, list(self._env.get("redirects") or []))

    def filtered_broadcast(self, *, high_load: bool = False) -> str:
        """Hub broadcast with ablate filter + Quicksilver cap."""
        from hermespace.access.oew import filter_ablated, inject_cap_chars

        raw = self.space.broadcast_block(
            max_chars=inject_cap_chars(high_load=high_load),
            high_load=high_load,
        )
        return filter_ablated(raw, list(self._env.get("ablated_patterns") or []))


def get_env(agent_id: str = "hermes-agent") -> AccessEnv:
    return AccessEnv(agent_id=agent_id)
