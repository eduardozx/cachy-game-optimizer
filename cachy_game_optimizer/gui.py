#!/usr/bin/env python3
"""
CachyOS Game Optimizer - PyQt6 GUI
Futuristic gaming performance suite with Kali-inspired dark green theme.
"""

import sys
import os
import asyncio
import subprocess
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGridLayout, QTabWidget, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QProgressBar, QTextEdit, QGroupBox,
    QSplitter, QFrame, QScrollArea, QComboBox, QCheckBox,
    QLineEdit, QMessageBox, QHeaderView, QAbstractItemView,
    QDialog, QDialogButtonBox, QFormLayout, QSpinBox,
    QTreeWidget, QTreeWidgetItem, QMenu
)
from PyQt6.QtCore import (
    Qt, QTimer, QThread, pyqtSignal, QPropertyAnimation,
    QEasingCurve, QRect, QSize, QPoint
)
from PyQt6.QtGui import (
    QFont, QColor, QPalette, QIcon, QPixmap, QPainter,
    QLinearGradient, QBrush, QPen, QFontDatabase
)

# Add project to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from cachy_game_optimizer.hardware import get_detector, SystemProfile
from cachy_game_optimizer.optimizer import get_optimizer, OptimizationEngine, OptimizationResult, OptimizationStatus
from cachy_game_optimizer.games import get_game_manager, GameManager, Game, GameSource, GameConfig
from .error_analyzer import GameErrorAnalyzer, FixResult
from .gui_wine_tab import WineProtonTab


# ============================================================
# THEME & STYLES
# ============================================================

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
KALI_ORANGE = "#ff8800"

STYLESHEET = f"""
QMainWindow {{
    background-color: {KALI_BG};
    color: {KALI_TEXT};
}}

QWidget {{
    background-color: {KALI_BG};
    color: {KALI_TEXT};
    font-family: 'JetBrains Mono', 'Fira Code', 'Monospace';
    font-size: 12px;
}}

QFrame#card {{
    background-color: {KALI_BG_CARD};
    border: 1px solid {KALI_BORDER};
    border-radius: 8px;
    padding: 12px;
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

QTabWidget::pane {{
    border: 1px solid {KALI_BORDER};
    border-radius: 8px;
    background-color: {KALI_BG_CARD};
    margin-top: -1px;
}}

QTabBar::tab {{
    background-color: {KALI_BG_LIGHT};
    color: {KALI_TEXT_DIM};
    padding: 10px 20px;
    border: 1px solid {KALI_BORDER};
    border-bottom: none;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    margin-right: 2px;
    font-weight: bold;
}}

QTabBar::tab:selected {{
    background-color: {KALI_BG_CARD};
    color: {KALI_GREEN};
    border-bottom: 1px solid {KALI_BG_CARD};
}}

QTabBar::tab:hover:!selected {{
    color: {KALI_GREEN};
    background-color: {KALI_BG};
}}

QPushButton {{
    background-color: {KALI_BG_LIGHT};
    color: {KALI_GREEN};
    border: 1px solid {KALI_BORDER};
    border-radius: 6px;
    padding: 10px 20px;
    font-weight: bold;
    font-size: 12px;
}}

QPushButton:hover {{
    background-color: {KALI_GREEN};
    color: {KALI_BG};
    border: 1px solid {KALI_GREEN};
}}

QPushButton:pressed {{
    background-color: {KALI_GREEN_DARK};
    color: {KALI_BG};
}}

QPushButton:disabled {{
    background-color: {KALI_BG_LIGHT};
    color: {KALI_TEXT_DIM};
    border: 1px solid {KALI_TEXT_DIM};
}}

QPushButton#primary {{
    background-color: {KALI_GREEN};
    color: {KALI_BG};
    border: 1px solid {KALI_GREEN};
}}

QPushButton#primary:hover {{
    background-color: {KALI_GREEN_DIM};
    border: 1px solid {KALI_GREEN_DIM};
}}

QPushButton#danger {{
    background-color: {KALI_BG_LIGHT};
    color: {KALI_RED};
    border: 1px solid {KALI_RED};
}}

QPushButton#danger:hover {{
    background-color: {KALI_RED};
    color: {KALI_BG};
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

QTableWidget::item:selected {{
    background-color: {KALI_GREEN};
    color: {KALI_BG};
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

QTextEdit, QPlainTextEdit {{
    background-color: {KALI_BG};
    color: {KALI_TEXT_DIM};
    border: 1px solid {KALI_BORDER};
    border-radius: 6px;
    padding: 8px;
    font-family: 'JetBrains Mono', 'Monospace';
    font-size: 11px;
}}

QLineEdit, QSpinBox, QComboBox {{
    background-color: {KALI_BG_LIGHT};
    color: {KALI_TEXT};
    border: 1px solid {KALI_BORDER};
    border-radius: 6px;
    padding: 8px;
    selection-background-color: {KALI_GREEN};
}}

QLineEdit:focus, QSpinBox:focus, QComboBox:focus {{
    border: 1px solid {KALI_GREEN};
}}

QComboBox::drop-down {{
    border: none;
    width: 20px;
}}

QComboBox QAbstractItemView {{
    background-color: {KALI_BG_CARD};
    color: {KALI_TEXT};
    border: 1px solid {KALI_BORDER};
    selection-background-color: {KALI_GREEN};
}}

QCheckBox {{
    color: {KALI_TEXT};
    spacing: 8px;
}}

QCheckBox::indicator {{
    width: 18px;
    height: 18px;
    border: 1px solid {KALI_BORDER};
    border-radius: 4px;
    background-color: {KALI_BG_LIGHT};
}}

QCheckBox::indicator:checked {{
    background-color: {KALI_GREEN};
    border: 1px solid {KALI_GREEN};
    image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iMTIiIHZpZXdCb3g9IjAgMCAxMiAxMiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTEwIDNMNC41IDguNUwyIDYiIHN0cm9rZT0iIzAwMDAwMCIgc3Ryb2tlLXdpZHRoPSIyIiBzdHJva2UtbGluZWNhcD0icm91bmQiIHN0cm9rZS1saW5lam9pbj0icm91bmQiLz4KPC9zdmc+);
}}

QScrollBar:vertical {{
    background-color: {KALI_BG};
    width: 10px;
    border: none;
}}

QScrollBar::handle:vertical {{
    background-color: {KALI_GREEN};
    border-radius: 5px;
    min-height: 30px;
}}

QScrollBar::handle:vertical:hover {{
    background-color: {KALI_GREEN_DIM};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}

QTreeWidget {{
    background-color: {KALI_BG_CARD};
    alternate-background-color: {KALI_BG_LIGHT};
    color: {KALI_TEXT};
    border: 1px solid {KALI_BORDER};
    border-radius: 6px;
}}

QTreeWidget::item {{
    padding: 8px;
    border-bottom: 1px solid {KALI_BORDER};
}}

QTreeWidget::item:selected {{
    background-color: {KALI_GREEN};
    color: {KALI_BG};
}}

QTreeWidget::branch:has-children:!has-siblings:closed,
QTreeWidget::branch:closed:has-children:has-siblings {{
    border-image: none;
    image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iMTIiIHZpZXdCb3g9IjAgMCAxMiAxMiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTQgM0w4IDZMNCA5IiBzdHJva2U9IiMwMGZmODgiIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIi8+Cjwvc3ZnPg==);
}}

QTreeWidget::branch:open:has-children:!has-siblings,
QTreeWidget::branch:open:has-children:has-siblings {{
    border-image: none;
    image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iMTIiIHZpZXdCb3g9IjAgMCAxMiAxMiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTMgNEx5IDhNNSA4TDcgNiIgc3Ryb2tlPSIjMDBmZjg4IiBzdHJva2Utd2lkdGg9IjIiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCIvPgo8L3N2Zz4=);
}}

QSplitter::handle {{
    background-color: {KALI_BORDER};
    width: 2px;
    height: 2px;
}}

QSplitter::handle:horizontal {{
    width: 2px;
}}

QSplitter::handle:vertical {{
    height: 2px;
}}

QDialog {{
    background-color: {KALI_BG_CARD};
    border: 1px solid {KALI_BORDER};
    border-radius: 8px;
}}

QMessageBox {{
    background-color: {KALI_BG_CARD};
    border: 1px solid {KALI_BORDER};
}}

QLabel#title {{
    color: {KALI_GREEN};
    font-size: 18px;
    font-weight: bold;
}}

QLabel#subtitle {{
    color: {KALI_TEXT_DIM};
    font-size: 11px;
}}

QLabel#stat-value {{
    color: {KALI_GREEN};
    font-size: 14px;
    font-weight: bold;
}}

QLabel#stat-label {{
    color: {KALI_TEXT_DIM};
    font-size: 11px;
}}

QLabel#status-ok {{
    color: {KALI_GREEN};
}}

QLabel#status-warn {{
    color: {KALI_YELLOW};
}}

QLabel#status-error {{
    color: {KALI_RED};
}}
"""


