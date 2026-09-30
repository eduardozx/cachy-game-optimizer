"""
CachyOS Game Optimizer - Main TUI Application
Futuristic terminal UI for game optimization and launching.
"""

import asyncio
import os
import sys
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.widgets import (
    Header, Footer, Static, Button, DataTable, TabbedContent, TabPane,
    Input, Select, Checkbox, Label, ProgressBar, RichLog, Sparkline, Collapsible
)
from textual.binding import Binding
from textual.screen import Screen
from textual.reactive import reactive
from textual.message import Message
from rich.text import Text
from rich.panel import Panel
from rich.table import Table
from rich.console import Console

from .hardware import get_detector, SystemProfile, CPUInfo, GPUInfo, MemoryInfo
from .optimizer import get_optimizer, OptimizationEngine, OptimizationResult, OptimizationStatus
from .games import get_game_manager, GameManager, Game, GameSource, GameConfig


class HardwarePanel(Static):
    """Display hardware information in a futuristic style."""
    
    profile: reactive[Optional[SystemProfile]] = reactive(None)
    
    def watch_profile(self, profile: Optional[SystemProfile]):
        self.update_content()
    
    def update_content(self):
        if not self.profile:
            self.update("Loading hardware info...")
            return
        
        cpu = self.profile.cpu
        gpu = self.profile.gpu
        mem = self.profile.memory
        
        content = Table.grid(padding=(0, 2))
        content.add_column(style="bold cyan", width=20)
        content.add_column(style="green")
        
        # CPU
        content.add_row("⚡ CPU", f"{cpu.model}")
        content.add_row("   Cores/Threads", f"{cpu.cores}C / {cpu.threads}T")
        content.add_row("   Base/Boost", f"{cpu.base_clock:.1f}GHz / {cpu.boost_clock:.1f}GHz")
        content.add_row("   Governor", f"[{'green' if cpu.governor == 'performance' else 'yellow'}]{cpu.governor}[/]")
        content.add_row("   Cache L3", cpu.cache_l3)
        
        content.add_row("", "")
        
        # GPU
        content.add_row("🎮 GPU", f"{gpu.vendor} {gpu.model}")
        content.add_row("   VRAM", f"{gpu.vram_mb} MB")
        content.add_row("   Driver", f"{gpu.driver_version}")
        content.add_row("   Vulkan", "✓" if gpu.vulkan_support else "✗")
        content.add_row("   PCIe", f"Gen {gpu.pcie_gen} {gpu.pcie_width}")
        
        content.add_row("", "")
        
        # Memory
        content.add_row("🧠 RAM", f"{mem.total_gb:.1f} GB {mem.type}-{mem.speed_mhz}")
        content.add_row("   Available", f"{mem.available_gb:.1f} GB ({mem.usage_percent:.1f}% used)")
        content.add_row("   Channels", f"{mem.channels}x")
        
        content.add_row("", "")
        
        # Kernel
        kernel = self.profile.kernel
        content.add_row("🐧 Kernel", kernel.version.split()[2] if len(kernel.version.split()) > 2 else kernel.version)
        content.add_row("   Scheduler", kernel.scheduler)
        content.add_row("   Swappiness", str(kernel.swappiness))
        content.add_row("   THP", kernel.transparent_hugepages)
        
        self.update(Panel(content, title="[bold magenta]HARDWARE PROFILE[/]", border_style="magenta"))


