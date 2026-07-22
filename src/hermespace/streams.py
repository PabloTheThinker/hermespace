"""Meta Brain & AI research → reverse-mapped Hermespace streams.

Sources (public research, not implants):
- Meta FAIR Brain & AI (Jean-Rémi King et al.)
- Brain2Qwerty / brain-to-text (MEG/EEG → characters/words/semantics)
- TRIBE v2 encoding model: predict fMRI from video + audio + text features
  (V-JEPA-class visual, Wav2Vec-BERT audio, LLaMA-class language)
- Hierarchy of language production: thought → lexical → motor/report
- Semantic decoders (e.g. UT Austin continuous language from fMRI)

REVERSE (what we can do without scanners):
  Encoding path  = stimulus features → workspace slots (TRIBE direction)
  Decoding path  = workspace → verbal report / say (Brain2Qwerty direction)
  Multimodal     = separate streams with cross-bind (not one bag of tokens)
  Hierarchy      = goal (intention) → concepts (semantics) → say (production)

Honesty: no MEG/EEG/fMRI on this host. Functional roles only.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from hermespace.cognition import Modality, Slot


@dataclass
class StreamBundle:
    """TRIBE-style multi-stream feature bag (text/audio/visual proxies)."""

    text: list[Slot] = field(default_factory=list)  # language stream
    audio: list[Slot] = field(default_factory=list)  # speech/prosody proxies
    visual: list[Slot] = field(default_factory=list)  # image/layout/path proxies
    production: list[Slot] = field(default_factory=list)  # output-bound (say path)

    def all_slots(self) -> list[Slot]:
        return self.text + self.audio + self.visual + self.production


_URL_RE = re.compile(r"https?://\S+|www\.\S+", re.I)
_PATH_RE = re.compile(r"(?:/[\w.-]+){2,}|(?:~/)[\w./-]+")
_IMAGE_RE = re.compile(r"\b(image|screenshot|png|jpg|jpeg|photo|visual|diagram)\b", re.I)
_AUDIO_RE = re.compile(
    r"\b(voice|audio|ogg|speak|speech|say out loud|tts|listen|sound)\b", re.I
)
_LANG_RE = re.compile(
    r"\b(language|semantic|meaning|word|sentence|decode|encode|brain|fmri|meg|eeg)\b",
    re.I,
)


def encode_stimulus(user_message: str, *, goal_hint: str = "") -> StreamBundle:
    """TRIBE reverse: message → multi-stream slots (encoding into workspace)."""
    msg = (user_message or "").strip()
    bundle = StreamBundle()
    if not msg:
        return bundle

    # Language / text stream (LLaMA-class features → language areas analogue)
    # Keep a compressed semantic gist, not full dump
    gist = " ".join(msg.split()[:40])
    sal = 0.7 if _LANG_RE.search(msg) else 0.55
    bundle.text.append(Slot(f"lang_stream: {gist[:160]}", Modality.VERBAL, sal))

    # Audio stream proxies (Wav2Vec-class) — presence of speech media cues
    if _AUDIO_RE.search(msg) or "voice.ogg" in msg.lower() or ".ogg" in msg.lower():
        bundle.audio.append(
            Slot("audio_stream: speech/voice channel active", Modality.VERBAL, 0.75)
        )

    # Visual stream proxies (V-JEPA-class)
    if _IMAGE_RE.search(msg) or _URL_RE.search(msg):
        bundle.visual.append(
            Slot("visual_stream: image/url stimulus present", Modality.STRUCT, 0.72)
        )
    for m in _PATH_RE.findall(msg)[:3]:
        bundle.visual.append(Slot(f"visual_stream: path {m[:80]}", Modality.STRUCT, 0.6))

    # Production hierarchy cue (thought→action): if user asks to communicate/output
    if re.search(r"\b(say|tell|reply|answer|report|write)\b", msg, re.I):
        bundle.production.append(
            Slot("production: prepare verbal report (decode path)", Modality.EXEC, 0.8)
        )

    if goal_hint:
        bundle.text.append(Slot(f"intention: {goal_hint[:100]}", Modality.VERBAL, 0.65))

    return bundle


def decode_to_report(
    *,
    goal: str,
    decision: str,
    focus_texts: list[str],
    load_level: str,
) -> str:
    """Brain2Qwerty reverse: workspace → compressed verbal report draft.

    Does not replace agent speech; supplies a candidate Say under hierarchy:
    intention → selected semantics (focus) → surface form.
    """
    bits: list[str] = []
    if goal:
        bits.append(goal.strip()[:120])
    if decision:
        bits.append(f"→ {decision.strip()[:80]}")
    if focus_texts:
        top = "; ".join(t[:40] for t in focus_texts[:2])
        bits.append(f"[{top}]")
    draft = " ".join(bits).strip()
    if load_level == "high" and len(draft) > 160:
        draft = draft[:157] + "..."
    return draft


def production_stages(goal: str, concepts: list[str], say: str) -> dict[str, str]:
    """Language-production hierarchy (Meta 'thought to action' spirit)."""
    return {
        "intention": (goal or "")[:200],
        "semantics": " | ".join(concepts[:5])[:240],
        "report": (say or "")[:200],
    }


def merge_streams_into_concepts(
    existing: list[str],
    bundle: StreamBundle,
    *,
    max_add: int = 6,
) -> list[str]:
    """Fold stream slots into desk concepts without unbounded growth."""
    out = list(existing)
    bodies = {Slot_text_body(c) for c in out}
    added = 0
    for slot in bundle.all_slots():
        if added >= max_add:
            break
        body = slot.text
        if body in bodies:
            continue
        out.append(slot.label())
        bodies.add(body)
        added += 1
    return out


def Slot_text_body(raw: str) -> str:
    from hermespace.cognition import parse_slot

    return parse_slot(raw).text
