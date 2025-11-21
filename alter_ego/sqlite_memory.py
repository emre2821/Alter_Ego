# sqlite_memory.py — zero-dep memory store
import sqlite3, time, os
from pathlib import Path
from typing import List, Tuple

def init_db(db_path: str):
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as con:
        con.execute("""
        CREATE TABLE IF NOT EXISTS memories(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts REAL NOT NULL,
            text TEXT NOT NULL,
            tags TEXT
        )""")
        con.commit()

def add(db_path: str, text: str, tags: str = None):
    with sqlite3.connect(db_path) as con:
        con.execute("INSERT INTO memories(ts, text, tags) VALUES(?,?,?)",
                    (time.time(), text, tags))
        con.commit()

def search(db_path: str, query: str, k: int = 3) -> List[str]:
    if not Path(db_path).exists():
        return []
    q = f"%{query[:64]}%"  # crude LIKE search over first 64 chars
    with sqlite3.connect(db_path) as con:
        rows = con.execute(
            "SELECT text FROM memories WHERE text LIKE ? ORDER BY ts DESC LIMIT ?",
            (q, k)
        ).fetchall()
    return [r[0] for r in rows]
