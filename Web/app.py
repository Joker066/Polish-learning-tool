from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3, datetime
import bcrypt
from file_writing import *

app = Flask(__name__)
app.secret_key = "hash123"

@app.route("/")
def index():
    if "username" in session and get_user_by_username(session["username"]):
        return redirect("/home") 
    
    return redirect("/login")

@app.route("/home")
def home():
    if "username" not in session:
        return redirect("/login") 
    
    username = session.get("username")
    role = session.get("role")
    
    return render_template("home.html", username=username, role=role)

admin_list = ["Hash"]
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        role = "admin" if username in admin_list else "user"

        # Hash the password before storing it
        hashed_password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())

        # Store the user in the database
        conn = sqlite3.connect("databases/users.db")
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO users (username, password, role)
            VALUES (?, ?, ?)
        """, (username, hashed_password, role))
        conn.commit()
        conn.close()

        return redirect("/login")  # Redirect to login after successful registration
    return render_template("register.html")

def get_user_by_username(username):
    conn = sqlite3.connect("databases/users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    conn.close()
    return user

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        user = get_user_by_username(username)
        if user and bcrypt.checkpw(password.encode("utf-8"), user[2]):  # user[2] is the hashed password
            session["username"] = user[1]
            session["role"] = user[3]
            return redirect("/home")
        else:
            flash("Invalid username or password", "danger")  # Error message if login fails
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

def get_words_db_connection():
    conn = sqlite3.connect("databases/words.db")
    conn.row_factory = sqlite3.Row
    return conn

def get_suggestions_db_connection():
    conn = sqlite3.connect("databases/suggestions.db")
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/suggestions', methods=['GET', 'POST'])
def suggestions():
    if 'username' not in session or session['role'] != 'admin':  # Check if the user is logged in and is an admin
        return redirect(url_for('login'))  # Redirect to login page if not logged in or not an admin

    conn = sqlite3.connect('databases/suggestions.db')
    cursor = conn.cursor()
    
    # Fetch all pending suggestions
    cursor.execute("SELECT * FROM suggestions WHERE status = 'pending'")
    pending_suggestions = cursor.fetchall()

    # Fetch all approved suggestions
    cursor.execute("SELECT * FROM suggestions WHERE status = 'approved'")
    approved_suggestions = cursor.fetchall()

    # Fetch all rejected suggestions
    cursor.execute("SELECT * FROM suggestions WHERE status = 'rejected'")
    rejected_suggestions = cursor.fetchall()

    conn.close()

    # Render suggestions page with lists of pending, approved, and rejected suggestions
    return render_template('suggestions.html', 
                           pending_suggestions=pending_suggestions, 
                           approved_suggestions=approved_suggestions, 
                           rejected_suggestions=rejected_suggestions)

@app.route("/add_suggestion", methods=["GET", "POST"])
def add_suggestion():
    if request.method == "POST":
        word = request.form["word"]
        meaning = request.form["meaning"]
        word_class = request.form["class"]
        suggested_by = session["username"]
        suggested_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        conn = sqlite3.connect("databases/suggestions.db")
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO suggestions (new_voc, new_meaning, new_class, status, suggested_by, suggested_at)
            VALUES (?, ?, ?, "pending", ?, ?)
        """, (word, meaning, word_class, suggested_by, suggested_at))
        conn.commit()
        conn.close()

        flash("Suggestion submitted!", "success")

        return redirect(request.referrer)
    return render_template("add_suggestion.html")

@app.route('/approve/<int:suggestion_id>', methods=['POST'])
def approve_suggestion(suggestion_id):
    # Check if the user is logged in
    if "username" not in session or not session["role"] == "admin":
        return redirect(url_for('login'))  # Redirect to login page if not logged in

    conn = sqlite3.connect("databases/words.db")
    cursor = conn.cursor()

    cursor.execute("SELECT new_voc, new_meaning, new_class FROM suggestions WHERE id = ?", (suggestion_id,))
    row = cursor.fetchone()

    if row:
        new_voc, new_meaning, new_class = row

        cursor.execute("SELECT COUNT(*) FROM words WHERE voc = ?", (new_voc,))
        exists = cursor.fetchone()[0] > 0

        if exists:
            cursor.execute("UPDATE words SET meaning = ?, class = ? WHERE voc = ?", (new_meaning, new_class, new_voc))
        else:
            cursor.execute("INSERT INTO words (voc, meaning, class) VALUES (?)", (new_voc, new_meaning, new_class))

        cursor.execute("UPDATE suggestions SET status = 'approved' WHERE id = ?", (suggestion_id,))
        conn.commit()
        conn.close()

        export_db_to_csv()

    return redirect("/suggestions")

@app.route('/reject/<int:suggestion_id>', methods=['POST'])
def reject_suggestion(suggestion_id):
    # Check if the user is logged in
    if "username" not in session or not session["role"] == "admin":
        return redirect(url_for('login'))  # Redirect to login page if not logged in

    conn = sqlite3.connect('databases/suggestions.db')
    cursor = conn.cursor()

    cursor.execute("UPDATE suggestions SET status = 'rejected' WHERE id = ?", (suggestion_id,))
    conn.commit()
    conn.close()

    return redirect("/suggestions")


@app.route("/words", methods=["GET", "POST"])
def words():
    search_query = request.args.get("search", "")  # Get search query from URL parameters
    conn = get_words_db_connection()

    if search_query:
        words = conn.execute("SELECT * FROM words WHERE voc LIKE ?", ("%" + search_query + "%",)).fetchall()
    else:
        words = conn.execute("SELECT * FROM words").fetchall()

    conn.close()
    return render_template("words.html", words=words, search_query=search_query)

if __name__ == "__main__":
    app.run(debug=True)
