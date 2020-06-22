DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS wordlists;
DROP TABLE IF EXISTS queries;
DROP TABLE IF EXISTS macros;
DROP TABLE IF EXISTS patterns;

CREATE TABLE users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT UNIQUE NOT NULL,
  password TEXT NOT NULL
);

CREATE TABLE queries (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  author_id INTEGER NOT NULL,
  modified TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  corpus TEXT,			--file-directory
  name TEXT NOT NULL,		--file-name
  query TEXT NOT NULL,		--file
  anchors TEXT,			--file
  regions TEXT,			--file
  pattern INTEGER,		--file
  FOREIGN KEY (author_id) REFERENCES users (id)
);

CREATE TABLE wordlists (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  author_id INTEGER NOT NULL,
  modified TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  corpus TEXT,			--file-directory
  name TEXT NOT NULL,		--file-name
  words TEXT NOT NULL,		--file
  p_att TEXT NOT NULL,		--file-name
  FOREIGN KEY (author_id) REFERENCES users (id)
);

CREATE TABLE macros (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  author_id INTEGER NOT NULL,
  modified TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  corpus TEXT,			--file-directory
  name TEXT NOT NULL,		--file-name
  macro TEXT NOT NULL,		--file
  FOREIGN KEY (author_id) REFERENCES users (id)
);

CREATE TABLE patterns (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  author_id INTEGER NOT NULL,
  modified TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  name TEXT,			--file
  template TEXT NOT NULL,	--file
  explanation TEXT,		--file
  FOREIGN KEY (author_id) REFERENCES users (id)
);
