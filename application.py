import os
import requests
import hashlib

from flask import Flask, session, render_template, request, flash
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from models import *


app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


@app.route("/", methods = ["GET", "POST"])
def index():
    return render_template('index.html')

@app.route("/test")
def test():
    res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "FNNcHf070O64hLKODokItA", "isbns": "9781632168146"})
    session['logged_in'] = False
    return str(session.get('logged_in'))


@app.route("/login", methods = ["GET","POST"])
def login():
    if request.method == "POST":
        username = request.form.get('username')
        password = request.form.get('password')
        password_hash = hashlib.md5(password.encode('utf-8')).hexdigest()
        session['logged_in'] = username
    return render_template('login.html')

@app.route("/register", methods = ["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get('username')
        password = request.form.get('password')
        password_retype = request.form.get('password_retype')
        if not password == password_retype:
            return render_template('error.html', message = "Check retyping password")
        password_hash = hashlib.md5(password.encode('utf-8')).hexdigest()
        session['logged_in'] = username
        user = Userlist(username = username, password = password_hash)
        # adding user to DATABAS
        # db.session.add(user)
        # db.session.commit()
    return render_template("register.html")
