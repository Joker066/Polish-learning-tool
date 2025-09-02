from __future__ import annotations
import sqlite3
from pathlib import Path
from .paths import APP_DB

DB_PATH: Path = APP_DB

def get_conn() -> sqlite3.Connection:
    """Open a SQLite connection with sane defaults."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA synchronous = NORMAL;")
    return conn

def ensure_app_schema() -> None:
    """Create tables & indexes if missing (idempotent)."""
    with get_conn() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
              id            INTEGER PRIMARY KEY AUTOINCREMENT,
              username      TEXT    NOT NULL UNIQUE,
              password_hash TEXT    NOT NULL,
              role          TEXT    NOT NULL DEFAULT 'user',
              created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
              updated_at    TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS words (
              id        INTEGER PRIMARY KEY AUTOINCREMENT,
              voc       TEXT    NOT NULL UNIQUE,
              meaning   TEXT,
              class     TEXT,
              forms     TEXT,
              adj_forms TEXT,
              approved  INTEGER NOT NULL DEFAULT 0
            );
            CREATE INDEX IF NOT EXISTS idx_words_class ON words(class);

            CREATE TABLE IF NOT EXISTS suggestions (
              id             INTEGER PRIMARY KEY AUTOINCREMENT,
              user_id        INTEGER NOT NULL,
              word_id        INTEGER,
              new_voc        TEXT,
              new_meaning    TEXT,
              new_class      TEXT,
              new_forms      TEXT,
              new_adj_forms  TEXT,
              status         TEXT    NOT NULL DEFAULT 'pending',
              created_at     TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
              updated_at     TIMESTAMP,
              reviewed_by    TEXT,
              reviewed_at    TIMESTAMP,
              reason         TEXT,
              model_label    TEXT,
              model_prob     REAL,
              FOREIGN KEY(user_id) REFERENCES users(id),
              FOREIGN KEY(word_id) REFERENCES words(id)
            );
            CREATE INDEX IF NOT EXISTS idx_sugg_status_created
              ON suggestions(status, created_at DESC);

            CREATE TABLE IF NOT EXISTS user_word_progress (
              id             INTEGER PRIMARY KEY AUTOINCREMENT,
              user_id        INTEGER NOT NULL,
              word_id        INTEGER NOT NULL,
              weight         INTEGER NOT NULL DEFAULT 10,
              accuracy       REAL,
              last_practiced TIMESTAMP,
              UNIQUE(user_id, word_id),
              FOREIGN KEY(user_id) REFERENCES users(id),
              FOREIGN KEY(word_id) REFERENCES words(id)
            );
            CREATE INDEX IF NOT EXISTS idx_uwp_user_weight ON user_word_progress(user_id, weight DESC);
            CREATE INDEX IF NOT EXISTS idx_uwp_user_last   ON user_word_progress(user_id, last_practiced);
            """
        )

if __name__ == "__main__":
    import argparse, sys, os, hashlib, binascii
    from pathlib import Path

    ap = argparse.ArgumentParser(
        description="Initialize app.db schema. Use --fresh to delete and recreate."
    )
    ap.add_argument(
        "--fresh",
        action="store_true",
        help="Delete the DB file (and -wal/-shm) then recreate schema from scratch.",
    )
    ap.add_argument(
        "--admin",
        type=str,
        help="Admin username to create/update (only honored with --fresh).",
    )
    ap.add_argument(
        "--admin_pass",
        type=str,
        help="Admin password for the user (only honored with --fresh).",
    )
    args = ap.parse_args()

    if args.fresh:
        # Make sure nothing else is using the DB before wiping.
        for p in [
            DB_PATH,
            DB_PATH.with_name(DB_PATH.name + "-wal"),
            DB_PATH.with_name(DB_PATH.name + "-shm"),
        ]:
            try:
                p.unlink()
            except FileNotFoundError:
                pass

        ensure_app_schema()
        print(f"Fresh DB created at {DB_PATH}")

        # Optional admin seeding
        if args.admin or args.admin_pass:
            if not (args.admin and args.admin_pass):
                print("Warning: --admin and --admin_pass must be provided together when using --fresh.")
            else:
                # Prefer Werkzeug's generator if available; otherwise emit a Werkzeug-compatible PBKDF2 hash.
                try:
                    from werkzeug.security import generate_password_hash
                    pw_hash = generate_password_hash(args.admin_pass)  # pbkdf2:sha256 by default
                except Exception:
                    # Fallback: pbkdf2:sha256:<iters>$<hexsalt>$<hexhash> (Werkzeug-compatible format)
                    iterations = 260000
                    salt = binascii.hexlify(os.urandom(16)).decode()
                    dk = hashlib.pbkdf2_hmac(
                        "sha256",
                        args.admin_pass.encode("utf-8"),
                        salt.encode("utf-8"),
                        iterations,
                    )
                    pw_hash = f"pbkdf2:sha256:{iterations}${salt}${binascii.hexlify(dk).decode()}"

                with get_conn() as conn:
                    conn.execute(
                        """
                        INSERT INTO users (username, password_hash, role)
                        VALUES (?, ?, 'admin')
                        ON CONFLICT(username) DO UPDATE SET
                          password_hash = excluded.password_hash,
                          role          = 'admin',
                          updated_at    = CURRENT_TIMESTAMP
                        """,
                        (args.admin, pw_hash),
                    )
                    conn.commit()
                print(f"Admin user '{args.admin}' created/updated.")

        sys.exit(0)

    ensure_app_schema()
    print(f"Initialized DB at {DB_PATH}")