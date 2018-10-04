import os
import requests
import hashlib
import json

from flask import Flask, session, render_template, request, flash, redirect, url_for, abort
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from flask_sqlalchemy import SQLAlchemy

from functools import wraps



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

# goodread
goodread_key = os.getenv("key")

# taken from flask webpage decorators
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session['logged_in'] is None or not session['logged_in']:
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def logout_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session['logged_in'] :
            return render_template('error.html', message = "User already logged in!")
        return f(*args, **kwargs)
    return decorated_function

@app.before_request
def before_request():
    try:
        if not session['logged_in']:
            session['logged_in'] = False
    except:
        session['logged_in'] = False
    # if request.method == "POST":
    #     if request.form.get('btn_home'):
    #         return render_template('index.html')
    #     if request.form.get('btn_search'):
    #         if session['logged_in']:
    #             return render_template('booksearch.html')
    #         else:
    #             return render_template('index.html')
    #     if request.form.get('btn_logout'):
    #         return redirect(url_for('logout'))
    # if not session['logged_in']:
    #     if request.endpoint not in ['index', 'login', 'register']:
    #         return render_template('index.html')
    # else:
    #     if request.endpoint in ['login', 'register']:
    #          return render_template('index.html')


@app.route('/', methods = ['GET', 'POST'])
def index():
    return render_template('index.html')

@app.route("/login", methods = ["GET","POST"])
@logout_required
def login():
    if request.method == "POST":
        username = request.form.get('username')
        password = request.form.get('password')
        password_hash = hashlib.md5(password.encode('utf-8')).hexdigest()
        # check db
        try:
            user_id = db.session.execute("SELECT id FROM users WHERE username = :username AND password_hash = :password_hash", {'username' : username, 'password_hash' : password_hash}).fetchone()[0]
            session['logged_in'] = user_id
            session['logged_in_name'] = username
            return render_template('booksearch.html')
        except:
            return render_template('error.html', message = "Incorrect username or password")
    return render_template('login.html')

@app.route("/logout")
@login_required
def logout():
    session['logged_in'] = False
    session['logged_in_name'] = False
    return render_template('index.html')

@app.route("/register", methods = ["GET", "POST"])
@logout_required
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
            return render_template('login.html', message = "Registration successful!")
            # user_id = db.session.execute("SELECT id FROM users WHERE username = :username", {'username' : username}).fetchone()[0]
            # session['logged_in'] = user_id
            # session['logged_in_name'] = username
            # return render_template('booksearch.html')
        except:
            return render_template("error.html", message = "User registration error")
    return render_template("register.html")

