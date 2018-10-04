# Project 1: **Book*2*Review**

Web Programming with Python and JavaScript

This application was developed using Python Flask, HTML and CSS.
This web page allows the users to register / login and search for books based on isbn, author, title or year of publication. Further, the users can review the books and rate them.

## Download
``` bash
git clone https://github.com/firaan1/book2read.git
```
## Start **Book*2*Review**
In order to setup the database, import data and start this app for the first time, please follow the instructions below,
  ``` bash
    # Install required python packages from requirements.txt file
    pip install -r requirements.txt
    # Source bashvars.sh file to setup environment variables. This contains FLASK_APP, DATABASE_URL and bookread key variables.
    source bashvars.sh
    # Create database models using models.sql.
    psql $DATABASE_URL -f models.sql
    # From bash, import book and author informations from books.csv file into the database.
    python import.py
    # Finally, start the flask application.
    flask run
  ```
After creating database tables and importing data, the application can be started using the following commands.
  ``` bash
    source bashvars.sh
    flask run
  ```
## Contents
The directory structure is shown below,
``` bash
book2review/
├── application.py # contains all the url definitions and functions
├── bashvars.sh # contains environment vaiables necessary for this application to run
├── books.csv # List of book information provided by CS50W
├── import.py # Python file to be used to import data from books.csv to postgres database
├── models.sql # postgres database table definitions and relations
├── README.md # readme file
├── requirements.txt # List of python requirements to be installed before running this application
├── static # contains static files
│   ├── css
│   │   └── mystyles.css # custom css style definitions
│   └── images
│       └── 2.png # Image used in the application
└── templates # contains all the html templates
    ├── bookinfo.html # Individual book page
    ├── booksearch.html # Search page
    ├── error.html
    ├── index.html
    ├── info.html
    ├── layout.html # html base layout
    ├── login.html
    └── register.html
```
