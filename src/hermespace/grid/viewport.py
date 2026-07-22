"""Operator viewport — look into the Hermespace pocket from the outside.

Read-only observation of desk + grid state. Does not execute agent actions.
"""

from __future__ import annotations

import html
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from hermespace.grid.boundary import load_policy, pocket_root, policy_markdown
from hermespace.grid.dream import last_dreams
from hermespace.grid.gates import gate_status
from hermespace.grid.lenses import get_active_lens
from hermespace.grid.missions import list_missions
from hermespace.grid.scars import list_scars
from hermespace.grid.secure_store import grid_root
from hermespace.grid.selftalk import recent as selftalk_recent
from hermespace.grid.skillbench import list_modules, list_proposals
from hermespace.grid.title_tree import get_profile
from hermespace.paths import desk_path, hermespace_home, state_dir
from hermespace.store import load_desk


def _utcnow() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def snapshot(agent_id: str = "default") -> dict[str, Any]:
    """Full read-only snapshot for viewport / API."""
    desk_md = ""
    desk_json: dict[str, Any] = {}
    try:
        dp = desk_path()
        if dp.is_file():
            desk_md = dp.read_text(encoding="utf-8")[:12000]
        desk = load_desk()
        desk_json = {
            "goal": desk.goal,
            "decision": desk.decision,
            "say": desk.say,
            "plan": list(desk.plan or []),
            "focus": list(desk.focus or [])[:8],
            "load": dict(desk.load or {}),
            "executive": desk.executive,
            "ready": desk.is_ready(),
        }
    except Exception as e:  # noqa: BLE001
        desk_json = {"error": type(e).__name__}

    lens = get_active_lens(agent_id)
    missions = [m.to_dict() for m in list_missions(agent_id)]
    scars = [s.to_dict() for s in list_scars(agent_id)]
    mods = [m.to_dict() for m in list_modules(agent_id)]
    props = [p.to_dict() for p in list_proposals(agent_id)]
    talk = selftalk_recent(agent_id, limit=15)
    dreams = last_dreams(agent_id, limit=5)
    profile = get_profile(agent_id)
    pol = load_policy()
    pending: list[dict[str, Any]] = []
    try:
        from hermespace.grid import access as access_mod

        pending = [
            r.to_dict() for r in access_mod.list_requests(agent_id=agent_id, status="pending")
        ]
    except Exception:  # noqa: BLE001
        pending = []

    out = {
        "generated_at": _utcnow(),
        "agent_id": agent_id,
        "pocket_root": str(pocket_root()),
        "state_dir": str(state_dir()),
        "grid_root": str(grid_root()),
        "desk": desk_json,
        "desk_markdown_head": desk_md[:4000],
        "lens": lens.to_dict(),
        "missions": missions,
        "scars": scars,
        "skill_modules": mods,
        "skill_proposals": props,
        "selftalk": talk,
        "dreams": dreams,
        "identity": profile,
        "gates": gate_status(),
        "boundary": pol.to_dict(),
        "access_pending": pending,
    }
    try:
        from hermespace.pulse import compact_summary

        out["pulse"] = compact_summary(agent_id)
    except Exception:
        pass
    try:
        from hermespace.grid.controls import controls_public

        out["controls"] = controls_public(agent_id=agent_id)
    except Exception:
        pass
    return out


