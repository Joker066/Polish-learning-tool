import argparse
import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from core.paths import APP_DB, DATA_DIR  # use central paths

def connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn

def assert_words_table_exists(conn: sqlite3.Connection) -> None:
    row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='words' LIMIT 1"
    ).fetchone()
    if row is None:
        raise RuntimeError(
            "Table 'words' does not exist. Initialize the DB first (e.g., `python -m core.db`)."
        )

def load_words_json(json_path: Path, encoding: str) -> List[Dict[str, Any]]:
    with json_path.open("r", encoding=encoding) as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError("JSON root must be a list of word objects.")
    return data

def to_text_or_none(v: Any) -> Optional[str]:
    if v is None:
        return None
    if isinstance(v, (dict, list)):
        return json.dumps(v, ensure_ascii=False)
    s = str(v).strip()
    return s if s != "" else None

def normalize_record(obj: Dict[str, Any]) -> Tuple[str, Optional[str], Optional[str], Optional[str], Optional[str]]:
    # matches words schema except 'id'
    voc = (obj.get("voc") or "").strip()
    if not voc:
        raise ValueError("Missing required 'voc'")
    meaning   = to_text_or_none(obj.get("meaning"))
    cls       = to_text_or_none(obj.get("class"))
    forms     = to_text_or_none(obj.get("forms"))
    adj_forms = to_text_or_none(obj.get("adj_forms"))
    return voc, meaning, cls, forms, adj_forms

def word_exists(conn: sqlite3.Connection, voc: str) -> bool:
    return conn.execute("SELECT 1 FROM words WHERE voc=? LIMIT 1;", (voc,)).fetchone() is not None

def upsert_word(conn: sqlite3.Connection, rec: Tuple[str, Optional[str], Optional[str], Optional[str], Optional[str]]) -> None:
    conn.execute(
        """
        INSERT INTO words (voc, meaning, class, forms, adj_forms)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(voc) DO UPDATE SET
          meaning   = excluded.meaning,
          class     = excluded.class,
          forms     = excluded.forms,
          adj_forms = excluded.adj_forms
        """,
        rec,
    )

def import_words(conn: sqlite3.Connection, items: List[Dict[str, Any]]) -> Dict[str, int]:
    total = len(items)
    inserted = updated = errors = 0
    for obj in items:
        try:
            rec = normalize_record(obj)
        except Exception:
            errors += 1
            continue
        existed = word_exists(conn, rec[0])
        try:
            upsert_word(conn, rec)
            if existed:
                updated += 1
            else:
                inserted += 1
        except Exception:
            errors += 1
    conn.commit()
    return {"total": total, "inserted": inserted, "updated": updated, "errors": errors}

def main():
    p = argparse.ArgumentParser(description="Import words from JSON into the existing app.db (no schema changes).")
    p.add_argument("--db", type=Path, default=APP_DB, help="Path to SQLite DB (default: core.paths.APP_DB)")
    p.add_argument("--json", type=Path, default=(DATA_DIR / "words.json"), help="Path to words.json (default: core.paths.DATA_DIR/words.json)")
    p.add_argument("--encoding", default="utf-8", help="JSON encoding (default: utf-8)")
    p.add_argument("--dry-run", action="store_true", help="Validate without writing changes")
    args = p.parse_args()

    conn = connect(args.db)
    assert_words_table_exists(conn)
    items = load_words_json(args.json, args.encoding)

    if args.dry_run:
        ok = err = 0
        for obj in items:
            try:
                normalize_record(obj)
                ok += 1
            except Exception:
                err += 1
        print(f"[DRY-RUN] Parsed OK: {ok}, invalid: {err}, total: {len(items)}")
        return

    summary = import_words(conn, items)
    print(f"Import summary: total={summary['total']}, inserted={summary['inserted']}, updated={summary['updated']}, errors={summary['errors']}")

if __name__ == "__main__":
    main()
