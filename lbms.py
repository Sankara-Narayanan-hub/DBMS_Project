from flask import Flask, render_template, request, flash, session, redirect, url_for
import mysql.connector
from mysql.connector import Error

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'


def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="No#123456",
        database="library_management"
    )

@app.route('/')
def home():
    return render_template("Home.html")


@app.route('/signup', methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        em = request.form["email"]
        pwd = request.form["password"]
        pwd2 = request.form["pwd2"]
        if pwd != pwd2:
            flash("Passwords don't match...", category='error')
            return render_template("signup.html")
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE email = %s", (em,))
            user = cursor.fetchone()
            if user:
                flash("User already exists...", category='error')
                return render_template("signup.html")
            query = "INSERT INTO users(email, password) VALUES (%s, %s)"
            cursor.execute(query, (em, pwd))
            conn.commit()
            session['email'] = em
            return redirect(url_for('index'))
        except Error as e:
            flash(f"An error occurred: {e}", category='error')
        finally:
            cursor.close()
            conn.close()
    return render_template("signup.html")


@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        em = request.form["email"]
        pwd = request.form["password"]
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE email = %s AND password = %s", (em, pwd))
            user = cursor.fetchone()
            if not user:
                flash("Invalid email or password...", category='error')
                return render_template("login.html")
            session['email'] = em
            return redirect(url_for('index'))
        except Error as e:
            flash(f"An error occurred: {e}", category='error')
        finally:
            cursor.close()
            conn.close()
    return render_template("login.html")


@app.route('/index', methods=["GET", "POST"])
def index():
    if 'email' not in session:
        return redirect(url_for('login'))

    e = session['email']
    borrowed_books = []
    search = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM books WHERE user = %s", (e,))
        borrowed_books = cursor.fetchall()

        if request.method == "POST":
            nam = request.form["sname"]
            query = "SELECT * FROM books WHERE book_title LIKE %s"
            cursor.execute(query, ("%" + nam + "%",))
            search = cursor.fetchall()
            print("Search Results:", search)    # This line for debugging
    except Error as e:
        flash(f"An error occurred: {e}", category='error')
    finally:
        cursor.close()
        conn.close()

    return render_template("index.html", borrowed_books=borrowed_books, search_results=search)

@app.route('/return', methods=["POST"])
def returnb():
    book_id = request.form['book_id']
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE books SET user = NULL, b_date = NULL, return_date = NULL WHERE bookid = %s", (book_id,))
        conn.commit()
    except Error as e:
        flash(f"An error occurred: {e}", category='error')
    finally:
        cursor.close()
        conn.close()
    return redirect(url_for('index'))

@app.route('/get', methods=["POST"])
def get():
    book_id = request.form['book_id']
    em = session['email']
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT user FROM books WHERE bookid = %s", (book_id,))
        current_user = cursor.fetchone()
        if current_user and current_user[0] is not None:
            flash("Book is already borrowed...", category='error')
            return redirect(url_for('index'))

        cursor.execute("UPDATE books SET user = %s, b_date = CURRENT_DATE, return_date = CURRENT_DATE + INTERVAL 7 DAY WHERE bookid = %s", (em, book_id))
        conn.commit()
    except Error as e:
        flash(f"An error occurred: {e}", category='error')
    finally:
        cursor.close()
        conn.close()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)