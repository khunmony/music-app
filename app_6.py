import sys
import os
from PyQt6.QtWidgets import (
    QApplication, QWidget, QPushButton, QVBoxLayout, QHBoxLayout,
    QLabel, QListWidget, QListWidgetItem, QSlider, QStackedWidget,
    QFileDialog, QMessageBox
)
from PyQt6.QtGui import QFont, QIcon, QPixmap
from PyQt6.QtCore import Qt, QUrl, QTimer

from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput

import database as db
import recommender
from library_scanner import LibraryScannerThread, scan_single_files

base_dir      = os.path.dirname(os.path.abspath(__file__))
play_icon     = os.path.join(base_dir, "icon", "6398977.png")
view_icon     = os.path.join(base_dir, "icon", "1383970.png")
plus_icon     = os.path.join(base_dir, "icon", "plus.png")
pause_icon    = os.path.join(base_dir, "icon", "pause-icon.png")
playl_icon    = os.path.join(base_dir, "icon", "play-icon.png")
forward_icon  = os.path.join(base_dir, "icon", "forward-icon.png")
backward_icon = os.path.join(base_dir, "icon", "backward-icon.png")
stop_icon     = os.path.join(base_dir, "icon", "stop-icon.png")
trash_icon    = os.path.join(base_dir, "icon", "trash-bin-icon.png")
menu_icon     = os.path.join(base_dir, "icon", "menu-icon.png")
music_icon     = os.path.join(base_dir, "icon", "musical-icon.png")
Sidebar_BG = "background-color: rgb(238,217,196);"
Content_BG = "background-color: rgb(255,240,219);"
Btn_Style  = (
    "QPushButton { background-color: rgb(238,217,196); color: rgb(0,0,0);"
    " border: none; text-align: left; padding-left: 6px; }"
    "QPushButton:checked { background-color: rgb(200,220,200); }"
    "QPushButton:hover   { background-color: rgb(220,205,190); }"
)
List_Style = """
    QListWidget {
        background-color: rgb(255,248,235);
        border: 1px solid rgb(200,180,160);
        border-radius: 8px;
        font-size: 13px;
        color: rgb(60,60,60);
    }
    QListWidget::item { padding: 8px 12px; border-bottom: 1px solid rgb(230,215,200); }
    QListWidget::item:selected { background-color: rgb(200,230,200); color: rgb(30,30,30); }
    QListWidget::item:hover { background-color: rgb(240,225,205); }
"""
Ctrl_Style = (
    "QPushButton { background-color: rgb(180,210,180); border: 1px solid rgb(140,170,140);"
    " border-radius: 6px; font-size: 12px; color: rgb(30,30,30); padding: 0 10px; }"
    "QPushButton:hover { background-color: rgb(150,200,150); }"
    "QPushButton:pressed { background-color: rgb(120,180,120); }"
)
Slider_Style = (
    "QSlider::groove:horizontal { height: 6px; background: rgb(210,195,180); border-radius: 3px; }"
    "QSlider::sub-page:horizontal { background: rgb(100,170,100); border-radius: 3px; }"
    "QSlider::handle:horizontal { width: 14px; height: 14px; margin: -4px 0;"
    " background: rgb(60,140,60); border-radius: 7px; }"
    "QSlider::handle:horizontal:hover { background: rgb(40,120,40); }"
)
menu_btn_style = (
            "QPushButton { background-color: rgb(238,217,196); border: none;"
            " font-size: 16px; color: rgb(60,60,60); }"
            "QPushButton:hover { background-color: rgb(220,205,190); }"
        )
Rec_Item_Style = """
    QListWidget {
        background-color: rgb(240,255,240);
        border: 1px solid rgb(160,200,160);
        border-radius: 8px;
        font-size: 12px;
        color: rgb(60,60,60);
    }
    QListWidget::item { padding: 6px 12px; border-bottom: 1px solid rgb(210,230,210); }
    QListWidget::item:selected { background-color: rgb(180,220,180); }
    QListWidget::item:hover { background-color: rgb(220,240,220); }
"""