def render_markdown(agent_id: str = "default", snap: dict[str, Any] | None = None) -> str:
    snap = snap if snap is not None else snapshot(agent_id)
    d = snap.get("desk") or {}
    lines = [
        f"# Hermespace viewport",
        f"_Generated {snap['generated_at']} · agent `{agent_id}`_",
        "",
        "## Pocket",
        f"- **Root:** `{snap['pocket_root']}`",
        f"- **Grid:** `{snap['grid_root']}`",
        f"- **Autonomy:** {'on' if (snap.get('gates') or {}).get('autonomy_enabled') else 'off'}",
        f"- **External writes:** `{(snap.get('boundary') or {}).get('project_write_default')}`",
        "",
        "## Desk",
        f"- **Goal:** {d.get('goal') or '_(empty)_'}",
        f"- **Decision:** {d.get('decision') or '—'}",
        f"- **Load:** {(d.get('load') or {}).get('level')} · **Exec:** {d.get('executive')}",
        f"- **Ready:** {d.get('ready')}",
        f"- **Report:** {d.get('say') or '—'}",
    ]
    if d.get("focus"):
        lines.append("### FOA")
        for f in d["focus"][:4]:
            lines.append(f"- {f}")
    if d.get("plan"):
        lines.append("### Plan")
        for i, step in enumerate(d["plan"][:6], 1):
            lines.append(f"{i}. {step}")

    lens = snap.get("lens") or {}
    lines += [
        "",
        "## Lens",
        f"- **{lens.get('title')}** (`{lens.get('name')}`)",
        f"- {lens.get('bias')}",
    ]

    lines += ["", "## Missions"]
    ms = snap.get("missions") or []
    if not ms:
        lines.append("_No missions._")
    for m in ms[:12]:
        lines.append(f"- **[{m.get('status')}]** {m.get('title')} `{m.get('id')}` p={m.get('priority')}")

    lines += ["", "## Scars"]
    sc = snap.get("scars") or []
    open_sc = [s for s in sc if s.get("status") == "open"]
    if not open_sc:
        lines.append("_No open scars._")
    for s in open_sc[-8:]:
        lines.append(f"- ({s.get('kind')}) {s.get('summary')}")

    lines += ["", "## Access requests (pending)"]
    pend = snap.get("access_pending") or []
    if not pend:
        lines.append("_None — agent stays in pocket._")
    for r in pend:
        lines.append(
            f"- `{r.get('id')}` → `{r.get('path')}` mode={r.get('mode')} {r.get('hours')}h — {r.get('reason')}"
        )
        lines.append(f"  - chat: `approve request {r.get('id')}` · `deny request {r.get('id')}`")

    lines += ["", "## Skillbench"]
    mods = snap.get("skill_modules") or []
    props = snap.get("skill_proposals") or []
    lines.append(f"- Modules: **{len(mods)}** · Proposals: **{len(props)}**")
    for m in mods[:10]:
        hot = "hot" if m.get("hot") else "cold"
        lines.append(f"- `{m.get('name')}` ({hot}, {m.get('source')})")
    draft_props = [p for p in props if p.get("status") == "draft"]
    for p in draft_props[-5:]:
        lines.append(f"- draft `{p.get('name')}` kind={p.get('kind')} id={p.get('id')}")

    ident = snap.get("identity") or {}
    lines += [
        "",
        "## Identity",
        f"- **Title:** {ident.get('title') or '_(unset)_'}",
        f"- Hot modules in tree: {ident.get('hot_count', '—')}",
    ]

    lines += ["", "## Self-talk (internal)"]
    talk = snap.get("selftalk") or []
    if not talk:
        lines.append("_Silent._")
    for t in talk[-10:]:
        lines.append(f"- **{t.get('role')}:** {t.get('text')}")

    lines += ["", "## Recent dreams"]
    for dr in (snap.get("dreams") or [])[-5:]:
        lines.append(
            f"- {dr.get('created')} material={dr.get('material')} — {dr.get('summary')}"
        )

    lines += ["", "## Pulse"]
    pu = snap.get("pulse") or {}
    if pu:
        lines.append(
            f"- Jobs: **{pu.get('jobs', '—')}** · due: **{pu.get('due', '—')}** · enabled: **{pu.get('enabled', '—')}**"
        )
        if pu.get("hint"):
            lines.append(f"- _{pu.get('hint')}_")
    else:
        lines.append("_No pulse summary._")

    lines += ["", "## Boundary (summary)"]
    lines.append("```")
    # compact policy head — avoid re-reading policy if already in snap
    bound = snap.get("boundary") or {}
    if bound.get("rules"):
        for rule in (bound.get("rules") or [])[:12]:
            lines.append(f"- {rule}")
    else:
        for line in policy_markdown().splitlines()[:16]:
            lines.append(line)
    lines.append("```")
    lines += [
        "",
        "---",
        "_Viewport observes the pocket. External writes need permit/approve. "
        "Serve with `hs view --serve` for live Approve/Deny._",
    ]
    return "\n".join(lines) + "\n"


def _h(s: Any) -> str:
    return html.escape("" if s is None else str(s))


def _kv(label: str, value: Any) -> str:
    return (
        f'<div class="kv"><span class="k">{_h(label)}</span>'
        f'<span class="v">{_h(value if value not in (None, "") else "—")}</span></div>'
    )


