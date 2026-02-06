#!/usr/bin/env python3
"""
Music Downloader GUI - Final Version
- Multi-language: English, Español, Français
- Spotify-inspired color scheme (black/green)
- Auto URL cleaning
- Emoji in text (not buttons)
- Yellow log text (friendlier than green Matrix style)
"""

import sys
import re
from pathlib import Path
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QProgressBar, QTextEdit, QFileDialog,
    QCheckBox, QLineEdit, QGroupBox, QMessageBox, QComboBox, QScrollArea
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont

from translations import Translator
from parse_spotify_playlist import parse_spotify_playlist
from download_music import download_from_csv


def clean_spotify_url(url):
    """
    Очищает Spotify URL от мусора (utm метки, случайные символы)

    Examples:
        https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M/sdfsdf
        → https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M

        https://open.spotify.com/playlist/ABC123?si=xyz&utm_source=copy-link
        → https://open.spotify.com/playlist/ABC123
    """
    pattern = r'(https://open\.spotify\.com/playlist/[\w\-]+)'
    match = re.search(pattern, url)

    if match:
        return match.group(1)
    return url


class ParseThread(QThread):
    """Thread for parsing Spotify playlist"""

    log = pyqtSignal(str)
    finished = pyqtSignal(bool, str, list)

    def __init__(self, playlist_url, translator):
        super().__init__()
        self.playlist_url = playlist_url
        self.tr = translator
        self._is_running = True

    def run(self):
        try:
            self.log.emit(f"🔍 {self.tr.tr('log_opening_playlist', url=self.playlist_url)}")

            from playwright.sync_api import sync_playwright
            import time

            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.set_viewport_size({"width": 1920, "height": 5000})

                self.log.emit(f"📡 {self.tr.tr('log_loading_page')}")
                page.goto(self.playlist_url, wait_until='domcontentloaded')
                page.wait_for_selector('[data-testid="tracklist-row"]', timeout=10000)
                time.sleep(3)

                playlist_name = "playlist"
                try:
                    h1_elements = page.locator('h1').all()
                    for h1 in h1_elements:
                        text = h1.inner_text().strip()
                        if text and text != "Your Library" and len(text) > 0:
                            playlist_name = text
                            break
                    self.log.emit(f"📀 {self.tr.tr('log_playlist_name', name=playlist_name)}")
                except:
                    pass

                self.log.emit(f"📜 {self.tr.tr('log_loading_tracks')}")
                previous_count = 0
                no_change_count = 0

                for scroll_attempt in range(100):
                    if not self._is_running:
                        browser.close()
                        self.finished.emit(False, "", [])
                        return

                    current_tracks = page.locator('[data-testid="tracklist-row"]').count()

                    if scroll_attempt % 10 == 0:
                        self.log.emit(f"   {self.tr.tr('log_tracks_loaded', count=current_tracks)}")

                    has_recommended = page.locator('h2:has-text("Recommended")').count() > 0
                    if has_recommended:
                        self.log.emit(f"📌 {self.tr.tr('log_recommended_found')}")
                        break

                    if current_tracks == previous_count:
                        no_change_count += 1
                        if no_change_count >= 10:
                            self.log.emit(f"✓ {self.tr.tr('log_all_tracks_loaded', count=current_tracks)}")
                            break
                    else:
                        no_change_count = 0

                    previous_count = current_tracks
                    page.evaluate("window.scrollBy(0, 1000)")
                    time.sleep(0.5)

                songs = []
                all_track_rows = page.locator('[data-testid="tracklist-row"]').all()
                self.log.emit(f"🎵 {self.tr.tr('log_parsing_tracks', count=len(all_track_rows))}")

                last_track_number = 0
                for idx, row in enumerate(all_track_rows):
                    if not self._is_running:
                        break

                    try:
                        try:
                            track_number_elem = row.locator('[aria-colindex="1"]').first
                            track_number_text = track_number_elem.inner_text().strip()

                            if track_number_text.isdigit():
                                current_number = int(track_number_text)
                                if last_track_number > 0 and current_number != last_track_number + 1:
                                    break
                                last_track_number = current_number
                            else:
                                if len(songs) > 0:
                                    break
                        except:
                            if len(songs) > 0:
                                break

                        track_name_elem = row.locator('[data-testid="internal-track-link"]').first
                        track_name = track_name_elem.inner_text() if track_name_elem.count() > 0 else ""

                        artist_links = row.locator('a[href*="/artist/"]').all()
                        artists = []
                        for artist_link in artist_links:
                            artist_text = artist_link.inner_text()
                            if artist_text and artist_text not in artists:
                                artists.append(artist_text)
                        artist_name = ', '.join(artists) if artists else ""

                        album_elem = row.locator('a[href*="/album/"]').first
                        album_name = album_elem.inner_text() if album_elem.count() > 0 else ""

                        if track_name:
                            songs.append({
                                '№': str(len(songs) + 1),
                                'Песня': track_name,
                                'Артист': artist_name,
                                'Альбом': album_name
                            })

                            if len(songs) % 10 == 0:
                                self.log.emit(f"   {self.tr.tr('log_processed_tracks', count=len(songs))}")

                    except:
                        if len(songs) > 0:
                            break
                        continue

                browser.close()

            if not songs:
                self.finished.emit(False, "", [])
                return

            self.log.emit(f"✅ {self.tr.tr('log_tracks_found', count=len(songs))}")
            self.finished.emit(True, playlist_name, songs)

        except Exception as e:
            self.log.emit(f"❌ {self.tr.tr('log_parse_error', error=str(e))}")
            self.finished.emit(False, "", [])

    def stop(self):
        self._is_running = False


