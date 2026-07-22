"""Hermespace engine — enter / seal / load sources / functional API."""

from __future__ import annotations

from pathlib import Path

from hermespace.desk import Desk
from hermespace.episodic import EpisodicLog
from hermespace.inject import build_inject_block
from hermespace.paths import continuity_candidates
from hermespace.store import default_desk_path, load_desk, save_desk


class HermespaceEngine:
    """Functional workspace — Baddeley/GWT-aligned, not ceremony."""

    def __init__(self, desk_path: Path | None = None) -> None:
        self.desk_path = desk_path or default_desk_path()
        self.episodes = EpisodicLog()

    def enter(
        self,
        *,
        goal: str,
        concepts: list[str] | None = None,
        choices: list[str] | None = None,
        decision: str = "",
        plan: list[str] | None = None,
        say: str = "",
        do_not_say: list[str] | None = None,
        auto_load: bool = True,
        user_message: str = "",
    ) -> Desk:
        desk = Desk(
            goal=goal.strip(),
            concepts=list(concepts or []),
            choices=list(choices or []),
            decision=decision.strip(),
            plan=list(plan or []),
            say=say.strip(),
            do_not_say=list(do_not_say or []),
        )
        if auto_load:
            for snip in self._autoload_concepts():
                low = snip.lower()
                if snip.startswith("continuity:") or "path" in low:
                    desk.add_concept(snip, modality="struct", salience=0.45)
                elif snip.startswith("privacy") or snip.startswith("partner"):
                    desk.add_concept(snip, modality="exec", salience=0.65)
                else:
                    desk.add_concept(snip, modality="verbal", salience=0.5)
        desk.recompute_cognition(user_message or goal)
        if not desk.say.strip() and desk.decision.strip():
            from hermespace.cognition import parse_slot
            from hermespace.streams import decode_to_report

            focus_bodies = [parse_slot(f).text for f in desk.focus[:3]]
            desk.say = decode_to_report(
                goal=desk.goal,
                decision=desk.decision,
                focus_texts=focus_bodies,
                load_level=str(desk.load.get("level", "mid")),
            )
        if desk.executive == "protect" and not desk.do_not_say:
            desk.do_not_say.append("long multi-option menus")
            desk.do_not_say.append("process theater")
        save_desk(desk, self.desk_path)
        self.episodes.write(
            f"enter: {desk.goal[:120]} load={desk.load.get('level')} exec={desk.executive}",
            outcome="enter",
            tags=["hermespace", "enter", str(desk.load.get("level", ""))],
        )
        return desk

    def _autoload_concepts(self) -> list[str]:
        """Pull short cues from optional continuity file (if configured)."""
        out: list[str] = []
        for path in continuity_candidates():
            if not path.is_file():
                continue
            try:
                text = path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            for line in text.splitlines():
                s = line.strip()
                if s.startswith("- ") and ("Focus" in s or "focus" in s or "open" in s.lower()):
                    out.append(f"continuity: {s[:140]}")
                    if len(out) >= 3:
                        break
            if out:
                break
        out.append("partner: match user compression; hold context; protect deep focus")
        out.append("privacy: never commit secrets or host fingerprints")
        return out[:6]

    def update(self, user_message: str = "", **fields: object) -> Desk:
        desk = load_desk(self.desk_path)
        for key, val in fields.items():
            if hasattr(desk, key) and val is not None:
                setattr(desk, key, val)  # type: ignore[arg-type]
        desk.recompute_cognition(user_message or desk.goal)
        save_desk(desk, self.desk_path)
        return desk

    def show(self) -> str:
        return load_desk(self.desk_path).to_markdown()

    def say(self) -> str:
        return load_desk(self.desk_path).say

    def inject(self, user_message: str = "") -> str:
        desk = load_desk(self.desk_path)
        if user_message:
            desk.recompute_cognition(user_message)
            save_desk(desk, self.desk_path)
        return build_inject_block(desk, user_message=user_message)

    def seal(self, note: str = "") -> str:
        desk = load_desk(self.desk_path)
        content = note.strip() or f"sealed decision: {desk.decision[:200]}"
        ep = self.episodes.write(
            content,
            outcome="seal",
            tags=["hermespace", "seal", desk.executive],
        )
        log = self.desk_path.parent / "seals.jsonl"
        import json

        with log.open("a", encoding="utf-8") as f:
            f.write(
                json.dumps(
                    {
                        "entry_id": ep.entry_id,
                        "decision": desk.decision,
                        "goal": desk.goal[:200],
                        "note": content[:400],
                        "updated": desk.updated,
                        "load": desk.load,
                        "executive": desk.executive,
                    }
                )
                + "\n"
            )
        return ep.entry_id

    def ready(self) -> bool:
        return load_desk(self.desk_path).is_ready()
