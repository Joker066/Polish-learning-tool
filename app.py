from __future__ import annotations
import os, json, sys, subprocess
from typing import Optional
from math import ceil
from datetime import datetime, timezone
from flask import Flask, render_template, request, redirect, url_for, flash, abort, session, jsonify
from flask_login import (
    LoginManager, UserMixin, login_user, login_required, current_user, logout_user
)
from werkzeug.security import generate_password_hash, check_password_hash

from core.paths import REPO
from core.db import get_conn, ensure_app_schema
from core import pos
from core.practice import pick_practice_batch, upsert_progress

# -------------------------------
# Basic constants (UI helpers)
# -------------------------------
CASES = ["NOM", "GEN", "DAT", "ACC", "INST", "LOC"]

# -------------------------------
# App bootstrap (web-only)
# -------------------------------
app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-secret-change-me")

# Ensure DB schema once (idempotent)
ensure_app_schema()

login_manager = LoginManager(app)
login_manager.login_view = "login"

# -------------------------------
# Small helpers
# -------------------------------
def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def _json_or_none(s: str | None):
    if not s:
        return None
    s = s.strip()
    if s in ("", "null", "None", "undefined"):
        return None
    try:
        return json.loads(s)
    except Exception:
        return s

def _ensure_json_text(v):
    """Store JSON objects as TEXT; leave None untouched."""
    if v is None:
        return None
    if isinstance(v, (dict, list)):
        return json.dumps(v, ensure_ascii=False)
    if isinstance(v, str):
        return v
    return json.dumps(v, ensure_ascii=False)

# -------------------------------
# Auth (minimal)
# -------------------------------
class User(UserMixin):
    def __init__(self, id: int, username: str, role: str):
        self.id = id
        self.username = username
        self.role = role

    @staticmethod
    def from_row(row) -> Optional["User"]:
        return None if row is None else User(row["id"], row["username"], row["role"])

def _get_user_by_id(uid: int) -> Optional[User]:
    with get_conn() as c:
        row = c.execute("SELECT id, username, role FROM users WHERE id=?", (uid,)).fetchone()
    return User.from_row(row)

def _get_user_by_username(username: str):
    with get_conn() as c:
        return c.execute(
            "SELECT id, username, role, password_hash FROM users WHERE username=?",
            (username,),
        ).fetchone()

@login_manager.user_loader
def load_user(user_id: str) -> Optional[User]:
    try:
        return _get_user_by_id(int(user_id))
    except Exception:
        return None