class DownloadThread(QThread):
    """Thread for downloading music"""

    progress = pyqtSignal(int, int)
    log = pyqtSignal(str)
    finished = pyqtSignal(bool, str)

    def __init__(self, songs, output_dir, normalize, translator):
        super().__init__()
        self.songs = songs
        self.output_dir = output_dir
        self.normalize = normalize
        self.tr = translator
        self._is_running = True

    def run(self):
        try:
            import csv
            import tempfile

            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv', encoding='utf-8') as tmp:
                tmp.write(f"# Playlist: Spotify Playlist\n")
                writer = csv.DictWriter(tmp, fieldnames=['№', 'Песня', 'Артист', 'Альбом'])
                writer.writeheader()
                writer.writerows(self.songs)
                tmp_path = tmp.name

            self.log.emit(f"📂 {self.tr.tr('log_starting_download', count=len(self.songs))}")
            self.log.emit(f"📁 {self.tr.tr('log_saving_to', folder=self.output_dir)}\n")

            # Колбэки для прогресса и лога
            def on_progress(current, total):
                if self._is_running:
                    self.progress.emit(current, total)

            def on_log(message):
                if self._is_running:
                    self.log.emit(message)

            download_from_csv(
                tmp_path,
                self.output_dir,
                normalize=self.normalize,
                progress_callback=on_progress,
                log_callback=on_log,
                stop_check=lambda: not self._is_running
            )
            Path(tmp_path).unlink()

            if self._is_running:
                success_msg = f"✅ Downloaded {len(self.songs)} tracks successfully!"
                self.finished.emit(True, success_msg)

        except Exception as e:
            self.log.emit(f"❌ {self.tr.tr('log_download_error', error=str(e))}")
            self.finished.emit(False, f"Error: {str(e)}")

    def stop(self):
        self._is_running = False


