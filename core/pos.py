from __future__ import annotations
from typing import Dict, Tuple
import json
import numpy as np

from .paths import REPO, DATA_DIR

# -------- paths --------
MODEL_PATH = REPO / "core" / "models" / "pos_model.npz"
MODEL_META_PATH = MODEL_PATH.with_suffix(".meta.json")

# -------- caches --------
_MODEL_CACHE: dict | None = None
_MODEL_META: dict | None = None

# =========================
# Meta helpers
# =========================
def _load_meta() -> dict:
    global _MODEL_META
    if _MODEL_META is not None:
        return _MODEL_META
    if MODEL_META_PATH.exists():
        try:
            _MODEL_META = json.loads(MODEL_META_PATH.read_text(encoding="utf-8"))
        except Exception:
            _MODEL_META = {}
    else:
        _MODEL_META = {}
    return _MODEL_META

def get_model_meta() -> dict:
    m = _load_meta()
    return {
        "model_version": m.get("model_version"),
        "model_hash": m.get("model_hash"),
    }

# =========================
# Model loading
# =========================
def _lazy_load() -> dict:
    """
    Load model once if pos_model.npz exists; else return {}.
    Expected keys:
      - W: np.ndarray (C, F)  or (F, C)
      - b: np.ndarray (C,) or scalar (optional)
      - classes: array/list length C
      - vocab: dict[str,int]  (saved via allow_pickle; may appear as 0-D object array)
    """
    global _MODEL_CACHE
    if _MODEL_CACHE is not None:
        return _MODEL_CACHE
    if MODEL_PATH.exists():
        data = np.load(MODEL_PATH, allow_pickle=True)
        cache = {k: data[k] for k in data.files}

        # Unwrap vocab if saved as 0-D object ndarray
        v = cache.get("vocab")
        if isinstance(v, np.ndarray) and v.dtype == object and v.shape == ():
            try:
                cache["vocab"] = v.item()
            except Exception:
                cache["vocab"] = None

        _MODEL_CACHE = cache
        return _MODEL_CACHE
    _MODEL_CACHE = {}
    return _MODEL_CACHE

# =========================
# Math helpers
# =========================
def _softmax(z: np.ndarray) -> np.ndarray:
    z = z.astype(np.float32)
    z = z - np.max(z)
    e = np.exp(z)
    s = e.sum()
    return e / (s + 1e-9)

# =========================
# Features
# =========================
def _featurize(voc: str, meaning: str, vocab: dict | None) -> np.ndarray:
    """
    Very small char-3gram bag. Requires vocab (dict of gram->index).
    Returns a length-|vocab| vector. If vocab is missing, caller should NOT
    attempt model inference (fallback to heuristic instead).
    """
    if not isinstance(vocab, dict) or not vocab:
        return np.zeros(0, dtype=np.float32)

    s = f"{(voc or '').lower()} {(meaning or '').lower()}"
    grams = [s[i:i + 3] for i in range(len(s) - 2)]
    x = np.zeros(len(vocab), dtype=np.float32)
    for g in grams:
        idx = vocab.get(g)
        if idx is not None:
            x[idx] += 1.0

    # L2 normalize to keep scales stable
    n = float(np.linalg.norm(x))
    if n > 0:
        x /= n
    return x

# =========================
# Simple heuristic fallback
# =========================
def _heuristic_pos(voc: str, meaning: str) -> Tuple[str, Dict[str, float]]:
    v = (voc or "").strip().lower()
    if " " in v:
        return "ph", {"ph": 0.8}
    if v.endswith(("ać", "eć", "ić", "yć", "uć", "nąć")):
        return "v", {"v": 0.7, "n": 0.2, "adj": 0.1}
    if v.endswith(("y", "i", "a")) and len(v) > 3:
        return "adj", {"adj": 0.6, "n": 0.3, "v": 0.1}
    return "n", {"n": 0.6, "adj": 0.25, "v": 0.15}

