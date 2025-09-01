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
              adj_forms TEXT
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
    ensure_app_schema()
    print(f"Initialized DB at {DB_PATH}")