class MusicDownloaderGUI(QMainWindow):
    """Main application window"""

    # Spotify color scheme
    SPOTIFY_BLACK = "#191414"
    SPOTIFY_GREEN = "#1DB954"
    SPOTIFY_DARK_GRAY = "#282828"
    SPOTIFY_LIGHT_GRAY = "#B3B3B3"
    SPOTIFY_WHITE = "#FFFFFF"

    def __init__(self):
        super().__init__()
        self.tr = Translator('en')
        self.playlist_url = None
        self.songs = []
        self.playlist_name = ""
        self.parse_thread = None
        self.download_thread = None
        self.init_ui()

    def init_ui(self):
        """Initialize UI"""
        self.setWindowTitle(self.tr.tr('window_title'))
        self.setGeometry(100, 100, 900, 650)
        self.setMinimumSize(850, 600)

        # Main widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)

        # Language selector
        lang_layout = QHBoxLayout()
        lang_layout.addStretch()
        lang_label = QLabel(self.tr.tr('language'))
        lang_label.setStyleSheet(f"color: {self.SPOTIFY_LIGHT_GRAY};")
        lang_layout.addWidget(lang_label)

        self.lang_combo = QComboBox()
        self.lang_combo.addItem("English", "en")
        self.lang_combo.addItem("Español", "es")
        self.lang_combo.addItem("Français", "fr")
        self.lang_combo.currentIndexChanged.connect(self.change_language)
        self.lang_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {self.SPOTIFY_DARK_GRAY};
                color: {self.SPOTIFY_WHITE};
                border: 1px solid {self.SPOTIFY_GREEN};
                padding: 5px;
                border-radius: 4px;
            }}
            QComboBox::drop-down {{
                border: none;
            }}
            QComboBox QAbstractItemView {{
                background-color: {self.SPOTIFY_DARK_GRAY};
                color: {self.SPOTIFY_WHITE};
                selection-background-color: {self.SPOTIFY_GREEN};
            }}
        """)
        lang_layout.addWidget(self.lang_combo)
        main_layout.addLayout(lang_layout)

        # Title
        self.title_label = QLabel(self.tr.tr('app_title'))
        title_font = QFont()
        title_font.setPointSize(20)
        title_font.setBold(True)
        self.title_label.setFont(title_font)
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet(f"color: {self.SPOTIFY_GREEN}; margin: 8px 0 5px 0;")
        main_layout.addWidget(self.title_label)

        self.subtitle_label = QLabel(self.tr.tr('app_subtitle'))
        self.subtitle_label.setAlignment(Qt.AlignCenter)
        self.subtitle_label.setStyleSheet(f"color: {self.SPOTIFY_LIGHT_GRAY}; font-size: 12px; margin-bottom: 10px;")
        main_layout.addWidget(self.subtitle_label)

        # URL Input
        self.url_group = QGroupBox(self.tr.tr('url_group_title'))
        url_layout = QVBoxLayout()

        url_input_layout = QHBoxLayout()
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText(self.tr.tr('url_placeholder'))
        self.url_input.textChanged.connect(self.on_url_changed)
        self.url_input.setMinimumHeight(40)
        self.url_input.setStyleSheet(f"""
            QLineEdit {{
                padding: 10px;
                font-size: 13px;
                background-color: {self.SPOTIFY_DARK_GRAY};
                color: {self.SPOTIFY_WHITE};
                border: 2px solid {self.SPOTIFY_DARK_GRAY};
                border-radius: 5px;
            }}
            QLineEdit:focus {{
                border: 2px solid {self.SPOTIFY_GREEN};
            }}
        """)
        url_input_layout.addWidget(self.url_input)

        self.paste_btn = QPushButton(self.tr.tr('btn_paste'))
        self.paste_btn.clicked.connect(self.paste_url)
        self.paste_btn.setMaximumWidth(100)
        self.paste_btn.setMinimumHeight(40)
        self.paste_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.SPOTIFY_DARK_GRAY};
                color: {self.SPOTIFY_WHITE};
                border: 2px solid {self.SPOTIFY_GREEN};
                padding: 10px;
                border-radius: 5px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {self.SPOTIFY_GREEN};
                color: {self.SPOTIFY_BLACK};
            }}
        """)
        url_input_layout.addWidget(self.paste_btn)
        url_layout.addLayout(url_input_layout)

        self.example_label = QLabel(self.tr.tr('url_example'))
        self.example_label.setStyleSheet(f"color: {self.SPOTIFY_LIGHT_GRAY}; font-size: 10px; font-style: italic; margin-top: 3px;")
        url_layout.addWidget(self.example_label)

        self.url_group.setLayout(url_layout)
        main_layout.addWidget(self.url_group)

        # Playlist Info
        self.playlist_info = QLabel(self.tr.tr('url_invalid'))
        self.playlist_info.setStyleSheet(f"""
            color: {self.SPOTIFY_LIGHT_GRAY};
            font-style: italic;
            padding: 8px;
            background-color: {self.SPOTIFY_DARK_GRAY};
            border-radius: 4px;
            margin: 5px 0;
            font-size: 12px;
        """)
        self.playlist_info.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.playlist_info)

        # Settings
        self.settings_group = QGroupBox(self.tr.tr('settings_group_title'))
        settings_layout = QVBoxLayout()

        path_layout = QHBoxLayout()
        self.output_label = QLabel(self.tr.tr('output_folder_label'))
        self.output_label.setStyleSheet(f"color: {self.SPOTIFY_WHITE};")
        path_layout.addWidget(self.output_label)

        self.output_path = QLineEdit()
        self.output_path.setText(str(Path.home() / "Music" / "Spotify Downloads"))
        self.output_path.setMinimumHeight(32)
        self.output_path.setStyleSheet(f"""
            QLineEdit {{
                padding: 8px;
                background-color: {self.SPOTIFY_DARK_GRAY};
                color: {self.SPOTIFY_WHITE};
                border: 1px solid {self.SPOTIFY_DARK_GRAY};
                border-radius: 4px;
            }}
        """)
        path_layout.addWidget(self.output_path)

        self.path_browse = QPushButton(self.tr.tr('btn_browse'))
        self.path_browse.clicked.connect(self.browse_output_dir)
        self.path_browse.setMaximumWidth(100)
        self.path_browse.setMinimumHeight(32)
        self.path_browse.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.SPOTIFY_DARK_GRAY};
                color: {self.SPOTIFY_WHITE};
                border: 1px solid {self.SPOTIFY_GREEN};
                padding: 8px;
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background-color: {self.SPOTIFY_GREEN};
                color: {self.SPOTIFY_BLACK};
            }}
        """)
        path_layout.addWidget(self.path_browse)
        settings_layout.addLayout(path_layout)

        self.normalize_checkbox = QCheckBox(self.tr.tr('normalize_checkbox'))
        self.normalize_checkbox.setChecked(True)
        self.normalize_checkbox.setStyleSheet(f"""
            QCheckBox {{
                color: {self.SPOTIFY_WHITE};
                margin-top: 8px;
            }}
            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
                border: 2px solid {self.SPOTIFY_GREEN};
                border-radius: 3px;
                background-color: {self.SPOTIFY_DARK_GRAY};
            }}
            QCheckBox::indicator:checked {{
                background-color: {self.SPOTIFY_GREEN};
                image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iMTAiIHZpZXdCb3g9IjAgMCAxMiAxMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cGF0aCBkPSJNMSA1TDQgOEwxMSAxIiBzdHJva2U9ImJsYWNrIiBzdHJva2Utd2lkdGg9IjIiIGZpbGw9Im5vbmUiLz48L3N2Zz4=);
            }}
        """)
        settings_layout.addWidget(self.normalize_checkbox)

        self.settings_group.setLayout(settings_layout)
        main_layout.addWidget(self.settings_group)

        # Progress
        self.progress_group = QGroupBox(self.tr.tr('progress_group_title'))
        progress_layout = QVBoxLayout()

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                border: 2px solid {self.SPOTIFY_DARK_GRAY};
                border-radius: 5px;
                text-align: center;
                height: 28px;
                background-color: {self.SPOTIFY_DARK_GRAY};
                color: {self.SPOTIFY_WHITE};
            }}
            QProgressBar::chunk {{
                background-color: {self.SPOTIFY_GREEN};
                border-radius: 3px;
            }}
        """)
        progress_layout.addWidget(self.progress_bar)

        self.progress_label = QLabel(self.tr.tr('status_ready'))
        self.progress_label.setAlignment(Qt.AlignCenter)
        self.progress_label.setStyleSheet(f"font-weight: bold; margin-top: 5px; color: {self.SPOTIFY_WHITE};")
        progress_layout.addWidget(self.progress_label)

        self.progress_group.setLayout(progress_layout)
        main_layout.addWidget(self.progress_group)

        # Log
        self.log_group = QGroupBox(self.tr.tr('log_group_title'))
        log_layout = QVBoxLayout()

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMinimumHeight(80)
        self.log_text.setMaximumHeight(80)
        self.log_text.setStyleSheet(f"""
            QTextEdit {{
                background-color: {self.SPOTIFY_BLACK};
                color: #FFD700;
                font-family: 'Courier New', monospace;
                font-size: 11px;
                padding: 8px;
                border: 1px solid {self.SPOTIFY_DARK_GRAY};
                border-radius: 4px;
            }}
        """)
        log_layout.addWidget(self.log_text)

        self.log_group.setLayout(log_layout)
        main_layout.addWidget(self.log_group)

        # Buttons
        buttons_layout = QHBoxLayout()

        self.download_btn = QPushButton(self.tr.tr('btn_download'))
        self.download_btn.setEnabled(False)
        self.download_btn.clicked.connect(self.start_download)
        self.download_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.SPOTIFY_GREEN};
                color: {self.SPOTIFY_BLACK};
                border: none;
                padding: 12px;
                border-radius: 20px;
                font-size: 14px;
                font-weight: bold;
            }}
            QPushButton:hover:enabled {{
                background-color: #1ED760;
            }}
            QPushButton:disabled {{
                background-color: {self.SPOTIFY_DARK_GRAY};
                color: {self.SPOTIFY_LIGHT_GRAY};
            }}
        """)
        buttons_layout.addWidget(self.download_btn)

        self.cancel_btn = QPushButton(self.tr.tr('btn_cancel'))
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.clicked.connect(self.cancel_operation)
        self.cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #ff4444;
                color: white;
                border: none;
                padding: 12px;
                border-radius: 20px;
                font-size: 14px;
                font-weight: bold;
            }}
            QPushButton:hover:enabled {{
                background-color: #ff6666;
            }}
            QPushButton:disabled {{
                background-color: {self.SPOTIFY_DARK_GRAY};
                color: {self.SPOTIFY_LIGHT_GRAY};
            }}
        """)
        buttons_layout.addWidget(self.cancel_btn)

        main_layout.addLayout(buttons_layout)

        # Window style
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {self.SPOTIFY_BLACK};
            }}
            QWidget {{
                background-color: {self.SPOTIFY_BLACK};
            }}
            QGroupBox {{
                font-weight: bold;
                font-size: 12px;
                border: 2px solid {self.SPOTIFY_DARK_GRAY};
                border-radius: 6px;
                margin-top: 8px;
                padding-top: 10px;
                color: {self.SPOTIFY_WHITE};
                background-color: {self.SPOTIFY_BLACK};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 6px;
                color: {self.SPOTIFY_GREEN};
            }}
        """)

    def change_language(self, index):
        """Change interface language"""
        lang_code = self.lang_combo.itemData(index)
        self.tr.set_language(lang_code)
        self.update_ui_text()

    def update_ui_text(self):
        """Update all UI text with current language"""
        self.setWindowTitle(self.tr.tr('window_title'))
        self.title_label.setText(self.tr.tr('app_title'))
        self.subtitle_label.setText(self.tr.tr('app_subtitle'))
        self.url_group.setTitle(self.tr.tr('url_group_title'))
        self.url_input.setPlaceholderText(self.tr.tr('url_placeholder'))
        self.paste_btn.setText(self.tr.tr('btn_paste'))
        self.example_label.setText(self.tr.tr('url_example'))
        self.settings_group.setTitle(self.tr.tr('settings_group_title'))
        self.output_label.setText(self.tr.tr('output_folder_label'))
        self.path_browse.setText(self.tr.tr('btn_browse'))
        self.normalize_checkbox.setText(self.tr.tr('normalize_checkbox'))
        self.progress_group.setTitle(self.tr.tr('progress_group_title'))
        self.log_group.setTitle(self.tr.tr('log_group_title'))
        self.download_btn.setText(self.tr.tr('btn_download'))
        self.cancel_btn.setText(self.tr.tr('btn_cancel'))

        if not self.playlist_url:
            self.playlist_info.setText(self.tr.tr('url_invalid'))
        else:
            self.playlist_info.setText(self.tr.tr('url_valid'))

    def paste_url(self):
        """Paste URL from clipboard"""
        clipboard = QApplication.clipboard()
        text = clipboard.text()
        if text:
            self.url_input.setText(text.strip())

    def on_url_changed(self, text):
        """Handle URL change with auto-cleaning"""
        cleaned_url = clean_spotify_url(text.strip())

        spotify_pattern = r'^https://open\.spotify\.com/playlist/[\w\-]+$'
        if re.match(spotify_pattern, cleaned_url):
            # Если URL был изменен, обновляем поле ввода
            if cleaned_url != text.strip():
                self.url_input.blockSignals(True)
                self.url_input.setText(cleaned_url)
                self.url_input.blockSignals(False)

            self.playlist_url = cleaned_url
            self.playlist_info.setText(self.tr.tr('url_valid'))
            self.playlist_info.setStyleSheet(f"""
                color: {self.SPOTIFY_BLACK};
                background-color: {self.SPOTIFY_GREEN};
                border: 1px solid {self.SPOTIFY_GREEN};
                padding: 8px;
                border-radius: 4px;
                margin: 5px 0;
                font-weight: bold;
                font-size: 12px;
            """)
            self.download_btn.setEnabled(True)
        else:
            self.playlist_url = None
            self.playlist_info.setText(self.tr.tr('url_invalid'))
            self.playlist_info.setStyleSheet(f"""
                color: {self.SPOTIFY_LIGHT_GRAY};
                font-style: italic;
                padding: 15px;
                background-color: {self.SPOTIFY_DARK_GRAY};
                border-radius: 5px;
                margin: 10px 0;
            """)
            self.download_btn.setEnabled(False)

    def browse_output_dir(self):
        """Browse for output directory"""
        dir_path = QFileDialog.getExistingDirectory(
            self,
            self.tr.tr('output_folder_label'),
            str(Path.home())
        )
        if dir_path:
            self.output_path.setText(dir_path)

    def log_message(self, message):
        """Add message to log"""
        self.log_text.append(message)

    def start_download(self):
        """Start process: parse -> download"""
        if not self.playlist_url:
            QMessageBox.warning(self, self.tr.tr('error_title'), self.tr.tr('error_no_url'))
            return

        self.download_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)
        self.url_input.setEnabled(False)

        self.log_text.clear()
        self.progress_bar.setValue(0)
        self.progress_label.setText(self.tr.tr('status_parsing'))

        self.parse_thread = ParseThread(self.playlist_url, self.tr)
        self.parse_thread.log.connect(self.log_message)
        self.parse_thread.finished.connect(self.on_parse_finished)
        self.parse_thread.start()

        self.log_message(f"🚀 {self.tr.tr('log_starting_parse')}")

    def on_parse_finished(self, success, playlist_name, songs):
        """Parsing finished, start download"""
        if not success or not songs:
            self.log_message(f"❌ {self.tr.tr('log_parse_failed')}")
            QMessageBox.warning(self, self.tr.tr('error_title'), self.tr.tr('error_parse_failed'))
            self.reset_ui()
            return

        self.songs = songs
        self.playlist_name = playlist_name
        self.progress_bar.setValue(20)

        self.log_message(f"\n✅ {self.tr.tr('log_playlist_recognized', name=playlist_name)}")
        self.log_message(f"📊 {self.tr.tr('log_tracks_to_download', count=len(songs))}\n")
        self.progress_label.setText(self.tr.tr('log_found_tracks', count=len(songs)))

        output_dir = self.output_path.text()
        if not output_dir:
            output_dir = str(Path.home() / "Music" / "Spotify Downloads")

        self.download_thread = DownloadThread(self.songs, output_dir, self.normalize_checkbox.isChecked(), self.tr)
        self.download_thread.log.connect(self.log_message)
        self.download_thread.progress.connect(self.update_progress)
        self.download_thread.finished.connect(self.on_download_finished)
        self.download_thread.start()

    def update_progress(self, current, total):
        """Update download progress"""
        progress = int(20 + (current / total) * 80)
        self.progress_bar.setValue(progress)
        self.progress_label.setText(self.tr.tr('status_downloading', current=current, total=total))

    def on_download_finished(self, success, message):
        """Download finished"""
        self.log_message(f"\n{message}")

        if success:
            self.progress_bar.setValue(100)
            self.progress_label.setText(self.tr.tr('status_done'))
            QMessageBox.information(
                self,
                self.tr.tr('success_title'),
                self.tr.tr('success_message', message=message, folder=self.output_path.text())
            )
        else:
            QMessageBox.warning(self, self.tr.tr('error_title'), message)

        self.reset_ui()

    def cancel_operation(self):
        """Cancel operation"""
        if self.parse_thread and self.parse_thread.isRunning():
            self.log_message(f"⏸️ {self.tr.tr('log_stopping_parse')}")
            self.parse_thread.stop()
            # Не ждем синхронно, чтобы не зависнуть
            self.parse_thread.quit()

        if self.download_thread and self.download_thread.isRunning():
            self.log_message(f"⏸️ {self.tr.tr('log_stopping_download')}")
            self.download_thread.stop()
            # Не ждем синхронно
            self.download_thread.quit()

        self.reset_ui()
        QApplication.processEvents()  # Обработать события GUI

    def reset_ui(self):
        """Reset UI to initial state"""
        self.download_btn.setEnabled(bool(self.playlist_url))
        self.cancel_btn.setEnabled(False)
        self.url_input.setEnabled(True)


def main():
    """Launch application"""
    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    window = MusicDownloaderGUI()
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