# ============================================================
# WORKER THREADS
# ============================================================

class HardwareDetectionWorker(QThread):
    """Background hardware detection."""
    finished = pyqtSignal(object, object)  # profile, recommendations
    error = pyqtSignal(str)
    log = pyqtSignal(str)

    def run(self):
        try:
            self.log.emit("🔍 Detecting hardware...")
            detector = get_detector()
            profile = detector.get_full_profile()
            recommendations = detector.get_optimization_recommendations()
            self.log.emit(f"✓ Hardware detected: {profile.cpu.model}")
            self.log.emit(f"✓ GPU: {profile.gpu.vendor} {profile.gpu.model} ({profile.gpu.vram_mb}MB VRAM)")
            self.log.emit(f"✓ RAM: {profile.memory.total_gb:.1f}GB {profile.memory.type}-{profile.memory.speed_mhz}")
            self.log.emit(f"✓ Found {len(recommendations)} optimization recommendations")
            self.finished.emit(profile, recommendations)
        except Exception as e:
            self.error.emit(str(e))


class OptimizationWorker(QThread):
    """Background optimization runner with real-time log output."""
    progress = pyqtSignal(str, str)  # action_id, status
    finished = pyqtSignal(list)  # results
    log = pyqtSignal(str)
    output_line = pyqtSignal(str)  # Real-time output from optimization actions

    def __init__(self, optimizer: OptimizationEngine, category: Optional[str] = None):
        super().__init__()
        self.optimizer = optimizer
        self.category = category
        # Set log callback to emit output_line signal
        self.optimizer.log_callback = self.output_line.emit
        self._should_stop = False

    def stop(self):
        """Signal the worker to stop gracefully."""
        self._should_stop = True

    def run(self):
        try:
            if self.category:
                self.log.emit(f"⚡ Running {self.category} optimizations...")
                self.output_line.emit(f"⚡ Running {self.category} optimizations...")
                results = self.optimizer.run_category(self.category)
            else:
                self.log.emit("⚡ Running all recommended optimizations...")
                self.output_line.emit("⚡ Running all recommended optimizations...")
                results = self.optimizer.run_all_recommended()

            for result in results:
                status_text = {
                    OptimizationStatus.PENDING: "⏳ PENDING",
                    OptimizationStatus.RUNNING: "🔄 RUNNING",
                    OptimizationStatus.SUCCESS: "✓ SUCCESS",
                    OptimizationStatus.FAILED: "✗ FAILED",
                    OptimizationStatus.SKIPPED: "⊘ SKIPPED",
                }.get(result.status, "?")
                self.progress.emit(result.action_id, status_text)

            success = sum(1 for r in results if r.status == OptimizationStatus.SUCCESS)
            failed = sum(1 for r in results if r.status == OptimizationStatus.FAILED)
            skipped = sum(1 for r in results if r.status == OptimizationStatus.SKIPPED)

            self.log.emit(f"✓ Complete: {success} success, {failed} failed, {skipped} skipped")
            self.output_line.emit(f"✓ Complete: {success} success, {failed} failed, {skipped} skipped")

            if any(r.requires_reboot for r in results):
                self.log.emit("⚠ Reboot required for some optimizations")
                self.output_line.emit("⚠ Reboot required for some optimizations")

            self.finished.emit(results)
        except Exception as e:
            self.log.emit(f"✗ Optimization error: {e}")
            self.output_line.emit(f"✗ Optimization error: {e}")
            self.finished.emit([])


class GameLaunchWorker(QThread):
    """Background game launcher with real-time log capture (full session)."""
    finished = pyqtSignal(bool, str)  # success, message
    log = pyqtSignal(str)
    output_line = pyqtSignal(str)  # Real-time stdout/stderr from game process

    def __init__(self, manager: GameManager, game_id: str):
        super().__init__()
        self.manager = manager
        self.game_id = game_id
        self.process = None
        self._should_stop = False

    def run(self):
        try:
            self.log.emit(f"🚀 Launching game: {self.game_id}")
            result = self.manager.launch_game(self.game_id, capture_output=True)
            
            if not result['success']:
                self.log.emit(f"✗ Launch failed: {result.get('error', 'Unknown error')}")
                self.finished.emit(False, result.get('error', 'Unknown error'))
                return

            self.process = result.get('process')
            pid = result.get('pid')
            
            if self.process:
                self.log.emit(f"✓ Process started (PID: {pid}) - capturing full session output...")
                
                # Read stdout and stderr in real-time until process AND children exit
                import select
                
                # Track if we've seen the main process exit
                main_exited = False
                exit_code = None
                
                while not self._should_stop:
                    # Check if process has ended
                    retcode = self.process.poll()
                    if retcode is not None:
                        if not main_exited:
                            main_exited = True
                            exit_code = retcode
                            self.log.emit(f"✓ Main process exited with code: {retcode} - waiting for children...")
                        # Check if all child processes are gone
                        if self._are_children_gone(pid):
                            self.log.emit(f"✓ All game processes terminated")
                            break
                    
                    # Read available output (non-blocking, shorter timeout for responsiveness)
                    ready, _, _ = select.select([self.process.stdout, self.process.stderr], [], [], 0.05)
                    
                    for stream in ready:
                        line = stream.readline()
                        if line:
                            self.output_line.emit(line.rstrip())
                    
                    # Small sleep to prevent busy loop when no output
                    if not ready:
                        import time
                        time.sleep(0.01)
                
                if self._should_stop:
                    self.finished.emit(False, "Capture stopped by user")
                else:
                    self.finished.emit(True, f"Game session ended (exit code: {exit_code})")
            else:
                # Fallback for Steam launches (no process capture)
                self.log.emit(f"✓ Launched successfully (PID: {pid}) - Steam launch, no output capture available")
                self.finished.emit(True, f"Launched via Steam (PID: {pid})")

        except Exception as e:
            self.log.emit(f"✗ Launch error: {e}")
            self.finished.emit(False, str(e))

    def _are_children_gone(self, parent_pid: int) -> bool:
        """Check if all child processes of the main game process have exited."""
        try:
            import psutil
            parent = psutil.Process(parent_pid)
            children = parent.children(recursive=True)
            return len(children) == 0
        except Exception:
            # If psutil not available, assume children are gone after main exits
            return True

    def stop(self):
        """Stop the game process if running."""
        self._should_stop = True
        if self.process and self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()


# ============================================================
# CUSTOM WIDGETS
# ============================================================

