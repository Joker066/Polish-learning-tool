from pathlib import Path
import os

# project root (…/core/paths.py -> parents[1] == repo root)
REPO = Path(__file__).resolve().parents[1]

# data dir (feedback, words.json, etc.)
DATA_DIR = Path(os.getenv("PLT_DATA_DIR", str(REPO / "data")))
DATA_DIR.mkdir(parents=True, exist_ok=True)

# databases dir (SQLite lives here now that /Web is gone)
DB_DIR = Path(os.getenv("PLT_DB_DIR", str(REPO / "databases")))
DB_DIR.mkdir(parents=True, exist_ok=True)

# commonly-used DB file path
APP_DB = DB_DIR / "app.db"
