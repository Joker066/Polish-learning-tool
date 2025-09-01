from __future__ import annotations
import time, hashlib
from typing import List, Dict, Optional, Sequence, Tuple

DEFAULT_WEIGHT  = 10
MIN_WEIGHT      = 1
MAX_WEIGHT      = 999
CANDIDATE_LIMIT = 200
ACCURACY_ALPHA  = 0.2  # EMA for accuracy

def _jitter(user_id: int, word_id: int, day_key: int) -> float:
    s = f"{user_id}:{word_id}:{day_key}".encode("utf-8")
    h = hashlib.sha256(s).digest()
    return int.from_bytes(h[:8], "big") / (1 << 64)  # [0,1)

def _score(weight: float, last_practiced_s: float, now_s: float) -> float:
    age_days = max(0.0, (now_s - (last_practiced_s or 0.0)) / 86400.0)
    age_term = min(age_days, 30.0)
    return 10.0 * float(weight) + age_term

def pick_practice_batch(
    conn,
    user_id: int,
    k: int = 20,
    search: Optional[str] = None,
    class_in: Optional[Sequence[str]] = None,
    now: Optional[float] = None,
) -> List[Dict]:
    """
    Returns k items shaped for the template:
      {word_id, voc, meaning, class, direction: "vm"|"mv"}
    Batch is independent (no cross-batch cooldown). Directions alternate.
    """
    now_s = float(now if now is not None else time.time())

    where, params = [], []
    # Only take answerable rows
    where.append("w.voc IS NOT NULL AND w.voc <> ''")
    where.append("w.meaning IS NOT NULL AND w.meaning <> ''")

    if search:
        where.append("(w.voc LIKE ? OR w.meaning LIKE ?)")
        pat = f"%{search}%"; params.extend([pat, pat])

    if class_in:
        placeholders = ",".join("?" for _ in class_in)
        where.append(f"w.class IN ({placeholders})")
        params.extend(list(class_in))

    where_sql = "WHERE " + " AND ".join(where)

    # Candidate pool
    select_sql = f"""
        SELECT
          w.id AS word_id,
          w.voc, w.meaning, w.class,
          COALESCE(uwp.weight, ?) AS weight,
          COALESCE(strftime('%s', uwp.last_practiced), 0) AS last_practiced_s
        FROM words w
        LEFT JOIN user_word_progress uwp
          ON uwp.user_id = ? AND uwp.word_id = w.id
        {where_sql}
        LIMIT {CANDIDATE_LIMIT}
    """
    args = [DEFAULT_WEIGHT, user_id, *params]
    rows = conn.execute(select_sql, args).fetchall()
    if not rows:
        return []

    day_key = int(now_s // 86400)
    scored: List[Tuple[float, float, int, str, str, str]] = []
    for r in rows:
        wid  = int(r["word_id"])
        voc  = (r["voc"] or "")
        mean = (r["meaning"] or "")
        cls  = (r["class"] or "")
        w    = float(r["weight"] or DEFAULT_WEIGHT)
        last = float(r["last_practiced_s"] or 0.0)

        score  = _score(w, last, now_s)
        jitter = _jitter(user_id, wid, day_key)
        scored.append((score, jitter, wid, voc, mean, cls))

    # Highest score first; jitter breaks ties
    scored.sort(key=lambda t: (-t[0], -t[1]))
    batch = scored[:k]

    # Alternate directions "vm", "mv"
    out: List[Dict] = []
    for i, (_sc, _jit, wid, voc, mean, cls) in enumerate(batch):
        direction = "vm" if (i % 2 == 0) else "mv"
        out.append({"word_id": wid, "voc": voc, "meaning": mean, "class": cls, "direction": direction})
    return out

def upsert_progress(
    conn,
    user_id: int,
    word_id: int,
    delta: int,         # e.g., -1 if correct, +2 if wrong
    is_correct: bool,
) -> None:
    # Ensure row exists
    conn.execute(
        """
        INSERT OR IGNORE INTO user_word_progress
            (user_id, word_id, weight, accuracy, last_practiced)
        VALUES (?, ?, ?, NULL, CURRENT_TIMESTAMP)
        """,
        (user_id, word_id, DEFAULT_WEIGHT),
    )
    # Update weight/accuracy/timestamp
    conn.execute(
        f"""
        UPDATE user_word_progress
        SET
          weight = MIN({MAX_WEIGHT}, MAX({MIN_WEIGHT}, weight + ?)),
          accuracy = CASE
              WHEN accuracy IS NULL THEN (CASE WHEN ? THEN 1.0 ELSE 0.0 END)
              ELSE ((1.0 - ?) * accuracy + (? * (CASE WHEN ? THEN 1.0 ELSE 0.0 END)))
          END,
          last_practiced = CURRENT_TIMESTAMP
        WHERE user_id = ? AND word_id = ?
        """,
        (delta, is_correct, ACCURACY_ALPHA, ACCURACY_ALPHA, is_correct, user_id, word_id),
    )
    conn.commit()