class StatCard(QFrame):
    """Stat display card."""
    def __init__(self, label: str, value: str, icon: str = "", status: str = "ok"):
        super().__init__()
        self.setObjectName("card")
        self.setFixedHeight(100)
        layout = QVBoxLayout(self)
        layout.setSpacing(4)
        layout.setContentsMargins(16, 12, 16, 12)

        # Icon + Label row
        top_layout = QHBoxLayout()
        if icon:
            icon_label = QLabel(icon)
            icon_label.setStyleSheet(f"color: {KALI_GREEN}; font-size: 20px;")
            top_layout.addWidget(icon_label)

        label_widget = QLabel(label)
        label_widget.setObjectName("stat-label")
        top_layout.addWidget(label_widget)
        top_layout.addStretch()
        layout.addLayout(top_layout)

        # Value
        self.value_label = QLabel(value)
        self.value_label.setObjectName("stat-value")
        layout.addWidget(self.value_label)

        # Status indicator
        status_colors = {
            "ok": KALI_GREEN,
            "warn": KALI_YELLOW,
            "error": KALI_RED,
        }
        status_indicator = QLabel("●")
        status_indicator.setStyleSheet(f"color: {status_colors.get(status, KALI_GREEN)}; font-size: 10px;")
        layout.addWidget(status_indicator, alignment=Qt.AlignmentFlag.AlignRight)


class LogPanel(QTextEdit):
    """Styled log panel."""
    def __init__(self):
        super().__init__()
        self.setReadOnly(True)
        self.setMaximumHeight(180)
        self.setFont(QFont("JetBrains Mono", 10))
        self.log("[dim]CachyOS Game Optimizer initialized[/dim]")
        self.log("[dim]Waiting for hardware detection...[/dim]")

    def log(self, message: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        # Simple color parsing
        if message.startswith("[dim]"):
            msg = message.replace("[dim]", "").replace("[/dim]", "")
            self.append(f'<span style="color: {KALI_TEXT_DIM};">[{timestamp}] {msg}</span>')
        elif "✓" in message or "✅" in message:
            self.append(f'<span style="color: {KALI_GREEN};">[{timestamp}] {message}</span>')
        elif "✗" in message or "❌" in message or "FAILED" in message:
            self.append(f'<span style="color: {KALI_RED};">[{timestamp}] {message}</span>')
        elif "⚠" in message or "⚡" in message:
            self.append(f'<span style="color: {KALI_YELLOW};">[{timestamp}] {message}</span>')
        elif "🔍" in message or "🎮" in message:
            self.append(f'<span style="color: {KALI_BLUE};">[{timestamp}] {message}</span>')
        else:
            self.append(f'<span style="color: {KALI_TEXT};">[{timestamp}] {message}</span>')

        # Auto-scroll
        self.verticalScrollBar().setValue(self.verticalScrollBar().maximum())


# ============================================================
# MAIN PANELS
# ============================================================

class HardwarePanel(QWidget):
    """Hardware information panel."""
    def __init__(self):
        super().__init__()
        self.profile: Optional[SystemProfile] = None
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # Title
        title = QLabel("⚡ HARDWARE PROFILE")
        title.setObjectName("title")
        layout.addWidget(title)

        # Scroll area for stats
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setSpacing(8)

        # Stat grid
        self.stat_grid = QGridLayout()
        self.stat_grid.setSpacing(8)
        content_layout.addLayout(self.stat_grid)
        content_layout.addStretch()

        scroll.setWidget(content)
        layout.addWidget(scroll)

    def update_profile(self, profile: SystemProfile):
        self.profile = profile
        self.refresh_stats()

    def refresh_stats(self):
        if not self.profile:
            return

        # Clear grid
        for i in reversed(range(self.stat_grid.count())):
            widget = self.stat_grid.itemAt(i).widget()
            if widget:
                widget.deleteLater()

        cpu = self.profile.cpu
        gpu = self.profile.gpu
        mem = self.profile.memory
        kernel = self.profile.kernel

        stats = [
            # CPU
            ("⚡ CPU Model", cpu.model, "", "ok"),
            ("🔢 Cores/Threads", f"{cpu.cores}C / {cpu.threads}T", "", "ok"),
            ("⏱️ Base/Boost", f"{cpu.base_clock:.1f}GHz / {cpu.boost_clock:.1f}GHz", "", "ok"),
            ("🎛️ Governor", cpu.governor, "", "ok" if cpu.governor == "performance" else "warn"),
            ("💾 L3 Cache", cpu.cache_l3, "", "ok"),
            # GPU
            ("🎮 GPU", f"{gpu.vendor} {gpu.model}", "", "ok"),
            ("📊 VRAM", f"{gpu.vram_mb} MB", "", "warn" if gpu.vram_mb <= 2048 else "ok"),
            ("🖥️ Driver", gpu.driver_version, "", "ok"),
            ("⚡ Vulkan", "✓" if gpu.vulkan_support else "✗", "", "ok" if gpu.vulkan_support else "error"),
            ("🔌 PCIe", f"Gen {gpu.pcie_gen} {gpu.pcie_width}", "", "ok"),
            # Memory
            ("🧠 Total RAM", f"{mem.total_gb:.1f} GB", "", "ok"),
            ("📈 Available", f"{mem.available_gb:.1f} GB ({mem.usage_percent:.1f}% used)", "", "ok"),
            ("🏷️ Type/Speed", f"{mem.type}-{mem.speed_mhz} MHz", "", "warn" if mem.type == "DDR3" else "ok"),
            ("🔀 Channels", f"{mem.channels}x", "", "ok"),
            # Kernel
            ("🐧 Kernel", kernel.version.split()[2] if len(kernel.version.split()) > 2 else kernel.version, "", "ok"),
            ("💿 I/O Scheduler", kernel.scheduler, "", "ok"),
            ("🔄 Swappiness", str(kernel.swappiness), "", "error" if kernel.swappiness > 10 else "ok"),
            ("📄 THP", kernel.transparent_hugepages, "", "warn" if kernel.transparent_hugepages != "madvise" else "ok"),
        ]

        row = 0
        col = 0
        max_cols = 2
        for label, value, icon, status in stats:
            card = StatCard(label, value, icon, status)
            self.stat_grid.addWidget(card, row, col)
            col += 1
            if col >= max_cols:
                col = 0
                row += 1


class OptimizationPanel(QWidget):
    """Optimization recommendations panel."""
    def __init__(self):
        super().__init__()
        self.recommendations: List[Dict] = []
        self.results: List[OptimizationResult] = []
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        # Header with actions
        header = QHBoxLayout()
        title = QLabel("⚡ OPTIMIZATIONS")
        title.setObjectName("title")
        header.addWidget(title)
        header.addStretch()

        self.optimize_all_btn = QPushButton("⚡ Optimize All")
        self.optimize_all_btn.setObjectName("primary")
        self.optimize_all_btn.setFixedWidth(160)
        header.addWidget(self.optimize_all_btn)

        self.optimize_cpu_btn = QPushButton("🔧 CPU")
        self.optimize_cpu_btn.setFixedWidth(80)
        header.addWidget(self.optimize_cpu_btn)

        self.optimize_gpu_btn = QPushButton("🎮 GPU")
        self.optimize_gpu_btn.setFixedWidth(80)
        header.addWidget(self.optimize_gpu_btn)

        self.optimize_mem_btn = QPushButton("🧠 Memory")
        self.optimize_mem_btn.setFixedWidth(100)
        header.addWidget(self.optimize_mem_btn)

        layout.addLayout(header)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Priority", "Action", "Description", "Status"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        layout.addWidget(self.table)

    def set_recommendations(self, recommendations: List[Dict]):
        self.recommendations = recommendations
        self.refresh_table()

    def set_results(self, results: List[OptimizationResult]):
        self.results = results
        self.refresh_table()

    def refresh_table(self):
        self.table.setRowCount(len(self.recommendations))
        status_map = {r.action_id: r.status for r in self.results}

        for row, rec in enumerate(self.recommendations):
            action_id = rec.get('action', '')
            status = status_map.get(action_id, OptimizationStatus.PENDING)

            # Priority
            priority = rec.get('priority', 'LOW')
            priority_item = QTableWidgetItem(priority)
            priority_colors = {'HIGH': KALI_RED, 'MEDIUM': KALI_YELLOW, 'LOW': KALI_GREEN}
            priority_item.setForeground(QColor(priority_colors.get(priority, KALI_TEXT)))
            priority_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 0, priority_item)

            # Action
            action_item = QTableWidgetItem(rec.get('title', ''))
            self.table.setItem(row, 1, action_item)

            # Description
            desc = rec.get('description', '')
            desc_item = QTableWidgetItem(desc[:80] + ("..." if len(desc) > 80 else ""))
            self.table.setItem(row, 2, desc_item)

            # Status
            status_text = {
                OptimizationStatus.PENDING: "⏳ PENDING",
                OptimizationStatus.RUNNING: "🔄 RUNNING",
                OptimizationStatus.SUCCESS: "✓ DONE",
                OptimizationStatus.FAILED: "✗ FAILED",
                OptimizationStatus.SKIPPED: "⊘ SKIP",
            }.get(status, "?")
            status_item = QTableWidgetItem(status_text)
            status_colors = {
                OptimizationStatus.PENDING: KALI_TEXT_DIM,
                OptimizationStatus.RUNNING: KALI_YELLOW,
                OptimizationStatus.SUCCESS: KALI_GREEN,
                OptimizationStatus.FAILED: KALI_RED,
                OptimizationStatus.SKIPPED: KALI_BLUE,
            }
            status_item.setForeground(QColor(status_colors.get(status, KALI_TEXT)))
            status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 3, status_item)