# -------------------------------
# Routes
# -------------------------------
@app.route("/")
def home():
    return render_template("home.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        password = request.form.get("password") or ""
        if not username or not password:
            flash("Username and password are required.")
            return redirect(url_for("register"))
        with get_conn() as c:
            exists = c.execute("SELECT 1 FROM users WHERE username=?", (username,)).fetchone()
            if exists:
                flash("Username already exists.")
                return redirect(url_for("register"))
            c.execute(
                "INSERT INTO users (username, password_hash, role) VALUES (?,?,?)",
                (username, generate_password_hash(password), "user"),
            )
        flash("Registered. Please log in.")
        return redirect(url_for("login"))
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        password = request.form.get("password") or ""
        row = _get_user_by_username(username)
        if not row:
            flash("Invalid credentials.")
            return redirect(url_for("login"))

        ph = row["password_hash"]
        if isinstance(ph, bytes):
            try:
                ph = ph.decode("utf-8")
            except Exception:
                ph = ""

        if not isinstance(ph, str) or "$" not in ph or not check_password_hash(ph, password):
            flash("Invalid credentials.")
            return redirect(url_for("login"))

        login_user(User.from_row(row))
        flash("Logged in.")
        return redirect(url_for("home"))
    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logged out.")
    return redirect(url_for("home"))

# -------------------------------
# Words list + detail (public)
# -------------------------------
@app.route("/words")
def words():
    q = (request.args.get("search") or "").strip()
    page = request.args.get("page", default=1, type=int) or 1
    per_page = 50
    offset = (page - 1) * per_page

    where = ""
    params = []
    if q:
        where = "WHERE voc LIKE ? OR meaning LIKE ?"
        params = [f"%{q}%", f"%{q}%"]

    with get_conn() as c:
        total = c.execute(f"SELECT COUNT(*) FROM words {where}", params).fetchone()[0]
        rows = c.execute(
            f"""
            SELECT id, voc, meaning, class
            FROM words
            {where}
            ORDER BY voc
            LIMIT ? OFFSET ?
            """,
            (*params, per_page, offset),
        ).fetchall()

    total_pages = max(1, ceil(total / per_page)) if total else 1
    return render_template(
        "words.html",
        words=rows,
        search_query=q,
        page=page,
        total_pages=total_pages,
        has_prev=(page > 1),
        has_next=(page < total_pages),
    )

@app.route("/word/<voc>")
def word_detail(voc: str):
    back_page = request.args.get("page", default=1, type=int) or 1
    back_search = request.args.get("search", default="", type=str) or ""
    with get_conn() as c:
        row = c.execute(
            "SELECT id, voc, meaning, class, forms, adj_forms FROM words WHERE voc=?",
            (voc,),
        ).fetchone()
    if not row:
        flash("Word not found.")
        return redirect(url_for("words", search=back_search, page=back_page))

    forms_json = json.loads(row["forms"]) if row["forms"] else None
    if isinstance(forms_json, str):
        try:
            forms_json = json.loads(forms_json)
        except Exception:
            pass

    adj_forms_json = json.loads(row["adj_forms"]) if row["adj_forms"] else None
    if isinstance(adj_forms_json, str):
        try:
            adj_forms_json = json.loads(adj_forms_json)
        except Exception:
            pass

    return render_template(
        "word_detail.html",
        word=row,
        forms_json=forms_json,
        adj_forms_json=adj_forms_json,
        back_page=back_page,
        back_search=back_search,
    )

# -------------------------------
# Suggestions (user submit)
# -------------------------------
@app.route("/suggest", methods=["GET", "POST"])
@login_required
def add_suggestion():
    if request.method == "GET":
        return render_template(
            "add_suggestion.html",
            CASES=CASES,
            pref_voc=request.args.get("voc", ""),
            pref_mean=request.args.get("meaning", ""),
            pref_class=request.args.get("class", "")
        )

    # POST
    voc        = (request.form.get("new_voc") or request.form.get("word") or "").strip()
    meaning    = (request.form.get("new_meaning") or request.form.get("meaning") or "").strip()
    user_class = (request.form.get("new_class") or request.form.get("class") or "").strip().lower()

    new_forms     = _json_or_none(request.form.get("new_forms"))
    new_adj_forms = _json_or_none(request.form.get("new_adj_forms"))

    # If class empty, predict once server-side and accept it
    model_label, model_prob = None, 0.0
    source = "manual"
    if not user_class:
        lbl, probs = pos.predict(voc, meaning)
        model_label = lbl
        model_prob  = float(probs.get(lbl, 0.0))
        user_class  = lbl
        source      = "auto_server"

    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO suggestions (
              user_id, new_voc, new_meaning, new_class, new_forms, new_adj_forms,
              status, created_at
            ) VALUES (?,?,?,?,?,?, 'pending', CURRENT_TIMESTAMP)
            """,
            (current_user.id, voc or None, meaning or None,
             user_class or None, _ensure_json_text(new_forms), _ensure_json_text(new_adj_forms)),
        )

    # Log rich metadata for future training (JSONL)
    pos.online_update(
        voc=voc, meaning=meaning, label=user_class,
        corrected=(user_class != (model_label or user_class)),
        model_label=model_label, model_prob=model_prob,
        source=source, confirmed=False, auto_filled=False,
        ts=_utc(), new_forms=new_forms, new_adj_forms=new_adj_forms
    )

    flash("Suggestion submitted.")
    return redirect(url_for("suggestions"))

# -------------------------------
# Suggestions admin
# -------------------------------
SELECT_SUGG_BY_STATUS = """
SELECT
  s.id, s.user_id,
  s.new_voc,
  s.new_meaning,
  s.new_class,
  s.new_forms, s.new_adj_forms,
  s.status, s.created_at, s.updated_at,
  s.reviewed_by, s.reviewed_at, s.reason
FROM suggestions s
WHERE s.status = ?
ORDER BY s.created_at DESC
"""

@app.route("/admin/suggestions")
@login_required
def suggestions():
    if getattr(current_user, "role", "user") != "admin":
        abort(403)
    with get_conn() as conn:
        pending  = conn.execute(SELECT_SUGG_BY_STATUS, ("pending",)).fetchall()
        approved = conn.execute(SELECT_SUGG_BY_STATUS, ("approved",)).fetchall()
        rejected = conn.execute(SELECT_SUGG_BY_STATUS, ("rejected",)).fetchall()
    return render_template("suggestions.html", pending=pending, approved=approved, rejected=rejected)

@app.post("/suggestions/approve/<int:sugg_id>")
@login_required
def approve_suggestion(sugg_id: int):
    if getattr(current_user, "role", "user") != "admin":
        abort(403)

    with get_conn() as conn:
        row = conn.execute(
            """
            SELECT id,
                new_voc,
                new_meaning,
                new_class,
                new_forms, new_adj_forms
            FROM suggestions WHERE id = ?
            """,
            (sugg_id,)
        ).fetchone()

        if not row:
            flash("Suggestion not found.", "warning")
            return redirect(url_for("suggestions"))

        voc         = (row["new_voc"] or "").strip()
        meaning     = (row["new_meaning"] or "").strip()
        final_label = (row["new_class"] or "").strip().lower()

        if not voc or not final_label:
            flash("Missing required fields for approval.", "warning")
            return redirect(url_for("suggestions"))

        # UPSERT into words (preserves word ID if it already exists)
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
            (voc, meaning or None, final_label, row["new_forms"], row["new_adj_forms"])
        )

        # Mark suggestion approved
        ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        conn.execute(
            "UPDATE suggestions SET status='approved', reviewed_by=?, reviewed_at=?, updated_at=? WHERE id=?",
            (getattr(current_user, "username", "admin"), ts, ts, sugg_id)
        )
        conn.commit()

    # Log confirmed feedback (for future retraining)
    ml, probs = pos.predict(voc, meaning)
    pos.online_update(
        voc=voc, label=final_label, meaning=meaning,
        corrected=(final_label != ml), confirmed=True, source="admin_approve",
        model_label=ml, model_prob=float(probs.get(ml, 0.0)),
        sugg_id=sugg_id, reviewer=getattr(current_user, "username", "admin"), ts=ts
    )

    # Fire retrain script; it will SKIP unless enough feedback rows exist
    subprocess.run(
        [
            sys.executable, "-m", "scripts.retrain_pos",
            "--reuse-vocab",
            "--feedback-weight", "2.0",
            "--require-feedback", "100",
            "--quiet"
        ],
        cwd=str(REPO),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    flash(f"Approved '{voc}' ({final_label}).", "success")
    return redirect(url_for("suggestions"))

@app.post("/admin/suggestions/<int:sid>/reject")
@login_required
def reject_suggestion(sid: int):
    if getattr(current_user, "role", "user") != "admin":
        abort(403)
    reason = (request.form.get("reason") or "").strip() or None
    with get_conn() as conn:
        conn.execute(
            """
            UPDATE suggestions
            SET status='rejected',
                reason=?,
                reviewed_by=?,
                reviewed_at=?,
                updated_at=CURRENT_TIMESTAMP
            WHERE id=?;
            """,
            (reason, getattr(current_user, "username", "admin"), _utc(), sid),
        )
    flash("Suggestion rejected.")
    return redirect(url_for("suggestions"))

# -------------------------------
# Practice
# -------------------------------
@app.route("/practice")
@login_required
def practice_page():
    user_id = getattr(current_user, "id", None) or 1  # dev fallback
    search = request.args.get("q") or None
    class_in = request.args.getlist("class") or None

    with get_conn() as conn:
        items = pick_practice_batch(conn, user_id, k=20, search=search, class_in=class_in)

    return render_template("practice.html", items=items)

@app.post("/practice/answer")
@login_required
def practice_answer():
    data = request.get_json(force=True, silent=True) or {}
    try:
        word_id = int(data.get("word_id", 0))
    except (TypeError, ValueError):
        return jsonify({"error": "invalid word_id"}), 400
    if word_id <= 0:
        return jsonify({"error": "invalid word_id"}), 400

    is_correct = bool(data.get("is_correct"))
    delta = -1 if is_correct else +2

    user_id = getattr(current_user, "id", None) or 1
    with get_conn() as conn:
        upsert_progress(conn, user_id, word_id, delta=delta, is_correct=is_correct)

    return jsonify({"ok": True})

# -------------------------------
# Auto-classify
# -------------------------------
@app.get("/classify")
@login_required
def classify():
    voc = (request.args.get("voc") or "").strip()
    meaning = (request.args.get("meaning") or "").strip()

    if not voc and not meaning:
        return jsonify({"error": "Missing 'voc' or 'meaning'"}), 400

    try:
        label, probs = pos.predict(voc, meaning)
        prob_map = {k: float(v) for k, v in (probs or {}).items()}
        top_p = float(prob_map.get(label, 0.0))
        return jsonify({"label": label, "prob": top_p, "probs": prob_map})
    except Exception as e:
        return jsonify({"error": f"classify failed: {e.__class__.__name__}: {e}"}), 500

# -------------------------------
# Deployment
# -------------------------------
@app.get("/healthz")
def healthz():
    return {"ok": True}, 200

# -------------------------------
# Entrypoint
# -------------------------------
if __name__ == "__main__":
    app.run(debug=True)
