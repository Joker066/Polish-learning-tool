import sqlite3, csv

def init_words_db():
    conn = sqlite3.connect("databases/words.db")
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS words")
    cursor.execute("""
        CREATE TABLE words (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            voc TEXT UNIQUE NOT NULL,
            meaning TEXT NOT NULL,
            class TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()
    print("words.db created successfully.")

def init_suggestions_db():
    conn = sqlite3.connect("databases/suggestions.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS suggestions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            new_voc TEXT NOT NULL,
            new_meaning TEXT,
            new_class TEXT,
            status TEXT DEFAULT 'pending', -- pending, approved, rejected
            suggested_by TEXT NOT NULL,
            suggested_at TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()
    print("suggestion.db created successfully.")

def init_users_db():
    conn = sqlite3.connect("databases/users.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL -- 'admin' or 'user'
        )
    """)
    conn.commit()
    conn.close()
    print("users.db created successfully.")

def import_CSV_to_db():
    conn = sqlite3.connect("databases/words.db")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS words (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            voc TEXT UNIQUE NOT NULL,
            meaning TEXT NOT NULL,
            class TEXT NOT NULL
        )
    """)

    with open("databases/words.csv", "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                cursor.execute("""
                    INSERT INTO words (voc, meaning, class)
                    VALUES (?, ?, ?)
                """, (row["voc"], row["meaning"], row["class"]))
            except sqlite3.IntegrityError:
                print(f"repeated: {row['voc']}")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_words_db()
    import_CSV_to_db()
    init_suggestions_db()
    init_users_db()