class GameLibraryPanel(QWidget):
    """Game library panel."""
    def __init__(self):
        super().__init__()
        self.games: List[Game] = []
        self.selected_game: Optional[Game] = None
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        # Header
        header = QHBoxLayout()
        title = QLabel("🎮 GAME LIBRARY")
        title.setObjectName("title")
        header.addWidget(title)
        header.addStretch()

        self.add_game_btn = QPushButton("➕ Add Custom Game")
        self.add_game_btn.setObjectName("primary")
        self.add_game_btn.setFixedWidth(180)
        header.addWidget(self.add_game_btn)

        self.launch_btn = QPushButton("🚀 Launch")
        self.launch_btn.setObjectName("primary")
        self.launch_btn.setFixedWidth(100)
        self.launch_btn.setEnabled(False)
        header.addWidget(self.launch_btn)

        self.config_btn = QPushButton("⚙️ Config")
        self.config_btn.setFixedWidth(100)
        self.config_btn.setEnabled(False)
        header.addWidget(self.config_btn)

        layout.addLayout(header)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["#", "Name", "Source", "Playtime", "Executable"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.itemSelectionChanged.connect(self.on_selection_changed)
        self.add_game_btn.clicked.connect(self.add_custom_game)
        layout.addWidget(self.table)

    def set_games(self, games: List[Game]):
        self.games = games
        self.refresh_table()

    def refresh_table(self):
        self.table.setRowCount(len(self.games))
        source_icons = {
            GameSource.STEAM: "🎮 Steam",
            GameSource.HEROIC: "🦸 Heroic",
            GameSource.LUTRIS: "🎲 Lutris",
            GameSource.BOTTLES: "🍾 Bottles",
            GameSource.FLATPAK: "📦 Flatpak",
            GameSource.NATIVE: "🐧 Native",
            GameSource.CUSTOM: "⚙️ Custom",
        }

        for row, game in enumerate(self.games):
            # Number
            num_item = QTableWidgetItem(str(row + 1))
            num_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 0, num_item)

            # Name
            name_item = QTableWidgetItem(game.name)
            self.table.setItem(row, 1, name_item)

            # Source
            source_text = source_icons.get(game.source, game.source.value)
            source_item = QTableWidgetItem(source_text)
            source_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 2, source_item)

            # Playtime
            playtime = f"{game.hours_played:.1f}h" if game.hours_played > 0 else "—"
            playtime_item = QTableWidgetItem(playtime)
            playtime_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 3, playtime_item)

            # Executable
            exe_name = Path(game.exe_path).name if game.exe_path else "—"
            exe_item = QTableWidgetItem(exe_name)
            self.table.setItem(row, 4, exe_item)

    def on_selection_changed(self):
        selected = self.table.selectionModel().selectedRows()
        if selected:
            row = selected[0].row()
            if 0 <= row < len(self.games):
                self.selected_game = self.games[row]
                self.launch_btn.setEnabled(True)
                self.config_btn.setEnabled(True)
        else:
            self.selected_game = None
            self.launch_btn.setEnabled(False)
            self.config_btn.setEnabled(False)

    def add_custom_game(self):
        """Open file dialog to add a custom game (.exe)"""
        from PyQt6.QtWidgets import QFileDialog
        
        file_dialog = QFileDialog(self)
        file_dialog.setWindowTitle("Select Game Executable")
        file_dialog.setNameFilter("Executables (*.exe *.sh *.AppImage);;All Files (*)")
        file_dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
        
        if file_dialog.exec() == QFileDialog.DialogCode.Accepted:
            selected_files = file_dialog.selectedFiles()
            if selected_files:
                exe_path = selected_files[0]
                self.create_custom_game_entry(exe_path)

    def create_custom_game_entry(self, exe_path: str):
        """Create a custom game entry from selected executable"""
        from pathlib import Path
        import uuid
        
        exe = Path(exe_path)
        game_name = exe.stem
        
        # Generate unique ID
        game_id = f"custom_{uuid.uuid4().hex[:8]}"
        
        # Create prefix directory
        prefix_path = Path.home() / '.local' / 'share' / 'cachy-game-optimizer' / 'prefixes' / game_id
        prefix_path.mkdir(parents=True, exist_ok=True)
        
        game = Game(
            id=game_id,
            name=game_name,
            source=GameSource.CUSTOM,
            source_id=game_id,
            install_path=str(exe.parent),
            exe_path=str(exe),
            exe_args="",
            config=GameConfig(),  # Default optimization config
            prefix_path=str(prefix_path),
        )
        
        self.game_manager.add_game(game)
        self.games.append(game)
        self.refresh_table()
        
        # Select the newly added game
        self.table.selectRow(len(self.games) - 1)
        self.log(f"✓ Added custom game: {game_name}")

    # Need to access game_manager and log from MainWindow
    def set_game_manager(self, manager):
        self.game_manager = manager
    
    def set_log_callback(self, callback):
        self.log = callback


