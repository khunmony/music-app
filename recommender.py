import math
from datetime import datetime
import database as db


WEIGHT_FREQUENCY  = 0.30
WEIGHT_RECENCY    = 0.30
WEIGHT_GENRE      = 0.20
WEIGHT_ARTIST     = 0.15
WEIGHT_LIKED      = 0.05
RECENCY_DECAY     = 0.1
MAX_RESULTS       = 10


def _recency_score(played_at_timestamp):
    if not played_at_timestamp:
        return 0.0
    hours_ago = (datetime.now().timestamp() - played_at_timestamp) / 3600
    return math.exp(-RECENCY_DECAY * hours_ago)


def _frequency_score(play_count, max_count):
    if max_count == 0:
        return 0.0
    return min(play_count / max_count, 1.0)


def _genre_score(song_genre, preferred_genres):
    if not song_genre or not preferred_genres:
        return 0.0
    g = song_genre.lower()
    total_plays = sum(preferred_genres.values())
    if total_plays == 0:
        return 0.0
    return preferred_genres.get(g, 0) / total_plays


def _artist_score(song_artist, preferred_artists):
    if not song_artist or not preferred_artists:
        return 0.0
    a = song_artist.lower()
    total_plays = sum(preferred_artists.values())
    if total_plays == 0:
        return 0.0
    return preferred_artists.get(a, 0) / total_plays


def _build_preferences(history_rows):
    genres   = {}
    artists  = {}
    max_count = 0
    history_map = {}

    for row in history_rows:
        sid= row["song_id"]
        play_count= row["play_count"] or 0
        genre= (row["genre"]   or "").lower()
        artist= (row["artist"]  or "").lower()

        history_map[sid] = {
            "play_count": play_count,
            "played_at":  row["played_at"],
            "liked":      bool(row["liked"]),
        }

        if genre:
            genres[genre]   = genres.get(genre, 0)   + play_count
        if artist:
            artists[artist] = artists.get(artist, 0) + play_count
        if play_count > max_count:
            max_count = play_count

    return history_map, genres, artists, max_count


def _reason(freq, recency, genre, artist, liked):
    parts = []
    if liked:
        parts.append("you liked this")
    if freq > 0.7:
        parts.append("frequently played")
    elif recency > 0.7:
        parts.append("recently played")
    if genre > 0.4:
        parts.append("matches your genre taste")
    if artist > 0.4:
        parts.append("favourite artist")
    return ", ".join(parts) if parts else "new discovery"


def get_recommendations(limit=MAX_RESULTS):
    all_songs   = db.get_all_songs()
    history_rows = db.get_history()

    if not all_songs:
        return []

    history_map, preferred_genres, preferred_artists, max_count = _build_preferences(history_rows)
    already_played = set(history_map.keys())

    scored = []
    for song in all_songs:
        sid    = song["id"]
        hist   = history_map.get(sid, {})

        freq   = _frequency_score(hist.get("play_count", 0), max_count)
        rec    = _recency_score(hist.get("played_at"))
        genre  = _genre_score(song["genre"], preferred_genres)
        artist = _artist_score(song["artist"], preferred_artists)
        liked  = 1.0 if hist.get("liked") else 0.0

        total = (
            WEIGHT_FREQUENCY * freq   +
            WEIGHT_RECENCY   * rec    +
            WEIGHT_GENRE     * genre  +
            WEIGHT_ARTIST    * artist +
            WEIGHT_LIKED     * liked
        )

        reason = _reason(freq, rec, genre, artist, hist.get("liked", False))

        scored.append({
            "song_id":   sid,
            "file_path": song["file_path"],
            "title":     song["title"],
            "artist":    song["artist"],
            "score":     total,
            "reason":    reason,
        })

    scored.sort(key=lambda x: x["score"], reverse=True)

    seen_paths = set()
    results    = []
    for item in scored:
        if item["file_path"] in seen_paths:
            continue
        seen_paths.add(item["file_path"])
        results.append(item)
        if len(results) >= limit:
            break

    if not results:
        for song in all_songs[:limit]:
            results.append({
                "song_id":   song["id"],
                "file_path": song["file_path"],
                "title":     song["title"],
                "artist":    song["artist"],
                "score":     0.0,
                "reason":    "new discovery",
            })

    return results
