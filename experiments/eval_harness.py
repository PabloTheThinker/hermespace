"""Eval harness — confirm functional behavior (not vibes)."""

from __future__ import annotations

import json
import sys
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1]
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from hermespace.desk import Desk  # noqa: E402
from hermespace.engine import HermespaceEngine  # noqa: E402
from hermespace.gate import should_inject  # noqa: E402
from hermespace.inject import build_inject_block  # noqa: E402
from hermespace.patterns import PATTERNS  # noqa: E402
from hermespace.semantic import consolidate  # noqa: E402


@dataclass
class CaseResult:
    name: str
    ok: bool
    detail: str


def run_eval() -> list[CaseResult]:
    results: list[CaseResult] = []

    # capacity
    d = Desk(concepts=[f"x{i}" for i in range(30)])
    d.clamp()
    results.append(
        CaseResult("capacity_clamp", len(d.concepts) == 12, f"n={len(d.concepts)}")
    )

    # ready requires say
    d2 = Desk(goal="g", decision="A", say="")
    results.append(CaseResult("ready_needs_say", not d2.is_ready(), "empty say"))
    d2.say = "hi"
    results.append(CaseResult("ready_with_say", d2.is_ready(), "ok"))

    # gate trivial
    inj, reason = should_inject("ok", desk_ready=True)
    results.append(CaseResult("gate_skip_trivial", not inj, reason))
    inj2, reason2 = should_inject("proceed build hermespace plugin", desk_ready=True)
    results.append(CaseResult("gate_material", inj2, reason2))

    # engine + inject
    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / "ACTIVE.md"
        eng = HermespaceEngine(desk_path=path)
        eng.enter(
            goal="eval goal",
            concepts=["c1"],
            choices=["A"],
            decision="A",
            plan=["p1"],
            say="eval say",
            auto_load=False,
        )
        block = eng.inject()
        results.append(
            CaseResult(
                "inject_contains_goal",
                "eval goal" in block and "eval say" in block,
                block[:80],
            )
        )
        eng.seal("eval seal")
        results.append(CaseResult("seal_runs", True, "sealed"))

    # patterns matrix
    confirmed = sum(1 for p in PATTERNS if p.confirmed)
    results.append(
        CaseResult(
            "patterns_majority",
            confirmed >= 18,
            f"{confirmed}/{len(PATTERNS)}",
        )
    )

    # consolidate doesn't crash
    cons = consolidate(limit=20)
    results.append(
        CaseResult("consolidate_ok", "scanned" in cons, json.dumps(cons)[:120])
    )

    # markdown roundtrip
    md = Desk(
        goal="rt",
        concepts=["a", "b"],
        decision="A",
        plan=["1"],
        say="s",
    ).to_markdown()
    back = Desk.from_markdown(md)
    results.append(CaseResult("md_roundtrip", back.goal == "rt" and back.say == "s", back.goal))

    return results


def main() -> int:
    rows = run_eval()
    # write results.tsv append
    root = Path(__file__).resolve().parents[1]
    out = root / "experiments" / "results.tsv"
    out.parent.mkdir(parents=True, exist_ok=True)
    passed = sum(1 for r in rows if r.ok)
    line = f"eval-v03\t{passed}/{len(rows)}\t{'pass' if passed == len(rows) else 'fail'}\tcomponent functional suite\n"
    with out.open("a", encoding="utf-8") as f:
        f.write(line)
    print(f"Hermespace eval: {passed}/{len(rows)}")
    for r in rows:
        mark = "OK " if r.ok else "FAIL"
        print(f"  {mark} {r.name}: {r.detail}")
    # write pattern matrix
    from hermespace.patterns import as_markdown

    matrix = root / "docs" / "04-pattern-matrix.md"
    matrix.parent.mkdir(parents=True, exist_ok=True)
    matrix.write_text(as_markdown() + "\n", encoding="utf-8")
    print(f"wrote {matrix}")
    return 0 if passed == len(rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())
