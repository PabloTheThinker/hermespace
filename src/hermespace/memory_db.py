"""Hermespace memory — studyable turn history for any Hermes agent.

Creates a small database + markdown journal under HERMESPACE_HOME so agents
can revisit prior workspace turns (input → output → decision).

Layout (default ~/.hermespace):
  memory/hermespace/
    hermespace.db          SQLite turns
    journal/YYYY-MM-DD.md  human-readable daily log
    ACTIVE.md              live desk (unchanged)
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from hermespace.paths import state_dir


def _utcnow() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _today() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


@dataclass
class MemoryRecord:
    turn_id: str
    session_id: str
    agent_id: str
    created_at: str
    message: str
    goal: str
    decision: str
    report: str
    plan_json: str
    context: str
    load_level: str
    executive: str
    skipped: int
    reason: str
    tags_json: str
    meta_json: str


class HermespaceMemory:
    """SQLite + markdown journal."""

    def __init__(self, root: Path | None = None) -> None:
        self.root = root or state_dir()
        self.root.mkdir(parents=True, exist_ok=True)
        self.db_path = self.root / "hermespace.db"
        self.journal_dir = self.root / "journal"
        self.journal_dir.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS turns (
                  turn_id TEXT PRIMARY KEY,
                  session_id TEXT,
                  agent_id TEXT,
                  created_at TEXT,
                  message TEXT,
                  goal TEXT,
                  decision TEXT,
                  report TEXT,
                  plan_json TEXT,
                  context TEXT,
                  load_level TEXT,
                  executive TEXT,
                  skipped INTEGER,
                  reason TEXT,
                  tags_json TEXT,
                  meta_json TEXT
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_turns_session ON turns(session_id, created_at)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_turns_created ON turns(created_at)"
            )
            conn.commit()

    def record(
        self,
        *,
        turn_id: str,
        session_id: str,
        agent_id: str,
        message: str,
        goal: str,
        decision: str,
        report: str,
        plan: list[str],
        context: str,
        load_level: str = "",
        executive: str = "",
        skipped: bool = False,
        reason: str = "",
        tags: list[str] | None = None,
        meta: dict[str, Any] | None = None,
    ) -> str:
        created = _utcnow()
        plan_json = json.dumps(list(plan or []))
        tags_json = json.dumps(list(tags or []))
        meta_json = json.dumps(meta or {})
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO turns (
                  turn_id, session_id, agent_id, created_at, message, goal, decision,
                  report, plan_json, context, load_level, executive, skipped, reason,
                  tags_json, meta_json
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    turn_id,
                    session_id,
                    agent_id,
                    created,
                    message,
                    goal,
                    decision,
                    report,
                    plan_json,
                    context,
                    load_level,
                    executive,
                    1 if skipped else 0,
                    reason,
                    tags_json,
                    meta_json,
                ),
            )
            conn.commit()

        self._append_journal(
            created=created,
            turn_id=turn_id,
            session_id=session_id,
            agent_id=agent_id,
            message=message,
            goal=goal,
            decision=decision,
            report=report,
            plan=plan or [],
            skipped=skipped,
            reason=reason,
            load_level=load_level,
            executive=executive,
        )
        return turn_id

    def _append_journal(self, **kw: Any) -> None:
        day = _today()
        path = self.journal_dir / f"{day}.md"
        if not path.exists():
            path.write_text(f"# Hermespace journal — {day}\n\n", encoding="utf-8")
        block = (
            f"## {kw['created']} · `{kw['turn_id'][:8]}`\n"
            f"- **session:** {kw['session_id']} · **agent:** {kw['agent_id']}\n"
            f"- **skipped:** {kw['skipped']} ({kw['reason']})\n"
            f"- **goal:** {kw['goal'][:200]}\n"
            f"- **message:** {kw['message'][:240]}\n"
            f"- **decision:** {kw['decision'][:160]}\n"
            f"- **report:** {kw['report'][:240]}\n"
            f"- **plan:** {', '.join(kw['plan'][:6])}\n"
            f"- **load/exec:** {kw['load_level']} / {kw['executive']}\n\n"
        )
        with path.open("a", encoding="utf-8") as f:
            f.write(block)

    def get(self, turn_id: str) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM turns WHERE turn_id = ?", (turn_id,)
            ).fetchone()
        return dict(row) if row else None

    def history(
        self,
        *,
        session_id: str | None = None,
        limit: int = 20,
        include_skipped: bool = False,
    ) -> list[dict[str, Any]]:
        q = "SELECT * FROM turns WHERE 1=1"
        args: list[Any] = []
        if session_id:
            q += " AND session_id = ?"
            args.append(session_id)
        if not include_skipped:
            q += " AND skipped = 0"
        q += " ORDER BY created_at DESC LIMIT ?"
        args.append(int(limit))
        with self._connect() as conn:
            rows = conn.execute(q, args).fetchall()
        return [dict(r) for r in rows]

    def study(self, query: str, *, limit: int = 20) -> list[dict[str, Any]]:
        """Simple substring study over goal/message/report/decision."""
        q = f"%{query.strip()}%"
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM turns
                WHERE skipped = 0 AND (
                  goal LIKE ? OR message LIKE ? OR report LIKE ?
                  OR decision LIKE ? OR context LIKE ?
                )
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (q, q, q, q, q, int(limit)),
            ).fetchall()
        return [dict(r) for r in rows]

    def journal_path_today(self) -> Path:
        return self.journal_dir / f"{_today()}.md"

    def paths(self) -> dict[str, str]:
        return {
            "db": str(self.db_path),
            "journal_dir": str(self.journal_dir),
            "journal_today": str(self.journal_path_today()),
            "state_dir": str(self.root),
        }
