#!/usr/bin/env python3
import argparse, json, sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from core.paths import APP_DB, DATA_DIR

def conn_open(p: Path) -> sqlite3.Connection:
    p.parent.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(str(p))
    c.row_factory = sqlite3.Row
    return c

def load_words_json(p: Path, encoding: str) -> List[Dict[str, Any]]:
    with p.open("r", encoding=encoding) as f:
        data = json.load(f)
    if not isinstance(data, list): raise ValueError("JSON root must be a list")
    return data

def to_text(v: Any) -> Optional[str]:
    if v is None: return None
    return json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else (s if (s:=str(v).strip()) else None)

def norm(obj: Dict[str, Any]) -> Tuple[str, Optional[str], Optional[str], Optional[str], Optional[str]]:
    voc = (obj.get("voc") or "").strip()
    if not voc: raise ValueError("Missing 'voc'")
    return voc, to_text(obj.get("meaning")), to_text(obj.get("class")), to_text(obj.get("forms")), to_text(obj.get("adj_forms"))

def main():
    ap = argparse.ArgumentParser(description="Import words.json into app.db; never overwrite approved rows.")
    ap.add_argument("--db", type=Path, default=APP_DB)
    ap.add_argument("--json", type=Path, default=(DATA_DIR / "words.json"))
    ap.add_argument("--encoding", default="utf-8")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    items = load_words_json(args.json, args.encoding)
    conn  = conn_open(args.db)

    # Single concise upsert: updates only when target row is unapproved.
    sql = """
    INSERT INTO words (voc, meaning, class, forms, adj_forms, approved)
    VALUES (?, ?, ?, ?, ?, 0)
    ON CONFLICT(voc) DO UPDATE SET
      meaning   = excluded.meaning,
      class     = excluded.class,
      forms     = excluded.forms,
      adj_forms = excluded.adj_forms
    WHERE words.approved = 0;
    """

    total = inserted = updated = skipped = errors = 0
    for obj in items:
        total += 1
        try:
            rec = norm(obj)
        except Exception:
            errors += 1
            continue

        if args.dry_run:
            row = conn.execute("SELECT approved FROM words WHERE voc=?", (rec[0],)).fetchone()
            if row is None: inserted += 1
            elif int(row["approved"] or 0) == 0: updated += 1
            else: skipped += 1
            continue

        # Pre-check for accurate counters but keep the write path compact.
        row = conn.execute("SELECT approved FROM words WHERE voc=?", (rec[0],)).fetchone()
        try:
            conn.execute(sql, (*rec,))  # approved forced to 0 for inserts
            if row is None: inserted += 1
            elif int(row["approved"] or 0) == 0: updated += 1
            else: skipped += 1
        except Exception:
            errors += 1

    if not args.dry_run:
        conn.commit()

    print(f"total={total} inserted={inserted} updated_unapproved={updated} skipped_approved={skipped} errors={errors}")

if __name__ == "__main__":
    main()