def _header_widget(icon_path, text):
    container  = QWidget()
    row        = QHBoxLayout(container)
    row.setContentsMargins(0, 0, 0, 0)
    row.setSpacing(8)
    lbl_icon   = QLabel()
    px         = QPixmap(icon_path).scaled(
        24, 24,
        Qt.AspectRatioMode.KeepAspectRatio,
        Qt.TransformationMode.SmoothTransformation
    )
    lbl_icon.setPixmap(px)
    lbl_icon.setFixedSize(24, 24)
    lbl_text   = QLabel(text)
    lbl_text.setFont(QFont("Arial", 14, QFont.Weight.Bold))
    lbl_text.setStyleSheet("color: black;")
    row.addWidget(lbl_icon)
    row.addWidget(lbl_text)
    row.addStretch()
    return container


class MiniSportify(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Mini Sportify")
        self.setWindowIcon(QIcon(music_icon))
        self.resize(800, 600)

        self.song_paths     = []
        self.song_id_map    = {}
        self.current_index  = -1
        self._user_dragging = False
        self._scanner       = None

        self.create_widgets()
        self.layout_widgets()
        self.connect_signals()
        self.view_btn.setChecked(True)
        self._load_saved_library()

    def create_widgets(self):
        self.sidebar_btn_wide   = QPushButton("")
        self.sidebar_btn_wide.setIcon(QIcon(QPixmap(menu_icon)))
        self.sidebar_btn_wide.setCheckable(True)

        self.sidebar_btn_narrow = QPushButton("")
        self.sidebar_btn_narrow.setIcon(QIcon(QPixmap(menu_icon)))
        self.sidebar_btn_narrow.setCheckable(True)

        self.view_btn     = QPushButton(QIcon(QPixmap(view_icon)), "view all")
        self.playlist_btn = QPushButton(QIcon(QPixmap(play_icon)), "playlist")
        self.add_btn      = QPushButton(QIcon(QPixmap(plus_icon)), "add")
        # self.mode_btn     = QPushButton("PushButton")

        for btn in (self.view_btn, self.playlist_btn, self.add_btn):
            btn.setCheckable(True)
            btn.setAutoExclusive(True)
            btn.setFixedHeight(40)
            btn.setStyleSheet(Btn_Style)
        # self.mode_btn.setFixedHeight(24)
        # self.mode_btn.setStyleSheet(Btn_Style)

        self.side_view = QPushButton()
        self.side_view.setIcon(QIcon(QPixmap(view_icon)))
        self.side_view.setCheckable(True)
        self.side_view.setAutoExclusive(True)
        self.side_view.setFixedSize(41, 40)
        self.side_view.setStyleSheet(Btn_Style)

        self.side_play = QPushButton()
        self.side_play.setIcon(QIcon(QPixmap(play_icon)))
        self.side_play.setCheckable(True)
        self.side_play.setAutoExclusive(True)
        self.side_play.setFixedSize(41, 40)
        self.side_play.setStyleSheet(Btn_Style)

        self.side_add = QPushButton()
        self.side_add.setIcon(QIcon(QPixmap(plus_icon)))
        self.side_add.setCheckable(True)
        self.side_add.setAutoExclusive(True)
        self.side_add.setFixedSize(41, 40)
        self.side_add.setStyleSheet(Btn_Style)

        # self.side_mode = QPushButton("P")
        # self.side_mode.setFixedSize(41, 24)
        # self.side_mode.setStyleSheet(Btn_Style)

        self.song_list = QListWidget()
        self.song_list.setStyleSheet(List_Style)

        self.rec_list = QListWidget()
        self.rec_list.setStyleSheet(Rec_Item_Style)
        self.rec_list.setMaximumHeight(180)

        self.now_playing_lbl = QLabel("Nothing playing")
        self.now_playing_lbl.setStyleSheet("font-size: 12px; color: rgb(100,100,100); padding: 4px;")
        self.now_playing_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.time_current = QLabel("0:00")
        self.time_current.setStyleSheet("font-size: 11px; color: rgb(100,100,100);")
        self.time_current.setFixedWidth(35)
        self.time_current.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.progress_bar = QSlider(Qt.Orientation.Horizontal)
        self.progress_bar.setRange(0, 1000)
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet(Slider_Style)

        self.time_total = QLabel("0:00")
        self.time_total.setStyleSheet("font-size: 11px; color: rgb(100,100,100);")
        self.time_total.setFixedWidth(35)

        self.btn_prev  = QPushButton("")
        self.btn_play  = QPushButton("")
        self.btn_pause = QPushButton("")
        self.btn_stop  = QPushButton("")
        self.btn_next  = QPushButton("")
        self.btn_like  = QPushButton("Like")

        self.btn_prev.setIcon(QIcon(QPixmap(backward_icon)))
        self.btn_play.setIcon(QIcon(QPixmap(playl_icon)))
        self.btn_pause.setIcon(QIcon(QPixmap(pause_icon)))
        self.btn_stop.setIcon(QIcon(QPixmap(stop_icon)))
        self.btn_next.setIcon(QIcon(QPixmap(forward_icon)))

        for btn in (self.btn_prev, self.btn_play, self.btn_pause,
                    self.btn_stop, self.btn_next, self.btn_like):
            btn.setFixedHeight(32)
            btn.setStyleSheet(Ctrl_Style)

        self.playlist_widget = QListWidget()
        self.playlist_widget.setStyleSheet(List_Style)

        self.btn_add_to_playlist = QPushButton("  Add selected to playlist")
        self.btn_add_to_playlist.setIcon(QIcon(QPixmap(plus_icon)))
        self.btn_add_to_playlist.setFixedHeight(30)
        self.btn_add_to_playlist.setStyleSheet(Ctrl_Style)

        self.btn_clear_playlist = QPushButton("  Clear playlist")
        self.btn_clear_playlist.setIcon(QIcon(QPixmap(trash_icon)))
        self.btn_clear_playlist.setFixedHeight(30)
        self.btn_clear_playlist.setStyleSheet(
            "QPushButton { background-color: rgb(230,180,180); border-radius: 6px;"
            " font-size: 12px; color: rgb(30,30,30); padding: 0 10px; }"
            "QPushButton:hover { background-color: rgb(210,150,150); }"
        )

        self.btn_browse = QPushButton(" Browse files…")
        self.btn_browse.setIcon(QIcon(QPixmap(view_icon)))
        self.btn_browse.setFixedSize(200, 40)
        self.btn_browse.setStyleSheet(Ctrl_Style)

        self.btn_browse_folder = QPushButton(" Add folder…")
        self.btn_browse_folder.setIcon(QIcon(QPixmap(plus_icon)))
        self.btn_browse_folder.setFixedSize(200, 40)
        self.btn_browse_folder.setStyleSheet(Ctrl_Style)

        self.btn_rescan = QPushButton(" Rescan folders")
        self.btn_rescan.setIcon(QIcon(QPixmap(plus_icon)))
        self.btn_rescan.setFixedSize(200, 40)
        self.btn_rescan.setStyleSheet(Ctrl_Style)

        self.btn_clean_missing = QPushButton(" Remove missing files")
        self.btn_clean_missing.setIcon(QIcon(QPixmap(trash_icon)))
        self.btn_clean_missing.setFixedSize(200, 40)
        self.btn_clean_missing.setStyleSheet(Ctrl_Style)

        self.add_status_lbl = QLabel("No songs loaded yet.")
        self.add_status_lbl.setStyleSheet("font-size: 12px; color: rgb(100,100,100); margin-top: 12px;")

        self.folder_list = QListWidget()
        self.folder_list.setStyleSheet(List_Style)
        self.folder_list.setMaximumHeight(130)

        self.player       = QMediaPlayer(self)
        self.audio_output = QAudioOutput(self)
        self.audio_output.setVolume(0.7)
        self.player.setAudioOutput(self.audio_output)

    def layout_widgets(self):
        narrow_sidebar = QWidget()
        narrow_sidebar.setFixedWidth(41)
        narrow_sidebar.setStyleSheet(Sidebar_BG)
        nl = QVBoxLayout(narrow_sidebar)
        nl.setContentsMargins(0, 0, 0, 0)
        nl.setSpacing(0)
        nl.addWidget(self.sidebar_btn_narrow)
        nl.addWidget(self.side_view)
        nl.addWidget(self.side_play)
        nl.addWidget(self.side_add)
        nl.addStretch()
        # nl.addWidget(self.side_mode)

        wide_sidebar = QWidget()
        wide_sidebar.setFixedWidth(110)
        wide_sidebar.setStyleSheet(Sidebar_BG)
        wl = QVBoxLayout(wide_sidebar)
        wl.setContentsMargins(0, 0, 0, 0)
        wl.setSpacing(0)
        wl.addWidget(self.sidebar_btn_wide)
        wl.addWidget(self.view_btn)
        wl.addWidget(self.playlist_btn)
        wl.addWidget(self.add_btn)
        wl.addStretch()
        # wl.addWidget(self.mode_btn)

        page_view = QWidget()
        page_view.setStyleSheet(Content_BG)
        v1 = QVBoxLayout(page_view)
        v1.setContentsMargins(16, 16, 16, 16)
        v1.setSpacing(8)
        v1.addWidget(_header_widget(view_icon, "All Songs"))
        v1.addWidget(self.song_list, 1)
        v1.addWidget(_header_widget(play_icon, "Recommended for You"))
        v1.addWidget(self.rec_list)
        v1.addWidget(self.now_playing_lbl)

        progress_row = QHBoxLayout()
        progress_row.setSpacing(8)
        progress_row.addWidget(self.time_current)
        progress_row.addWidget(self.progress_bar)
        progress_row.addWidget(self.time_total)
        v1.addLayout(progress_row)

        controls_row = QHBoxLayout()
        controls_row.setSpacing(8)
        for btn in (self.btn_prev, self.btn_play, self.btn_pause,
                    self.btn_stop, self.btn_next, self.btn_like):
            controls_row.addWidget(btn)
        v1.addLayout(controls_row)

        page_playlist = QWidget()
        page_playlist.setStyleSheet(Content_BG)
        v2 = QVBoxLayout(page_playlist)
        v2.setContentsMargins(16, 16, 16, 16)
        v2.setSpacing(8)
        v2.addWidget(_header_widget(play_icon, "Playlist"))
        v2.addWidget(self.playlist_widget)
        pl_btns = QHBoxLayout()
        pl_btns.addWidget(self.btn_add_to_playlist)
        pl_btns.addWidget(self.btn_clear_playlist)
        v2.addLayout(pl_btns)

        page_add = QWidget()
        page_add.setStyleSheet(Content_BG)
        v3 = QVBoxLayout(page_add)
        v3.setContentsMargins(16, 16, 16, 16)
        v3.setSpacing(8)
        v3.setAlignment(Qt.AlignmentFlag.AlignTop)
        v3.addWidget(_header_widget(plus_icon, "Add Music"))
        v3.addWidget(_header_widget(view_icon, "Saved Folders"))
        v3.addWidget(self.folder_list)
        v3.addWidget(self.btn_browse_folder)
        v3.addWidget(self.btn_rescan)
        v3.addWidget(self.btn_browse)
        v3.addWidget(self.btn_clean_missing)
        v3.addWidget(self.add_status_lbl)

        self.stack = QStackedWidget()
        self.stack.addWidget(page_view)
        self.stack.addWidget(page_playlist)
        self.stack.addWidget(page_add)

        self.wide_sidebar   = wide_sidebar
        self.narrow_sidebar = narrow_sidebar


        self.sidebar_btn_wide.setFixedSize(41, 30)
        self.sidebar_btn_wide.setStyleSheet(menu_btn_style)
        self.sidebar_btn_narrow.setFixedSize(41, 30)
        self.sidebar_btn_narrow.setStyleSheet(menu_btn_style)

        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(self.narrow_sidebar)
        root.addWidget(self.wide_sidebar)
        root.addWidget(self.stack, 1)

        self.narrow_sidebar.setVisible(False)
        self.wide_sidebar.setVisible(True)

    def connect_signals(self):
        self.sidebar_btn_wide.toggled.connect(self.toggle_sidebar)
        self.sidebar_btn_narrow.toggled.connect(self.toggle_sidebar)

        self.view_btn.toggled.connect(lambda c: self.show_page(0) if c else None)
        self.playlist_btn.toggled.connect(lambda c: self.show_page(1) if c else None)
        self.add_btn.toggled.connect(lambda c: self.show_page(2) if c else None)

        self.side_view.toggled.connect(lambda c: self.show_page(0) if c else None)
        self.side_play.toggled.connect(lambda c: self.show_page(1) if c else None)
        self.side_add.toggled.connect(lambda c: self.show_page(2) if c else None)

        self.view_btn.toggled.connect(self.side_view.setChecked)
        self.playlist_btn.toggled.connect(self.side_play.setChecked)
        self.add_btn.toggled.connect(self.side_add.setChecked)
        self.side_view.toggled.connect(self.view_btn.setChecked)
        self.side_play.toggled.connect(self.playlist_btn.setChecked)
        self.side_add.toggled.connect(self.add_btn.setChecked)
        # self.mode_btn.toggled.connect(self.side_mode.setChecked)
        # self.side_mode.toggled.connect(self.mode_btn.setChecked)

        self.btn_prev.clicked.connect(self.play_prev)
        self.btn_play.clicked.connect(self.play_current)
        self.btn_pause.clicked.connect(self.player.pause)
        self.btn_stop.clicked.connect(self.player.stop)
        self.btn_next.clicked.connect(self.play_next)
        self.btn_like.clicked.connect(self.toggle_like)

        self.btn_browse.clicked.connect(self.browse_files)
        self.btn_browse_folder.clicked.connect(self.browse_folder)
        self.btn_rescan.clicked.connect(self.rescan_folders)
        self.btn_clean_missing.clicked.connect(self.clean_missing)
        self.btn_add_to_playlist.clicked.connect(self.add_selected_to_playlist)
        self.btn_clear_playlist.clicked.connect(self.playlist_widget.clear)

        self.song_list.itemDoubleClicked.connect(self.on_song_double_clicked)
        self.playlist_widget.itemDoubleClicked.connect(self.on_playlist_double_clicked)
        self.rec_list.itemDoubleClicked.connect(self.on_rec_double_clicked)

        self.player.mediaStatusChanged.connect(self.on_media_status_changed)
        self.player.positionChanged.connect(self.on_position_changed)
        self.player.durationChanged.connect(self.on_duration_changed)

        self.progress_bar.sliderPressed.connect(self.on_slider_pressed)
        self.progress_bar.sliderReleased.connect(self.on_slider_released)

    def _load_saved_library(self):
        for row in db.get_all_songs():
            if os.path.exists(row["file_path"]):
                self._add_song_to_ui(row["file_path"], row["title"], row["artist"], row["id"])

        for folder in db.get_folders():
            self.folder_list.addItem(folder)

        total = len(self.song_paths)
        if total:
            self.add_status_lbl.setText(f"  {total} song{'s' if total != 1 else ''} loaded")

        self._refresh_recommendations()

    def _add_song_to_ui(self, file_path, title, artist, song_id=None):
        if file_path in self.song_paths:
            return
        self.song_paths.append(file_path)
        label = f"{title}  -  {artist}" if artist else title
        item  = QListWidgetItem(label)
        item.setData(Qt.ItemDataRole.UserRole, file_path)
        self.song_list.addItem(item)
        if song_id is not None:
            self.song_id_map[file_path] = song_id

    def _refresh_recommendations(self):
        self.rec_list.clear()
        recs = recommender.get_recommendations(10)
        for r in recs:
            if not os.path.exists(r["file_path"]):
                continue
            label = f"♪  {r['title']}  -  {r['artist']}   ({r['reason']})"
            item  = QListWidgetItem(label)
            item.setData(Qt.ItemDataRole.UserRole, r["file_path"])
            item.setData(Qt.ItemDataRole.UserRole + 1, r["title"])
            self.rec_list.addItem(item)

    def toggle_sidebar(self, collapsed):
        self.wide_sidebar.setVisible(not collapsed)
        self.narrow_sidebar.setVisible(collapsed)
        self.sidebar_btn_wide.setChecked(collapsed)
        self.sidebar_btn_narrow.setChecked(collapsed)

    def show_page(self, index):
        self.stack.setCurrentIndex(index)

    def browse_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "Pick audio files", "",
            "Audio Files (*.mp3 *.wav *.ogg *.flac *.m4a *.aac)"
        )
        if not files:
            return
        results = scan_single_files(files)
        for song_id, meta in results:
            self._add_song_to_ui(meta["file_path"], meta["title"], meta["artist"], song_id)
        total = len(self.song_paths)
        self.add_status_lbl.setText(f"  {total} song{'s' if total != 1 else ''} loaded")
        self._refresh_recommendations()

    def browse_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select music folder")
        if not folder:
            return
        db.add_folder(folder)
        if self.folder_list.findItems(folder, Qt.MatchFlag.MatchExactly) == []:
            self.folder_list.addItem(folder)
        self._start_folder_scan([folder])

    def rescan_folders(self):
        folders = db.get_folders()
        if not folders:
            self.add_status_lbl.setText("No saved folders to rescan.")
            return
        self._start_folder_scan(folders)

    def _start_folder_scan(self, folders):
        if self._scanner and self._scanner.isRunning():
            return
        self.add_status_lbl.setText("Scanning…")
        self._scanner = LibraryScannerThread(folders, self)
        self._scanner.song_found.connect(self._on_scanner_song_found)
        self._scanner.scan_done.connect(self._on_scan_done)
        self._scanner.scan_error.connect(self._on_scan_error)
        self._scanner.start()

    def _on_scanner_song_found(self, song_id, meta):
        self._add_song_to_ui(meta["file_path"], meta["title"], meta["artist"], song_id)

    def _on_scan_done(self, total):
        self.add_status_lbl.setText(f"  Scan complete — {len(self.song_paths)} songs total")
        self._refresh_recommendations()

    def _on_scan_error(self, msg):
        self.add_status_lbl.setText(f"error  {msg}")

    def clean_missing(self):
        missing = db.find_missing_files()
        if not missing:
            QMessageBox.information(self, "Clean library", "No missing files found.")
            return
        for path in missing:
            db.delete_song(path)
            if path in self.song_paths:
                self.song_paths.remove(path)
            for i in range(self.song_list.count()):
                if self.song_list.item(i).data(Qt.ItemDataRole.UserRole) == path:
                    self.song_list.takeItem(i)
                    break
        self.add_status_lbl.setText(f"🗑  Removed {len(missing)} missing file(s)")
        self._refresh_recommendations()

    def add_selected_to_playlist(self):
        for item in self.song_list.selectedItems():
            new_item = QListWidgetItem(item.text())
            new_item.setData(Qt.ItemDataRole.UserRole, item.data(Qt.ItemDataRole.UserRole))
            self.playlist_widget.addItem(new_item)

    def on_song_double_clicked(self, item):
        self.current_index = self.song_list.row(item)
        self.load_and_play(item.data(Qt.ItemDataRole.UserRole), item.text())

    def on_playlist_double_clicked(self, item):
        self.load_and_play(item.data(Qt.ItemDataRole.UserRole), item.text())

    def on_rec_double_clicked(self, item):
        path  = item.data(Qt.ItemDataRole.UserRole)
        label = item.text()
        for i in range(self.song_list.count()):
            if self.song_list.item(i).data(Qt.ItemDataRole.UserRole) == path:
                self.current_index = i
                break
        self.load_and_play(path, label)

    def load_and_play(self, path, label):
        self.player.setSource(QUrl.fromLocalFile(path))
        self.player.play()
        self.now_playing_lbl.setText(f"  {label}")
        song_id = self.song_id_map.get(path)
        if song_id is None:
            row = db.get_song_by_path(path)
            if row:
                song_id = row["id"]
                self.song_id_map[path] = song_id
        if song_id is not None:
            db.record_play(song_id)
            QTimer.singleShot(500, self._refresh_recommendations)

    def toggle_like(self):
        item = self.song_list.currentItem()
        if not item:
            return
        path    = item.data(Qt.ItemDataRole.UserRole)
        song_id = self.song_id_map.get(path)
        if song_id is None:
            row = db.get_song_by_path(path)
            if row:
                song_id = row["id"]
                self.song_id_map[path] = song_id
        if song_id is None:
            return
        history = db.get_history()
        current_liked = next(
            (bool(r["liked"]) for r in history if r["song_id"] == song_id), False
        )
        db.set_liked(song_id, not current_liked)
        self.btn_like.setText("♥ Liked" if not current_liked else "♡ Like")
        self._refresh_recommendations()

    def play_current(self):
        if self.current_index == -1 and self.song_paths:
            self.current_index = 0
            self.song_list.setCurrentRow(0)
            item = self.song_list.item(0)
            self.load_and_play(item.data(Qt.ItemDataRole.UserRole), item.text())
        else:
            self.player.play()

    def play_prev(self):
        if not self.song_paths:
            return
        self.current_index = max(0, self.current_index - 1)
        self.play_by_index(self.current_index)

    def play_next(self):
        if not self.song_paths:
            return
        self.current_index = min(len(self.song_paths) - 1, self.current_index + 1)
        self.play_by_index(self.current_index)

    def play_by_index(self, idx):
        item = self.song_list.item(idx)
        if item is None:
            return
        self.song_list.setCurrentRow(idx)
        self.load_and_play(item.data(Qt.ItemDataRole.UserRole), item.text())

    def on_media_status_changed(self, status):
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            self.play_next()

    @staticmethod
    def ms_to_str(ms):
        if ms <= 0:
            return "0:00"
        s = ms // 1000
        return f"{s // 60}:{s % 60:02d}"

    def on_position_changed(self, position_ms):
        if not self._user_dragging:
            duration = self.player.duration()
            if duration > 0:
                self.progress_bar.setValue(int(position_ms / duration * 1000))
            self.time_current.setText(self.ms_to_str(position_ms))

    def on_duration_changed(self, duration_ms):
        self.time_total.setText(self.ms_to_str(duration_ms))
        self.progress_bar.setValue(0)

    def on_slider_pressed(self):
        self._user_dragging = True

    def on_slider_released(self):
        self._user_dragging = False
        duration = self.player.duration()
        if duration > 0:
            self.player.setPosition(int(self.progress_bar.value() / 1000 * duration))


if __name__ == "__main__":
    app    = QApplication(sys.argv)
    window = MiniSportify()
    window.show()
    sys.exit(app.exec())
