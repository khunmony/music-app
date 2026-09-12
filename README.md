# MiniSportify 🎵

A desktop music player built with **PyQt6**, styled after Spotify's clean, sidebar-driven interface. MiniSportify started as a learning project to explore Python desktop app development and Git — and grew into a fully working local music player with library management and personalized recommendations.

## Features

- **Sidebar navigation** — collapsible sidebar (wide/narrow views) for switching between Library, Playlist, and Add Music sections
- **Automatic library scanning** — a background `QThread`-based scanner reads folders and extracts metadata (title, artist, genre) via `mutagen`
- **Persistent library** — songs, play history, and watched folders are stored in a local **SQLite** database
- **Folder management** — add music folders, rescan for new files, and remove entries for files that no longer exist on disk
- **Playback controls** — play, pause, stop, next/previous, with a draggable progress bar and live elapsed/total time
- **Like button** — mark favorite tracks
- **"Recommended for You"** — a weighted scoring engine suggests tracks based on listening history, genre matching, and recency
- **Auto-refreshing recommendations** — the recommendation panel updates automatically after each play event

## Tech Stack

| Purpose | Tool |
|---|---|
| UI | PyQt6 |
| Metadata / audio tags | mutagen |
| Data persistence | SQLite |
| Audio playback | QMediaPlayer / python-vlc |
| Background scanning | QThread |

## Project Structure

```
MiniSportify/
├── app_6.py            # UI layer (entry point)
├── database.py          # SQLite persistence layer
├── library_scanner.py    # Background folder scanning (LibraryScannerThread)
├── recommender.py        # Weighted scoring recommendation engine
├── icon/                 # UI icon assets
└── .gitignore
```

## Getting Started

1. **Clone the repo**
   ```bash
   git clone https://github.com/khunmony/music-app.git
   cd music-app
   ```

2. **Install dependencies**
   ```bash
   pip install PyQt6 mutagen
   ```

3. **Run the app**
   ```bash
   python app_6.py
   ```

## Coding Convention

This project follows a consistent internal standard across all UI classes:
- Each UI class implements exactly three methods: `create_widgets()`, `layout_widgets()`, `connect_signals()`
- No `Ui_` wrapper classes
- No hard-coded geometry — layouts use `QVBoxLayout` / `QHBoxLayout`
- No inline comments in working source files (annotated/experimental versions are kept separately)

## About

MiniSportify is a personal project built to practice Python, PyQt6, and Git/GitHub workflows, with an emphasis on clean architecture and readable code organization.

## Author

**Khun Mony** ([@khunmony](https://github.com/khunmony))
