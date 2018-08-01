import os
import requests
import hashlib

from flask import Flask, session, render_template, request, flash, redirect, url_for
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from flask_sqlalchemy import SQLAlchemy



app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# jinja2
app.jinja_env.add_extension('jinja2.ext.loopcontrols')

# Set up database
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
db = SQLAlchemy()
db.init_app(app)

Session(app)

@app.before_request
def before_request():
    try:
        if not session['logged_in']:
            session['logged_in'] = False
    except:
        session['logged_in'] = False
    if not session['logged_in']:
        if request.endpoint not in ['index', 'login', 'register']:
            return render_template('index.html')
    else:
        if request.endpoint in ['index', 'login', 'register']:
            return render_template('booksearch.html')


@app.route('/', methods = ['GET', 'POST'])
def index():
    return render_template('index.html')

@app.route('/home', methods = ['GET', 'POST'])
def home():
    return render_template('index.html')

@app.route("/login", methods = ["GET","POST"])
def login():
    if request.method == "POST":
        username = request.form.get('username')
        password = request.form.get('password')
        password_hash = hashlib.md5(password.encode('utf-8')).hexdigest()
        # check db
        try:
            user_id = db.session.execute("SELECT id FROM users WHERE username = :username AND password_hash = :password_hash", {'username' : username, 'password_hash' : password_hash}).fetchone()[0]
            session['logged_in'] = user_id
            return render_template('booksearch.html')
        except:
            return render_template('error.html', message = "Incorrect username or password")
    return render_template('login.html')

@app.route("/logout")
def logout():
    session['logged_in'] = False
    return render_template('index.html')

@app.route("/register", methods = ["GET", "POST"])
def register():
    if session['logged_in']:
        return render_template('booksearch.html')
    if request.method == "POST":
        username = request.form.get('username')
        password = request.form.get('password')
        password_retype = request.form.get('password_retype')
        if not password == password_retype:
            return render_template('error.html', message = "Check retyping password")
        password_hash = hashlib.md5(password.encode('utf-8')).hexdigest()
        # adding user to DATABASE
        try:
            db.session.execute("INSERT INTO users (username, password_hash) VALUES (:username, :password_hash)", {'username' : username, 'password_hash' : password_hash})
            db.session.commit()
            user_id = db.session.execute("SELECT id FROM users WHERE username = :username", {'username' : username}).fetchone()[0]
            session['logged_in'] = user_id
            return render_template('booksearch.html')
        except:
            return render_template("error.html", message = "User registration error")
    return render_template("register.html")

@app.route("/booksearch", methods = ["GET", "POST"])
def booksearch():
    if request.method == "POST":
        book_cols = ['isbn', 'title', 'author', 'year']
        searchcol = request.form.get('searchcol')
        searchtag = request.form.get('searchtag')
        searchtag = f"%{searchtag.lower()}%"
        if searchcol not in book_cols:
            return render_template('error.html', message="Unknown access")
        try:
            # books = db.session.execute('SELECT * FROM books WHERE LOWER((:searchcol)::text) LIKE :searchtag', {'searchcol' : searchcol, 'searchtag' : searchtag}).fetchone()
            books = db.session.execute(f"SELECT * FROM books WHERE LOWER(({searchcol})::text) LIKE :searchtag", {'searchtag' : searchtag }).fetchall()
            if not books:
                return render_template('info.html', message = "Couldn't find your requested book")
        except:
            return render_template('error.html', message = "Error in accessing books database")
        return render_template('booksearch.html', books = books)
    else:
        return render_template('booksearch.html', books = False)

@app.route("/booksearch/<int:book_id>", methods = ["GET", "POST"])
def Book(book_id):
    user_id = session['logged_in']
    try:
        book = db.session.execute("SELECT * FROM books WHERE id = :book_id", {"book_id" : book_id}).fetchone()
        overall_rating = db.session.execute("SELECT AVG(user_rating) FROM ratings WHERE book_id = :book_id", {'book_id' : book_id}).fetchone()[0]
        user_rating = db.session.execute("SELECT AVG(user_rating) FROM ratings WHERE book_id = :book_id AND user_id = :user_id", {'book_id' : book_id, 'user_id' : user_id}).fetchone()[0]
        if not overall_rating:
            overall_rating = False
        if not user_rating:
            user_rating = False
    except:
        return render_template('error.html', message = "Error in accessing books database")
    if request.method == "POST":
        if not request.form.get('user_rating'):
            return redirect( url_for(request.endpoint, book_id = book_id))
        if not user_rating:
            user_rating = request.form.get('user_rating')
            try:
                db.session.execute("INSERT INTO ratings (book_id, user_id, user_rating) VALUES (:book_id, :user_id, :user_rating)", {'book_id' : book_id, 'user_id' : user_id, 'user_rating' : user_rating})
                db.session.commit()
            except:
                return render_template('error.html', message = "Error in accessing books database")
        else:
            user_rating = request.form.get('user_rating')
            try:
                db.session.execute("UPDATE ratings SET user_rating = :user_rating WHERE user_id = :user_id AND book_id = :book_id", {'user_id' : user_id, 'book_id' : book_id, 'user_rating' : user_rating})
                db.session.commit()
            except:
                return render_template('error.html', message = "Error in accessing books database")
        overall_rating = db.session.execute("SELECT AVG(user_rating) FROM ratings WHERE book_id = :book_id", {'book_id' : book_id}).fetchone()[0]
    if user_rating:
        user_rating = round(int(user_rating), 1)
    if overall_rating:
        overall_rating = round(overall_rating, 1)
    return render_template('bookinfo.html', book = book, user_rating = user_rating, overall_rating = overall_rating)

@app.route("/booksearch/<int:book_id>/<string:book_col>")
def Bookcol(book_id,book_col):
    book_cols = ['isbn', 'title', 'author', 'year']
    if book_col not in book_cols:
        return render_template('error.html', message = 'Restricted access')
    try:
        col_value = db.session.execute(f"SELECT {book_col} FROM books WHERE id = :book_id", {'book_id' : book_id}).fetchone()[0]
    except:
        return render_template('error.html', message = "Error in accessing books database")
    try:
        books = db.session.execute(f"SELECT * FROM books WHERE {book_col} = :col_value", {'col_value' : col_value }).fetchall()
    except:
        return render_template('error.html', message = "Error in accessing books database")
    return render_template('booksearch.html',books = books)