class GameConfigDialog(QDialog):
    """Game configuration dialog."""
    def __init__(self, game: Game, parent=None, game_manager=None):
        super().__init__(parent)
        self.game = game
        self.config = game.config
        self.game_manager = game_manager
        self.setWindowTitle(f"Configure: {game.name}")
        self.setMinimumSize(500, 600)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # Tabs
        tabs = QTabWidget()
        layout.addWidget(tabs)

        # Wine/Proton tab
        wine_tab = QWidget()
        wine_layout = QFormLayout(wine_tab)
        wine_layout.setSpacing(10)

        # Compatibility Tool (single selector for Proton + Wine)
        self.compat_tool = QComboBox()
        self.compat_tool.setEditable(True)
        self.compat_tool.addItem(self.config.compat_tool or "Auto")
        # Add available tools from game manager
        if hasattr(self, 'game_manager') and self.game_manager:
            for tool in self.game_manager.get_compat_tools():
                self.compat_tool.addItem(tool)
        self.compat_tool.setCurrentText(self.config.compat_tool or "Auto")
        wine_layout.addRow("Compatibility Tool:", self.compat_tool)

        # Component versions (auto-detected from selected tool, but overridable)
        self.dxvk_version = QLineEdit(self.config.dxvk_version)
        wine_layout.addRow("DXVK Version:", self.dxvk_version)

        self.vkd3d_version = QLineEdit(self.config.vkd3d_version)
        wine_layout.addRow("VKD3D Version:", self.vkd3d_version)

        tabs.addTab(wine_tab, "🍷 Wine/Proton")

        # Performance tab
        perf_tab = QWidget()
        perf_layout = QFormLayout(perf_tab)
        perf_layout.setSpacing(10)

        self.gamemode = QCheckBox("Enable")
        self.gamemode.setChecked(self.config.gamemode)
        perf_layout.addRow("GameMode:", self.gamemode)

        self.mangohud = QCheckBox("Enable")
        self.mangohud.setChecked(self.config.mangohud)
        perf_layout.addRow("MangoHud:", self.mangohud)

        self.vkbasalt = QCheckBox("Enable CAS Sharpening")
        self.vkbasalt.setChecked(self.config.vkbasalt)
        perf_layout.addRow("vkBasalt:", self.vkbasalt)

        self.fsr = QCheckBox("Enable FSR Upscaling")
        self.fsr.setChecked(self.config.fsr)
        perf_layout.addRow("FSR:", self.fsr)

        self.fps_limit = QSpinBox()
        self.fps_limit.setRange(0, 360)
        self.fps_limit.setValue(self.config.fps_limit)
        self.fps_limit.setSuffix(" FPS (0 = unlimited)")
        perf_layout.addRow("FPS Limit:", self.fps_limit)

        # ===== FPS BOOST / STUTTER REDUCTION =====
        perf_layout.addRow(QLabel(""))  # Spacer
        perf_layout.addRow(QLabel("<b>🚀 FPS Boost & Stutter Reduction</b>"))

        self.dxvk_async = QCheckBox("Enable (reduces shader compile stutter)")
        self.dxvk_async.setChecked(getattr(self.config, 'dxvk_async', False))
        perf_layout.addRow("DXVK Async:", self.dxvk_async)

        self.vkd3d_async = QCheckBox("Enable")
        self.vkd3d_async.setChecked(getattr(self.config, 'vkd3d_async', False))
        perf_layout.addRow("VKD3D Async:", self.vkd3d_async)

        self.disable_esync = QCheckBox("Disable (fixes some stutter/crashes)")
        self.disable_esync.setChecked(getattr(self.config, 'disable_esync', False))
        perf_layout.addRow("PROTON_NO_ESYNC:", self.disable_esync)

        self.disable_fsync = QCheckBox("Disable (if esync causes issues)")
        self.disable_fsync.setChecked(getattr(self.config, 'disable_fsync', False))
        perf_layout.addRow("PROTON_NO_FSYNC:", self.disable_fsync)

        self.nvapi_disable = QCheckBox("Disable (fixes NVAPI crashes on non-NVIDIA)")
        self.nvapi_disable.setChecked(getattr(self.config, 'nvapi_disable', False))
        perf_layout.addRow("PROTON_DISABLE_NVAPI:", self.nvapi_disable)

        self.wine_fullscreen_hack = QCheckBox("Enable (fixes fullscreen issues)")
        self.wine_fullscreen_hack.setChecked(getattr(self.config, 'wine_fullscreen_hack', False))
        perf_layout.addRow("WINE_FULLSCREEN_FSR:", self.wine_fullscreen_hack)

        self.prefer_d3d11 = QCheckBox("Prefer D3D11 over D3D12 (more stable)")
        self.prefer_d3d11.setChecked(getattr(self.config, 'prefer_d3d11', False))
        perf_layout.addRow("PROTON_FORCE_D3D11:", self.prefer_d3d11)

        self.gst_disable = QCheckBox("Disable (fixes video playback crashes)")
        self.gst_disable.setChecked(getattr(self.config, 'gst_disable', False))
        perf_layout.addRow("PROTON_NO_GSTREAMER:", self.gst_disable)

        # Memory/CPU
        perf_layout.addRow(QLabel(""))
        perf_layout.addRow(QLabel("<b>🧠 Memory & CPU</b>"))

        self.cpu_affinity = QLineEdit(self.config.cpu_affinity)
        self.cpu_affinity.setPlaceholderText("e.g., 0-3 for first 4 cores")
        perf_layout.addRow("CPU Affinity:", self.cpu_affinity)

        self.cpu_priority = QSpinBox()
        self.cpu_priority.setRange(-20, 19)
        self.cpu_priority.setValue(self.config.cpu_priority)
        perf_layout.addRow("Nice Priority:", self.cpu_priority)

        self.high_priority = QCheckBox("Run game at high priority (nice -10)")
        self.high_priority.setChecked(getattr(self.config, 'high_priority', False))
        perf_layout.addRow("High Priority:", self.high_priority)

        self.force_cores = QLineEdit(getattr(self.config, 'force_cores', ""))
        self.force_cores.setPlaceholderText("e.g., 4 (force 4 threads)")
        perf_layout.addRow("Force CPU Threads:", self.force_cores)

        self.large_address_aware = QCheckBox("Enable (allows >2GB RAM for 32-bit games)")
        self.large_address_aware.setChecked(getattr(self.config, 'large_address_aware', True))
        perf_layout.addRow("Large Address Aware:", self.large_address_aware)

        tabs.addTab(perf_tab, "🚀 Performance")

        # CPU tab
        cpu_tab = QWidget()
        cpu_layout = QFormLayout(cpu_tab)
        cpu_layout.setSpacing(10)

        tabs.addTab(cpu_tab, "🧠 CPU")

        # Launch options tab
        launch_tab = QWidget()
        launch_layout = QVBoxLayout(launch_tab)

        launch_label = QLabel("Launch Options (one per line):")
        launch_layout.addWidget(launch_label)

        self.launch_options = QTextEdit()
        self.launch_options.setPlainText("\n".join(self.config.launch_options))
        self.launch_options.setMaximumHeight(150)
        launch_layout.addWidget(self.launch_options)

        tabs.addTab(launch_tab, "🚀 Launch Options")

        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        buttons.setStyleSheet(f"""
            QDialogButtonBox QPushButton {{
                background-color: {KALI_BG_LIGHT};
                color: {KALI_GREEN};
                border: 1px solid {KALI_BORDER};
                border-radius: 6px;
                padding: 8px 20px;
                font-weight: bold;
                min-width: 80px;
            }}
            QDialogButtonBox QPushButton:hover {{
                background-color: {KALI_GREEN};
                color: {KALI_BG};
            }}
        """)
        layout.addWidget(buttons)

    def accept(self):
        # Update config
        self.config.compat_tool = self.compat_tool.currentText()
        self.config.dxvk_version = self.dxvk_version.text()
        self.config.vkd3d_version = self.vkd3d_version.text()
        self.config.gamemode = self.gamemode.isChecked()
        self.config.mangohud = self.mangohud.isChecked()
        self.config.vkbasalt = self.vkbasalt.isChecked()
        self.config.fsr = self.fsr.isChecked()
        self.config.fps_limit = self.fps_limit.value()
        
        # FPS Boost / Stutter Reduction
        self.config.dxvk_async = self.dxvk_async.isChecked()
        self.config.vkd3d_async = self.vkd3d_async.isChecked()
        self.config.disable_esync = self.disable_esync.isChecked()
        self.config.disable_fsync = self.disable_fsync.isChecked()
        self.config.nvapi_disable = self.nvapi_disable.isChecked()
        self.config.wine_fullscreen_hack = self.wine_fullscreen_hack.isChecked()
        self.config.prefer_d3d11 = self.prefer_d3d11.isChecked()
        self.config.gst_disable = self.gst_disable.isChecked()
        
        # Memory & CPU
        self.config.cpu_affinity = self.cpu_affinity.text()
        self.config.cpu_priority = self.cpu_priority.value()
        self.config.high_priority = self.high_priority.isChecked()
        self.config.force_cores = self.force_cores.text()
        self.config.large_address_aware = self.large_address_aware.isChecked()
        
        self.config.launch_options = [line.strip() for line in self.launch_options.toPlainText().split('\n') if line.strip()]
        super().accept()