class OptimizationPanel(Static):
    """Display optimization recommendations and status."""
    
    recommendations: reactive[List[Dict]] = reactive([])
    results: reactive[List[OptimizationResult]] = reactive([])
    
    def watch_recommendations(self, recs: List[Dict]):
        self.update_content()
    
    def watch_results(self, results: List[OptimizationResult]):
        self.update_content()
    
    def update_content(self):
        if not self.recommendations:
            self.update("No recommendations - run hardware detection first")
            return
        
        table = Table.grid(padding=(0, 1))
        table.add_column(style="bold yellow", width=8)
        table.add_column(style="cyan", width=30)
        table.add_column(style="white", width=50)
        table.add_column(style="green", width=12)
        
        table.add_row("PRIORITY", "ACTION", "DESCRIPTION", "STATUS")
        
        # Build status map from results
        status_map = {r.action_id: r.status for r in self.results}
        
        for rec in self.recommendations:
            action_id = rec.get('action', '')
            status = status_map.get(action_id, OptimizationStatus.PENDING)
            
            status_style = {
                OptimizationStatus.PENDING: "dim white",
                OptimizationStatus.RUNNING: "yellow",
                OptimizationStatus.SUCCESS: "green",
                OptimizationStatus.FAILED: "red",
                OptimizationStatus.SKIPPED: "blue",
            }.get(status, "white")
            
            status_text = {
                OptimizationStatus.PENDING: "⏳ PENDING",
                OptimizationStatus.RUNNING: "🔄 RUNNING",
                OptimizationStatus.SUCCESS: "✓ DONE",
                OptimizationStatus.FAILED: "✗ FAILED",
                OptimizationStatus.SKIPPED: "⊘ SKIP",
            }.get(status, "?")
            
            table.add_row(
                f"[{rec.get('priority', 'LOW')}]",
                rec.get('title', ''),
                rec.get('description', '')[:50] + ("..." if len(rec.get('description', '')) > 50 else ""),
                f"[{status_style}]{status_text}[/]"
            )
        
        self.update(Panel(table, title="[bold magenta]OPTIMIZATIONS[/]", border_style="magenta"))


class GameLibraryPanel(Static):
    """Display game library with launch buttons."""
    
    games: reactive[List[Game]] = reactive([])
    selected_game: reactive[Optional[Game]] = reactive(None)
    
    def watch_games(self, games: List[Game]):
        self.update_content()
    
    def update_content(self):
        if not self.games:
            self.update("No games found. Click 'Scan Libraries' to detect games.")
            return
        
        table = Table.grid(padding=(0, 1))
        table.add_column(style="bold cyan", width=3, justify="right")
        table.add_column(style="white", width=35)
        table.add_column(style="yellow", width=12)
        table.add_column(style="green", width=10)
        table.add_column(style="magenta", width=10)
        
        table.add_row("#", "NAME", "SOURCE", "PLAYTIME", "ACTION")
        
        for i, game in enumerate(self.games):
            is_selected = self.selected_game and self.selected_game.id == game.id
            style = "bold reverse" if is_selected else ""
            
            source_icon = {
                GameSource.STEAM: "🎮 Steam",
                GameSource.HEROIC: "🦸 Heroic",
                GameSource.LUTRIS: "🎲 Lutris",
                GameSource.BOTTLES: "🍾 Bottles",
                GameSource.FLATPAK: "📦 Flatpak",
                GameSource.NATIVE: "🐧 Native",
                GameSource.CUSTOM: "⚙️ Custom",
            }.get(game.source, game.source.value)
            
            playtime = f"{game.hours_played:.1f}h" if game.hours_played > 0 else "—"
            
            table.add_row(
                f"[{style}]{i+1}[/]",
                f"[{style}]{game.name[:33]}[/]",
                f"[{style}]{source_icon}[/]",
                f"[{style}]{playtime}[/]",
                f"[{style}][LAUNCH][/]" if is_selected else "",
            )
        
        self.update(Panel(table, title="[bold magenta]GAME LIBRARY[/]", border_style="magenta"))


