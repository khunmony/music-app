import os
import sqlite3
import threading
from datetime import datetime

base_dir = os.path.dirname(os.path.abspath(__file__))
DB_PATH   = os.path.join(base_dir, "minisportify.db")

_local = threading.local()


def get_connection():
    if not hasattr(_local, "conn") or _local.conn is None:
        _local.conn = sqlite3.connect(DB_PATH)
        _local.conn.row_factory = sqlite3.Row
        _create_tables(_local.conn)
    return _local.conn


def _create_tables(conn):
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS music_files (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            file_path     TEXT    UNIQUE NOT NULL,
            title         TEXT    NOT NULL DEFAULT '',
            artist        TEXT    NOT NULL DEFAULT '',
            album         TEXT    NOT NULL DEFAULT '',
            genre         TEXT    NOT NULL DEFAULT '',
            duration      REAL    NOT NULL DEFAULT 0.0,
            last_modified REAL    NOT NULL DEFAULT 0.0
        );

        CREATE TABLE IF NOT EXISTS user_history (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            song_id    INTEGER NOT NULL REFERENCES music_files(id) ON DELETE CASCADE,
            played_at  REAL    NOT NULL,
            play_count INTEGER NOT NULL DEFAULT 1,
            liked      INTEGER NOT NULL DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS music_folders (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            folder_path TEXT UNIQUE NOT NULL
        );
    """)
    conn.commit()


def upsert_song(file_path, title, artist, album, genre, duration, last_modified):
    conn = get_connection()
    conn.execute("""
        INSERT INTO music_files (file_path, title, artist, album, genre, duration, last_modified)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(file_path) DO UPDATE SET
            title=excluded.title, artist=excluded.artist, album=excluded.album,
            genre=excluded.genre, duration=excluded.duration, last_modified=excluded.last_modified
    """, (file_path, title, artist, album, genre, duration, last_modified))
    conn.commit()
    row = conn.execute("SELECT id FROM music_files WHERE file_path = ?", (file_path,)).fetchone()
    return row["id"]


def get_all_songs():
    return get_connection().execute("SELECT * FROM music_files ORDER BY title").fetchall()


def get_song_by_path(file_path):
    return get_connection().execute(
        "SELECT * FROM music_files WHERE file_path = ?", (file_path,)
    ).fetchone()


def delete_song(file_path):
    conn = get_connection()
    conn.execute("DELETE FROM music_files WHERE file_path = ?", (file_path,))
    conn.commit()


def record_play(song_id):
    conn  = get_connection()
    now   = datetime.now().timestamp()
    row   = conn.execute(
        "SELECT id, play_count FROM user_history WHERE song_id = ?", (song_id,)
    ).fetchone()
    if row:
        conn.execute(
            "UPDATE user_history SET play_count = ?, played_at = ? WHERE id = ?",
            (row["play_count"] + 1, now, row["id"])
        )
    else:
        conn.execute(
            "INSERT INTO user_history (song_id, played_at, play_count, liked) VALUES (?, ?, 1, 0)",
            (song_id, now)
        )
    conn.commit()


def set_liked(song_id, liked: bool):
    conn = get_connection()
    now  = datetime.now().timestamp()
    row  = conn.execute("SELECT id FROM user_history WHERE song_id = ?", (song_id,)).fetchone()
    if row:
        conn.execute("UPDATE user_history SET liked = ? WHERE id = ?", (int(liked), row["id"]))
    else:
        conn.execute(
            "INSERT INTO user_history (song_id, played_at, play_count, liked) VALUES (?, ?, 0, ?)",
            (song_id, now, int(liked))
        )
    conn.commit()


def get_history():
    return get_connection().execute("""
        SELECT uh.*, mf.file_path, mf.title, mf.artist, mf.genre
        FROM user_history uh
        JOIN music_files mf ON mf.id = uh.song_id
    """).fetchall()


def add_folder(folder_path):
    conn = get_connection()
    conn.execute(
        "INSERT OR IGNORE INTO music_folders (folder_path) VALUES (?)", (folder_path,)
    )
    conn.commit()


def get_folders():
    return [r["folder_path"] for r in
            get_connection().execute("SELECT folder_path FROM music_folders").fetchall()]


def remove_folder(folder_path):
    conn = get_connection()
    conn.execute("DELETE FROM music_folders WHERE folder_path = ?", (folder_path,))
    conn.commit()


def find_missing_files():
    missing = []
    for row in get_all_songs():
        if not os.path.exists(row["file_path"]):
            missing.append(row["file_path"])
    return missing