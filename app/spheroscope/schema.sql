DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS wordlists;
DROP TABLE IF EXISTS queries;

CREATE TABLE users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT UNIQUE NOT NULL,
  password TEXT NOT NULL
);

CREATE TABLE wordlists (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  author_id INTEGER NOT NULL,
  created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  p_att TEXT NOT NULL,
  name TEXT NOT NULL,
  words TEXT NOT NULL,
  FOREIGN KEY (author_id) REFERENCES users (id)
);

CREATE TABLE queries (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  author_id INTEGER NOT NULL,
  created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  name TEXT NOT NULL,
  query TEXT NOT NULL,
  anchors TEXT,
  regions TEXT,
  pattern INTEGER,
  FOREIGN KEY (author_id) REFERENCES users (id)
);