class GameConfigPanel(Static):
    """Game-specific configuration panel."""
    
    game: reactive[Optional[Game]] = reactive(None)
    
    def watch_game(self, game: Optional[Game]):
        self.update_content()
    
    def update_content(self):
        if not self.game:
            self.update("Select a game to configure")
            return
        
        config = self.game.config
        
        content = Table.grid(padding=(0, 2))
        content.add_column(style="bold cyan", width=25)
        content.add_column(style="green")
        
        content.add_row("🎮 Game", self.game.name)
        content.add_row("📁 Source", self.game.source.value)
        content.add_row("📂 Install Path", self.game.install_path or "—")
        content.add_row("🎯 Executable", Path(self.game.exe_path).name if self.game.exe_path else "—")
        content.add_row("", "")
        
        content.add_row("⚙️ Wine/Proton", "")
        content.add_row("   Backend", config.wine_backend)
        content.add_row("   Proton Version", config.proton_version or "Auto")
        content.add_row("   DXVK", config.dxvk_version)
        content.add_row("   VKD3D", config.vkd3d_version)
        content.add_row("", "")
        
        content.add_row("🚀 Performance", "")
        content.add_row("   GameMode", "✓" if config.gamemode else "✗")
        content.add_row("   MangoHud", "✓" if config.mangohud else "✗")
        content.add_row("   vkBasalt (CAS)", "✓" if config.vkbasalt else "✗")
        content.add_row("   FSR Upscaling", "✓" if config.fsr else "✗")
        content.add_row("   FPS Limit", str(config.fps_limit) if config.fps_limit > 0 else "Unlimited")
        content.add_row("", "")
        
        content.add_row("🧠 CPU", "")
        content.add_row("   Affinity", config.cpu_affinity or "All cores")
        content.add_row("   Priority (nice)", str(config.cpu_priority))
        content.add_row("", "")
        
        content.add_row("🎮 Launch Options", "")
        if config.launch_options:
            for opt in config.launch_options:
                content.add_row("   ", opt)
        else:
            content.add_row("   ", "(none)")
        
        self.update(Panel(content, title="[bold magenta]GAME CONFIG[/]", border_style="magenta"))


class LogPanel(RichLog):
    """Application log panel."""
    
    def __init__(self):
        super().__init__()
        self.write("[dim]CachyOS Game Optimizer initialized[/dim]")
        self.write("[dim]Waiting for hardware detection...[/dim]")


