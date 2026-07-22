"""CLI — INPUT/OUTPUT + memory for any Hermes agent."""

from __future__ import annotations

import argparse
import json
import runpy
import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1]
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from hermespace.engine import HermespaceEngine  # noqa: E402
from hermespace.io_contract import HermespaceInput  # noqa: E402
from hermespace.memory_db import HermespaceMemory  # noqa: E402
from hermespace.store import load_desk  # noqa: E402
from hermespace.workflow import Workflow  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        prog="hermespace",
        description="Hermespace — INPUT→workspace→OUTPUT for Hermes agents",
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    # INPUT: start a turn
    tr = sub.add_parser("turn", help="INPUT message → OUTPUT report+context (+memory)")
    tr.add_argument("--message", "-m", default="", help="User message (required input)")
    tr.add_argument("--goal", default="")
    tr.add_argument("--decision", default="")
    tr.add_argument("--say", default="", help="Optional report draft")
    tr.add_argument("--concept", action="append", default=[])
    tr.add_argument("--choice", action="append", default=[])
    tr.add_argument("--plan", action="append", default=[])
    tr.add_argument("--session-id", default="default")
    tr.add_argument("--agent-id", default="hermes-agent")
    tr.add_argument("--force", action="store_true")
    tr.add_argument("--seal", action="store_true")
    tr.add_argument("--seal-note", default="")
    tr.add_argument("--json", action="store_true", help="Full HermespaceOutput JSON")
    tr.add_argument(
        "--output",
        choices=("report", "context", "json", "both"),
        default="both",
        help="What to print (default both: context then report)",
    )

    inn = sub.add_parser("input", help="Show INPUT schema / validate JSON file")
    inn.add_argument("--file", "-f", default="", help="JSON file to validate as input")
    inn.add_argument("--example", action="store_true")

    outp = sub.add_parser("output", help="Print last turn output fields from memory")
    outp.add_argument("--turn-id", default="")
    outp.add_argument("--session-id", default="")
    outp.add_argument("--field", choices=("report", "context", "json"), default="json")

    hist = sub.add_parser("history", help="List prior Hermespace turns (memory DB)")
    hist.add_argument("--session-id", default="")
    hist.add_argument("--limit", type=int, default=10)
    hist.add_argument("--include-skipped", action="store_true")

    study = sub.add_parser("study", help="Search memory DB / journal")
    study.add_argument("query")
    study.add_argument("--limit", type=int, default=10)

    sub.add_parser("status", help="Desk + memory paths JSON")
    sub.add_parser("workflow", help="Print workflow stages")
    sub.add_parser("memory-paths", help="Show DB + journal locations")

    ent = sub.add_parser("enter", help="Clear and write a new desk")
    ent.add_argument("--goal", required=True)
    ent.add_argument("--decision", default="")
    ent.add_argument("--say", default="")
    ent.add_argument("--concept", action="append", default=[])
    ent.add_argument("--choice", action="append", default=[])
    ent.add_argument("--plan", action="append", default=[])
    ent.add_argument("--message", "-m", default="")
    ent.add_argument("--no-autoload", action="store_true")

    sub.add_parser("show", help="Print ACTIVE desk markdown")
    sub.add_parser("say", help="Print report only")
    sub.add_parser("inject", help="Print context inject block")
    sub.add_parser("ready", help="Exit 0 if desk ready")

    seal = sub.add_parser("seal", help="Seal decision to episodic log")
    seal.add_argument("--note", default="")

    up = sub.add_parser("set", help="Update fields on current desk")
    up.add_argument("--goal")
    up.add_argument("--decision")
    up.add_argument("--say")
    up.add_argument("--concept", action="append")
    up.add_argument("--plan", action="append")
    up.add_argument("--message", "-m", default="")

    sub.add_parser("json", help="Print desk JSON")
    sub.add_parser("consolidate", help="Episodic → semantic notes")
    sub.add_parser("patterns", help="Pattern matrix")
    sub.add_parser("eval", help="Eval harness")
    fab = sub.add_parser("fabric", help="Hermes MEMORY/USER + ranked skills snapshot")
    fab.add_argument("--goal", default="")
    fab.add_argument("--message", "-m", default="")
    sk = sub.add_parser("skills", help="Rank Hermes skills for a goal")
    sk.add_argument("--goal", required=True)
    sk.add_argument("--message", "-m", default="")
    sk.add_argument("--limit", type=int, default=8)

    wb = sub.add_parser("workbench", help="Pocket-dimension workbench for an agent")
    wb_sub = wb.add_subparsers(dest="wb_cmd", required=True)
    wbe = wb_sub.add_parser("enter")
    wbe.add_argument("--agent-id", default="hermes-agent")
    wbe.add_argument("--session-id", default="default")
    wbs = wb_sub.add_parser("status")
    wbs.add_argument("--agent-id", default="hermes-agent")
    wbs.add_argument("--session-id", default="default")
    wbi = wb_sub.add_parser("idle")
    wbi.add_argument("--agent-id", default="hermes-agent")
    wbi.add_argument("--session-id", default="default")
    wbp = wb_sub.add_parser("park")
    wbp.add_argument("--goal", required=True)
    wbp.add_argument("--note", default="")
    wbp.add_argument("--agent-id", default="hermes-agent")
    wbp.add_argument("--session-id", default="default")
    wbo = wb_sub.add_parser("order")
    wbo.add_argument("--message", "-m", required=True)
    wbo.add_argument("--goal", default="")
    wbo.add_argument("--decision", default="A — proceed")
    wbo.add_argument("--say", default="")
    wbo.add_argument("--plan", action="append", default=[])
    wbo.add_argument("--agent-id", default="hermes-agent")
    wbo.add_argument("--session-id", default="default")
    wbo.add_argument("--json", action="store_true")
    wbpop = wb_sub.add_parser("pop")
    wbpop.add_argument("--agent-id", default="hermes-agent")
    wbpop.add_argument("--session-id", default="default")
    wbenv = wb_sub.add_parser("env")
    wbenv.add_argument("--agent-id", default="hermes-agent")
    wbenv.add_argument("--session-id", default="default")
    wbenv.add_argument("--markdown", action="store_true")

    neu = sub.add_parser("neural", help="Neural space status / pull / sync")
    neu_sub = neu.add_subparsers(dest="neural_cmd", required=True)
    neu_sub.add_parser("status", help="Field snapshot")
    npull = neu_sub.add_parser("pull", help="Attractor pull for a probe text")
    npull.add_argument("--text", "-t", required=True)
    neu_sub.add_parser("sync", help="Sync neural field from current desk")
    neu_sub.add_parser("caps", help="Local model capability probe")
    neu_sub.add_parser("eval", help="Rank-quality hash vs ollama embed")

    # Grid — autonomy world (missions, lenses, dream, skillbench, selftalk)
    gr = sub.add_parser("grid", help="Autonomy grid: missions, lenses, dream, skillbench, selftalk")
    gr_sub = gr.add_subparsers(dest="grid_cmd", required=True)
    gs = gr_sub.add_parser("status")
    gs.add_argument("--agent-id", default="default")
    gc = gr_sub.add_parser("context")
    gc.add_argument("--agent-id", default="default")
    gm = gr_sub.add_parser("mission-add")
    gm.add_argument("--title", required=True)
    gm.add_argument("--priority", type=int, default=50)
    gm.add_argument("--agent-id", default="default")
    gml = gr_sub.add_parser("mission-list")
    gml.add_argument("--agent-id", default="default")
    gu = gr_sub.add_parser("mission-update")
    gu.add_argument("--id", required=True)
    gu.add_argument("--status", default="")
    gu.add_argument("--note", default="")
    gu.add_argument("--agent-id", default="default")
    gl = gr_sub.add_parser("lens-set")
    gl.add_argument("--name", required=True)
    gl.add_argument("--agent-id", default="default")
    gr_sub.add_parser("lens-list")
    gd = gr_sub.add_parser("dream")
    gd.add_argument("--agent-id", default="default")
    gd.add_argument("--force", action="store_true")
    gt = gr_sub.add_parser("think")
    gt.add_argument("--text", "-t", required=True)
    gt.add_argument("--role", default="self")
    gt.add_argument("--agent-id", default="default")
    gtitle = gr_sub.add_parser("title-set")
    gtitle.add_argument("--title", required=True)
    gtitle.add_argument("--agent-id", default="default")
    gta = gr_sub.add_parser("title-adopt")
    gta.add_argument("--agent-id", default="default")
    gtr = gr_sub.add_parser("tree-rebuild")
    gtr.add_argument("--agent-id", default="default")
    gmod = gr_sub.add_parser("skill-register")
    gmod.add_argument("--name", required=True)
    gmod.add_argument("--file", required=True, help="Path to markdown body")
    gmod.add_argument("--agent-id", default="default")
    gmerge = gr_sub.add_parser("skill-merge")
    gmerge.add_argument("--a", required=True)
    gmerge.add_argument("--b", required=True)
    gmerge.add_argument("--note", default="")
    gmerge.add_argument("--agent-id", default="default")
    gmut = gr_sub.add_parser("skill-mutate")
    gmut.add_argument("--name", required=True)
    gmut.add_argument("--delta", required=True)
    gmut.add_argument("--agent-id", default="default")
    gprom = gr_sub.add_parser("skill-promote")
    gprom.add_argument("--id", required=True)
    gprom.add_argument("--to-hermes", action="store_true")
    gprom.add_argument("--agent-id", default="default")
    gsl = gr_sub.add_parser("skill-list")
    gsl.add_argument("--agent-id", default="default")
    gsc = gr_sub.add_parser("scar-open")
    gsc.add_argument("--kind", default="tool_error")
    gsc.add_argument("--summary", required=True)
    gsc.add_argument("--agent-id", default="default")
    gr_sub.add_parser("gates")
    gr_sub.add_parser("policy")
    gperm = gr_sub.add_parser("permit", help="Time-limited write access outside pocket")
    gperm.add_argument("--path", required=True)
    gperm.add_argument("--hours", type=float, default=1.0)
    gperm.add_argument("--mode", default="write", choices=("write", "write_delete", "read"))
    gperm.add_argument("--note", default="")
    grev = gr_sub.add_parser("permit-revoke")
    grev.add_argument("--path", default="")
    gall = gr_sub.add_parser("allowlist-add")
    gall.add_argument("--path", required=True)
    galr = gr_sub.add_parser("allowlist-remove")
    galr.add_argument("--path", required=True)
    gchk = gr_sub.add_parser("check-path")
    gchk.add_argument("--path", required=True)
    gchk.add_argument("--mode", default="write", choices=("read", "write", "delete", "exec"))

    # Operator viewport — look into the pocket
    vw = sub.add_parser("view", help="User viewport into Hermespace")
    vw.add_argument("--agent-id", default="default")
    vw.add_argument(
        "--format",
        choices=("markdown", "json", "html", "write"),
        default="markdown",
        help="markdown (default), json, html, or write files under HERMESPACE_HOME/viewport",
    )
    vw.add_argument("--open", action="store_true", help="Print path to HTML after write")
    vw.add_argument(
        "--serve",
        action="store_true",
        help="HTTP viewport server (default 127.0.0.1; use --tailscale for any tailnet client)",
    )
    vw.add_argument("--port", type=int, default=8764)
    vw.add_argument(
        "--host",
        default="127.0.0.1",
        help="Bind host: 127.0.0.1 (default), 0.0.0.0, or explicit Tailscale IP",
    )
    vw.add_argument(
        "--tailscale",
        action="store_true",
        help="Bind this machine's Tailscale IPv4 only (portable across users' tailnets)",
    )
    vw.add_argument(
        "--bind-all",
        action="store_true",
        help="Bind 0.0.0.0 (all interfaces). Requires --allow-remote. Prefer --tailscale.",
    )
    vw.add_argument(
        "--allow-remote",
        action="store_true",
        help="Permit non-loopback bind (needed for --bind-all; Tailscale CGNAT IP OK without it)",
    )
    vw.add_argument(
        "--pulse-every",
        type=int,
        default=60,
        help="In-process Pulse tick seconds while serving (0=off)",
    )
    vw.add_argument("--no-pulse", action="store_true", help="Disable in-process Pulse while serving")

    # World — persistent agent world
    wo = sub.add_parser("world", help="Persistent world model (world.md / world.json)")
    wo_sub = wo.add_subparsers(dest="world_cmd", required=True)
    wo_sub.add_parser("show", help="Render world.md")
    wo_sub.add_parser("inject", help="Render cluster context block")
    wo_sub.add_parser("evolve", help="Run evolution cycle")
    woe = wo_sub.add_parser("enter", help="Agent enters the world")
    wol = wo_sub.add_parser("leave", help="Agent leaves the world")
    wol.add_argument("--note", default="")
    wb = wo_sub.add_parser("add-belief", help="Add a belief")
    wb.add_argument("--statement", required=True)
    wb.add_argument("--confidence", type=float, default=0.5)
    wb.add_argument("--source", default="cli")
    wl = wo_sub.add_parser("add-landmark", help="Add a landmark event")
    wl.add_argument("--event", required=True)
    wt = wo_sub.add_parser("set-trait", help="Add an identity trait")
    wt.add_argument("--trait", required=True)
    wo_sub.add_parser("write-md", help="Write world.md file")

    # Archive querying
    ws = wo_sub.add_parser("search", help="Search timeline archive")
    ws.add_argument("term", help="Search term")
    ws.add_argument("--type", dest="search_type", default="", help="Filter by entry type")
    ws.add_argument("--limit", type=int, default=20)

    wtl = wo_sub.add_parser("timeline", help="List timeline entries")
    wtl.add_argument("--type", dest="tl_type", default="", help="Filter by entry type")
    wtl.add_argument("--limit", type=int, default=20)
    wtl.add_argument("--json", action="store_true", help="JSON output")

    wo_sub.add_parser("archive-stats", help="Archive entry type breakdown")

    # Causal chains
    wr = wo_sub.add_parser("resolve", help="Resolve outcome for an entry")
    wr.add_argument("--entry-id", required=True)
    wr.add_argument("--outcome", required=True, choices=("success", "failure", "pending", "superseded"))

    wt = wo_sub.add_parser("trace", help="Trace causal chain for an entry")
    wt.add_argument("--entry-id", required=True)

    wsg = wo_sub.add_parser("set-goal", help="Set current goal")
    wsg.add_argument("--goal", required=True)
    wsg.add_argument("--decision", default="")
    wsg.add_argument("--plan", action="append", default=[])

    ctrl = sub.add_parser("controls", help="Pocket toggles (autonomy, pulse jobs)")
    ctrl_sub = ctrl.add_subparsers(dest="controls_cmd", required=True)
    ctrl_sub.add_parser("show", help="Show flags + pulse jobs")
    ctset = ctrl_sub.add_parser("set", help="Set a flag")
    ctset.add_argument("flag", choices=("autonomy","pulse_runtime","auto_dream","auto_order"))
    ctset.add_argument("value", choices=("on","off","1","0","true","false"))
    ctj = ctrl_sub.add_parser("job", help="Enable/disable pulse job")
    ctj.add_argument("--id", required=True)
    ctj.add_argument("--on", action="store_true")
    ctj.add_argument("--off", action="store_true")

    # Everyday ops
    op = sub.add_parser("ops", help="Doctor / boot / tick-all for everyday use")
    op_sub = op.add_subparsers(dest="ops_cmd", required=True)
    opd = op_sub.add_parser("doctor", help="Health checks")
    opd.add_argument("--agent-id", default="default")
    opd.add_argument("--port", type=int, default=8764)
    opb = op_sub.add_parser("boot", help="Seed pulse, tick once, write viewport")
    opb.add_argument("--agent-id", default="default")
    opb.add_argument("--no-tick", action="store_true")
    opt = op_sub.add_parser("tick-all", help="Pulse tick + optional dream + viewport")
    opt.add_argument("--agent-id", default="default")
    opt.add_argument("--dream", action="store_true", help="Force a dream cycle")
    ops = op_sub.add_parser("status", help="Compact ops block (for agents)")
    ops.add_argument("--agent-id", default="default")


    # Access request / chat regulation CLI
    gar = gr_sub.add_parser("access-request")
    gar.add_argument("--path", required=True)
    gar.add_argument("--reason", default="")
    gar.add_argument("--hours", type=float, default=1.0)
    gar.add_argument("--agent-id", default="default")
    gap = gr_sub.add_parser("access-approve")
    gap.add_argument("--id", required=True)
    gap.add_argument("--hours", type=float, default=0)
    gdn = gr_sub.add_parser("access-deny")
    gdn.add_argument("--id", required=True)
    gpl = gr_sub.add_parser("access-pending")
    gpl.add_argument("--agent-id", default="default")
    gre = gr_sub.add_parser("regulate", help="Parse chat phrase for boundary regulation")
    gre.add_argument("--message", "-m", required=True)
    gre.add_argument("--agent-id", default="default")

    # Pulse — pocket runtime (smarter than bare cron)
    pu = sub.add_parser("pulse", help="Hermespace pulse runtime (desk-aware jobs)")
    pu_sub = pu.add_subparsers(dest="pulse_cmd", required=True)
    pu_sub.add_parser("status")
    pt = pu_sub.add_parser("tick", help="Run one evaluation cycle (cron-friendly)")
    pt.add_argument("--agent-id", default="")
    pt.add_argument("--force", action="store_true", help="Ignore due/conditions")
    pd = pu_sub.add_parser("daemon", help="Loop ticks in-process")
    pd.add_argument("--interval", type=int, default=60)
    pd.add_argument("--agent-id", default="")
    pd.add_argument("--max-ticks", type=int, default=0, help="0=forever")
    pu_sub.add_parser("list")
    pr = pu_sub.add_parser("run", help="Force-run one job by id")
    pr.add_argument("--id", required=True)
    pe = pu_sub.add_parser("enable")
    pe.add_argument("--id", required=True)
    px = pu_sub.add_parser("disable")
    px.add_argument("--id", required=True)
    pa = pu_sub.add_parser("add")
    pa.add_argument("--id", default="")
    pa.add_argument("--name", required=True)
    pa.add_argument("--action", required=True, choices=(
        "idle_tick", "dream", "viewport", "mission_pulse", "access_watch", "selftalk_hygiene", "world_evolve"
    ))
    pa.add_argument("--every-sec", type=int, default=900)
    pa.add_argument("--agent-id", default="default")
    pa.add_argument("--priority", type=int, default=50)
    pa.add_argument("--require-idle", action="store_true", default=True)
    pa.add_argument("--no-require-idle", action="store_true")
    pa.add_argument("--max-load", type=float, default=0.85)
    pu_sub.add_parser(
        "install-timer",
        help="Print/install user-crontab wake for hs pulse tick (script)",
    )

    args = p.parse_args(argv)
    eng = HermespaceEngine()
    mem = HermespaceMemory()
    wf = Workflow(eng, mem)

    if args.cmd == "turn":
        inp = HermespaceInput(
            message=args.message or args.goal or "",
            goal=args.goal or "",
            decision=args.decision or "",
            plan=args.plan or [],
            say=args.say or "",
            concepts=args.concept or [],
            choices=args.choice or [],
            session_id=args.session_id,
            agent_id=args.agent_id,
            force=args.force or bool(args.goal),
            seal=args.seal,
            seal_note=args.seal_note,
        )
        result = wf.run(inp)
        if args.json or args.output == "json":
            print(result.to_json())
        elif result.skipped:
            print(f"# skipped: {result.reason}")
        elif args.output == "report":
            print(result.report)
        elif args.output == "context":
            print(result.context)
        else:
            # both: context for model, then clear OUTPUT marker for user reply
            if result.context:
                print(result.context)
                print("\n--- HERMESPACE_OUTPUT ---\n")
            print(result.report)
            print(
                f"\n# {result.summary()} memory={result.memory_path}",
                file=sys.stderr,
            )
        return 0 if (result.skipped or result.ready or result.report or result.context) else 1

    if args.cmd == "input":
        if args.example or not args.file:
            ex = HermespaceInput(
                message="User asks to fix the login bug",
                goal="Fix login bug",
                decision="A — patch auth",
                plan=["reproduce", "patch", "test"],
                say="I'll patch auth and verify login.",
                session_id="sess-1",
                agent_id="hermes-agent",
            )
            print(ex.to_json())
            return 0
        data = json.loads(Path(args.file).read_text(encoding="utf-8"))
        inp = HermespaceInput.from_dict(data)
        print(inp.to_json())
        return 0

    if args.cmd == "output":
        if args.turn_id:
            row = mem.get(args.turn_id)
            rows = [row] if row else []
        else:
            rows = mem.history(session_id=args.session_id or None, limit=1)
        if not rows:
            print("{}", end="\n")
            return 1
        row = rows[0]
        if args.field == "report":
            print(row.get("report") or "")
        elif args.field == "context":
            print(row.get("context") or "")
        else:
            print(json.dumps(row, indent=2, default=str))
        return 0

    if args.cmd == "history":
        rows = mem.history(
            session_id=args.session_id or None,
            limit=args.limit,
            include_skipped=args.include_skipped,
        )
        print(json.dumps(rows, indent=2, default=str))
        return 0

    if args.cmd == "study":
        rows = mem.study(args.query, limit=args.limit)
        print(json.dumps(rows, indent=2, default=str))
        return 0

    if args.cmd == "memory-paths":
        print(json.dumps(mem.paths(), indent=2))
        return 0

    if args.cmd == "status":
        print(json.dumps(wf.status(), indent=2))
        return 0

    if args.cmd == "workflow":
        root = Path(__file__).resolve().parents[2]
        doc = root / "WORKFLOW.md"
        print(doc if doc.is_file() else "WORKFLOW.md")
        print("INPUT → GATE → ENCODE → DESK → PLAN → DECODE → OUTPUT(report+context) → ACT → SEAL")
        print("Memory: SQLite hermespace.db + journal/*.md under HERMESPACE_HOME")
        return 0

    if args.cmd == "enter":
        desk = eng.enter(
            goal=args.goal,
            concepts=args.concept,
            choices=args.choice,
            decision=args.decision,
            plan=args.plan,
            say=args.say,
            auto_load=not args.no_autoload,
            user_message=args.message or args.goal,
        )
        print(desk.to_markdown())
        print(f"\n# ready={desk.is_ready()} path={eng.desk_path}", file=sys.stderr)
        return 0

    if args.cmd == "show":
        print(eng.show())
        return 0

    if args.cmd == "say":
        print(eng.say())
        return 0

    if args.cmd == "inject":
        block = eng.inject()
        print(block)
        return 0 if block.strip() else 1

    if args.cmd == "ready":
        ok = eng.ready()
        print("ready" if ok else "not-ready")
        return 0 if ok else 1

    if args.cmd == "seal":
        print(eng.seal(args.note))
        return 0

    if args.cmd == "set":
        fields: dict = {}
        if args.goal is not None:
            fields["goal"] = args.goal
        if args.decision is not None:
            fields["decision"] = args.decision
        if args.say is not None:
            fields["say"] = args.say
        if args.concept is not None:
            fields["concepts"] = args.concept
        if args.plan is not None:
            fields["plan"] = args.plan
        desk = eng.update(user_message=args.message, **fields)
        print(desk.to_markdown())
        return 0

    if args.cmd == "json":
        desk = load_desk()
        print(
            json.dumps(
                {
                    "goal": desk.goal,
                    "concepts": desk.concepts,
                    "decision": desk.decision,
                    "plan": desk.plan,
                    "report": desk.say,
                    "ready": desk.is_ready(),
                    "load": desk.load,
                    "executive": desk.executive,
                    "streams": desk.meta.get("streams"),
                    "updated": desk.updated,
                },
                indent=2,
            )
        )
        return 0

    if args.cmd == "consolidate":
        from hermespace.semantic import consolidate

        print(json.dumps(consolidate(), indent=2))
        return 0

    if args.cmd == "patterns":
        from hermespace.patterns import as_markdown

        print(as_markdown())
        return 0

    if args.cmd == "fabric":
        from hermespace.hermes_fabric import snapshot_fabric
        snap = snapshot_fabric(goal=args.goal, message=args.message)
        print(json.dumps(snap.to_dict(), indent=2))
        print("\n" + snap.inject_markdown())
        return 0
    if args.cmd == "skills":
        from hermespace.agent_api import rank_skills
        print(json.dumps(rank_skills(args.goal, args.message, limit=args.limit), indent=2))
        return 0
    if args.cmd == "eval":
        harness = Path(__file__).resolve().parents[2] / "experiments" / "eval_harness.py"
        if not harness.is_file():
            from hermespace.paths import package_root

            harness = package_root() / "experiments" / "eval_harness.py"
        g = runpy.run_path(str(harness))
        return int(g.get("main", lambda: 1)())

    if args.cmd == "neural":
        from hermespace.neural_space import NeuralSpace
        from hermespace.store import load_desk, save_desk

        ns = NeuralSpace()
        if args.neural_cmd == "status":
            print(json.dumps(ns.status(), indent=2))
            return 0
        if args.neural_cmd == "pull":
            print(ns.field.attractor_pull(args.text))
            return 0
        if args.neural_cmd == "sync":
            desk = load_desk()
            snap = ns.sync_from_desk(desk, user_message=desk.goal)
            save_desk(desk)
            print(json.dumps(snap, indent=2))
            return 0
        if args.neural_cmd == "caps":
            from hermespace.local_model import local_capabilities
            print(json.dumps(local_capabilities(), indent=2))
            return 0
        if args.neural_cmd == "eval":
            import runpy
            from hermespace.paths import package_root
            harness = package_root() / "experiments" / "neural_rank_eval.py"
            g = runpy.run_path(str(harness))
            return int(g.get("main", lambda: 1)())
        return 2


    if args.cmd == "workbench":
        from hermespace.workbench import Workbench
        wb = Workbench(agent_id=getattr(args, "agent_id", "hermes-agent"), session_id=getattr(args, "session_id", "default"))
        if args.wb_cmd == "enter":
            print(json.dumps(wb.enter(), indent=2)); return 0
        if args.wb_cmd == "status":
            print(json.dumps(wb.status(), indent=2)); return 0
        if args.wb_cmd == "idle":
            print(json.dumps(wb.idle_tick(), indent=2)); return 0
        if args.wb_cmd == "park":
            print(json.dumps(wb.park_goal(args.goal, note=args.note), indent=2)); return 0
        if args.wb_cmd == "pop":
            print(json.dumps(wb.pop_park() or {}, indent=2)); return 0
        if args.wb_cmd == "env":
            env = wb.environment()
            if args.markdown:
                print(env.get("markdown") or "")
            else:
                print(json.dumps({k:v for k,v in env.items() if k!="markdown"}, indent=2, default=str))
            return 0
        if args.wb_cmd == "order":
            res = wb.receive_order(
                args.message,
                goal=args.goal,
                decision=args.decision,
                plan=args.plan,
                say=args.say,
                force=True,
            )
            if args.json:
                print(json.dumps(res, indent=2, default=str))
            else:
                print(res.get("user_reply") or "")
                print(f"# mode={res.get('workbench',{}).get('mode')} skipped={res.get('skipped')}", file=sys.stderr)
            return 0
        return 2

    if args.cmd == "grid":
        from hermespace.grid import Grid
        from hermespace.grid.lenses import list_lenses
        from hermespace.grid.gates import gate_status

        aid = getattr(args, "agent_id", None) or "default"
        g = Grid(aid)
        cmd = args.grid_cmd
        if cmd == "status":
            print(json.dumps(g.status(), indent=2, default=str))
            return 0
        if cmd == "context":
            print(g.context_block())
            return 0
        if cmd == "mission-add":
            m = g.add_mission(args.title, priority=args.priority)
            print(json.dumps(m.to_dict(), indent=2))
            return 0
        if cmd == "mission-list":
            print(json.dumps([m.to_dict() for m in g.list_missions()], indent=2))
            return 0
        if cmd == "mission-update":
            m = g.update_mission(
                args.id,
                status=args.status or None,
                note=args.note or None,
            )
            print(json.dumps(m.to_dict() if m else {}, indent=2))
            return 0 if m else 1
        if cmd == "lens-set":
            print(json.dumps(g.set_lens(args.name).to_dict(), indent=2))
            return 0
        if cmd == "lens-list":
            print(json.dumps(list_lenses(), indent=2))
            return 0
        if cmd == "dream":
            r = g.dream(force_material=bool(args.force))
            print(json.dumps(r.to_dict(), indent=2))
            return 0
        if cmd == "think":
            u = g.think(args.text, role=args.role)
            print(json.dumps(u.to_dict(), indent=2))
            return 0
        if cmd == "title-set":
            print(json.dumps(g.set_title(args.title), indent=2))
            return 0
        if cmd == "title-adopt":
            print(json.dumps(g.adopt_title(), indent=2))
            return 0
        if cmd == "tree-rebuild":
            print(json.dumps(g.rebuild_tree(), indent=2))
            return 0
        if cmd == "skill-register":
            body = Path(args.file).read_text(encoding="utf-8")
            print(json.dumps(g.register_skill(args.name, body).to_dict(), indent=2))
            return 0
        if cmd == "skill-merge":
            p = g.merge_skills(args.a, args.b, note=args.note)
            print(json.dumps(p.to_dict(), indent=2))
            return 0
        if cmd == "skill-mutate":
            p = g.mutate_skill(args.name, args.delta)
            print(json.dumps(p.to_dict(), indent=2))
            return 0
        if cmd == "skill-promote":
            print(json.dumps(g.promote(args.id, to_hermes=bool(args.to_hermes)), indent=2))
            return 0
        if cmd == "skill-list":
            from hermespace.grid import skillbench as sb

            print(json.dumps([m.to_dict() for m in sb.list_modules(aid)], indent=2))
            return 0
        if cmd == "scar-open":
            print(json.dumps(g.open_scar(args.kind, args.summary).to_dict(), indent=2))
            return 0
        if cmd == "gates":
            print(json.dumps(gate_status(), indent=2))
            return 0
        if cmd == "policy":
            from hermespace.grid.boundary import policy_markdown

            print(policy_markdown())
            return 0
        if cmd == "permit":
            from hermespace.grid.boundary import grant_permit

            print(
                json.dumps(
                    grant_permit(args.path, hours=args.hours, mode=args.mode, note=args.note),
                    indent=2,
                )
            )
            return 0
        if cmd == "permit-revoke":
            from hermespace.grid.boundary import revoke_permits

            n = revoke_permits(path=args.path or None)
            print(json.dumps({"revoked": n}))
            return 0
        if cmd == "allowlist-add":
            from hermespace.grid.boundary import add_allowlist

            print(json.dumps(add_allowlist(args.path), indent=2))
            return 0
        if cmd == "allowlist-remove":
            from hermespace.grid.boundary import remove_allowlist

            print(json.dumps(remove_allowlist(args.path), indent=2))
            return 0
        if cmd == "check-path":
            from hermespace.grid.boundary import check_path
            from dataclasses import asdict

            d = check_path(args.path, args.mode)
            print(json.dumps(asdict(d), indent=2))
            return 0 if d.allowed else 1
        if cmd == "access-request":
            from hermespace.grid import access as access_mod

            r = access_mod.request_access(
                args.path, agent_id=args.agent_id, hours=args.hours, reason=args.reason
            )
            print(json.dumps(r.to_dict(), indent=2))
            return 0
        if cmd == "access-approve":
            from hermespace.grid import access as access_mod

            hours = args.hours if args.hours and args.hours > 0 else None
            print(json.dumps(access_mod.approve_request(args.id, resolver="cli", hours=hours), indent=2))
            return 0
        if cmd == "access-deny":
            from hermespace.grid import access as access_mod

            print(json.dumps(access_mod.deny_request(args.id, resolver="cli"), indent=2))
            return 0
        if cmd == "access-pending":
            from hermespace.grid import access as access_mod

            print(
                json.dumps(
                    [r.to_dict() for r in access_mod.list_requests(agent_id=args.agent_id, status="pending")],
                    indent=2,
                )
            )
            return 0
        if cmd == "regulate":
            from hermespace.grid.converse import regulate
            from dataclasses import asdict

            r = regulate(args.message, agent_id=args.agent_id)
            print(json.dumps(asdict(r), indent=2, default=str))
            return 0 if r.handled else 1
        return 2

    if args.cmd == "view":
        from hermespace.grid.viewport import (
            render_html,
            render_markdown,
            snapshot,
            write_viewport_files,
        )

        aid = args.agent_id
        if args.serve:
            from hermespace.grid.view_server import serve

            pe = 0 if args.no_pulse else int(args.pulse_every)
            host = args.host
            if getattr(args, "tailscale", False):
                host = "tailscale"
            elif getattr(args, "bind_all", False):
                host = "0.0.0.0"
            serve(
                host=host,
                port=int(args.port),
                agent_id=aid,
                pulse_every_sec=pe if pe > 0 else None,
                open_network=bool(getattr(args, "allow_remote", False)),
            )
            return 0
        if args.format == "json":
            print(json.dumps(snapshot(aid), indent=2, default=str))
            return 0
        if args.format == "html":
            print(render_html(aid))
            return 0
        if args.format == "write":
            paths = write_viewport_files(aid)
            print(json.dumps(paths, indent=2))
            if args.open:
                print(paths.get("html"), file=sys.stderr)
            return 0
        print(render_markdown(aid))
        return 0

    if args.cmd == "pulse":
        from hermespace import pulse as pulse_mod

        cmd = args.pulse_cmd
        if cmd == "status":
            print(json.dumps(pulse_mod.status(), indent=2, default=str))
            return 0
        if cmd == "list":
            pulse_mod.ensure_defaults()
            print(json.dumps([j.to_dict() for j in pulse_mod.load_jobs()], indent=2))
            return 0
        if cmd == "tick":
            aid = args.agent_id or None
            print(json.dumps(pulse_mod.tick(agent_id=aid, force=bool(args.force)), indent=2, default=str))
            return 0
        if cmd == "daemon":
            aid = args.agent_id or None
            pulse_mod.daemon_loop(
                interval_sec=int(args.interval),
                agent_id=aid,
                max_ticks=int(args.max_ticks),
            )
            return 0
        if cmd == "run":
            j = pulse_mod.get_job(args.id)
            if not j:
                print(json.dumps({"ok": False, "error": "not_found"}))
                return 1
            print(json.dumps(pulse_mod.run_job(j, force=True), indent=2, default=str))
            return 0
        if cmd == "enable":
            j = pulse_mod.set_enabled(args.id, True)
            print(json.dumps(j.to_dict() if j else {"ok": False}, indent=2))
            return 0 if j else 1
        if cmd == "disable":
            j = pulse_mod.set_enabled(args.id, False)
            print(json.dumps(j.to_dict() if j else {"ok": False}, indent=2))
            return 0 if j else 1
        if cmd == "add":
            jid = args.id or args.name.lower().replace(" ", "_")[:24]
            job = pulse_mod.PulseJob(
                id=jid,
                name=args.name,
                action=args.action,
                every_sec=int(args.every_sec),
                agent_id=args.agent_id,
                priority=int(args.priority),
                require_idle=not bool(args.no_require_idle),
                max_load=float(args.max_load),
            )
            pulse_mod.upsert_job(job)
            print(json.dumps(job.to_dict(), indent=2))
            return 0
        if cmd == "install-timer":
            import subprocess

            script = Path(__file__).resolve().parents[2] / "scripts" / "install_pulse_timer.sh"
            if not script.is_file():
                print(json.dumps({"ok": False, "error": "install_pulse_timer.sh missing"}))
                return 1
            r = subprocess.run(["bash", str(script)], capture_output=True, text=True)
            print(r.stdout or r.stderr)
            return r.returncode
        return 2

    if args.cmd == "ops":
        from hermespace import ops as ops_mod

        cmd = args.ops_cmd
        if cmd == "doctor":
            d = ops_mod.doctor(agent_id=args.agent_id, port=int(args.port))
            print(json.dumps(d, indent=2, default=str))
            return 0 if d.get("ok") else 1
        if cmd == "boot":
            out = ops_mod.boot(agent_id=args.agent_id, tick=not args.no_tick)
            print(json.dumps(out, indent=2, default=str))
            return 0 if out.get("ok") else 1
        if cmd == "tick-all":
            out = ops_mod.tick_all(agent_id=args.agent_id, force_dream=bool(args.dream))
            print(json.dumps(out, indent=2, default=str))
            return 0
        if cmd == "status":
            print(ops_mod.compact_status(agent_id=args.agent_id))
            return 0
        return 2


    if args.cmd == "world":
        from hermespace.world import WorldModel

        wm = WorldModel(agent_id=getattr(args, "agent_id", "hermes-agent"))
        cmd = args.world_cmd
        if cmd == "show":
            print(wm.render_markdown())
            return 0
        if cmd == "inject":
            print(wm.context_block())
            return 0
        if cmd == "evolve":
            result = wm.evolve()
            print(wm.render_markdown())
            print(json.dumps(result, indent=2))
            return 0
        if cmd == "enter":
            from hermespace.store import load_desk
            wm.enter(desk=load_desk())
            print(wm.render_markdown())
            return 0
        if cmd == "leave":
            note = getattr(args, "note", "")
            wm.leave(note=note)
            print(wm.render_markdown())
            return 0
        if cmd == "add-belief":
            wm.add_belief(args.statement, confidence=args.confidence, source=args.source)
            print(json.dumps({"ok": True, "beliefs": len(wm.state.beliefs)}))
            return 0
        if cmd == "add-landmark":
            wm.add_landmark(args.event)
            print(json.dumps({"ok": True, "landmarks": len(wm.state.landmarks)}))
            return 0
        if cmd == "set-trait":
            wm.set_trait(args.trait)
            print(json.dumps({"ok": True, "traits": wm.state.identity_traits}))
            return 0
        if cmd == "write-md":
            p = wm.write_world_md()
            print(json.dumps({"path": str(p)}))
            return 0
        if cmd == "search":
            results = wm.archive.search(args.term, entry_type=args.search_type or None, limit=args.limit)
            print(json.dumps([asdict(e) for e in results], indent=2, default=str))
            return 0
        if cmd == "timeline":
            entries = wm.archive.query(entry_type=args.tl_type or None, limit=args.limit)
            if args.json:
                print(json.dumps([asdict(e) for e in entries], indent=2, default=str))
            else:
                for e in reversed(entries):
                    print(f"[{e.timestamp[:19]}] {e.entry_type}: {e.description[:120]}")
            return 0
        if cmd == "archive-stats":
            stats = wm.archive.count_by_type()
            total = sum(stats.values())
            print(json.dumps({"total": total, "by_type": stats}, indent=2))
            return 0
        if cmd == "resolve":
            ok = wm.resolve_outcome(args.entry_id, args.outcome)
            print(json.dumps({"ok": ok, "entry_id": args.entry_id, "outcome": args.outcome}))
            return 0 if ok else 1
        if cmd == "trace":
            chain = wm.trace_chain(args.entry_id)
            if not chain:
                print(json.dumps({"ok": False, "error": "entry not found"}))
                return 1
            print(json.dumps([asdict(e) for e in chain], indent=2, default=str))
            return 0
        if cmd == "set-goal":
            wm.set_goal(args.goal, decision=args.decision, plan=args.plan or None)
            print(wm.render_markdown())
            return 0
        return 2

    if args.cmd == "controls":
        from hermespace.grid.controls import apply_control_patch, controls_public, set_flag

        cmd = args.controls_cmd
        if cmd == "show":
            print(json.dumps(controls_public(), indent=2, default=str))
            return 0
        if cmd == "set":
            on = str(args.value).lower() in ("on", "1", "true", "yes")
            out = set_flag(args.flag, on, source="cli")
            print(json.dumps(out, indent=2, default=str))
            return 0
        if cmd == "job":
            if args.on == args.off:
                print(json.dumps({"ok": False, "error": "pass --on or --off"}))
                return 1
            out = apply_control_patch({"job_id": args.id, "enabled": bool(args.on)}, source="cli")
            print(json.dumps(out, indent=2, default=str))
            return 0 if out.get("ok") else 1
        return 2

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