@app.route("/booksearch", methods = ["GET", "POST"])
@login_required
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
@login_required
def Book(book_id):
    user_id = session['logged_in']
    gread_dict = {}
    try:
        # book rating
        book = db.session.execute("SELECT * FROM books WHERE id = :book_id", {"book_id" : book_id}).fetchone()
        # goodread data
        gread = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": goodread_key, "isbns": book[1]})
        if gread.status_code == 200:
            gread_dict = json.loads(gread.content)
        # our database
        # overall_rating = db.session.execute("SELECT AVG(user_rating) FROM ratings WHERE book_id = :book_id", {'book_id' : book_id}).fetchone()[0]
        overall_rating = db.session.execute("SELECT AVG(user_rating),COUNT(user_rating) FROM ratings WHERE book_id = :book_id", {'book_id' : book_id}).fetchone()
        user_rating = db.session.execute("SELECT AVG(user_rating) FROM ratings WHERE book_id = :book_id AND user_id = :user_id", {'book_id' : book_id, 'user_id' : user_id}).fetchone()[0]
        if not overall_rating[0]:
            overall_rating = False
            overall_rating_list = False
        if not user_rating:
            user_rating = False
        # book reviews
        overall_reviews = db.session.execute("SELECT username, user_review FROM reviews JOIN users ON reviews.user_id = users.id WHERE book_id = :book_id", {'book_id' : book_id}).fetchall()
        user_review = db.session.execute("SELECT user_review FROM reviews WHERE book_id = :book_id AND user_id = :user_id", {'book_id' : book_id, 'user_id' : user_id}).fetchone()
        if not user_review:
            user_review = False
        else:
            user_review = user_review[0]
        if not overall_reviews:
            overall_reviews = False
    except:
        return render_template('error.html', message = "Error in accessing books database")
    if request.method == "POST":
        if request.form.get('buttonsrc') == "deletereview":
            try:
                db.session.execute("DELETE FROM reviews WHERE user_id = :user_id AND book_id = :book_id", {'user_id' : user_id, 'book_id' : book_id})
                db.session.commit()
                user_review = False
            except:
                return render_template('error.html', message = "Error in accessing books database")
        elif request.form.get('buttonsrc') == "review":
            user_review = request.form.get('user_review')
            try:
                # preventing refresh post
                db.session.execute("INSERT INTO reviews (book_id, user_id, user_review) SELECT :book_id, :user_id, :user_review WHERE (SELECT COUNT(*) FROM reviews WHERE book_id = :book_id AND user_id = :user_id) = 0", {'book_id' : book_id, 'user_id' : user_id, 'user_review' : user_review})
                db.session.commit()
            except:
                render_template('error.html', message = "Error in accessing books database")
        else:
            if not request.form.get('user_rating'):
                return redirect( url_for(request.endpoint, book_id = book_id))
            if not user_rating:
                user_rating = request.form.get('user_rating')
                try:
                    # preventing refresh post
                    db.session.execute("INSERT INTO ratings (book_id, user_id, user_rating) SELECT :book_id, :user_id, :user_rating WHERE (SELECT COUNT(*) FROM ratings WHERE book_id = :book_id AND user_id = :user_id) = 0", {'book_id' : book_id, 'user_id' : user_id, 'user_rating' : user_rating})
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
        # overall_rating = db.session.execute("SELECT user_rating FROM ratings WHERE book_id = :book_id", {'book_id' : book_id}).fetchone()[0]
        overall_rating = db.session.execute("SELECT AVG(user_rating), COUNT(user_rating) FROM ratings WHERE book_id = :book_id", {'book_id' : book_id}).fetchone()
        overall_reviews = db.session.execute("SELECT username, user_review FROM reviews JOIN users ON reviews.user_id = users.id WHERE book_id = :book_id", {'book_id' : book_id}).fetchall()
        if not overall_reviews:
            overall_reviews = False
    if user_rating:
        user_rating = round(int(user_rating), 1)
    if overall_rating:
        if overall_rating[0]:
            overall_rating_list = []
            for o in overall_rating:
                overall_rating_list.append(o)
            overall_rating_list[0] = round(overall_rating_list[0],2)
    if not gread_dict:
        gread_rating = False
    else:
        gread_rating = gread_dict['books'][0]
    return render_template('bookinfo.html', book = book, user_rating = user_rating, overall_rating = overall_rating_list, user_review = user_review, overall_reviews = overall_reviews, gread_rating = gread_rating)

@app.route("/booksearch/<int:book_id>/<string:book_col>")
@login_required
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

@app.route("/api/<string:isbn_code>")
@login_required
def BookAPI(isbn_code):
    bookapi = {}
    try:
        book_info1 = db.session.execute("SELECT * FROM books WHERE isbn = :isbn", {'isbn' : isbn_code}).fetchone()
        if book_info1:
            book_id, isbn, title, author, year = book_info1
            gread = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": goodread_key, "isbns": isbn})
            if gread.status_code == 200:
                gread_dict = json.loads(gread.content)['books'][0]
                gread_review_count = gread_dict['reviews_count']
                gread_average_score = gread_dict['average_rating']
                gread_rating_count = gread_dict['ratings_count']
            else:
                gread_review_count = gread_average_score = gread_rating_count = "-"
            review_count = db.session.execute("SELECT COUNT(user_review) FROM reviews WHERE book_id = :book_id", {'book_id' : book_id}).fetchone()
            average_score, rating_count = db.session.execute("SELECT AVG(user_rating), COUNT(user_rating) FROM ratings WHERE book_id = :book_id", {'book_id' : book_id}).fetchone()
            if not average_score:
                average_score = ""
            else:
                average_score = str(round(average_score, 2))
            if review_count:
                review_count = review_count[0]
            bookapi = {
                "title" : title,
                "author" : author,
                "year" : year,
                "isbn" : isbn,
                "review_count" : review_count,
                "average_score" : average_score,
                "rating_count" : rating_count,
                "goodread_review_count": gread_review_count,
                "goodread_average_score" : gread_average_score,
                "goodread_rating_count" : gread_rating_count
            }
    except:
        return render_template('error.html', message = "Error in accessing books database")
    if bookapi:
        return str(bookapi)
    else:
        abort(404)
        return render_template('error.html', message = "Invalid ISBN Number"), 404