class CachyGameOptimizerApp(App):
    """Main application class."""
    
    TITLE = "CachyOS Game Optimizer"
    SUB_TITLE = "Futuristic Gaming Performance Suite"
    
    CSS = """
    Screen {
        background: #0d0d0d;
    }
    
    Header {
        background: #1a1a1a;
        color: #00ff88;
        text-style: bold;
        border-bottom: solid #00ff88;
    }
    
    Footer {
        background: #1a1a1a;
        color: #00ff88;
        border-top: solid #00ff88;
    }
    
    .panel {
        border: solid #00ff88;
        background: #111111;
        margin: 1;
        padding: 1;
    }
    
    .panel-title {
        color: #00ff88;
        text-style: bold;
    }
    
    Button {
        background: #1a1a1a;
        color: #00ff88;
        border: solid #00ff88;
        margin: 0 1;
    }
    
    Button:hover {
        background: #00ff88;
        color: #0d0d0d;
    }
    
    Button:focus {
        background: #00ff88;
        color: #0d0d0d;
    }
    
    .button-primary {
        background: #00ff88;
        color: #0d0d0d;
        border: solid #00ff88;
    }
    
    .button-primary:hover {
        background: #00cc66;
    }
    
    .button-danger {
        background: #1a1a1a;
        color: #ff4444;
        border: solid #ff4444;
    }
    
    .button-danger:hover {
        background: #ff4444;
        color: #0d0d0d;
    }
    
    DataTable {
        background: #111111;
        color: #d4d4d4;
    }
    
    DataTable > .datatable--header {
        background: #1a1a1a;
        color: #00ff88;
        text-style: bold;
    }
    
    DataTable > .datatable--cursor {
        background: #00ff88;
        color: #0d0d0d;
    }
    
    Input {
        background: #1a1a1a;
        color: #d4d4d4;
        border: solid #333333;
    }
    
    Input:focus {
        border: solid #00ff88;
    }
    
    Select {
        background: #1a1a1a;
        color: #d4d4d4;
        border: solid #333333;
    }
    
    Select:focus {
        border: solid #00ff88;
    }
    
    Checkbox {
        color: #d4d4d4;
    }
    
    Checkbox:focus {
        color: #00ff88;
    }
    
    TabbedContent {
        background: #111111;
    }
    
    TabPane {
        background: #111111;
    }
    
    .tab {
        color: #888888;
        background: #1a1a1a;
        border: solid #333333;
    }
    
    .tab:focus, .tab--active {
        color: #00ff88;
        background: #111111;
        border: solid #00ff88;
    }
    
    Log {
        background: #0a0a0a;
        color: #888888;
        border: solid #333333;
    }
    
    ProgressBar {
        background: #1a1a1a;
        color: #00ff88;
    }
    
    Sparkline {
        color: #00ff88;
    }
    
    #main-container {
        layout: grid;
        grid-size: 3;
        grid-gutter: 1;
        grid-rows: 1fr 1fr;
        grid-columns: 1fr 2fr 1fr;
    }
    
    #hardware-panel {
        row-span: 2;
    }
    
    #optimization-panel {
        row-span: 2;
    }
    
    #game-library {
        height: 1fr;
    }
    
    #game-config {
        height: 1fr;
    }
    
    #log-panel {
        column-span: 3;
        height: 20;
    }
    """
    
    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("r", "refresh", "Refresh"),
        Binding("o", "optimize_all", "Optimize All"),
        Binding("s", "scan_games", "Scan Games"),
        Binding("l", "launch_game", "Launch Game"),
        Binding("c", "config_game", "Config Game"),
        Binding("ctrl+c", "quit", "Quit"),
    ]
    
    def __init__(self):
        super().__init__()
        self.detector = get_detector()
        self.optimizer = get_optimizer()
        self.game_manager = get_game_manager()
        self.profile: Optional[SystemProfile] = None
        self.recommendations: List[Dict] = []
        self.optimization_results: List[OptimizationResult] = []
    
    def compose(self) -> ComposeResult:
        yield Header()
        
        with Container(id="main-container"):
            # Left column - Hardware
            yield HardwarePanel(id="hardware-panel", classes="panel")
            
            # Middle column - Optimizations + Game Library
            with Vertical():
                yield OptimizationPanel(id="optimization-panel", classes="panel")
                with Horizontal():
                    yield Button("🔍 Scan Libraries", id="btn-scan", variant="primary")
                    yield Button("⚡ Optimize All", id="btn-optimize", variant="primary")
                    yield Button("🚀 Launch", id="btn-launch", variant="primary")
                yield GameLibraryPanel(id="game-library", classes="panel")
            
            # Right column - Game Config
            yield GameConfigPanel(id="game-config", classes="panel")
        
        # Log panel at bottom
        yield LogPanel(id="log-panel")
        
        yield Footer()
    
    def on_mount(self):
        self.log_panel = self.query_one("#log-panel", LogPanel)
        self.hardware_panel = self.query_one("#hardware-panel", HardwarePanel)
        self.optimization_panel = self.query_one("#optimization-panel", OptimizationPanel)
        self.game_library = self.query_one("#game-library", GameLibraryPanel)
        self.game_config = self.query_one("#game-config", GameConfigPanel)
        
        # Start hardware detection
        self.call_later(self.detect_hardware)
    
    async def detect_hardware(self):
        """Detect hardware in background."""
        self.log("🔍 Detecting hardware...")
        
        def _detect():
            profile = self.detector.get_full_profile()
            recommendations = self.detector.get_optimization_recommendations()
            return profile, recommendations
        
        try:
            profile, recs = await asyncio.get_event_loop().run_in_executor(None, _detect)
            self.profile = profile
            self.recommendations = recs
            
            self.hardware_panel.profile = profile
            self.optimization_panel.recommendations = recs
            
            self.log(f"✓ Hardware detected: {profile.cpu.model}")
            self.log(f"✓ GPU: {profile.gpu.vendor} {profile.gpu.model} ({profile.gpu.vram_mb}MB VRAM)")
            self.log(f"✓ RAM: {profile.memory.total_gb:.1f}GB {profile.memory.type}-{profile.memory.speed_mhz}")
            self.log(f"✓ Found {len(recs)} optimization recommendations")
            
            # Auto-load games
            await self.scan_games()
            
        except Exception as e:
            self.log(f"✗ Hardware detection failed: {e}")
    
    async def scan_games(self):
        """Scan all game libraries."""
        self.log("🔍 Scanning game libraries...")
        
        def _scan():
            return self.game_manager.scan_all_sources()
        
        try:
            results = await asyncio.get_event_loop().run_in_executor(None, _scan)
            total = sum(len(games) for games in results.values())
            self.log(f"✓ Found {total} games across all sources")
            
            for source, games in results.items():
                if games:
                    self.log(f"  {source.value}: {len(games)} games")
            
            # Update game library panel
            all_games = []
            for games in results.values():
                all_games.extend(games)
            self.game_library.games = all_games
            
        except Exception as e:
            self.log(f"✗ Game scan failed: {e}")
    
    def log(self, message: str):
        """Log message to log panel."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_panel.write_line(f"[dim]{timestamp}[/dim] {message}")
    
    def on_button_pressed(self, event: Button.Pressed):
        button_id = event.button.id
        
        if button_id == "btn-scan":
            self.action_scan_games()
        elif button_id == "btn-optimize":
            self.action_optimize_all()
        elif button_id == "btn-launch":
            self.action_launch_game()
    
    def action_refresh(self):
        """Refresh hardware detection and game library."""
        self.log("🔄 Refreshing...")
        self.call_later(self.detect_hardware)
    
    def action_scan_games(self):
        """Scan game libraries."""
        self.call_later(self.scan_games)
    
    def action_optimize_all(self):
        """Run all recommended optimizations."""
        if not self.recommendations:
            self.log("⚠ No recommendations available")
            return
        
        self.log("⚡ Running all optimizations...")
        self.optimization_panel.results = []  # Clear previous
        
        async def _run_optimizations():
            results = self.optimizer.run_all_recommended()
            self.optimization_results = results
            self.optimization_panel.results = results
            
            success = sum(1 for r in results if r.status == OptimizationStatus.SUCCESS)
            failed = sum(1 for r in results if r.status == OptimizationStatus.FAILED)
            skipped = sum(1 for r in results if r.status == OptimizationStatus.SKIPPED)
            
            self.log(f"✓ Optimizations complete: {success} success, {failed} failed, {skipped} skipped")
            
            # Re-detect hardware to show updated state
            await self.detect_hardware()
        
        self.call_later(_run_optimizations)
    
    def action_optimize_category(self, category: str):
        """Run optimizations for a specific category."""
        self.log(f"⚡ Running {category} optimizations...")
        
        async def _run():
            results = self.optimizer.run_category(category)
            self.optimization_results.extend(results)
            self.optimization_panel.results = self.optimization_results
            
            success = sum(1 for r in results if r.status == OptimizationStatus.SUCCESS)
            self.log(f"✓ {category}: {success} optimizations applied")
        
        self.call_later(_run)
    
    def action_launch_game(self):
        """Launch selected game."""
        game = self.game_library.selected_game
        if not game:
            self.log("⚠ No game selected")
            return
        
        self.log(f"🚀 Launching {game.name}...")
        
        async def _launch():
            result = self.game_manager.launch_game(game.id)
            if result['success']:
                self.log(f"✓ Launched {game.name} (PID: {result.get('pid', 'N/A')})")
            else:
                self.log(f"✗ Launch failed: {result.get('error', 'Unknown error')}")
        
        self.call_later(_launch)
    
    def action_config_game(self):
        """Open game configuration."""
        game = self.game_library.selected_game
        if game:
            self.game_config.game = game
            self.log(f"⚙️ Configuring {game.name}")
    
    def on_data_table_row_selected(self, event: DataTable.RowSelected):
        """Handle game selection."""
        if event.data_table.id == "game-table":
            row_index = event.row_index
            games = self.game_library.games
            if 0 <= row_index < len(games):
                game = games[row_index]
                self.game_library.selected_game = game
                self.game_config.game = game
                self.log(f"🎮 Selected: {game.name}")


def main():
    """Entry point."""
    app = CachyGameOptimizerApp()
    app.run()


if __name__ == "__main__":
    main()