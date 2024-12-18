import sqlite3, csv, os, sys

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(parent_dir)
from files import *

def word_to_CSV():
    words = load_words(child=True)
    with open("databases/words.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["voc", "meaning", "class"])
        for word in words:
            writer.writerow([word["voc"], word["meaning"], word["class"]])

def init_words_db():
    conn = sqlite3.connect("databases/words.db")
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS words")  # 刪除舊的表格
    print("Dropping old table if it exists...")
    cursor.execute("""
        CREATE TABLE words (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            voc TEXT UNIQUE NOT NULL,
            meaning TEXT NOT NULL,
            class TEXT NOT NULL
        )
    """)
    print("Creating new table...")
    conn.commit()
    conn.close()
    print("Table created successfully.")


def init_suggestions_db():
    conn = sqlite3.connect("databases/suggestions.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS suggestions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            voc TEXT NOT NULL,
            suggestion_type TEXT NOT NULL, -- 'add' or 'modify'
            new_meaning TEXT,
            new_class TEXT,
            status TEXT DEFAULT 'pending', -- pending, approved, rejected
            suggested_by TEXT NOT NULL,
            suggested_at TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def import_words_to_db():
    csv_file = "databases/words.csv"
    db_file = "databases/words.db"

    # 連接 SQLite 資料庫
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()

    # 檢查或建立表格
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS words (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            voc TEXT UNIQUE NOT NULL,
            meaning TEXT NOT NULL,
            class TEXT NOT NULL
        )
    """)

    with open(csv_file, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                print(f"Inserting word: {row['voc']}")  # Debug: print the word being inserted
                cursor.execute("""
                    INSERT INTO words (voc, meaning, class)
                    VALUES (?, ?, ?)
                """, (row["voc"], row["meaning"], row["class"]))
            except sqlite3.IntegrityError:
                print(f"跳過重複的詞彙: {row['voc']}")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_words_db()
    init_suggestions_db()
    word_to_CSV()
    import_words_to_db()