def render_html(agent_id: str = "default", snap: dict[str, Any] | None = None) -> str:
    """App-shell dashboard: sidebar nav + main workspace (dark ops UI)."""
    snap = snap if snap is not None else snapshot(agent_id)
    d = snap.get("desk") or {}
    lens = snap.get("lens") or {}
    bound = snap.get("boundary") or {}
    gates = snap.get("gates") or {}
    pu = snap.get("pulse") or {}
    pending = snap.get("access_pending") or []
    missions = snap.get("missions") or []
    scars = [s for s in (snap.get("scars") or []) if s.get("status") == "open"]
    mods = snap.get("skill_modules") or []
    props = [p for p in (snap.get("skill_proposals") or []) if p.get("status") == "draft"]
    talk = snap.get("selftalk") or []
    dreams = snap.get("dreams") or []
    load = d.get("load") or {}
    auto_on = bool(gates.get("autonomy_enabled"))
    writes = bound.get("project_write_default") or "deny"
    load_level = load.get("level") or "—"
    load_tot = load.get("total")
    load_s = f"{load_level}" + (f" · {load_tot}" if load_tot is not None else "")

    acc_parts: list[str] = []
    for r in pending:
        rid = _h(r.get("id"))
        acc_parts.append(
            f'<article class="card" data-id="{rid}">'
            f'<div class="card-top"><span class="mono">{rid}</span>'
            f'<span class="pill">{_h(r.get("mode"))} · {_h(r.get("hours"))}h</span></div>'
            f'<div class="path mono">{_h(r.get("path"))}</div>'
            f'<div class="muted">{_h(r.get("reason") or "no reason")}</div>'
            f'<div class="row">'
            f'<button type="button" class="btn" data-act="approve" data-id="{rid}">Approve</button>'
            f'<button type="button" class="btn ghost" data-act="deny" data-id="{rid}">Deny</button>'
            f"</div></article>"
        )
    access_html = (
        "\n".join(acc_parts)
        if acc_parts
        else '<div class="empty-state"><div class="empty-ico">◌</div><div>No pending access</div><div class="muted">Pocket sealed · agent stays inside</div></div>'
    )

    mis_parts: list[str] = []
    for m in missions[:16]:
        st = _h(m.get("status") or "?")
        mis_parts.append(
            f'<div class="list-row"><span class="pill">{st}</span>'
            f'<span class="grow">{_h(m.get("title"))}</span>'
            f'<span class="muted mono">p={_h(m.get("priority"))}</span></div>'
        )
    missions_html = (
        "\n".join(mis_parts)
        if mis_parts
        else '<div class="empty-state"><div>No missions</div></div>'
    )

    foa = "".join(f"<li>{_h(x)}</li>" for x in (d.get("focus") or [])[:5])
    plan = "".join(f"<li>{_h(x)}</li>" for x in (d.get("plan") or [])[:8])
    foa_html = f"<ul class='bullets'>{foa}</ul>" if foa else '<div class="muted">FOA empty</div>'
    plan_html = f"<ol class='bullets'>{plan}</ol>" if plan else '<div class="muted">No plan</div>'

    scars_html = (
        "".join(
            f'<div class="list-row"><span class="pill warn">{_h(s.get("kind"))}</span>'
            f'<span class="grow">{_h(s.get("summary"))}</span></div>'
            for s in scars[-10:]
        )
        or '<div class="muted">No open scars</div>'
    )
    mods_html = (
        "".join(
            f'<div class="list-row"><span class="pill">{"hot" if m.get("hot") else "cold"}</span>'
            f'<span class="mono grow">{_h(m.get("name"))}</span>'
            f'<span class="muted">{_h(m.get("source"))}</span></div>'
            for m in mods[:14]
        )
        or '<div class="muted">No modules</div>'
    )
    if props:
        mods_html += "".join(
            f'<div class="list-row"><span class="pill warn">draft</span>'
            f'<span class="mono grow">{_h(pr.get("name"))}</span></div>'
            for pr in props[-6:]
        )
    talk_html = (
        "".join(
            f'<div class="talk"><span class="role">{_h(t.get("role"))}</span>'
            f'<span>{_h(t.get("text"))}</span></div>'
            for t in talk[-10:]
        )
        or '<div class="muted">Silent</div>'
    )
    dream_html = (
        "".join(
            f'<div class="list-row"><span class="muted mono">{_h(dr.get("created"))}</span>'
            f'<span class="grow">{_h(dr.get("summary"))}</span></div>'
            for dr in dreams[-6:]
        )
        or '<div class="muted">No dreams yet</div>'
    )

    title = _h(f"Hermespace · {agent_id}")
    agent_js = json.dumps(agent_id)
    gen = _h(snap.get("generated_at", ""))
    pocket = _h(snap.get("pocket_root", ""))
    goal = _h(d.get("goal") or "—")
    decision = _h(d.get("decision") or "—")
    report = _h(d.get("say") or "—")
    lens_s = _h(lens.get("title") or lens.get("name") or "—")
    pend_n = len(pending)
    auto_label = "on" if auto_on else "off"

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>{title}</title>
<style>
:root {{
  color-scheme: dark;
  --bg: #05080d;
  --bg2: #0a1018;
  --panel: #0e1520;
  --panel2: #121b28;
  --line: #1a2636;
  --line2: #243247;
  --text: #e8eef6;
  --muted: #8b9bb0;
  --faint: #5c6b7c;
  --accent: #3d8bfd;
  --accent2: #6eb0ff;
  --good: #3dd68c;
  --warn: #f5a524;
  --bad: #f31260;
  --side-w: 248px;
  --top-h: 56px;
  --radius: 12px;
  --font: ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
  --mono: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
}}
* {{ box-sizing: border-box; }}
html, body {{ height: 100%; }}
body {{
  margin: 0;
  font-family: var(--font);
  color: var(--text);
  background: var(--bg);
  overflow: hidden;
}}
/* shell */
.app {{ display: grid; grid-template-columns: var(--side-w) 1fr; height: 100vh; }}
.sidebar {{
  background: linear-gradient(180deg, #0b1220 0%, #080d14 100%);
  border-right: 1px solid var(--line);
  display: flex; flex-direction: column;
  min-height: 0;
}}
.side-brand {{
  display: flex; align-items: center; gap: .7rem;
  padding: 1rem 1rem .85rem;
  border-bottom: 1px solid var(--line);
}}
.mark {{
  width: 32px; height: 32px; border-radius: 9px;
  background: linear-gradient(145deg, #1a6bff, #0a2a6b);
  display: grid; place-items: center; font-weight: 800; font-size: .85rem;
  box-shadow: 0 0 0 1px rgba(61,139,253,.35), 0 8px 20px rgba(0,0,0,.35);
}}
.brand-txt {{ display: flex; flex-direction: column; min-width: 0; }}
.brand-txt strong {{ font-size: .95rem; letter-spacing: .01em; }}
.brand-txt span {{ font-size: .68rem; color: var(--muted); }}
.side-nav {{
  padding: .75rem .55rem;
  display: flex; flex-direction: column; gap: .2rem;
  overflow: auto; flex: 1;
}}
.nav-label {{
  font-size: .62rem; font-weight: 700; letter-spacing: .1em; text-transform: uppercase;
  color: var(--faint); padding: .55rem .65rem .25rem;
}}
.nav-item {{
  display: flex; align-items: center; gap: .55rem;
  padding: .55rem .7rem; border-radius: 9px;
  color: var(--muted); text-decoration: none; font-size: .86rem; font-weight: 500;
  border: 1px solid transparent; cursor: pointer; background: transparent;
  width: 100%; text-align: left; font-family: inherit;
}}
.nav-item:hover {{ background: rgba(255,255,255,.03); color: var(--text); }}
.nav-item.active {{
  background: rgba(61,139,253,.12);
  color: var(--accent2);
  border-color: rgba(61,139,253,.25);
}}
.nav-item .ic {{ width: 1.1rem; text-align: center; opacity: .85; font-size: .9rem; }}
.nav-item .cnt {{
  margin-left: auto; font-size: .68rem; font-weight: 700;
  background: rgba(245,165,36,.15); color: var(--warn);
  border-radius: 999px; padding: .05rem .4rem; min-width: 1.2rem; text-align: center;
}}
.nav-item .cnt.zero {{ background: rgba(255,255,255,.04); color: var(--faint); }}
.side-foot {{
  border-top: 1px solid var(--line); padding: .75rem .9rem 1rem;
  display: flex; flex-direction: column; gap: .45rem;
}}
.chip-row {{ display: flex; flex-wrap: wrap; gap: .35rem; }}
.chip {{
  font-size: .68rem; font-weight: 600; padding: .2rem .5rem; border-radius: 999px;
  border: 1px solid var(--line2); background: var(--panel); color: var(--muted);
}}
.chip.live {{ color: var(--good); border-color: rgba(61,214,140,.35); }}
.chip.warn {{ color: var(--warn); border-color: rgba(245,165,36,.35); }}
.chip.bad {{ color: var(--bad); border-color: rgba(243,18,96,.35); }}
.main {{ display: flex; flex-direction: column; min-width: 0; min-height: 0; background:
  radial-gradient(900px 420px at 100% 0%, rgba(26,107,255,.08), transparent 55%),
  radial-gradient(700px 380px at 0% 100%, rgba(10,42,107,.12), transparent 50%),
  var(--bg2);
}}
.topbar {{
  height: var(--top-h); flex-shrink: 0;
  display: flex; align-items: center; justify-content: space-between; gap: 1rem;
  padding: 0 1.25rem; border-bottom: 1px solid var(--line);
  background: rgba(8,12,18,.72); backdrop-filter: blur(12px);
}}
.top-left {{ display: flex; align-items: baseline; gap: .75rem; min-width: 0; }}
.top-left h1 {{ margin: 0; font-size: 1.05rem; font-weight: 650; }}
.top-left .sub {{ color: var(--muted); font-size: .78rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 42vw; }}
.top-actions {{ display: flex; align-items: center; gap: .45rem; flex-shrink: 0; }}
.meta {{ color: var(--faint); font-size: .75rem; font-variant-numeric: tabular-nums; }}
.content {{ flex: 1; overflow: auto; padding: 1.1rem 1.25rem 2.5rem; }}
.view {{ display: none; animation: fade .18s ease; }}
.view.active {{ display: block; }}
@keyframes fade {{ from {{ opacity: 0; transform: translateY(4px); }} to {{ opacity: 1; transform: none; }} }}
.grid {{ display: grid; gap: .9rem; }}
.grid.cols-2 {{ grid-template-columns: 1fr; }}
.grid.cols-3 {{ grid-template-columns: repeat(3, 1fr); }}
@media (min-width: 960px) {{
  .grid.cols-2 {{ grid-template-columns: 1.15fr 1fr; }}
}}
@media (max-width: 820px) {{
  .app {{ grid-template-columns: 1fr; }}
  .sidebar {{ display: none; }}
  .grid.cols-3 {{ grid-template-columns: 1fr 1fr; }}
}}
.panel {{
  background: linear-gradient(180deg, var(--panel) 0%, var(--panel2) 100%);
  border: 1px solid var(--line);
  border-radius: var(--radius);
  padding: 1rem 1.05rem 1.05rem;
  box-shadow: 0 12px 32px rgba(0,0,0,.22);
}}
.panel h2 {{
  margin: 0 0 .85rem; font-size: .72rem; font-weight: 700;
  letter-spacing: .08em; text-transform: uppercase; color: var(--accent2);
  display: flex; align-items: center; justify-content: space-between; gap: .5rem;
}}
.panel h3 {{
  margin: 1rem 0 .45rem; font-size: .78rem; font-weight: 650; color: var(--muted);
}}
.kpi-row {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: .55rem; margin-bottom: .85rem; }}
.kpi {{
  border: 1px solid var(--line); border-radius: 10px; padding: .65rem .7rem;
  background: rgba(0,0,0,.2); text-align: center;
}}
.kpi .n {{ font-size: 1.2rem; font-weight: 750; font-variant-numeric: tabular-nums; line-height: 1.15; }}
.kpi .l {{ font-size: .65rem; color: var(--muted); text-transform: uppercase; letter-spacing: .06em; margin-top: .2rem; }}
.kpi.good .n {{ color: var(--good); }}
.kpi.warn .n {{ color: var(--warn); }}
.kv {{
  display: grid; grid-template-columns: 6.5rem 1fr; gap: .3rem .75rem;
  padding: .32rem 0; border-bottom: 1px solid rgba(26,38,54,.7); font-size: .88rem;
}}
.kv:last-child {{ border-bottom: 0; }}
.k {{ color: var(--muted); }}
.v {{ word-break: break-word; }}
.mono {{ font-family: var(--mono); font-size: .8rem; }}
.muted {{ color: var(--muted); font-size: .8rem; }}
.path {{ margin: .35rem 0; word-break: break-all; }}
.card {{
  border: 1px solid var(--line2); border-radius: 11px; padding: .8rem;
  background: rgba(0,0,0,.22); margin: .5rem 0;
}}
.card-top {{ display: flex; justify-content: space-between; gap: .5rem; align-items: center; }}
.row {{ display: flex; flex-wrap: wrap; gap: .45rem; align-items: center; margin-top: .65rem; }}
.btn, button.btn {{
  appearance: none; border: 0; border-radius: 8px;
  background: var(--accent); color: #fff; font: inherit; font-size: .78rem; font-weight: 600;
  padding: .42rem .8rem; cursor: pointer;
}}
.btn:hover {{ filter: brightness(1.08); }}
.btn.ghost {{ background: transparent; border: 1px solid var(--line2); color: var(--text); }}
.btn:disabled {{ opacity: .5; cursor: wait; }}
.pill {{
  display: inline-flex; align-items: center; padding: .12rem .45rem; border-radius: 999px;
  border: 1px solid var(--line2); background: #152033; color: var(--muted);
  font-size: .68rem; font-weight: 650; text-transform: lowercase;
}}
.pill.warn {{ color: var(--warn); border-color: rgba(245,165,36,.35); }}
.list-row {{
  display: flex; gap: .5rem; align-items: baseline; padding: .4rem 0;
  border-bottom: 1px solid rgba(26,38,54,.55); font-size: .86rem;
}}
.list-row:last-child {{ border-bottom: 0; }}
.grow {{ flex: 1; min-width: 0; word-break: break-word; }}
.bullets {{ margin: .15rem 0 .15rem 1.1rem; padding: 0; font-size: .88rem; }}
.bullets li {{ margin: .22rem 0; }}
.talk {{
  display: grid; grid-template-columns: 5rem 1fr; gap: .4rem;
  padding: .4rem 0; border-bottom: 1px solid rgba(26,38,54,.5); font-size: .85rem;
}}
.role {{ color: var(--accent2); font-weight: 700; font-size: .72rem; text-transform: uppercase; }}
.empty-state {{
  text-align: center; padding: 1.4rem .8rem; color: var(--muted); font-size: .88rem;
}}
.empty-ico {{ font-size: 1.4rem; opacity: .5; margin-bottom: .35rem; }}
#toast {{
  position: fixed; bottom: 1.1rem; right: 1.1rem; z-index: 50;
  min-width: 12rem; max-width: 22rem; padding: .65rem .85rem; border-radius: 10px;
  background: #102018; border: 1px solid rgba(61,214,140,.35); color: var(--good);
  font-size: .8rem; box-shadow: 0 12px 30px rgba(0,0,0,.4);
  opacity: 0; pointer-events: none; transition: opacity .2s;
}}
#toast.show {{ opacity: 1; }}
.toggle-row {{
  display: flex; align-items: center; justify-content: space-between; gap: .75rem;
  padding: .5rem 0; border-bottom: 1px solid rgba(26,38,54,.55); font-size: .88rem;
}}
.toggle-row:last-child {{ border-bottom: 0; }}
.toggle {{
  position: relative; width: 2.7rem; height: 1.45rem; border-radius: 999px;
  background: #243041; border: 1px solid var(--line2); cursor: pointer; flex-shrink: 0;
  transition: background .15s ease;
}}
.toggle.on {{ background: rgba(61,139,253,.55); border-color: var(--accent); }}
.toggle::after {{
  content: ""; position: absolute; top: 2px; left: 2px; width: 1.05rem; height: 1.05rem;
  border-radius: 999px; background: #e8eef7; transition: transform .15s ease;
}}
.toggle.on::after {{ transform: translateX(1.2rem); }}
.ctrl-note {{ color: var(--muted); font-size: .72rem; margin-top: .12rem; }}
.hero {{
  display: flex; flex-wrap: wrap; gap: .75rem 1.25rem; align-items: flex-start;
  justify-content: space-between; margin-bottom: .25rem;
}}
.hero-goal {{ font-size: 1.15rem; font-weight: 650; max-width: 46rem; line-height: 1.35; }}
.hero-meta {{ color: var(--muted); font-size: .85rem; margin-top: .35rem; }}
code {{ font-family: var(--mono); font-size: .78rem; color: #c5e0ff; }}
.mobile-nav {{
  display: none; gap: .35rem; overflow-x: auto; padding: .55rem .75rem;
  border-bottom: 1px solid var(--line); background: var(--bg);
}}
@media (max-width: 820px) {{
  .mobile-nav {{ display: flex; }}
  body {{ overflow: auto; }}
  .app {{ height: auto; min-height: 100vh; }}
  .main {{ min-height: 100vh; }}
}}
</style>
</head>
<body>
<div class="app">
  <aside class="sidebar">
    <div class="side-brand">
      <div class="mark">H</div>
      <div class="brand-txt">
        <strong>Hermespace</strong>
        <span>pocket viewport</span>
      </div>
    </div>
    <nav class="side-nav" id="side-nav">
      <div class="nav-label">Workspace</div>
      <button type="button" class="nav-item active" data-view="overview"><span class="ic">◈</span> Overview</button>
      <button type="button" class="nav-item" data-view="desk"><span class="ic">▣</span> Desk</button>
      <button type="button" class="nav-item" data-view="access"><span class="ic">⬡</span> Access
        <span class="cnt {'zero' if pend_n==0 else ''}" id="nav-access-cnt">{pend_n}</span></button>
      <button type="button" class="nav-item" data-view="pulse"><span class="ic">◉</span> Pulse</button>
      <div class="nav-label">Control</div>
      <button type="button" class="nav-item" data-view="controls"><span class="ic">☰</span> Controls</button>
      <button type="button" class="nav-item" data-view="missions"><span class="ic">◎</span> Missions
        <span class="cnt {'zero' if not missions else ''}" id="nav-mis-cnt">{len(missions)}</span></button>
      <div class="nav-label">Grid</div>
      <button type="button" class="nav-item" data-view="grid"><span class="ic">⬚</span> Grid intel</button>
    </nav>
    <div class="side-foot">
      <div class="chip-row">
        <span class="chip" id="live-badge">viewport</span>
        <span class="chip" id="auto-chip">{'autonomy ' + auto_label}</span>
        <span class="chip">writes {_h(writes)}</span>
      </div>
      <div class="muted mono" style="font-size:.68rem;word-break:break-all">{pocket}</div>
    </div>
  </aside>

  <div class="main">
    <div class="mobile-nav" id="mobile-nav"></div>
    <header class="topbar">
      <div class="top-left">
        <h1 id="view-title">Overview</h1>
        <span class="sub" id="view-sub">agent {_h(agent_id)}</span>
      </div>
      <div class="top-actions">
        <span class="meta" id="gen-ts">{gen}</span>
        <button type="button" class="btn ghost" id="btn-refresh">Refresh</button>
        <button type="button" class="btn" id="btn-tick">Run tick</button>
      </div>
    </header>

    <div class="content">
      <!-- OVERVIEW -->
      <section class="view active" id="view-overview">
        <div class="hero">
          <div>
            <div class="hero-goal">{goal}</div>
            <div class="hero-meta">Decision · {decision} · Lens · {lens_s}</div>
          </div>
        </div>
        <div class="grid cols-3" style="margin-top:1rem">
          <div class="kpi {'good' if auto_on else ''}"><div class="n" id="kpi-auto">{auto_label}</div><div class="l">autonomy</div></div>
          <div class="kpi"><div class="n">{_h(load_s)}</div><div class="l">load</div></div>
          <div class="kpi {'warn' if pend_n else ''}"><div class="n" id="kpi-access">{pend_n}</div><div class="l">access queue</div></div>
        </div>
        <div class="grid cols-2" style="margin-top:.9rem">
          <div class="panel">
            <h2>Report</h2>
            <div style="font-size:.95rem;line-height:1.45">{report}</div>
            <h3>FOA</h3>
            {foa_html}
          </div>
          <div class="panel">
            <h2>At a glance</h2>
            {_kv('missions', len(missions))}
            {_kv('scars open', len(scars))}
            {_kv('pulse jobs', pu.get('jobs', '—'))}
            {_kv('ext writes', writes)}
            {_kv('ready', d.get('ready'))}
            {_kv('executive', d.get('executive') or '—')}
          </div>
        </div>
      </section>

      <!-- DESK -->
      <section class="view" id="view-desk">
        <div class="grid cols-2">
          <div class="panel">
            <h2>Desk</h2>
            {_kv('goal', d.get('goal') or '—')}
            {_kv('decision', d.get('decision') or '—')}
            {_kv('executive', d.get('executive') or '—')}
            {_kv('ready', d.get('ready'))}
            {_kv('report', d.get('say') or '—')}
            {_kv('lens', lens.get('title') or lens.get('name') or '—')}
          </div>
          <div class="panel">
            <h2>Plan</h2>
            {plan_html}
            <h3>Focus of attention</h3>
            {foa_html}
          </div>
        </div>
      </section>

      <!-- ACCESS -->
      <section class="view" id="view-access">
        <div class="panel">
          <h2>Access requests <span class="pill" id="access-pill">{pend_n}</span></h2>
          <p class="muted">Agent cannot leave the pocket without OK. Chat: <code>approve request &lt;id&gt;</code> · <code>allow ~/path for 2h</code></p>
          <div id="requests">{access_html}</div>
        </div>
      </section>

      <!-- PULSE -->
      <section class="view" id="view-pulse">
        <div class="panel">
          <h2>Pulse runtime</h2>
          <div class="kpi-row">
            <div class="kpi"><div class="n" id="pulse-jobs">{_h(pu.get("jobs", "—"))}</div><div class="l">jobs</div></div>
            <div class="kpi"><div class="n" id="pulse-due">{_h(pu.get("due", "—"))}</div><div class="l">due</div></div>
            <div class="kpi"><div class="n" id="pulse-en">{_h(pu.get("enabled", "—"))}</div><div class="l">enabled</div></div>
          </div>
          <div id="pulse-list" class="list"></div>
          <div class="row">
            <button type="button" class="btn" id="btn-tick-2">Run pulse tick</button>
            <span class="muted" id="pulse-hint">{_h(pu.get("hint") or "")}</span>
          </div>
        </div>
      </section>

      <!-- CONTROLS -->
      <section class="view" id="view-controls">
        <div class="panel" id="controls-panel">
          <h2>Agent controls</h2>
          <p class="muted">Turn Hermespace features on/off for this pocket. Requires live serve.</p>
          <div class="toggle-row">
            <div><div><strong>Autonomy</strong></div><div class="ctrl-note">Budgeted self-orders inside the pocket</div></div>
            <button type="button" class="toggle" id="ctrl-autonomy" data-flag="autonomy" aria-label="Autonomy"></button>
          </div>
          <div class="toggle-row">
            <div><div><strong>Pulse runtime</strong></div><div class="ctrl-note">Master switch for unattended ticks</div></div>
            <button type="button" class="toggle" id="ctrl-pulse_runtime" data-flag="pulse_runtime" aria-label="Pulse runtime"></button>
          </div>
          <div class="toggle-row">
            <div><div><strong>Auto dream</strong></div><div class="ctrl-note">Dream job when pulse runs</div></div>
            <button type="button" class="toggle" id="ctrl-auto_dream" data-flag="auto_dream" aria-label="Auto dream"></button>
          </div>
          <div class="toggle-row">
            <div><div><strong>Auto order</strong></div><div class="ctrl-note">Plugin may auto-receive_order</div></div>
            <button type="button" class="toggle" id="ctrl-auto_order" data-flag="auto_order" aria-label="Auto order"></button>
          </div>
          <h3>Pulse jobs</h3>
          <div id="ctrl-jobs"><div class="muted">Load via serve…</div></div>
          <div class="muted" id="ctrl-status" style="margin-top:.75rem">—</div>
        </div>
      </section>

      <!-- MISSIONS -->
      <section class="view" id="view-missions">
        <div class="panel">
          <h2>Missions <span class="pill">{len(missions)}</span></h2>
          {missions_html}
        </div>
      </section>

      <!-- GRID -->
      <section class="view" id="view-grid">
        <div class="grid cols-2">
          <div class="panel"><h2>Scars</h2>{scars_html}</div>
          <div class="panel"><h2>Skillbench</h2>{mods_html}</div>
          <div class="panel"><h2>Self-talk</h2>{talk_html}</div>
          <div class="panel"><h2>Dreams</h2>{dream_html}</div>
        </div>
      </section>
    </div>
  </div>
</div>
<div id="toast"></div>
<script>
const AGENT = {agent_js};
const $ = (id) => document.getElementById(id);
const served = location.protocol.startsWith('http');
const TITLES = {{
  overview: ['Overview', 'desk + status'],
  desk: ['Desk', 'goal · FOA · plan'],
  access: ['Access', 'approve pocket exits'],
  pulse: ['Pulse', 'runtime jobs'],
  controls: ['Controls', 'autonomy · switches'],
  missions: ['Missions', 'active work'],
  grid: ['Grid intel', 'scars · skills · dreams']
}};

function toast(t) {{
  const el = $('toast');
  if (!el) return;
  el.textContent = t;
  el.classList.add('show');
  clearTimeout(window.__tt);
  window.__tt = setTimeout(() => el.classList.remove('show'), 2800);
}}

function showView(name) {{
  document.querySelectorAll('.view').forEach(v => v.classList.toggle('active', v.id === 'view-' + name));
  document.querySelectorAll('.nav-item').forEach(b => b.classList.toggle('active', b.getAttribute('data-view') === name));
  const t = TITLES[name] || [name, ''];
  const ht = $('view-title'); if (ht) ht.textContent = t[0];
  const hs = $('view-sub'); if (hs) hs.textContent = t[1] + ' · agent ' + AGENT;
  try {{ history.replaceState(null, '', '#' + name); }} catch (e) {{}}
}}

async function act(kind, id) {{
  if (!served) {{ toast('Open via hs view --serve'); return; }}
  try {{
    const res = await fetch('/api/' + kind, {{
      method: 'POST', headers: {{'Content-Type':'application/json'}},
      body: JSON.stringify({{id, agent_id: AGENT}})
    }});
    const data = await res.json();
    toast(data.ok ? (kind + ' · ' + id) : ('fail: ' + (data.reason || res.status)));
    if (data.ok) setTimeout(() => location.reload(), 450);
  }} catch (e) {{ toast('API unreachable'); }}
}}

async function pulseTick() {{
  if (!served) {{ toast('Serve required for pulse tick'); return; }}
  ['btn-tick','btn-tick-2'].forEach(id => {{ const b=$(id); if (b) b.disabled = true; }});
  try {{
    const res = await fetch('/api/pulse/tick', {{
      method: 'POST', headers: {{'Content-Type':'application/json'}}, body: '{{}}'
    }});
    const data = await res.json();
    toast(data.ok ? ('tick ran=' + data.ran + ' skip=' + data.skipped) : 'tick failed');
    await hydratePulse();
    await hydrateControls();
  }} catch (e) {{ toast('pulse API missing'); }}
  finally {{
    ['btn-tick','btn-tick-2'].forEach(id => {{ const b=$(id); if (b) b.disabled = false; }});
  }}
}}

async function hydratePulse() {{
  if (!served) return;
  try {{
    const res = await fetch('/api/pulse?agent=' + encodeURIComponent(AGENT));
    if (!res.ok) return;
    const data = await res.json();
    const jobs = data.jobs || [];
    const due = jobs.filter(j => j.due && j.conditions_ok).length;
    const en = jobs.filter(j => j.enabled).length;
    const jEl = $('pulse-jobs'); if (jEl) jEl.textContent = String(jobs.length);
    const dEl = $('pulse-due'); if (dEl) dEl.textContent = String(due);
    const eEl = $('pulse-en'); if (eEl) eEl.textContent = String(en);
    const list = $('pulse-list');
    if (list) {{
      list.innerHTML = jobs.slice(0, 16).map(j => {{
        const label = !j.enabled ? 'off' : (j.due && j.conditions_ok ? 'due' : (j.due_reason || 'ok'));
        const cls = (j.due && j.conditions_ok) ? 'pill warn' : 'pill';
        return '<div class="list-row"><span class="' + cls + '">' + label +
          '</span><span class="grow">' + (j.name || j.id) +
          '</span><span class="muted mono">' + (j.action || '') + '</span></div>';
      }}).join('') || '<div class="muted">No jobs</div>';
    }}
    const badge = $('live-badge');
    if (badge) {{ badge.textContent = 'live'; badge.classList.add('live'); }}
  }} catch (e) {{}}
}}

async function setFlag(flag, enabled) {{
  if (!served) {{ toast('Serve required for controls'); return; }}
  const res = await fetch('/api/controls', {{
    method: 'POST', headers: {{'Content-Type':'application/json'}},
    body: JSON.stringify({{ agent_id: AGENT, flags: {{ [flag]: enabled }} }})
  }});
  const data = await res.json();
  toast(data.ok ? (flag + ' → ' + (enabled ? 'on' : 'off')) : 'control failed');
  await hydrateControls();
  if (flag === 'autonomy') {{
    const n = $('kpi-auto'); if (n) n.textContent = enabled ? 'on' : 'off';
    const c = $('auto-chip'); if (c) c.textContent = 'autonomy ' + (enabled ? 'on' : 'off');
  }}
}}

async function setJob(id, enabled) {{
  if (!served) {{ toast('Serve required'); return; }}
  const res = await fetch('/api/controls', {{
    method: 'POST', headers: {{'Content-Type':'application/json'}},
    body: JSON.stringify({{ agent_id: AGENT, job_id: id, enabled }})
  }});
  const data = await res.json();
  toast(data.ok ? ('job ' + id + ' → ' + (enabled ? 'on' : 'off')) : 'job failed');
  await hydrateControls();
  await hydratePulse();
}}

async function hydrateControls() {{
  if (!served) return;
  try {{
    const res = await fetch('/api/controls?agent=' + encodeURIComponent(AGENT));
    if (!res.ok) return;
    const data = await res.json();
    const flags = data.flags || {{}};
    ['autonomy','pulse_runtime','auto_dream','auto_order'].forEach(f => {{
      const el = $('ctrl-' + f);
      if (!el) return;
      const on = !!flags[f];
      el.classList.toggle('on', on);
      el.setAttribute('aria-pressed', on ? 'true' : 'false');
    }});
    const st = $('ctrl-status');
    if (st) st.textContent = 'autonomy effective: ' + (data.autonomy_effective ? 'on' : 'off')
      + (flags.updated ? ' · saved ' + flags.updated : '');
    const jobs = data.pulse_jobs || [];
    const box = $('ctrl-jobs');
    if (box) {{
      box.innerHTML = jobs.map(j => {{
        const on = !!j.enabled;
        return '<div class="toggle-row"><div><div><strong>' + (j.name||j.id) + '</strong></div>'
          + '<div class="ctrl-note mono">' + (j.action||'') + ' · every ' + (j.every_sec||'?') + 's</div></div>'
          + '<button type="button" class="toggle' + (on?' on':'') + '" data-job="' + j.id + '"></button></div>';
      }}).join('') || '<div class="muted">No pulse jobs</div>';
      box.querySelectorAll('[data-job]').forEach(btn => {{
        btn.addEventListener('click', () => {{
          const id = btn.getAttribute('data-job');
          setJob(id, !btn.classList.contains('on'));
        }});
      }});
    }}
  }} catch (e) {{}}
}}

// nav
document.querySelectorAll('#side-nav [data-view]').forEach(btn => {{
  btn.addEventListener('click', () => showView(btn.getAttribute('data-view')));
}});
// mobile clone
const mob = $('mobile-nav');
if (mob) {{
  document.querySelectorAll('#side-nav [data-view]').forEach(btn => {{
    const b = btn.cloneNode(true);
    b.addEventListener('click', () => showView(b.getAttribute('data-view')));
    mob.appendChild(b);
  }});
}}

document.getElementById('requests')?.addEventListener('click', (ev) => {{
  const t = ev.target;
  if (!(t instanceof HTMLElement)) return;
  const kind = t.getAttribute('data-act');
  const id = t.getAttribute('data-id');
  if (kind && id) act(kind, id);
}});
$('btn-tick')?.addEventListener('click', () => pulseTick());
$('btn-tick-2')?.addEventListener('click', () => pulseTick());
$('btn-refresh')?.addEventListener('click', () => location.reload());
document.querySelectorAll('#controls-panel [data-flag]').forEach(btn => {{
  btn.addEventListener('click', () => {{
    const flag = btn.getAttribute('data-flag');
    setFlag(flag, !btn.classList.contains('on'));
  }});
}});

const hash = (location.hash || '#overview').slice(1);
if (TITLES[hash]) showView(hash);

if (served) {{
  hydratePulse();
  hydrateControls();
  setInterval(() => {{ hydratePulse(); hydrateControls(); }}, 10000);
}} else {{
  const badge = $('live-badge');
  if (badge) {{ badge.textContent = 'static'; badge.classList.add('warn'); }}
  const st = $('ctrl-status');
  if (st) st.textContent = 'static snapshot — start hs view --serve for toggles';
}}
</script>
</body>
</html>
"""



def write_viewport_files(agent_id: str = "default") -> dict[str, str]:
    """Write snapshot artifacts under pocket for the user to open."""
    out_dir = hermespace_home() / "viewport"
    out_dir.mkdir(parents=True, exist_ok=True)
    snap = snapshot(agent_id)
    md_path = out_dir / "VIEW.md"
    html_path = out_dir / "index.html"
    json_path = out_dir / "snapshot.json"
    # Single snapshot — avoid triple re-scan of grid state
    md_path.write_text(render_markdown(agent_id, snap=snap), encoding="utf-8")
    html_path.write_text(render_html(agent_id, snap=snap), encoding="utf-8")
    json_path.write_text(json.dumps(snap, indent=2, default=str) + "\n", encoding="utf-8")
    return {
        "markdown": str(md_path),
        "html": str(html_path),
        "json": str(json_path),
        "dir": str(out_dir),
    }
