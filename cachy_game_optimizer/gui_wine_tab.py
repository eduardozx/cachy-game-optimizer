"""
CachyOS Game Optimizer - Wine/Proton Downloads Tab
Isolated UI component for managing Wine/Proton versions.
"""

from pathlib import Path
from typing import List, Optional

from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QPushButton,
    QLabel,
    QComboBox,
    QProgressBar,
    QGroupBox,
    QFormLayout,
    QMessageBox,
    QAbstractItemView,
    QMenu,
)
from PyQt6.QtGui import QFont, QColor, QAction

from .wine_downloader import (
    WineProtonDownloader,
    ToolType,
    Release,
    ReleaseAsset,
    DownloadProgress,
    format_changelog,
    format_file_size,
    RateLimitError,
    NetworkError,
    GitHubAPIError,
)
from .workers.wine_download_worker import WineDownloadWorker


# Theme constants (matching main gui.py)
KALI_GREEN = "#00ff88"
KALI_GREEN_DIM = "#00cc66"
KALI_GREEN_DARK = "#008844"
KALI_BG = "#0d0d0d"
KALI_BG_LIGHT = "#1a1a1a"
KALI_BG_CARD = "#111111"
KALI_BORDER = "#00ff88"
KALI_TEXT = "#d4d4d4"
KALI_TEXT_DIM = "#888888"
KALI_RED = "#ff4444"
KALI_YELLOW = "#ccaa00"
KALI_BLUE = "#0099cc"


