import sqlite3, json
from pathlib import Path

SCHEMA = """
PRAGMA journal_mode=WAL;
CREATE TABLE IF NOT EXISTS files(
  id INTEGER PRIMARY KEY,
  path TEXT UNIQUE,
  parent TEXT,
  duration REAL,
  language TEXT
);
CREATE TABLE IF NOT EXISTS segments(
  id INTEGER PRIMARY KEY,
  file_id INTEGER,
  start REAL,
  "end" REAL,
  text TEXT,
  sentiment TEXT,
  tones TEXT,
  FOREIGN KEY(file_id) REFERENCES files(id)
);
CREATE VIRTUAL TABLE IF NOT EXISTS seg_fts USING fts5(text, content='segments', content_rowid='id');
CREATE TRIGGER IF NOT EXISTS seg_ai AFTER INSERT ON segments BEGIN
  INSERT INTO seg_fts(rowid, text) VALUES (new.id, new.text);
END;
CREATE TRIGGER IF NOT EXISTS seg_ad AFTER DELETE ON segments BEGIN
  INSERT INTO seg_fts(seg_fts, rowid, text) VALUES ('delete', old.id, old.text);
END;
CREATE TRIGGER IF NOT EXISTS seg_au AFTER UPDATE ON segments BEGIN
  INSERT INTO seg_fts(seg_fts, rowid, text) VALUES ('delete', old.id, old.text);
  INSERT INTO seg_fts(rowid, text) VALUES (new.id, new.text);
END;
"""

def open_db(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(path)
    con.execute("PRAGMA foreign_keys=ON")
    con.executescript(SCHEMA)
    return con

def insert_file(con, path, parent, duration, language) -> int:
    cur = con.execute(
        "INSERT OR IGNORE INTO files(path,parent,duration,language) VALUES (?,?,?,?)",
        (str(path), str(parent), duration, language),
    )
    if cur.lastrowid:
        return cur.lastrowid
    row = con.execute("SELECT id FROM files WHERE path=?", (str(path),)).fetchone()
    return row[0]

def insert_segments(con, file_id: int, segments: list):
    for s in segments:
        con.execute(
            'INSERT INTO segments(file_id,start,"end",text,sentiment,tones) VALUES (?,?,?,?,?,?)',
            (file_id, s["start"], s["end"], s["text"], s.get("sentiment"),
             json.dumps(s.get("tones", []), ensure_ascii=False)),
        )
    con.commit()
