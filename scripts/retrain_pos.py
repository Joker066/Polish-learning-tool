import argparse, json, hashlib, sys
from pathlib import Path
from typing import Dict, List, Tuple
from collections import Counter
import numpy as np
from sklearn.linear_model import LogisticRegression

from core.paths import DATA_DIR, REPO

# Where core/pos.py will load from
MODEL_PATH = REPO / "core" / "models" / "pos_model.npz"
META_PATH  = MODEL_PATH.with_suffix(".meta.json")

CLASSES = ["n","v","adj","adv","pron","prep","aux","ph","other"]  # fixed order

def load_words_json(p: Path) -> List[Tuple[str,str,str]]:
    if not p.exists(): return []
    data = json.loads(p.read_text(encoding="utf-8"))
    out = []
    for obj in data:
        voc = (obj.get("voc") or "").strip()
        meaning = (obj.get("meaning") or "").strip()
        label = (obj.get("class") or "").strip()
        if voc and meaning and label in CLASSES:
            out.append((voc, meaning, label))
    return out

def load_feedback_jsonl(p: Path) -> List[Tuple[str,str,str]]:
    if not p.exists(): return []
    out = []
    with p.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line: continue
            try:
                obj = json.loads(line)
            except Exception:
                continue
            voc = (obj.get("voc") or "").strip()
            meaning = (obj.get("meaning") or "").strip()
            label = (obj.get("label") or "").strip()
            if voc and meaning and label in CLASSES:
                out.append((voc, meaning, label))
    return out

def char_3grams(text: str) -> List[str]:
    s = text.lower()
    return [s[i:i+3] for i in range(len(s)-2)] if len(s) >= 3 else []

def build_vocab(samples: List[Tuple[str,str,str]], size: int) -> Dict[str,int]:
    freq = Counter()
    for voc, meaning, _ in samples:
        freq.update(char_3grams(f"{voc} {meaning}"))
    most = freq.most_common(size)
    return {g:i for i,(g,_c) in enumerate(most)}

def vectorize(samples: List[Tuple[str,str,str]], vocab: Dict[str,int]) -> Tuple[np.ndarray, np.ndarray]:
    F = len(vocab)
    X = np.zeros((len(samples), F), dtype=np.float32)
    y = np.zeros((len(samples),), dtype=np.int64)
    label2idx = {c:i for i,c in enumerate(CLASSES)}
    for i,(voc, meaning, label) in enumerate(samples):
        for g in char_3grams(f"{voc} {meaning}"):
            j = vocab.get(g)
            if j is not None: X[i, j] += 1.0
        n = float(np.linalg.norm(X[i])); 
        if n > 0: X[i] /= n
        y[i] = label2idx[label]
    return X, y

def reuse_existing_vocab() -> Dict[str,int] | None:
    if not MODEL_PATH.exists(): return None
    with np.load(str(MODEL_PATH), allow_pickle=True) as z:
        voc = z.get("vocab", None)
        if isinstance(voc, np.ndarray) and voc.shape == () and voc.dtype == object:
            return voc.item()
        if isinstance(voc, dict):
            return voc
    return None

def save_model(W: np.ndarray, b: np.ndarray, classes: List[str], vocab: Dict[str,int]) -> None:
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    np.savez(MODEL_PATH, W=W.astype(np.float32), b=b.astype(np.float32), classes=np.array(classes), vocab=vocab)
    h = hashlib.sha1(); h.update(W.astype(np.float32).tobytes()); h.update(b.astype(np.float32).tobytes())
    META_PATH.write_text(json.dumps({"model_version": "pos-lr-3gram", "model_hash": h.hexdigest()},
                                    ensure_ascii=False, indent=2), encoding="utf-8")

def main():
    ap = argparse.ArgumentParser(description="Train/retrain POS model. Saves to core/models/pos_model.npz.")
    ap.add_argument("--words", type=Path, default=(DATA_DIR/"words.json"))
    ap.add_argument("--feedback", type=Path, default=(DATA_DIR/"pos_feedback.jsonl"))
    ap.add_argument("--vocab-size", type=int, default=5000)
    ap.add_argument("--reuse-vocab", action="store_true")
    ap.add_argument("--feedback-weight", type=float, default=2.0)
    ap.add_argument("--require-feedback", type=int, default=-1)
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    base = load_words_json(args.words)
    fb = load_feedback_jsonl(args.feedback)
    if not args.quiet:
        print(f"base rows: {len(base)}  |  feedback rows: {len(fb)}")

    if args.require_feedback >= 0 and len(fb) < args.require_feedback:
        if not args.quiet:
            print(f"SKIP: feedback rows {len(fb)} < require-feedback {args.require_feedback}")
        return 0

    if fb and args.feedback_weight > 1.0:
        k = max(1, int(round(args.feedback_weight)))
        fb = fb * k

    samples = base + fb
    if not samples:
        print("No data to train.", file=sys.stderr)
        return 1

    vocab = reuse_existing_vocab() if args.reuse_vocab else None
    if vocab is None:
        vocab = build_vocab(samples, size=args.vocab_size)
        if not args.quiet: print(f"Built new vocab: {len(vocab)}")
    else:
        if not args.quiet: print(f"Reused vocab: {len(vocab)}")

    X, y = vectorize(samples, vocab)
    if not args.quiet:
        print(f"Vectorized: X={X.shape}, y={y.shape}, nnz={int(np.count_nonzero(X))}")

    clf = LogisticRegression(multi_class="multinomial", solver="lbfgs", max_iter=1000)
    clf.fit(X, y)

    F = X.shape[1]
    W_full = np.zeros((len(CLASSES), F), dtype=np.float32)
    b_full = np.zeros((len(CLASSES),), dtype=np.float32)
    for row_idx, class_idx in enumerate(clf.classes_):
        W_full[class_idx, :] = clf.coef_[row_idx]
        b_full[class_idx] = clf.intercept_[row_idx]

    save_model(W_full, b_full, CLASSES, vocab)
    if not args.quiet:
        nz = int(np.count_nonzero(W_full))
        print(f"Saved model: {MODEL_PATH}  W.nonzero={nz}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