class WineProtonTab(QWidget):
    """Wine/Proton Downloads management tab."""

    # Signal to communicate with main window log panel
    log_message = pyqtSignal(str)
    # Signal emitted when a download completes successfully (for auto-refresh of version lists)
    downloads_updated = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.downloader = WineProtonDownloader()
        self.current_tool_type = ToolType.PROTON_GE
        self.releases: List[Release] = []
        self.download_worker: Optional[WineDownloadWorker] = None
        self.destination_dir = Path.home() / ".local" / "share" / "cachy-game-optimizer" / "compat" / "tools"
        self._refresh_timer: Optional[QTimer] = None

        self.setup_ui()
        self.apply_style()
        self.load_releases()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(12, 12, 12, 12)

        # ===== Header =====
        header = QHBoxLayout()
        title = QLabel("📦 WINE / PROTON DOWNLOADS")
        title.setObjectName("title")
        title.setStyleSheet(f"color: {KALI_GREEN}; font-size: 18px; font-weight: bold;")
        header.addWidget(title)
        header.addStretch()

        # Tool type selector
        self.tool_selector = QComboBox()
        self.tool_selector.addItems(["🍷 Proton-GE", "🍾 Wine-GE"])
        self.tool_selector.setCurrentIndex(0)
        self.tool_selector.setFixedWidth(180)
        self.tool_selector.currentIndexChanged.connect(self.on_tool_type_changed)
        header.addWidget(QLabel("Type:"))
        header.addWidget(self.tool_selector)

        # Refresh button
        self.refresh_btn = QPushButton("🔄 Refresh")
        self.refresh_btn.setFixedWidth(120)
        self.refresh_btn.clicked.connect(self.load_releases)
        header.addWidget(self.refresh_btn)

        layout.addLayout(header)

        # ===== Destination Path =====
        path_group = QGroupBox("📁 Installation Path")
        path_layout = QFormLayout(path_group)
        self.path_label = QLabel(str(self.destination_dir))
        self.path_label.setStyleSheet(f"color: {KALI_TEXT_DIM}; font-family: monospace;")
        self.path_label.setWordWrap(True)
        path_layout.addRow("Destination:", self.path_label)

        self.change_path_btn = QPushButton("Change...")
        self.change_path_btn.setFixedWidth(100)
        self.change_path_btn.clicked.connect(self.change_destination)
        path_layout.addRow("", self.change_path_btn)
        layout.addWidget(path_group)

        # ===== Releases Table =====
        table_group = QGroupBox("Available Versions")
        table_layout = QVBoxLayout(table_group)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Version", "Released", "Size", "Changelog", "Action"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)
        table_layout.addWidget(self.table)

        layout.addWidget(table_group, 1)

        # ===== Progress Bar (Global) =====
        self.global_progress = QProgressBar()
        self.global_progress.setVisible(False)
        self.global_progress.setTextVisible(True)
        self.global_progress.setFormat("%p% - %v/%m")
        layout.addWidget(self.global_progress)

        # ===== Status Bar =====
        self.status_label = QLabel("Ready")
        self.status_label.setObjectName("subtitle")
        layout.addWidget(self.status_label)

    def apply_style(self):
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {KALI_BG};
                color: {KALI_TEXT};
                font-family: 'JetBrains Mono', 'Fira Code', 'Monospace';
                font-size: 12px;
            }}
            QGroupBox {{
                background-color: {KALI_BG_CARD};
                border: 1px solid {KALI_BORDER};
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 16px;
                font-weight: bold;
                color: {KALI_GREEN};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 8px;
                color: {KALI_GREEN};
            }}
            QTableWidget {{
                background-color: {KALI_BG_CARD};
                alternate-background-color: {KALI_BG_LIGHT};
                color: {KALI_TEXT};
                gridline-color: {KALI_BORDER};
                border: 1px solid {KALI_BORDER};
                border-radius: 6px;
                selection-background-color: {KALI_GREEN};
                selection-color: {KALI_BG};
            }}
            QTableWidget::item {{
                padding: 8px;
                border-bottom: 1px solid {KALI_BORDER};
            }}
            QHeaderView::section {{
                background-color: {KALI_BG_LIGHT};
                color: {KALI_GREEN};
                padding: 10px;
                border: 1px solid {KALI_BORDER};
                font-weight: bold;
            }}
            QPushButton {{
                background-color: {KALI_BG_LIGHT};
                color: {KALI_GREEN};
                border: 1px solid {KALI_BORDER};
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {KALI_GREEN};
                color: {KALI_BG};
            }}
            QPushButton:pressed {{
                background-color: {KALI_GREEN_DARK};
            }}
            QPushButton:disabled {{
                background-color: {KALI_BG_LIGHT};
                color: {KALI_TEXT_DIM};
                border: 1px solid {KALI_TEXT_DIM};
            }}
            QPushButton#primary {{
                background-color: {KALI_GREEN};
                color: {KALI_BG};
            }}
            QPushButton#primary:hover {{
                background-color: {KALI_GREEN_DIM};
            }}
            QPushButton#danger {{
                color: {KALI_RED};
                border: 1px solid {KALI_RED};
            }}
            QPushButton#danger:hover {{
                background-color: {KALI_RED};
                color: {KALI_BG};
            }}
            QComboBox {{
                background-color: {KALI_BG_LIGHT};
                color: {KALI_TEXT};
                border: 1px solid {KALI_BORDER};
                border-radius: 6px;
                padding: 8px;
            }}
            QComboBox::drop-down {{ border: none; width: 20px; }}
            QComboBox QAbstractItemView {{
                background-color: {KALI_BG_CARD};
                color: {KALI_TEXT};
                border: 1px solid {KALI_BORDER};
                selection-background-color: {KALI_GREEN};
            }}
            QProgressBar {{
                background-color: {KALI_BG_LIGHT};
                border: 1px solid {KALI_BORDER};
                border-radius: 6px;
                text-align: center;
                color: {KALI_GREEN};
                font-weight: bold;
            }}
            QProgressBar::chunk {{
                background-color: {KALI_GREEN};
                border-radius: 5px;
            }}
            QLabel#title {{ color: {KALI_GREEN}; font-size: 18px; font-weight: bold; }}
            QLabel#subtitle {{ color: {KALI_TEXT_DIM}; font-size: 11px; }}
            QLabel#status-ok {{ color: {KALI_GREEN}; }}
            QLabel#status-warn {{ color: {KALI_YELLOW}; }}
            QLabel#status-error {{ color: {KALI_RED}; }}
        """)

    def on_tool_type_changed(self, index: int):
        self.current_tool_type = ToolType.PROTON_GE if index == 0 else ToolType.WINE_GE
        self.load_releases()

    def change_destination(self):
        from PyQt6.QtWidgets import QFileDialog
        new_dir = QFileDialog.getExistingDirectory(
            self, "Select Installation Directory", str(self.destination_dir)
        )
        if new_dir:
            self.destination_dir = Path(new_dir)
            self.path_label.setText(str(self.destination_dir))
            self.log_message.emit(f"📁 Installation path changed to: {self.destination_dir}")

    def load_releases(self):
        """Load releases from GitHub API (async via timer to not block UI)."""
        self.refresh_btn.setEnabled(False)
        self.refresh_btn.setText("🔄 Loading...")
        self.status_label.setText(f"Fetching {self.current_tool_type.value} releases...")
        self.status_label.setObjectName("status-warn")

        # Use QTimer to allow UI to update before blocking call
        QTimer.singleShot(50, self._do_load_releases)

    def _do_load_releases(self):
        try:
            self.releases = self.downloader.fetch_releases(self.current_tool_type)
            self.populate_table()
            self.status_label.setText(f"✓ Loaded {len(self.releases)} {self.current_tool_type.value} releases")
            self.status_label.setObjectName("status-ok")
            self.log_message.emit(f"✓ Loaded {len(self.releases)} {self.current_tool_type.value} releases")
        except RateLimitError as e:
            self.status_label.setText(f"⚠ Rate limited: {e}")
            self.status_label.setObjectName("status-warn")
            self.show_error("Rate Limited", str(e))
            # Try to show cached data
            self.releases = self.downloader._cache.get(self.current_tool_type, [])
            self.populate_table()
        except NetworkError as e:
            self.status_label.setText(f"✗ Network error: {e}")
            self.status_label.setObjectName("status-error")
            self.show_error("Network Error", str(e))
            # Try to show cached data
            self.releases = self.downloader._cache.get(self.current_tool_type, [])
            self.populate_table()
        except GitHubAPIError as e:
            self.status_label.setText(f"✗ API error: {e}")
            self.status_label.setObjectName("status-error")
            self.show_error("API Error", str(e))
        except Exception as e:
            self.status_label.setText(f"✗ Unexpected error: {e}")
            self.status_label.setObjectName("status-error")
            self.show_error("Error", f"Unexpected error: {e}")
        finally:
            self.refresh_btn.setEnabled(True)
            self.refresh_btn.setText("🔄 Refresh")
            self.apply_style()  # Refresh objectName styles

    def populate_table(self):
        self.table.setRowCount(len(self.releases))

        for row, release in enumerate(self.releases):
            # Version
            version_item = QTableWidgetItem(release.tag_name)
            version_item.setToolTip(release.name)
            if release.prerelease:
                version_item.setForeground(QColor(KALI_YELLOW))
                version_item.setToolTip(f"{release.name} (Pre-release)")
            self.table.setItem(row, 0, version_item)

            # Released date
            try:
                from datetime import datetime
                dt = datetime.fromisoformat(release.published_at.replace("Z", "+00:00"))
                date_str = dt.strftime("%Y-%m-%d %H:%M")
            except Exception:
                date_str = release.published_at
            date_item = QTableWidgetItem(date_str)
            date_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 1, date_item)

            # Size (largest asset)
            max_size = max((a.size for a in release.assets), default=0)
            size_item = QTableWidgetItem(format_file_size(max_size))
            size_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(row, 2, size_item)

            # Changelog
            changelog = format_changelog(release.body, max_lines=3)
            changelog_item = QTableWidgetItem(changelog)
            changelog_item.setToolTip(release.body[:500] if release.body else "No changelog")
            self.table.setItem(row, 3, changelog_item)

            # Action button
            download_btn = QPushButton("⬇️ Download")
            download_btn.setObjectName("primary")
            download_btn.setFixedWidth(110)
            download_btn.clicked.connect(lambda checked, r=release: self.start_download(r))
            # Check if already installed
            if self.is_installed(release):
                download_btn.setText("✓ Installed")
                download_btn.setEnabled(False)
                download_btn.setObjectName("")
            self.table.setCellWidget(row, 4, download_btn)

        self.table.resizeRowsToContents()

    def is_installed(self, release: Release) -> bool:
        """Check if any asset from this release is already extracted."""
        for asset in release.assets:
            extract_name = asset.name
            for suffix in [".tar.gz", ".tar.xz", ".tar.zst", ".tgz", ".txz"]:
                if extract_name.endswith(suffix):
                    extract_name = extract_name[: -len(suffix)]
                    break
            if (self.destination_dir / extract_name).exists():
                return True
        return False

    def start_download(self, release: Release):
        """Start downloading the best asset for current architecture."""
        asset = self.downloader.find_asset(release)
        if not asset:
            self.show_error("No Asset", "No suitable archive found for this release")
            return

        # Confirm download
        reply = QMessageBox.question(
            self,
            "Confirm Download",
            f"Download and install:\n{release.tag_name}\n\nAsset: {asset.name}\nSize: {format_file_size(asset.size)}\n\nDestination: {self.destination_dir}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        # Disable button
        self.set_row_buttons_enabled(release, False)

        # Show progress bar
        self.global_progress.setVisible(True)
        self.global_progress.setRange(0, asset.size)
        self.global_progress.setValue(0)

        # Create and start worker
        self.download_worker = WineDownloadWorker(asset, self.destination_dir)
        self.download_worker.progress.connect(self.on_download_progress)
        self.download_worker.finished.connect(self.on_download_finished)
        self.download_worker.log.connect(self.log_message.emit)
        self.download_worker.start()

        self.status_label.setText(f"⬇️ Downloading {asset.name}...")
        self.status_label.setObjectName("status-warn")
        self.log_message.emit(f"⬇️ Starting download: {release.tag_name} - {asset.name}")

    def set_row_buttons_enabled(self, release: Release, enabled: bool):
        for row, r in enumerate(self.releases):
            if r == release:
                btn = self.table.cellWidget(row, 4)
                if btn:
                    btn.setEnabled(enabled)
                break

    def on_download_progress(self, progress: DownloadProgress):
        self.global_progress.setValue(progress.downloaded)
        self.global_progress.setFormat(f"{progress.asset_name}: %p% ({format_file_size(progress.downloaded)}/{format_file_size(progress.total)})")

    def on_download_finished(self, success: bool, message: str):
        self.global_progress.setVisible(False)
        self.global_progress.setValue(0)

        if success:
            self.status_label.setText("✓ Download and extraction completed")
            self.status_label.setObjectName("status-ok")
            self.log_message.emit(f"✓ {message}")
            # Refresh table to show installed status
            self.load_releases()
            # Emit signal for other components to refresh their version lists
            self.downloads_updated.emit()
        else:
            self.status_label.setText(f"✗ Download failed: {message}")
            self.status_label.setObjectName("status-error")
            self.log_message.emit(f"✗ Download failed: {message}")
            self.show_error("Download Failed", message)
            # Re-enable buttons for this release
            # We don't know which release, so refresh
            self.load_releases()

        self.apply_style()

    def show_context_menu(self, pos):
        row = self.table.rowAt(pos.y())
        if row < 0:
            return
        release = self.releases[row]

        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{
                background-color: {KALI_BG_CARD};
                border: 1px solid {KALI_BORDER};
                color: {KALI_TEXT};
            }}
            QMenu::item:selected {{
                background-color: {KALI_GREEN};
                color: {KALI_BG};
            }}
        """)

        # View on GitHub
        github_action = QAction("🔗 View on GitHub", self)
        github_action.triggered.connect(lambda: self.open_github(release))
        menu.addAction(github_action)

        # Open install folder
        if self.is_installed(release):
            open_action = QAction("📁 Open Install Folder", self)
            open_action.triggered.connect(lambda: self.open_install_folder(release))
            menu.addAction(open_action)

        # Re-download (force)
        redownload_action = QAction("🔄 Re-download", self)
        redownload_action.triggered.connect(lambda: self.start_download(release))
        menu.addAction(redownload_action)

        menu.exec(self.table.viewport().mapToGlobal(pos))

    def open_github(self, release: Release):
        import webbrowser
        webbrowser.open(release.html_url)
        self.log_message.emit(f"🔗 Opened {release.html_url}")

    def open_install_folder(self, release: Release):
        import subprocess
        for asset in release.assets:
            extract_name = asset.name
            for suffix in [".tar.gz", ".tar.xz", ".tar.zst", ".tgz", ".txz"]:
                if extract_name.endswith(suffix):
                    extract_name = extract_name[: -len(suffix)]
                    break
            path = self.destination_dir / extract_name
            if path.exists():
                subprocess.Popen(["xdg-open", str(path)])
                break

    def show_error(self, title: str, message: str):
        QMessageBox.critical(self, title, message)

    def closeEvent(self, event):
        """Cleanup on close."""
        if self.download_worker and self.download_worker.isRunning():
            self.download_worker.stop()
            self.download_worker.wait(3000)
        event.accept()