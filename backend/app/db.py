from contextlib import contextmanager
from pathlib import Path
import sqlite3, json, datetime as dt

DB_PATH = Path(__file__).parent / "chat.db"


def init_db() -> None:
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("""
        CREATE TABLE IF NOT EXISTS chats (
            chat_id     TEXT      PRIMARY KEY,
            title       TEXT,
            created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );""")

        cur.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id       INTEGER   PRIMARY KEY AUTOINCREMENT,
            chat_id  TEXT      REFERENCES chats(chat_id) ON DELETE CASCADE,
            role     TEXT,               -- 'user' | 'assistant'
            content  TEXT,               -- JSON 직렬화
            ts       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );""")
        conn.commit()

        cur.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id        INTEGER  PRIMARY KEY AUTOINCREMENT,
            chat_id   TEXT     REFERENCES chats(chat_id) ON DELETE CASCADE,
            product   TEXT     -- JSON 직렬
        );""")


@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH, isolation_level=None)
    conn.row_factory = sqlite3.Row
    yield conn
    conn.close()
