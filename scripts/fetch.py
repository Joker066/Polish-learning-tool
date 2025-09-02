#!/usr/bin/env python3
import argparse, json, sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional
from core.paths import APP_DB, DATA_DIR

def conn_open(p: Path) -> sqlite3.Connection:
    c = sqlite3.connect(str(p)); c.row_factory = sqlite3.Row; return c

def read_json(p: Path, enc: str) -> List[Dict[str, Any]]:
    if not p.exists(): return []
    with p.open("r", encoding=enc) as f:
        data = json.load(f)
    if not isinstance(data, list): raise ValueError("words.json root must be a list")
    return data

def to_obj(s: Optional[str]):
    if s is None or str(s).strip()=="":
        return None
    try:
        return json.loads(s)
    except Exception:
        return s

def main():
    ap = argparse.ArgumentParser(description="Fetch ALL rows from app.db into words.json (merge by voc).")
    ap.add_argument("--db", type=Path, default=APP_DB)
    ap.add_argument("--json", type=Path, default=(DATA_DIR / "words.json"))
    ap.add_argument("--encoding", default="utf-8")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    conn = conn_open(args.db)
    rows = conn.execute("SELECT voc, meaning, class, forms, adj_forms FROM words").fetchall()
    current = read_json(args.json, args.encoding)

    by_voc: Dict[str, Dict[str, Any]] = { (x.get("voc") or "").strip(): x for x in current if (x.get("voc") or "").strip() }
    for r in rows:
        voc = (r["voc"] or "").strip()
        if not voc: continue
        by_voc[voc] = {
            "voc": voc,
            "meaning": to_obj(r["meaning"]),
            "class":   to_obj(r["class"]),
            "forms":   to_obj(r["forms"]),
            "adj_forms": to_obj(r["adj_forms"]),
        }

    merged = list(by_voc.values())
    merged.sort(key=lambda x: (x.get("voc") or "").lower())

    if args.dry_run:
        print(f"[DRY-RUN] db_rows={len(rows)} json_before={len(current)} json_after={len(merged)}")
        return

    args.json.parent.mkdir(parents=True, exist_ok=True)
    with args.json.open("w", encoding=args.encoding) as f:
        json.dump(merged, f, ensure_ascii=False, indent=2)
    print(f"Updated {args.json}: db_rows={len(rows)} total_entries={len(merged)}")

if __name__ == "__main__":
    main()
