CREATE TABLE books (
    id SERIAL PRIMARY KEY,
    isbn VARCHAR NOT NULL,
    title VARCHAR NOT NULL,
    author VARCHAR NOT NULL,
    year INTEGER NOT NULL
);

CREATE TABLE users (
  id SERIAL PRIMARY KEY,
  username VARCHAR NOT NULL UNIQUE,
  password_hash VARCHAR NOT NULL,
  question VARCHAR NOT NULL,
  answer VARCHAR NOT NULL
);

CREATE TABLE reviews (
  id SERIAL PRIMARY KEY,
  book_id INTEGER REFERENCES books,
  user_id INTEGER REFERENCES users,
  user_review VARCHAR NOT NULL
);

CREATE TABLE ratings (
  id SERIAL PRIMARY KEY,
  book_id INTEGER REFERENCES books,
  user_id INTEGER REFERENCES users,
  user_rating INTEGER NOT NULL
);
