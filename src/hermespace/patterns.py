"""Pattern registry — confirmed components vs research sources."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Pattern:
    component: str
    source: str
    property: str
    hermespace_impl: str
    confirmed: bool
    evidence: str


PATTERNS: list[Pattern] = [
    Pattern(
        "desk.capacity",
        "Cowan FOA ~4; Baddeley activated WM; Miller 7±2",
        "Limited workspace capacity",
        "FOCUS_CAP=4 + ACTIVATED_CAP=12",
        True,
        "cognition.py + desk.clamp",
    ),
    Pattern(
        "wm.phonological",
        "Baddeley phonological loop",
        "Verbal/acoustic working store",
        "Modality.VERBAL buffer + soft cap 6",
        True,
        "partition_buffers verbal",
    ),
    Pattern(
        "wm.visuospatial",
        "Baddeley visuospatial sketchpad",
        "Structural/spatial schematic store",
        "Modality.STRUCT for paths/architecture",
        True,
        "parse_slot heuristics + STRUCT",
    ),
    Pattern(
        "wm.episodic_buffer",
        "Baddeley 2000 episodic buffer",
        "Bind multimodal chunks",
        "bind_episode → [bind] concept",
        True,
        "cognition.bind_episode",
    ),
    Pattern(
        "wm.central_executive",
        "Baddeley central executive",
        "Control: update/select/protect (inhibit, shift)",
        "executive_mode + do_not_say inhibit",
        True,
        "executive protect under high load",
    ),
    Pattern(
        "gwt.competition",
        "Baars/Dehaene GWT ignition/competition",
        "Salience competition for broadcast",
        "compete_for_focus by salience",
        True,
        "cognition.compete_for_focus",
    ),
    Pattern(
        "gwt.broadcast",
        "GWT global broadcast + Conductor inject",
        "Winning contents available to speech/control",
        "build_inject_block focus-first",
        True,
        "inject.py + hermes plugin",
    ),
    Pattern(
        "load.sweller",
        "Sweller cognitive load theory",
        "Intrinsic / extraneous / germane",
        "classify_message_load",
        True,
        "cognition.classify_message_load",
    ),
    Pattern(
        "load.protect",
        "Monotropism + high load / EF tax (ops layer)",
        "Under high load shrink options and menus",
        "executive=protect + inject compression",
        True,
        "inject high-load path",
    ),
    Pattern(
        "desk.verbalizable",
        "Anthropic J-space reportability",
        "Contents poised for report/speech",
        "required say field; cli say",
        True,
        "is_ready requires say",
    ),
    Pattern(
        "desk.modulable",
        "J-space modulation + attention set",
        "Task shifts workspace contents",
        "enter CLEAR + recompute_cognition(user_message)",
        True,
        "engine.enter + plugin",
    ),
    Pattern(
        "desk.pre_output",
        "J-space silent deliberation",
        "Workspace before user-visible speech",
        "save_desk + pre_llm inject",
        True,
        "plugin pre_llm_call",
    ),
    Pattern(
        "gate.selectivity",
        "J-space selective mediation",
        "Not all cognition uses workspace",
        "gate.should_inject",
        True,
        "gate.py tests",
    ),
    Pattern(
        "episodic.ring",
        "Conductor EpisodicStore",
        "Capped event log",
        "EpisodicLog max 500",
        True,
        "episodic.py",
    ),
    Pattern(
        "semantic.consolidate",
        "Conductor consolidate + semantic memory",
        "Episodes → durable notes",
        "semantic.consolidate()",
        True,
        "semantic.py",
    ),
    Pattern(
        "meta.tribe_encode",
        "Meta TRIBE v2 multi-stream encoding",
        "Stimulus streams → neural prediction (reversed: → desk slots)",
        "streams.encode_stimulus text/audio/visual/production",
        True,
        "streams.py + desk.recompute",
    ),
    Pattern(
        "meta.b2q_decode",
        "Meta Brain2Qwerty brain→text decode",
        "Internal state → linguistic report",
        "streams.decode_to_report → Say draft",
        True,
        "engine.enter decode path",
    ),
    Pattern(
        "meta.production_hierarchy",
        "Meta thought-to-action language production",
        "Intention → semantics → report",
        "production_stages in desk.meta",
        True,
        "streams.production_stages",
    ),
    Pattern(
        "neural.field",
        "GWT ignition + continuous attractor field",
        "Vector competition for FOA / broadcast",
        "NeuralField + NeuralSpace.sync_from_desk",
        True,
        "neural_field.py / neural_space.py",
    ),
    Pattern(
        "neural.dual_workspace",
        "Symbolic desk + continuous field",
        "Two-layer workspace (discrete + geometric)",
        "desk.meta['neural'] + ACTIVE concepts",
        True,
        "workflow 5b neural sync",
    ),
    Pattern(
        "local.ollama_embed",
        "Local embedding model (nomic-embed-text)",
        "Real vectors for FOA competition",
        "OllamaEmbedBackend via /api/embeddings",
        True,
        "local_model.py",
    ),
    Pattern(
        "local.verbalizer",
        "Local chat model reportable concepts",
        "Behavioral verbalizable workspace",
        "verbalize_workspace → desk concepts",
        True,
        "local_model.verbalize_workspace",
    ),
    Pattern(
        "neural.jlens",
        "Anthropic Jacobian lens",
        "Read true activation workspace",
        "NOT implemented (honest gap)",
        False,
        "docs — future open-weight only",
    ),
]


def as_markdown() -> str:
    lines = [
        "# Pattern confirmation matrix",
        "",
        "| Component | Source | Property | Impl | OK |",
        "|-----------|--------|----------|------|----|",
    ]
    for p in PATTERNS:
        ok = "yes" if p.confirmed else "gap"
        lines.append(
            f"| `{p.component}` | {p.source} | {p.property} | `{p.hermespace_impl}` | {ok} |"
        )
    lines.append("")
    lines.append(f"Confirmed: {sum(1 for p in PATTERNS if p.confirmed)} / {len(PATTERNS)}")
    return "\n".join(lines)
