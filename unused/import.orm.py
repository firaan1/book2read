import os
import requests
import hashlib
import csv

from flask import Flask, session, render_template, request, flash
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from models import *


app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Set up database
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)


def main():
    f = open("books.csv")
    reader = csv.reader(f)
    for isbn, title, author, year in reader:
        if isbn == "isbn":
            continue
        try:
            db_isbn = Booklist.query.filter_by(isbn = isbn).one()
            if str(isbn) == str(db_isbn.isbn):
                print(f"Skipping Book --- {title} already exist")
                continue
        except:
            pass
        book = Booklist(isbn = isbn, title = title, author = author, year = year)
        db.session.add(book)
        print(f"Added book titled {title} by {author} ({year})")
    try:
        db.session.commit()
    except:
        print("Error commiting to database"


if __name__ == "__main__":
    with app.app_context():
        main()
