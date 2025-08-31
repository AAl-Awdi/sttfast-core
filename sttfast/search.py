import sqlite3
from typing import Iterable

def search_phrase(con: sqlite3.Connection, phrase: str) -> Iterable[dict]:
    rows = con.execute("""
      SELECT s.id, f.path, s.start, s."end", s.text
      FROM seg_fts ft
      JOIN segments s ON s.id = ft.rowid
      JOIN files f ON f.id = s.file_id
      WHERE seg_fts MATCH ?
      ORDER BY f.path, s.start
    """, (phrase,)).fetchall()
    for r in rows:
        yield {"segment_id": r[0], "file": r[1], "start": r[2], "end": r[3], "text": r[4]}
