import os
from PyQt6.QtCore import QThread, pyqtSignal

try:
    from mutagen import File as MutagenFile
    MUTAGEN_OK = True
except ImportError:
    MUTAGEN_OK = False

import database as db

AUDIO_EXTENSIONS = {".mp3", ".wav", ".ogg", ".flac", ".m4a", ".aac"}


def extract_metadata(file_path):
    title         = os.path.splitext(os.path.basename(file_path))[0]
    artist        = ""
    album         = ""
    genre         = ""
    duration      = 0.0
    last_modified = os.path.getmtime(file_path)

    if MUTAGEN_OK:
        try:
            audio = MutagenFile(file_path, easy=False)
            if audio:
                if audio.info:
                    duration = audio.info.length
                tags = audio.tags
                if tags:
                    if "TIT2" in tags:
                        title  = str(tags["TIT2"].text[0])
                    if "TPE1" in tags:
                        artist = str(tags["TPE1"].text[0])
                    if "TALB" in tags:
                        album  = str(tags["TALB"].text[0])
                    if "TCON" in tags:
                        genre  = str(tags["TCON"].text[0])
        except Exception:
            pass

    return {
        "file_path":     file_path,
        "title":         title,
        "artist":        artist,
        "album":         album,
        "genre":         genre,
        "duration":      duration,
        "last_modified": last_modified,
    }


def collect_audio_files(folder_path):
    found = []
    if not os.path.isdir(folder_path):
        return found
    for root, _, files in os.walk(folder_path):
        for fname in files:
            if os.path.splitext(fname)[1].lower() in AUDIO_EXTENSIONS:
                found.append(os.path.join(root, fname))
    return found


def scan_file(file_path):
    meta = extract_metadata(file_path)
    song_id = db.upsert_song(
        meta["file_path"], meta["title"], meta["artist"],
        meta["album"],     meta["genre"], meta["duration"],
        meta["last_modified"]
    )
    return song_id, meta


class LibraryScannerThread(QThread):
    song_found   = pyqtSignal(int, dict)
    scan_done    = pyqtSignal(int)
    scan_error   = pyqtSignal(str)

    def __init__(self, folders, parent=None):
        super().__init__(parent)
        self.folders = folders

    def run(self):
        total = 0
        for folder in self.folders:
            if not os.path.isdir(folder):
                self.scan_error.emit(f"Folder not found: {folder}")
                continue
            for file_path in collect_audio_files(folder):
                try:
                    song_id, meta = scan_file(file_path)
                    self.song_found.emit(song_id, meta)
                    total += 1
                except Exception as e:
                    self.scan_error.emit(f"Error scanning {file_path}: {e}")
        self.scan_done.emit(total)


def scan_single_files(file_paths):
    results = []
    for path in file_paths:
        if not os.path.isfile(path):
            continue
        try:
            song_id, meta = scan_file(path)
            results.append((song_id, meta))
        except Exception:
            pass
    return results
