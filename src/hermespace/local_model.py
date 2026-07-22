"""Local model backends for Hermespace Neural Space.

Priority (auto):
1. ollama_embed  — nomic-embed-text (or HERMESPACE_EMBED_MODEL)
2. ollama_verbal — small chat model proposes reportable concepts (J-space *role*)
3. hash          — deterministic fallback (always on)

Jacobian-lens (anthropics/jacobian-lens) needs torch+transformers+fitted lens;
see docs/12-local-model-neural.md. Not default on this host until venv exists.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any

import numpy as np

from hermespace.neural_field import DEFAULT_DIM, embed_text


OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434").rstrip("/")
DEFAULT_EMBED_MODEL = os.environ.get("HERMESPACE_EMBED_MODEL", "nomic-embed-text")
DEFAULT_VERBAL_MODEL = os.environ.get("HERMESPACE_VERBAL_MODEL", "llama3.1:8b")


def _http_json(url: str, payload: dict, timeout: float = 60.0) -> dict[str, Any] | None:
    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError, OSError):
        return None


def ollama_embed(text: str, model: str = DEFAULT_EMBED_MODEL) -> np.ndarray | None:
    data = _http_json(f"{OLLAMA_HOST}/api/embeddings", {"model": model, "prompt": text or " "}, timeout=30.0)
    if not data or "embedding" not in data:
        return None
    v = np.asarray(data["embedding"], dtype=np.float64)
    n = np.linalg.norm(v)
    if n > 1e-12:
        v /= n
    return v


def ollama_embeddings_available(model: str = DEFAULT_EMBED_MODEL) -> bool:
    v = ollama_embed("ping", model=model)
    return v is not None and v.size > 0


def project_to_dim(v: np.ndarray, dim: int = DEFAULT_DIM) -> np.ndarray:
    """Fit arbitrary embed dim into field dim (pad/truncate + renorm)."""
    if v.size == dim:
        out = v.astype(np.float64, copy=True)
    elif v.size > dim:
        # structured downsample
        idx = np.linspace(0, v.size - 1, dim).astype(int)
        out = v[idx].astype(np.float64)
    else:
        out = np.zeros(dim, dtype=np.float64)
        out[: v.size] = v
    n = np.linalg.norm(out)
    if n > 1e-12:
        out /= n
    return out


@dataclass
class EmbedBackend:
    name: str
    model: str = ""

    def embed(self, text: str, dim: int = DEFAULT_DIM) -> np.ndarray:
        raise NotImplementedError


class HashEmbedBackend(EmbedBackend):
    def __init__(self) -> None:
        super().__init__(name="hash")

    def embed(self, text: str, dim: int = DEFAULT_DIM) -> np.ndarray:
        return embed_text(text, dim)


class OllamaEmbedBackend(EmbedBackend):
    def __init__(self, model: str = DEFAULT_EMBED_MODEL) -> None:
        super().__init__(name="ollama_embed", model=model)
        self._cache: dict[str, np.ndarray] = {}

    def embed(self, text: str, dim: int = DEFAULT_DIM) -> np.ndarray:
        key = f"{self.model}\0{text}\0{dim}"
        hit = self._cache.get(key)
        if hit is not None:
            return hit
        v = ollama_embed(text, self.model)
        if v is None:
            out = embed_text(text, dim)
        else:
            out = project_to_dim(v, dim)
        if len(self._cache) < 2048:
            self._cache[key] = out
        return out


def select_embed_backend(prefer: str | None = None) -> EmbedBackend:
    prefer = (prefer or os.environ.get("HERMESPACE_NEURAL_BACKEND", "auto")).strip().lower()
    if prefer in {"hash", "geometric"}:
        return HashEmbedBackend()
    if prefer in {"ollama", "ollama_embed", "auto", ""}:
        if ollama_embeddings_available():
            return OllamaEmbedBackend()
        if prefer.startswith("ollama"):
            return OllamaEmbedBackend()  # will soft-fallback per call
        return HashEmbedBackend()
    if prefer == "jlens":
        # not installed by default
        return HashEmbedBackend()
    return HashEmbedBackend()


def verbalize_workspace(
    *,
    goal: str,
    message: str,
    concepts: list[str],
    model: str = DEFAULT_VERBAL_MODEL,
    timeout: float = 90.0,
) -> list[str]:
    """Ask a local chat model which concepts are 'on the desk' (reportable).

    This is a *behavioral* J-space analogue: reportable / task-relevant concepts,
    not Jacobian activations. Fails soft → [].
    """
    concept_lines = "\n".join(f"- {c}" for c in concepts[:16]) or "- (none)"
    prompt = f"""You are a workspace verbalizer for an AI agent.
Given GOAL, USER MESSAGE, and CANDIDATE CONCEPTS, list 3-6 concepts that should be in the agent's active workspace now — reportable, task-relevant, not fluff.

Rules:
- Output ONLY a JSON array of short strings (no markdown).
- Prefer concrete nouns/tasks over vague words.
- You may add 1 new concept if missing but critical.

GOAL: {goal[:300]}
USER: {message[:400]}
CANDIDATES:
{concept_lines}
"""
    data = _http_json(
        f"{OLLAMA_HOST}/api/generate",
        {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.1, "num_predict": 200},
        },
        timeout=timeout,
    )
    if not data:
        return []
    text = str(data.get("response") or "").strip()
    # extract JSON array
    start = text.find("[")
    end = text.rfind("]")
    if start < 0 or end <= start:
        return []
    try:
        arr = json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return []
    out: list[str] = []
    if isinstance(arr, list):
        for item in arr:
            s = str(item).strip()
            if s and s not in out:
                out.append(s[:120])
    return out[:8]


def local_capabilities() -> dict[str, Any]:
    emb_ok = ollama_embeddings_available()
    # light tags check
    tags = _http_json(f"{OLLAMA_HOST}/api/tags", {}, timeout=5.0)
    # GET not POST for tags
    models: list[str] = []
    try:
        req = urllib.request.Request(f"{OLLAMA_HOST}/api/tags", method="GET")
        with urllib.request.urlopen(req, timeout=5.0) as resp:
            tags = json.loads(resp.read().decode())
        for m in tags.get("models") or []:
            name = m.get("name") or m.get("model")
            if name:
                models.append(str(name))
    except Exception:
        pass
    jlens = False
    try:
        import jlens  # noqa: F401

        jlens = True
    except ImportError:
        pass
    torch_ok = False
    try:
        import torch  # noqa: F401

        torch_ok = True
    except ImportError:
        pass
    return {
        "ollama_host": OLLAMA_HOST,
        "embeddings_ok": emb_ok,
        "embed_model": DEFAULT_EMBED_MODEL,
        "verbal_model": DEFAULT_VERBAL_MODEL,
        "ollama_models_sample": models[:12],
        "torch": torch_ok,
        "jacobian_lens_importable": jlens,
        "recommended_backend": "ollama_embed" if emb_ok else "hash",
        "next_upgrade": (
            "Install torch+transformers+jlens; fit lens on gemma3:4b or qwen2.5-coder:7b-class HF weights"
            if not jlens
            else "Fit lens.pt and set HERMESPACE_JLENS_PATH"
        ),
    }