# =========================
# Inference
# =========================
def predict(voc: str, meaning: str) -> Tuple[str, Dict[str, float]]:
    """
    Return (label, probs_dict). Uses trained model if available, else heuristics.
    Robust to W being saved as (C,F) or (F,C). Requires vocab to run the model.
    """
    m = _lazy_load()
    classes = m.get("classes")
    W = m.get("W")
    b = m.get("b")
    vocab = m.get("vocab")

    # Unwrap vocab if needed
    if isinstance(vocab, np.ndarray) and vocab.dtype == object and vocab.shape == ():
        try:
            vocab = vocab.item()
        except Exception:
            vocab = None

    # Use model path only if classes, W, and vocab are valid
    if classes is not None and isinstance(W, np.ndarray) and isinstance(vocab, dict) and len(vocab) > 0:
        x = _featurize(voc, meaning, vocab)  # -> (F,)
        if x.size == 0:
            return _heuristic_pos(voc, meaning)

        x = np.asarray(x, dtype=np.float32).reshape(-1)
        W = np.asarray(W, dtype=np.float32)
        C = int(len(classes))

        if W.ndim != 2:
            return _heuristic_pos(voc, meaning)

        # Two standard layouts supported:
        #  - scikit-learn coef_: (C, F)  -> logits = W @ x
        #  - (F, C)               -> logits = x @ W
        if W.shape[0] == C and W.shape[1] == x.shape[0]:
            logits = W @ x  # (C,)
        elif W.shape[0] == x.shape[0] and W.shape[1] == C:
            logits = x @ W  # (C,)
        else:
            return _heuristic_pos(voc, meaning)

        if b is not None:
            b_arr = np.asarray(b, dtype=np.float32)
            if b_arr.ndim == 0:
                logits = logits + float(b_arr)
            elif b_arr.ndim == 1 and b_arr.shape[0] == C:
                logits = logits + b_arr

        probs = _softmax(np.asarray(logits))
        cls_list = [str(c) for c in (classes.tolist() if hasattr(classes, "tolist") else classes)]
        out = {c: float(p) for c, p in zip(cls_list, probs)}
        label = cls_list[int(np.argmax(probs))]
        return label, out

    # No usable model → heuristic
    return _heuristic_pos(voc, meaning)

# =========================
# Diagnostics (for UI)
# =========================
def model_status() -> dict:
    """
    Diagnostics for UI/API to confirm .npz participation.
    """
    m = _lazy_load()
    W = m.get("W")
    classes = m.get("classes")
    vocab = m.get("vocab")

    if isinstance(vocab, np.ndarray) and vocab.dtype == object and vocab.shape == ():
        try:
            vocab = vocab.item()
        except Exception:
            vocab = None

    side = _load_meta()
    return {
        "loaded": bool(classes is not None and isinstance(W, np.ndarray)),
        "format": "linear-3gram" if (classes is not None and isinstance(W, np.ndarray)) else "fallback",
        "has_vocab": isinstance(vocab, dict),
        "vocab_size": (len(vocab) if isinstance(vocab, dict) else None),
        "W_shape": (tuple(W.shape) if isinstance(W, np.ndarray) else None),
        "num_classes": (int(len(classes)) if classes is not None else None),
        "model_path": str(MODEL_PATH),
        "model_version": side.get("model_version"),
        "model_hash": side.get("model_hash"),
    }

# =========================
# Lightweight feedback logging (for future retraining)
# =========================
def online_update(voc: str, label: str, meaning: str, corrected: bool = False, **meta) -> None:
    """
    Append lightweight feedback for future retraining. Doesn’t mutate the model live.
    File: /data/pos_feedback.jsonl (one JSON object per line).
    Accepts extra metadata via **meta (e.g., prob, source, confirmed, ts).
    """
    rec = {
        "voc": voc,
        "label": label,
        "meaning": meaning,
        "corrected": bool(corrected),
        **meta,
    }
    p = DATA_DIR / "pos_feedback.jsonl"
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")

# =========================
# Reload model after retraining
# =========================
def reload_model() -> dict:
    """Drop caches and reload model+meta; returns model_status()."""
    global _MODEL_CACHE, _MODEL_META
    _MODEL_CACHE = None
    _MODEL_META = None
    return model_status()
