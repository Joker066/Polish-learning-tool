from flask import Flask, request, jsonify
import sqlite3
from datetime import datetime

app = Flask(__name__)

# 初始化資料庫
def init_db():
    conn = sqlite3.connect('vocabulary.db')
    c = conn.cursor()
    # 詞彙表 (已批准的詞彙)
    c.execute('''CREATE TABLE IF NOT EXISTS words
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  word TEXT UNIQUE NOT NULL,
                  definition TEXT NOT NULL,
                  added_at TEXT)''')

    # 建議表 (待審核的新增/修改建議)
    c.execute('''CREATE TABLE IF NOT EXISTS suggestions
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  word TEXT NOT NULL,
                  definition TEXT NOT NULL,
                  suggestion_type TEXT CHECK(suggestion_type IN ('add', 'modify')) NOT NULL,
                  submitted_at TEXT,
                  approved INTEGER DEFAULT 0)''')
    conn.commit()
    conn.close()

# 查詢詞彙 (模糊匹配)
@app.route('/search', methods=['GET'])
def search_words():
    query = request.args.get('q', '').lower()
    conn = sqlite3.connect('vocabulary.db')
    c = conn.cursor()
    c.execute("SELECT word, definition FROM words WHERE LOWER(word) LIKE ?", (f"%{query}%",))
    results = [{"word": row[0], "definition": row[1]} for row in c.fetchall()]
    conn.close()
    return jsonify(results), 200

# 查詢單一詞彙的細節
@app.route('/word/<word>', methods=['GET'])
def get_word_detail(word):
    conn = sqlite3.connect('vocabulary.db')
    c = conn.cursor()
    c.execute("SELECT word, definition FROM words WHERE word = ?", (word,))
    result = c.fetchone()
    conn.close()
    if result:
        return jsonify({"word": result[0], "definition": result[1]}), 200
    else:
        return jsonify({"message": "Word not found"}), 404

# 使用者提交新增或修改建議
@app.route('/suggest', methods=['POST'])
def submit_suggestion():
    data = request.json
    word = data.get('word', '').strip()
    definition = data.get('definition', '').strip()
    suggestion_type = data.get('type', 'add')  # 預設為新增建議

    if not word or not definition:
        return jsonify({"message": "Word and definition cannot be empty"}), 400

    conn = sqlite3.connect('vocabulary.db')
    c = conn.cursor()
    c.execute('''INSERT INTO suggestions (word, definition, suggestion_type, submitted_at)
                 VALUES (?, ?, ?, ?)''',
              (word, definition, suggestion_type, datetime.now()))
    conn.commit()
    conn.close()
    return jsonify({"message": "Suggestion submitted successfully"}), 201

# 管理員審核建議 (批准新增/修改)
@app.route('/approve/<int:suggestion_id>', methods=['POST'])
def approve_suggestion(suggestion_id):
    conn = sqlite3.connect('vocabulary.db')
    c = conn.cursor()
    c.execute("SELECT word, definition, suggestion_type FROM suggestions WHERE id = ?", (suggestion_id,))
    suggestion = c.fetchone()

    if not suggestion:
        conn.close()
        return jsonify({"message": "Suggestion not found"}), 404

    word, definition, suggestion_type = suggestion
    if suggestion_type == 'add':
        # 新增詞彙
        c.execute("INSERT OR IGNORE INTO words (word, definition, added_at) VALUES (?, ?, ?)",
                  (word, definition, datetime.now()))
    elif suggestion_type == 'modify':
        # 修改詞彙
        c.execute("UPDATE words SET definition = ?, added_at = ? WHERE word = ?",
                  (definition, datetime.now(), word))

    # 標記建議為已批准
    c.execute("UPDATE suggestions SET approved = 1 WHERE id = ?", (suggestion_id,))
    conn.commit()
    conn.close()
    return jsonify({"message": "Suggestion approved"}), 200

# 查詢所有待審核建議 (管理員查看)
@app.route('/pending_suggestions', methods=['GET'])
def get_pending_suggestions():
    conn = sqlite3.connect('vocabulary.db')
    c = conn.cursor()
    c.execute("SELECT id, word, definition, suggestion_type, submitted_at FROM suggestions WHERE approved = 0")
    suggestions = [{"id": row[0], "word": row[1], "definition": row[2],
                    "type": row[3], "submitted_at": row[4]} for row in c.fetchall()]
    conn.close()
    return jsonify(suggestions), 200

# 啟動程式前初始化資料庫
if __name__ == '__main__':
    init_db()
    app.run(debug=True)
