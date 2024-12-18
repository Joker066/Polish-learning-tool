from flask import Flask, request, render_template, redirect, url_for, jsonify
import sqlite3
import datetime

app = Flask(__name__)

# 查詢詞彙
@app.route("/")
def index():
    query = request.args.get("query")
    results = []
    if query:
        conn = sqlite3.connect("databases/words.db")
        cursor = conn.cursor()
        cursor.execute("SELECT word, meaning, class FROM words WHERE word = ?", (query,))
        results = cursor.fetchall()
        conn.close()
    return render_template("index.html", results=results, query=query)

# 提交建議
@app.route("/suggest", methods=["GET", "POST"])
def suggest():
    if request.method == "POST":
        word = request.form["word"]
        suggestion_type = request.form["suggestion_type"]
        new_meaning = request.form["meaning"]
        new_class = request.form["class"]
        user = request.form["user"]

        # 插入到 suggestions.db
        conn = sqlite3.connect("databases/suggestions.db")
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO suggestions (word, suggestion_type, new_meaning, new_class, status, suggested_by, suggested_at)
            VALUES (?, ?, ?, ?, 'pending', ?, ?)
        """, (word, suggestion_type, new_meaning, new_class, user, datetime.datetime.now()))
        conn.commit()
        conn.close()
        return redirect(url_for("index"))
    return render_template("suggest.html")

# 管理員審核建議
@app.route("/admin", methods=["GET", "POST"])
def admin():
    if request.method == "POST":
        suggestion_id = request.form["suggestion_id"]
        action = request.form["action"]

        conn_suggest = sqlite3.connect("databases/suggestions.db")
        cursor_suggest = conn_suggest.cursor()
        
        # 取得建議內容
        cursor_suggest.execute("SELECT * FROM suggestions WHERE id = ?", (suggestion_id,))
        suggestion = cursor_suggest.fetchone()

        if suggestion and action == "approve":
            # 新增或修改 words.db
            conn_vocab = sqlite3.connect("databases/words.db")
            cursor_vocab = conn_vocab.cursor()

            if suggestion[2] == "add":
                cursor_vocab.execute("""
                    INSERT INTO words (word, meaning, class, created_by, created_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (suggestion[1], suggestion[3], suggestion[4], suggestion[6], datetime.datetime.now()))
            elif suggestion[2] == "modify":
                cursor_vocab.execute("""
                    UPDATE words SET meaning = ?, class = ? WHERE word = ?
                """, (suggestion[3], suggestion[4], suggestion[1]))

            conn_vocab.commit()
            conn_vocab.close()
            cursor_suggest.execute("UPDATE suggestions SET status = 'approved' WHERE id = ?", (suggestion_id,))

        elif action == "reject":
            cursor_suggest.execute("UPDATE suggestions SET status = 'rejected' WHERE id = ?", (suggestion_id,))
        
        conn_suggest.commit()
        conn_suggest.close()
    
    # 顯示所有 pending 狀態的建議
    conn = sqlite3.connect("databases/suggestions.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM suggestions WHERE status = 'pending'")
    suggestions = cursor.fetchall()
    conn.close()
    return render_template("admin.html", suggestions=suggestions)

if __name__ == "__main__":
    app.run(debug=True)
