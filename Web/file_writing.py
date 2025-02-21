import sqlite3, csv

def export_db_to_csv():
    conn = sqlite3.connect("databases/words.db")
    cursor = conn.cursor()

    cursor.execute("SELECT voc, meaning, class FROM words")
    rows = cursor.fetchall()

    with open("databases/words.csv", mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(["voc", "meaning", "class"])
        writer.writerows(rows)

    conn.close()