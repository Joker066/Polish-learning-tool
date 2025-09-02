# Polish Learning Tool (PLT)

*A containerized Flask app for Polish vocabulary practice with an admin review workflow and a lightweight POS classifier.*

**Status:** Deployment‑ready (Docker Compose + Nginx on Ubuntu). Public hosting optional.

---

## ✨ Features

* **Practice engine:** Fixed **batches of 20** mixed Q→A / A→Q; no in‑batch repeats; realtime progress updates (SQLite).
* **Admin suggestions:** Pending → approve/reject; **approved entries upsert** into `words` table.
* **ML assist:** Lightweight POS classifier (`pos_model.npz` via NumPy); **feedback logged** to `data/pos_feedback.jsonl` for offline retraining (no live model mutation).
* **Ops docs:** Runbook for local dev, containerized deploy on Ubuntu, backups, upgrades, and a 5‑minute smoke test.

**Stack:** Python (Flask, Jinja), SQLite, NumPy, Gunicorn, Docker, Docker Compose, Nginx.

---

## 🏗 Architecture

```
[Internet]
   ↓
[Nginx container]  :80  ──►  reverse_proxy  ──►  [Web container] :8000  ──►  Flask (Gunicorn)
                                   │
                       volumes: db (SQLite), data (assets + logs)
```

**Volumes**

* `db`  → `/app/databases` (SQLite `.db` files)
* `data`→ `/app/data` (assets + `pos_feedback.jsonl`)

---

## 📦 Repository Layout

```
.
├── Dockerfile
├── README.md
├── app.py
├── core/
│   ├── __init__.py
│   ├── db.py
│   ├── grammar.py
│   ├── models/
│   │   ├── pos_model.meta.json
│   │   └── pos_model.npz
│   ├── paths.py
│   ├── pos.py
│   └── practice.py
├── data/
│   ├── pos_feedback.jsonl
│   └── words.json
├── databases/
│   └── app.db
├── docker-compose.yml
├── docker-entrypoint.sh
├── nginx.conf
├── requirements.txt
├── scripts/
│   ├── __init__.py
│   ├── import.py                 # NEW: import JSON → DB (does NOT overwrite approved rows)
│   ├── fetch.py                  # NEW: fetch DB → JSON (merges all rows; drops 'approved' flag)
│   ├── import_words_json_to_appdb.py     # (legacy) can be replaced by scripts/import.py
│   ├── regenerate_words_json.py  # regenerate seed JSON from grammar rules (pre‑DB)
│   └── retrain_pos.py
└── templates/
    ├── add_suggestion.html
    ├── base.html
    ├── home.html
    ├── login.html
    ├── practice.html
    ├── register.html
    ├── suggestions.html
    ├── word_detail.html
    └── words.html
```

**Notes**

* `core/models/pos_model.npz` (+ meta) are versioned model artifacts.
* `data/words.json` is the tracked **seed vocabulary** and can be **regenerated** from `core/grammar.py` via `scripts/regenerate_words_json.py` (run **before** creating `databases/app.db` or whenever grammar rules change).
* `data/pos_feedback.jsonl` is a runtime log (ignored in Git).
* `databases/app.db` is a runtime SQLite DB (do **not** version it; re-import from `data/words.json` if you regenerate).

### 🧰 Scripts (usage)

* **Regenerate seed** `data/words.json` **from grammar rules** (`core/grammar.py`). Run this **before creating** `databases/app.db` or whenever grammar rules change.

  ```bash
  docker compose exec web python scripts/regenerate_words_json.py
  ```
* **Import** seed JSON → SQLite (creates/updates `app.db`; **does not overwrite** rows where `approved=1`).

  ```bash
  docker compose exec web python scripts/import.py --json data/words.json
  # legacy script (will overwrite): scripts/import_words_json_to_appdb.py → prefer scripts/import.py
  ```
* **Fetch** DB → JSON (merges all rows by `voc`; **does not** write the `approved` flag into JSON).

  ```bash
  docker compose exec web python scripts/fetch.py --json data/words.json
  ```
* **Retrain** POS model (example path):

  ```bash
  docker compose exec web python scripts/retrain_pos.py core/models/pos_model.npz
  ```

---

## ⚙️ Prerequisites

* Docker Engine + Docker Compose (v2)
* Ubuntu 22.04 LTS recommended for VM deployments

---

## 🚀 Quickstart (Local via Docker Compose)

1. Clone & configure

```bash
git clone <your_repo_url> plt && cd plt
# Create .env
cat > .env <<'EOF'
SECRET_KEY=$(python3 - <<PY
import secrets; print(secrets.token_urlsafe(48))
PY
)
TZ=Asia/Taipei
GUNICORN_WORKERS=4
EOF
chmod +x docker-entrypoint.sh
```

2. Build & run

```bash
docker compose build
docker compose up -d
```