class GameLaunchLogDialog(QDialog):
    """Real-time game launch log dialog."""
    def __init__(self, game_name: str, parent=None):
        super().__init__(parent)
        self.game_name = game_name
        self.setWindowTitle(f"🚀 Launching: {game_name}")
        self.setMinimumSize(800, 600)
        self.resize(1000, 700)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(12, 12, 12, 12)
        
        # Header
        header = QHBoxLayout()
        title = QLabel(f"🎮 {self.game_name}")
        title.setObjectName("title")
        header.addWidget(title)
        header.addStretch()
        
        self.status_label = QLabel("⏳ Starting...")
        self.status_label.setObjectName("subtitle")
        header.addWidget(self.status_label)
        
        self.close_btn = QPushButton("Close")
        self.close_btn.setFixedWidth(80)
        self.close_btn.setEnabled(False)
        self.close_btn.clicked.connect(self.accept)
        header.addWidget(self.close_btn)
        
        self.kill_btn = QPushButton("⛔ Kill Process")
        self.kill_btn.setObjectName("danger")
        self.kill_btn.setFixedWidth(120)
        self.kill_btn.clicked.connect(self.kill_process)
        header.addWidget(self.kill_btn)
        
        layout.addLayout(header)
        
        # Log display
        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        self.log_display.setFont(QFont("JetBrains Mono", 10))
        self.log_display.setStyleSheet(f"""
            QTextEdit {{
                background-color: {KALI_BG};
                color: {KALI_TEXT};
                border: 1px solid {KALI_BORDER};
                border-radius: 6px;
                padding: 8px;
            }}
        """)
        layout.addWidget(self.log_display, 1)
        
        # Progress bar (indeterminate while launching)
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)  # Indeterminate
        self.progress.setTextVisible(False)
        self.progress.setFixedHeight(4)
        layout.addWidget(self.progress)

        # Auto-fix panel (initially hidden)
        self.fix_panel = QGroupBox("🔧 Auto-Fix Detected Issues")
        self.fix_panel.setVisible(False)
        fix_layout = QVBoxLayout(self.fix_panel)

        self.fix_text = QTextEdit()
        self.fix_text.setReadOnly(True)
        self.fix_text.setMaximumHeight(150)
        self.fix_text.setFont(QFont("JetBrains Mono", 9))
        fix_layout.addWidget(self.fix_text)

        fix_btn_layout = QHBoxLayout()
        self.analyze_btn = QPushButton("🔍 Analyze Logs")
        self.analyze_btn.clicked.connect(self.analyze_and_show_fixes)
        fix_btn_layout.addWidget(self.analyze_btn)

        self.apply_fixes_btn = QPushButton("⚡ Apply Fixes")
        self.apply_fixes_btn.setObjectName("primary")
        self.apply_fixes_btn.clicked.connect(self.apply_detected_fixes)
        self.apply_fixes_btn.setEnabled(False)
        fix_btn_layout.addWidget(self.apply_fixes_btn)

        self.dry_run_btn = QPushButton("👁 Dry Run")
        self.dry_run_btn.clicked.connect(lambda: self.apply_detected_fixes(dry_run=True))
        self.dry_run_btn.setEnabled(False)
        fix_btn_layout.addWidget(self.dry_run_btn)

        fix_btn_layout.addStretch()
        fix_layout.addLayout(fix_btn_layout)

        layout.addWidget(self.fix_panel)

        self.process_stopped = False
        self._log_lines = []  # Store all log lines for analysis
        self._analyzer = None
        self._pending_fixes = []
        
    def add_log_line(self, line: str):
        """Add a line from game process output."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Colorize based on content
        if any(keyword in line.lower() for keyword in ['error', 'fail', 'fatal', 'crash', 'exception', 'traceback']):
            color = KALI_RED
            prefix = "✗ "
        elif any(keyword in line.lower() for keyword in ['warn', 'warning']):
            color = KALI_YELLOW
            prefix = "⚠ "
        elif any(keyword in line.lower() for keyword in ['success', 'ok', 'started', 'initialized', 'loaded']):
            color = KALI_GREEN
            prefix = "✓ "
        elif any(keyword in line.lower() for keyword in ['info', 'debug']):
            color = KALI_BLUE
            prefix = "ℹ "
        else:
            color = KALI_TEXT
            prefix = ""
            
        self.log_display.append(
            f'<span style="color: {KALI_TEXT_DIM};">[{timestamp}]</span> '
            f'<span style="color: {color};">{prefix}{line}</span>'
        )
        # Auto-scroll
        self.log_display.verticalScrollBar().setValue(self.log_display.verticalScrollBar().maximum())
        
    def set_status(self, status: str, is_final: bool = False):
        """Update status label."""
        self.status_label.setText(status)
        if is_final:
            self.progress.setRange(0, 1)
            self.progress.setValue(1)
            self.close_btn.setEnabled(True)
            self.kill_btn.setEnabled(False)
            self.process_stopped = True
            
    def kill_process(self):
        """Signal to kill the game/optimization process."""
        worker = getattr(self, 'launch_worker', None) or getattr(self, 'optim_worker', None)
        if worker:
            worker.stop()
            self.add_log_line("[User requested process termination]")
            self.set_status("⛔ Process terminated by user", is_final=True)

    def closeEvent(self, event):
        if not self.process_stopped:
            # Ask user if they want to kill the process
            from PyQt6.QtWidgets import QMessageBox
            reply = QMessageBox.question(
                self, "Game Running",
                f"{self.game_name} is still running. Close anyway?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.kill_process()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()

    def add_log_line(self, line: str):
        """Add a line from game process output (also stores for analysis)."""
        self._log_lines.append(line)
        timestamp = datetime.now().strftime("%H:%M:%S")

        # Colorize based on content
        if any(keyword in line.lower() for keyword in ['error', 'fail', 'fatal', 'crash', 'exception', 'traceback']):
            color = KALI_RED
            prefix = "✗ "
        elif any(keyword in line.lower() for keyword in ['warn', 'warning']):
            color = KALI_YELLOW
            prefix = "⚠ "
        elif any(keyword in line.lower() for keyword in ['success', 'ok', 'started', 'initialized', 'loaded']):
            color = KALI_GREEN
            prefix = "✓ "
        elif any(keyword in line.lower() for keyword in ['info', 'debug']):
            color = KALI_BLUE
            prefix = "ℹ "
        else:
            color = KALI_TEXT
            prefix = ""

        self.log_display.append(
            f'<span style="color: {KALI_TEXT_DIM};">[{timestamp}]</span> '
            f'<span style="color: {color};">{prefix}{line}</span>'
        )
        # Auto-scroll
        self.log_display.verticalScrollBar().setValue(self.log_display.verticalScrollBar().maximum())

    def analyze_and_show_fixes(self):
        """Analyze collected logs and show suggested fixes."""
        if not self._log_lines:
            self.fix_text.setHtml("<span style='color: #888;'>No logs captured yet</span>")
            return

        # Get game prefix path
        game = None
        if hasattr(self, 'launch_worker') and self.launch_worker:
            game_id = self.launch_worker.game_id
            if hasattr(self, 'game_manager') and self.game_manager:
                game = self.game_manager.get_game(game_id)

        prefix_path = game.prefix_path if game else None
        if not prefix_path and hasattr(self, 'parent') and self.parent():
            # Try to get from parent main window
            main = self.parent()
            if hasattr(main, 'game_library') and main.game_library.selected_game:
                prefix_path = main.game_library.selected_game.prefix_path

        if not prefix_path:
            self.fix_text.setHtml("<span style='color: #ff8800;'>Could not determine game prefix path</span>")
            return

        # Analyze
        self._analyzer = GameErrorAnalyzer(prefix_path)
        issues = self._analyzer.analyze_logs(self._log_lines)

        if not issues:
            self.fix_text.setHtml("<span style='color: #00ff88;'>✅ No known error patterns detected</span>")
            self.fix_panel.setVisible(True)
            self.apply_fixes_btn.setEnabled(False)
            self.dry_run_btn.setEnabled(False)
            return

        # Show analysis
        report = self._analyzer.generate_report()
        # Convert to HTML for display
        html_report = report.replace("\n", "<br>").replace("  ", "&nbsp;&nbsp;")
        self.fix_text.setHtml(f"<span style='color: #ccaa00;'>{html_report}</span>")

        self.fix_panel.setVisible(True)
        self.apply_fixes_btn.setEnabled(True)
        self.dry_run_btn.setEnabled(True)
        self._pending_fixes = self._analyzer.get_recommended_fixes()

    def apply_detected_fixes(self, dry_run: bool = False):
        """Apply the detected fixes to the game prefix."""
        if not self._analyzer:
            return

        # Get prefix path (same logic as analyze)
        game = None
        if hasattr(self, 'launch_worker') and self.launch_worker:
            game_id = self.launch_worker.game_id
            if hasattr(self, 'game_manager') and self.game_manager:
                game = self.game_manager.get_game(game_id)

        prefix_path = game.prefix_path if game else None
        if not prefix_path and hasattr(self, 'parent') and self.parent():
            main = self.parent()
            if hasattr(main, 'game_library') and main.game_library.selected_game:
                prefix_path = main.game_library.selected_game.prefix_path

        if not prefix_path:
            self.fix_text.append("<br><span style='color: #ff4444;'>❌ Could not determine game prefix path</span>")
            return

        # Apply fixes
        self.apply_fixes_btn.setEnabled(False)
        self.dry_run_btn.setEnabled(False)
        self.analyze_btn.setEnabled(False)
        self.fix_text.append("<br><span style='color: #00ff88;'>⚡ Applying fixes...</span>")

        # Run in a simple way (blocking - could be improved with worker thread)
        results = self._analyzer.apply_fixes(prefix_path, dry_run=dry_run)

        for result in results:
            status = "✅" if result.success else "❌"
            color = "#00ff88" if result.success else "#ff4444"
            self.fix_text.append(
                f'<br><span style="color: {color};">{status} '
                f'{", ".join(result.winetricks_applied)}: {result.message}</span>'
            )

        if not dry_run:
            self.fix_text.append('<br><span style="color: #00ff88;">✅ Fixes applied. Try launching again.</span>')
        else:
            self.fix_text.append('<br><span style="color: #0099cc;">👁 Dry run complete. Click "Apply Fixes" to execute.</span>')

        self.apply_fixes_btn.setEnabled(True)
        self.dry_run_btn.setEnabled(True)
        self.analyze_btn.setEnabled(True)


# ============================================================
# MAIN WINDOW
# ============================================================

class MainWindow(QMainWindow):
    """Main application window."""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CachyOS Game Optimizer")
        self.setMinimumSize(1400, 900)
        self.resize(1600, 1000)

        # Core components
        self.detector = get_detector()
        self.optimizer = get_optimizer()
        self.game_manager = get_game_manager()

        # State
        self.profile: Optional[SystemProfile] = None
        self.recommendations: List[Dict] = []
        self.optimization_results: List[OptimizationResult] = []

        # Workers
        self.hw_worker: Optional[HardwareDetectionWorker] = None
        self.opt_worker: Optional[OptimizationWorker] = None
        self.launch_worker: Optional[GameLaunchWorker] = None

        self.setup_ui()
        self.apply_theme()
        self.start_hardware_detection()

    def setup_ui(self):
        # Central widget with splitter
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setSpacing(8)
        main_layout.setContentsMargins(8, 8, 8, 8)

        # Top toolbar
        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)

        title_label = QLabel("CachyOS Game Optimizer")
        title_label.setObjectName("title")
        title_label.setStyleSheet(f"color: {KALI_GREEN}; font-size: 20px; font-weight: bold;")
        toolbar.addWidget(title_label)

        toolbar.addStretch()

        self.refresh_btn = QPushButton("🔄 Refresh")
        self.refresh_btn.setFixedWidth(120)
        toolbar.addWidget(self.refresh_btn)

        self.optimize_all_btn = QPushButton("⚡ Optimize All")
        self.optimize_all_btn.setObjectName("primary")
        self.optimize_all_btn.setFixedWidth(160)
        toolbar.addWidget(self.optimize_all_btn)

        toolbar.addSpacing(20)

        # System status
        self.status_label = QLabel("🔄 Detecting hardware...")
        self.status_label.setObjectName("subtitle")
        toolbar.addWidget(self.status_label)

        main_layout.addLayout(toolbar)

        # Main splitter
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        main_splitter.setChildrenCollapsible(False)
        main_layout.addWidget(main_splitter, 1)

        # Left panel - Hardware
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setSpacing(8)
        left_layout.setContentsMargins(0, 0, 0, 0)

        self.hardware_panel = HardwarePanel()
        left_layout.addWidget(self.hardware_panel)

        main_splitter.addWidget(left_widget)

        # Center panel - Optimizations + Games
        center_widget = QWidget()
        center_layout = QVBoxLayout(center_widget)
        center_layout.setSpacing(8)
        center_layout.setContentsMargins(0, 0, 0, 0)

        center_splitter = QSplitter(Qt.Orientation.Vertical)
        center_splitter.setChildrenCollapsible(False)
        center_layout.addWidget(center_splitter, 1)

        self.optimization_panel = OptimizationPanel()
        center_splitter.addWidget(self.optimization_panel)

        self.game_library = GameLibraryPanel()
        self.game_library.set_game_manager(self.game_manager)
        self.game_library.set_log_callback(self.log)
        center_splitter.addWidget(self.game_library)

        # Wine/Proton Downloads tab
        self.wine_proton_tab = WineProtonTab()
        self.wine_proton_tab.log_message.connect(self.log)
        self.wine_proton_tab.downloads_updated.connect(self.on_wine_proton_updated)
        center_splitter.addWidget(self.wine_proton_tab)

        center_splitter.setSizes([300, 300, 300])
        main_splitter.addWidget(center_widget)

        # Right panel - Game Config (empty initially, filled on selection)
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setSpacing(8)
        right_layout.setContentsMargins(0, 0, 0, 0)

        self.config_label = QLabel("⚙️ GAME CONFIG")
        self.config_label.setObjectName("title")
        right_layout.addWidget(self.config_label)

        self.config_scroll = QScrollArea()
        self.config_scroll.setWidgetResizable(True)
        self.config_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.config_scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        self.config_content = QLabel("Select a game to configure")
        self.config_content.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.config_content.setStyleSheet(f"color: {KALI_TEXT_DIM}; font-size: 14px; padding: 40px;")
        self.config_scroll.setWidget(self.config_content)
        right_layout.addWidget(self.config_scroll)

        main_splitter.addWidget(right_widget)

        # Set splitter sizes
        main_splitter.setSizes([350, 700, 350])

        # Bottom log panel
        self.log_panel = LogPanel()
        main_layout.addWidget(self.log_panel)

        # Connect signals
        self.refresh_btn.clicked.connect(self.start_hardware_detection)
        self.optimize_all_btn.clicked.connect(self.run_optimizations)
        self.optimization_panel.optimize_all_btn.clicked.connect(self.run_optimizations)
        self.optimization_panel.optimize_cpu_btn.clicked.connect(lambda: self.run_optimizations("cpu"))
        self.optimization_panel.optimize_gpu_btn.clicked.connect(lambda: self.run_optimizations("gpu"))
        self.optimization_panel.optimize_mem_btn.clicked.connect(lambda: self.run_optimizations("memory"))
        self.game_library.launch_btn.clicked.connect(self.launch_selected_game)
        self.game_library.config_btn.clicked.connect(self.configure_selected_game)

    def apply_theme(self):
        self.setStyleSheet(STYLESHEET)
        # Set window icon if available
        # self.setWindowIcon(QIcon("icon.png"))

    def log(self, message: str):
        self.log_panel.log(message)

    def start_hardware_detection(self):
        self.status_label.setText("🔄 Detecting hardware...")
        self.optimize_all_btn.setEnabled(False)

        self.hw_worker = HardwareDetectionWorker()
        self.hw_worker.finished.connect(self.on_hardware_detected)
        self.hw_worker.error.connect(self.on_hardware_error)
        self.hw_worker.log.connect(self.log)
        self.hw_worker.start()

    def on_hardware_detected(self, profile: SystemProfile, recommendations: List[Dict]):
        self.profile = profile
        self.recommendations = recommendations

        self.hardware_panel.update_profile(profile)
        self.optimization_panel.set_recommendations(recommendations)

        self.status_label.setText(f"✓ {profile.cpu.model} | {profile.gpu.vendor} {profile.gpu.model} | {profile.memory.total_gb:.1f}GB RAM")
        self.optimize_all_btn.setEnabled(True)

        # Load existing games from library (no auto-scan)
        existing_games = self.game_manager.list_games()
        self.game_library.set_games(existing_games)

    def on_hardware_error(self, error: str):
        self.log(f"✗ Hardware detection failed: {error}")
        self.status_label.setText("✗ Hardware detection failed")
        self.optimize_all_btn.setEnabled(True)

    def on_wine_proton_updated(self):
        """Called when Wine/Proton downloads tab finishes a download."""
        # The GameConfigDialog will pick up new versions on next open
        # since it queries game_manager.get_proton_versions() dynamically
        self.log("🔄 Wine/Proton versions updated - new versions available in game config")

    def run_optimizations(self, category: Optional[str] = None):
        if not self.recommendations:
            QMessageBox.warning(self, "No Recommendations", "Run hardware detection first.")
            return

        self.optimize_all_btn.setEnabled(False)
        self.optimize_all_btn.setText("⚡ Optimizing...")

        # Create optimization log dialog
        self.optim_dialog = GameLaunchLogDialog("System Optimizations", self)
        self.optim_dialog.setWindowTitle("⚡ Applying Optimizations")
        
        self.optim_worker = OptimizationWorker(self.optimizer, category)
        self.optim_worker.launch_dialog = self.optim_dialog  # For kill button
        
        # Connect signals
        self.optim_worker.finished.connect(self.on_optimizations_finished)
        self.optim_worker.log.connect(self.log)
        self.optim_worker.output_line.connect(self.optim_dialog.add_log_line)
        self.optim_worker.finished.connect(lambda results: self.optim_dialog.set_status(
            f"✓ Complete: {sum(1 for r in results if r.status == OptimizationStatus.SUCCESS)} success, "
            f"{sum(1 for r in results if r.status == OptimizationStatus.FAILED)} failed, "
            f"{sum(1 for r in results if r.status == OptimizationStatus.SKIPPED)} skipped", 
            is_final=True
        ))
        
        # Show dialog (non-blocking)
        self.optim_dialog.show()
        
        # Start the worker
        self.optim_worker.start()

    def on_optimization_progress(self, action_id: str, status: str):
        self.optimization_panel.set_results(self.optim_worker.optimizer.results if self.optim_worker else [])

    def on_optimizations_finished(self, results: List[OptimizationResult]):
        self.optimization_results = results
        self.optimization_panel.set_results(results)
        self.optimize_all_btn.setEnabled(True)
        self.optimize_all_btn.setText("⚡ Optimize All")

        # Re-detect hardware to show updated state
        self.start_hardware_detection()

    def launch_selected_game(self):
        game = self.game_library.selected_game
        if not game:
            return

        self.game_library.launch_btn.setEnabled(False)
        self.game_library.launch_btn.setText("🚀 Launching...")

        # Create launch log dialog
        self.launch_dialog = GameLaunchLogDialog(game.name, self)
        self.launch_dialog.launch_worker = self.launch_worker = GameLaunchWorker(self.game_manager, game.id)
        
        # Connect signals
        self.launch_worker.finished.connect(self.on_game_launched)
        self.launch_worker.log.connect(self.log)
        self.launch_worker.output_line.connect(self.launch_dialog.add_log_line)
        self.launch_worker.finished.connect(lambda success, msg: self.launch_dialog.set_status(msg, is_final=True))
        
        # Show dialog (non-blocking)
        self.launch_dialog.show()
        
        # Start the worker
        self.launch_worker.start()

    def on_game_launched(self, success: bool, message: str):
        self.game_library.launch_btn.setEnabled(True)
        self.game_library.launch_btn.setText("🚀 Launch")

        if not success:
            QMessageBox.critical(self, "Launch Failed", message)

    def configure_selected_game(self):
        game = self.game_library.selected_game
        if not game:
            return

        dialog = GameConfigDialog(game, self, game_manager=self.game_manager)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.game_manager.save_library()
            self.log(f"⚙️ Configuration saved for {game.name}")

            # Update config display
            self.update_config_display(game)

    def update_config_display(self, game: Game):
        config = game.config

        # Clear existing content
        if self.config_scroll.widget():
            self.config_scroll.widget().deleteLater()

        # Create new config display
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setSpacing(12)

        # Game info
        info_group = QGroupBox("🎮 Game Info")
        info_layout = QFormLayout(info_group)
        info_layout.addRow("Name:", QLabel(game.name))
        info_layout.addRow("Source:", QLabel(game.source.value))
        info_layout.addRow("Path:", QLabel(game.install_path or "—"))
        info_layout.addRow("Executable:", QLabel(Path(game.exe_path).name if game.exe_path else "—"))
        info_layout.addRow("Prefix:", QLabel(game.prefix_path or "—"))
        layout.addWidget(info_group)

        # Wine/Proton
        wine_group = QGroupBox("🍷 Wine/Proton")
        wine_layout = QFormLayout(wine_group)
        wine_layout.addRow("Compat Tool:", QLabel(config.compat_tool or "Auto"))
        wine_layout.addRow("DXVK:", QLabel(config.dxvk_version))
        wine_layout.addRow("VKD3D:", QLabel(config.vkd3d_version))
        layout.addWidget(wine_group)

        # Performance
        perf_group = QGroupBox("🚀 Performance")
        perf_layout = QFormLayout(perf_group)
        perf_layout.addRow("GameMode:", QLabel("✓ Enabled" if config.gamemode else "✗ Disabled"))
        perf_layout.addRow("MangoHud:", QLabel("✓ Enabled" if config.mangohud else "✗ Disabled"))
        perf_layout.addRow("vkBasalt:", QLabel("✓ Enabled" if config.vkbasalt else "✗ Disabled"))
        perf_layout.addRow("FSR:", QLabel("✓ Enabled" if config.fsr else "✗ Disabled"))
        perf_layout.addRow("FPS Limit:", QLabel(str(config.fps_limit) if config.fps_limit > 0 else "Unlimited"))
        layout.addWidget(perf_group)

        # CPU
        cpu_group = QGroupBox("🧠 CPU")
        cpu_layout = QFormLayout(cpu_group)
        cpu_layout.addRow("Affinity:", QLabel(config.cpu_affinity or "All cores"))
        cpu_layout.addRow("Nice:", QLabel(str(config.cpu_priority)))
        layout.addWidget(cpu_group)

        # Launch options
        if config.launch_options:
            launch_group = QGroupBox("🚀 Launch Options")
            launch_layout = QVBoxLayout(launch_group)
            for opt in config.launch_options:
                launch_layout.addWidget(QLabel(f"  {opt}"))
            layout.addWidget(launch_group)

        layout.addStretch()
        self.config_scroll.setWidget(content)


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("CachyOS Game Optimizer")
    app.setApplicationVersion("1.0.0")

    # Load font
    QFontDatabase.addApplicationFont("/usr/share/fonts/TTF/JetBrainsMono-Regular.ttf")

    # Set default font
    default_font = QFont("JetBrains Mono", 10)
    if not default_font.exactMatch():
        default_font = QFont("Fira Code", 10)
    if not default_font.exactMatch():
        default_font = QFont("Monospace", 10)
    app.setFont(default_font)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()