Visit **[http://localhost/](http://localhost/)** (Nginx → Flask).

3. (Optional) If you tweak grammar rules, **regenerate seed** `data/words.json` from `core/grammar.py`

```bash
docker compose exec web python scripts/regenerate_words_json.py
```

4. Initialize / sync DB from JSON (**won't overwrite approved rows**)

```bash
docker compose exec web python scripts/import.py --json data/words.json
```

5. (Optional) Sync JSON from DB (merge all rows)

```bash
docker compose exec web python scripts/fetch.py --json data/words.json
```

6. (Optional) Make yourself admin (if roles apply)

```bash
docker compose exec web sqlite3 /app/databases/app.db \
  "UPDATE users SET role='admin' WHERE email='you@example.com';"
```

---

## 🔐 Configuration

Create **.env** in the repo root:

```dotenv
TZ=Asia/Taipei
SECRET_KEY=<long-random-string>
GUNICORN_WORKERS=4
```

Generate a key quickly:

```bash
python3 - <<'PY'
import secrets; print(secrets.token_urlsafe(48))
PY
```

---

## 🐳 Docker & Nginx

### docker-compose.yml

```yaml
services:
  web:
    build: .
    image: plt-polish-web:latest
    environment:
      - SECRET_KEY=${SECRET_KEY}
      - TZ=${TZ}
      - GUNICORN_WORKERS=${GUNICORN_WORKERS:-4}
    volumes:
      - db:/app/databases
      - data:/app/data
    restart: unless-stopped

  nginx:
    image: nginx:1.27-alpine
    depends_on: [web]
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/conf.d/default.conf:ro
      - data:/app/data:ro
    restart: unless-stopped

volumes:
  db:
  data:
```

### Dockerfile

```dockerfile
FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
WORKDIR /app

# System deps (if needed)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential && rm -rf /var/lib/apt/lists/*

# Python deps
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# App code
COPY . .
RUN chmod +x docker-entrypoint.sh
EXPOSE 8000
# Use the entrypoint script if it starts Gunicorn/does setup
ENTRYPOINT ["./docker-entrypoint.sh"]
# Or, if you prefer a direct CMD (comment out ENTRYPOINT above)
# CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8000", "app:app"]
```

### nginx.conf

```nginx
server {
  listen 80;
  server_name _;
  client_max_body_size 16m;

  location /static/ {
    alias /app/data/static/;  # if you mount static assets under data
    access_log off;
    expires 7d;
  }

  location / {
    proxy_pass http://web:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_http_version 1.1;
    proxy_set_header Connection "";
  }
}
```

---

## 📊 Data lifecycle with approvals (canonical)

**Goals**: Protect admin‑approved data from being overwritten; keep `words.json` as portable seed; enable round‑trip sync.

* **Schema**: add `approved INTEGER NOT NULL DEFAULT 0` to `words`.
* **Importer (`scripts/import.py`)**: inserts with `approved=0`; on conflict **updates only when `approved=0`**; **skips** rows where `approved=1`.
* **Fetch (`scripts/fetch.py`)**: reads **all** rows (approved + unapproved) and **merges** into `data/words.json` by `voc`; it **does not** write the `approved` field to JSON.
* **Admin approval**: UPSERT sets `approved=1` and merges fields with `COALESCE` to avoid null‑overwrites.

### Canonical UPSERT on approval

```sql
INSERT INTO words (voc, meaning, class, forms, adj_forms, approved)
VALUES (?, ?, ?, ?, ?, 1)
ON CONFLICT(voc) DO UPDATE SET
  meaning   = COALESCE(excluded.meaning,   words.meaning),
  class     = COALESCE(excluded.class,     words.class),
  forms     = COALESCE(excluded.forms,     words.forms),
  adj_forms = COALESCE(excluded.adj_forms, words.adj_forms),
  approved  = 1;
```

### DB lifecycle (core/db.py)

* Idempotent init:

  ```bash
  docker compose exec web python -m core.db
  ```
* Fresh rebuild (wipe DB, recreate schema):

  ```bash
  docker compose exec web python -m core.db --fresh
  ```
* Fresh + seed admin:

  ```bash
  docker compose exec web python -m core.db --fresh --admin adminname --admin_pass "S3cureP@ss"
  ```

### Migrating an **existing** DB

If upgrading an old DB without `approved`:

```bash
docker compose exec web sqlite3 /app/databases/app.db \
  "ALTER TABLE words ADD COLUMN approved INTEGER NOT NULL DEFAULT 0;"
```

(Optional) If you want to **freeze** current rows so future imports won’t touch them:

```bash
docker compose exec web sqlite3 /app/databases/app.db \
  "UPDATE words SET approved=1;"
```

Then re‑run importer/fetch as needed.

---

## 🖥️ VM Deployment (Ubuntu 22.04 LTS)

1. Install Docker

```bash
sudo apt-get update && sudo apt-get -y install ca-certificates curl gnupg
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg
. /etc/os-release
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
https://download.docker.com/linux/ubuntu $VERSION_CODENAME stable" | \
sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update && sudo apt-get -y install docker-ce docker-ce-cli containerd.io
sudo usermod -aG docker $USER  # re-login
```

2. Clone repo & configure

```bash
mkdir -p ~/plt && cd ~/plt
git clone <your_repo_url> .
cp .env.example .env
python3 scripts/generate_secret_key.py >> .env
```

3. Launch

```bash
docker compose build --no-cache
docker compose up -d
sudo ufw allow OpenSSH && sudo ufw allow 80/tcp && sudo ufw enable
```

4. Initialize DB (if needed)

```bash
docker compose exec web python -c "from core.db import init_db; init_db()"
```

**Optional HTTPS**

* **Cloudflare proxy:** point domain A record to VM IP, enable orange cloud (HTTPS to users; origin stays HTTP:80).
* **Caddy:** replace Nginx with a Caddy container for automatic Let’s Encrypt.

---

## 🛠 Operations Runbook

### Rebuild & deploy new version

```bash
docker compose pull || true
docker compose build
docker compose up -d
```

### Health checks & logs

```bash
docker ps
docker compose logs --tail=200 web
```

### Restart a service

```bash
docker compose restart web
```

### Disk cleanup

```bash
docker system df
docker system prune -f
```

### Backup & restore

Scripts provided under `scripts/`.

`scripts/backup.sh`

```bash
#!/usr/bin/env bash
set -euo pipefail
STAMP=$(date +%F-%H%M%S)
OUT=plt-backup-$STAMP.tar.gz
cd /var/lib/docker/volumes
sudo tar -czf ~/"$OUT" \
  $(docker volume ls -q | grep -E '_(db|data)$')
echo "Backup written to ~/$OUT"
```

`scripts/restore.sh`

```bash
#!/usr/bin/env bash
set -euo pipefail
if [ -z "${1:-}" ]; then echo "Usage: restore.sh <backup.tgz>"; exit 1; fi
sudo tar -xzf "$1" -C /var/lib/docker/volumes
```

`scripts/generate_secret_key.py`

```python
import secrets, os
key = secrets.token_urlsafe(48)
print(f"SECRET_KEY={key}")
```

---

## 🧪 5‑Minute Smoke Test

1. Open site (VM IP or domain) → home loads.
2. Login as admin → open **Suggestions**.
3. Create a test suggestion → **approve** → entry appears in **Words**.
4. Run one practice session (20 Qs) → completes; check no repeats in batch.
5. Confirm a new line appended to `/app/data/pos_feedback.jsonl`.
6. `docker compose logs -f nginx web` shows 200s for requests.

---

## 🔒 Security Checklist (minimum)

* Strong, unique **SECRET\_KEY**; never commit `.env`.
* Keep VM patched monthly: `sudo apt-get update && sudo apt-get -y upgrade`.
* SSH hardening: key‑based auth; disable password login.
* Optional HTTPS via Cloudflare or Caddy.

---

## 🧩 Troubleshooting

* **Blank page / 502**: `docker compose logs -f web nginx`; ensure Gunicorn is running and bound to `0.0.0.0:8000`.
* **Entrypoint not executing**: make sure `docker-entrypoint.sh` is executable (`chmod +x`) and referenced as `ENTRYPOINT` in the Dockerfile.
* **SQLite locked**: Avoid concurrent writes; back up with the stack down.
* **Static files 404**: Ensure `/static/` assets exist or remove the `location /static/` block in `nginx.conf`.

---

## 📝 .gitignore

```
# Python
__pycache__/
*.pyc

# Env & secrets
.env

# Runtime DB & logs (keep words.json tracked)
databases/*.db
data/pos_feedback.jsonl

# OS/IDE
.DS_Store
.vscode/
```

If `databases/app.db` is currently tracked, remove it from history and rely on the scripts/seed:

```bash
git rm --cached databases/app.db
git commit -m "Stop tracking runtime DB"
```

---

## 🧼 GitHub housekeeping

* Keep `data/words.json` **tracked** as seed; keep `data/pos_feedback.jsonl` **untracked**.
* Avoid committing real user data; treat `databases/app.db` as ephemeral.
* Add a short **About** in your repo description and link the **Handover & Launch Checklist**.

---

## 📚 License

Choose a license. Example (MIT):

```
MIT License

Copyright (c) 2025 <Your Name>

Permission is hereby granted, free of charge, to any person obtaining a copy
... (standard MIT text)
```

---

## 🎓 CV‑ready blurb

> Deployment‑ready Flask application packaged with Docker Compose and Nginx on Ubuntu; includes an operations runbook (backups, health checks, rebuilds) and a 5‑minute smoke test; integrates a lightweight POS classifier with an offline feedback loop.

---

## 🙌 Acknowledgements

* Built as an independent learning + engineering project.

---

> For questions or academic reference (e.g., WUT application), link to this README and the **Handover & Launch Checklist** in your docs.
