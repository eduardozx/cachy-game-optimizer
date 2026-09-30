"""
CachyOS Game Optimizer - CLI Module
Command-line interface for the optimizer.
"""

import sys
import json
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

from .hardware import get_detector, SystemProfile
from .optimizer import get_optimizer, OptimizationEngine, OptimizationStatus
from .games import get_game_manager, GameManager, GameSource


console = Console()


def detect_hardware() -> SystemProfile:
    """Detect and display hardware profile."""
    detector = get_detector()
    profile = detector.get_full_profile()
    
    cpu = profile.cpu
    gpu = profile.gpu
    mem = profile.memory
    kernel = profile.kernel
    
    # Hardware table
    table = Table(title="[bold magenta]HARDWARE PROFILE[/]", border_style="magenta")
    table.add_column("Component", style="bold cyan", width=20)
    table.add_column("Details", style="green")
    
    # CPU
    table.add_row("CPU Model", cpu.model)
    table.add_row("Cores/Threads", f"{cpu.cores}C / {cpu.threads}T")
    table.add_row("Base/Boost Clock", f"{cpu.base_clock:.1f}GHz / {cpu.boost_clock:.1f}GHz")
    table.add_row("Governor", f"[{'green' if cpu.governor == 'performance' else 'yellow'}]{cpu.governor}[/]")
    table.add_row("L3 Cache", cpu.cache_l3)
    table.add_row("Architecture", cpu.architecture)
    
    table.add_row("", "")
    
    # GPU
    table.add_row("GPU Vendor", gpu.vendor)
    table.add_row("GPU Model", gpu.model)
    table.add_row("VRAM", f"{gpu.vram_mb} MB")
    table.add_row("Driver", gpu.driver_version)
    table.add_row("Vulkan", "✓" if gpu.vulkan_support else "✗")
    table.add_row("OpenCL", "✓" if gpu.opencl_support else "✗")
    table.add_row("PCIe", f"Gen {gpu.pcie_gen} {gpu.pcie_width}")
    
    table.add_row("", "")
    
    # Memory
    table.add_row("Total RAM", f"{mem.total_gb:.1f} GB")
    table.add_row("Available", f"{mem.available_gb:.1f} GB ({mem.usage_percent:.1f}% used)")
    table.add_row("Type/Speed", f"{mem.type}-{mem.speed_mhz} MHz")
    table.add_row("Channels", f"{mem.channels}x")
    
    table.add_row("", "")
    
    # Kernel
    table.add_row("Kernel", kernel.version.split()[2] if len(kernel.version.split()) > 2 else kernel.version)
    table.add_row("I/O Scheduler", kernel.scheduler)
    table.add_row("Swappiness", str(kernel.swappiness))
    table.add_row("Transparent Hugepages", kernel.transparent_hugepages)
    
    table.add_row("", "")
    
    # System
    table.add_row("Distro", profile.distro)
    table.add_row("Desktop", profile.desktop)
    table.add_row("Laptop", "Yes" if profile.is_laptop else "No")
    
    console.print(table)
    return profile


def show_recommendations(profile: Optional[SystemProfile] = None):
    """Show optimization recommendations."""
    detector = get_detector()
    if profile is None:
        profile = detector.get_full_profile()
    
    recommendations = detector.get_optimization_recommendations()
    
    if not recommendations:
        console.print("[yellow]No recommendations available[/yellow]")
        return
    
    table = Table(title="[bold magenta]OPTIMIZATION RECOMMENDATIONS[/]", border_style="magenta")
    table.add_column("Priority", style="bold yellow", width=8)
    table.add_column("Category", style="cyan", width=12)
    table.add_column("Action", style="white", width=30)
    table.add_column("Description", style="dim white", width=60)
    
    for rec in recommendations:
        priority = rec.get('priority', 'LOW')
        priority_color = {'HIGH': 'red', 'MEDIUM': 'yellow', 'LOW': 'green'}.get(priority, 'white')
        
        table.add_row(
            f"[{priority_color}]{priority}[/]",
            rec.get('category', ''),
            rec.get('title', ''),
            rec.get('description', '')
        )
    
    console.print(table)
    console.print(f"\nTotal: {len(recommendations)} recommendations")


def run_optimizations(category: Optional[str] = None):
    """Run optimizations."""
    optimizer = get_optimizer()
    optimizer.load_profile()
    
    if category:
        results = optimizer.run_category(category)
        console.print(f"[cyan]Running {category} optimizations...[/cyan]")
    else:
        results = optimizer.run_all_recommended()
        console.print("[cyan]Running all recommended optimizations...[/cyan]")
    
    # Results table
    table = Table(title="[bold magenta]OPTIMIZATION RESULTS[/]", border_style="magenta")
    table.add_column("Action", style="white", width=35)
    table.add_column("Status", style="bold", width=12)
    table.add_column("Message", style="dim white", width=50)
    table.add_column("Reboot", style="yellow", width=6)
    
    success = 0
    failed = 0
    skipped = 0
    
    for result in results:
        status_style = {
            OptimizationStatus.PENDING: "white",
            OptimizationStatus.RUNNING: "yellow",
            OptimizationStatus.SUCCESS: "green",
            OptimizationStatus.FAILED: "red",
            OptimizationStatus.SKIPPED: "blue",
        }.get(result.status, "white")
        
        status_text = {
            OptimizationStatus.PENDING: "⏳ PENDING",
            OptimizationStatus.RUNNING: "🔄 RUNNING",
            OptimizationStatus.SUCCESS: "✓ SUCCESS",
            OptimizationStatus.FAILED: "✗ FAILED",
            OptimizationStatus.SKIPPED: "⊘ SKIPPED",
        }.get(result.status, "?")
        
        if result.status == OptimizationStatus.SUCCESS:
            success += 1
        elif result.status == OptimizationStatus.FAILED:
            failed += 1
        elif result.status == OptimizationStatus.SKIPPED:
            skipped += 1
        
        reboot_text = "Yes" if result.requires_reboot else "No"
        
        table.add_row(
            result.action_id,
            f"[{status_style}]{status_text}[/]",
            result.message,
            reboot_text
        )
    
    console.print(table)
    console.print(f"\n[bold]Summary:[/bold] [green]{success} success[/green] | [red]{failed} failed[/red] | [blue]{skipped} skipped[/blue]")
    
    # Check if reboot needed
    if any(r.requires_reboot for r in results):
        console.print("[yellow]⚠ Reboot required for some optimizations to take effect[/yellow]")


def scan_games():
    """Scan all game libraries."""
    manager = get_game_manager()
    console.print("[cyan]Scanning game libraries...[/cyan]")
    
    results = manager.scan_all_sources()
    
    total = 0
    for source, games in results.items():
        if games:
            console.print(f"  [green]✓[/green] {source.value}: [bold]{len(games)}[/bold] games")
            total += len(games)
    
    console.print(f"\n[bold]Total games found: {total}[/bold]")
    
    if total > 0:
        list_games()


def list_games():
    """List all games in library."""
    manager = get_game_manager()
    games = manager.list_games()
    
    if not games:
        console.print("[yellow]No games in library. Run 'scan' first.[/yellow]")
        return
    
    table = Table(title="[bold magenta]GAME LIBRARY[/]", border_style="magenta")
    table.add_column("ID", style="dim cyan", width=30)
    table.add_column("Name", style="white", width=35)
    table.add_column("Source", style="yellow", width=12)
    table.add_column("Playtime", style="green", width=10)
    table.add_column("Executable", style="dim white", width=30)
    
    for game in games:
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
        exe_name = Path(game.exe_path).name if game.exe_path else "—"
        
        table.add_row(game.id, game.name[:33], source_icon, playtime, exe_name[:28])
    
    console.print(table)


def launch_game(game_id: str):
    """Launch a game."""
    manager = get_game_manager()
    console.print(f"[cyan]Launching game: {game_id}[/cyan]")
    
    result = manager.launch_game(game_id)
    
    if result['success']:
        console.print(f"[green]✓ Launched successfully[/green] (PID: {result.get('pid', 'N/A')})")
        if 'command' in result:
            console.print("[dim]Command:[/dim] " + " ".join(result['command']))
    else:
        console.print(f"[red]✗ Launch failed: {result.get('error', 'Unknown error')}[/red]")


def show_game_config(game_id: str):
    """Show game configuration."""
    manager = get_game_manager()
    game = manager.get_game(game_id)
    
    if not game:
        console.print(f"[red]Game not found: {game_id}[/red]")
        return
    
    config = game.config
    
    console.print(Panel(f"[bold]{game.name}[/bold]", border_style="magenta"))
    
    table = Table(show_header=False, border_style="magenta")
    table.add_column("Setting", style="bold cyan", width=25)
    table.add_column("Value", style="green")
    
    table.add_row("Source", game.source.value)
    table.add_row("Install Path", game.install_path or "—")
    table.add_row("Executable", Path(game.exe_path).name if game.exe_path else "—")
    table.add_row("Prefix Path", game.prefix_path or "—")
    table.add_row("", "")
    table.add_row("Wine Backend", config.wine_backend)
    table.add_row("Proton Version", config.proton_version or "Auto")
    table.add_row("DXVK Version", config.dxvk_version)
    table.add_row("VKD3D Version", config.vkd3d_version)
    table.add_row("", "")
    table.add_row("GameMode", "✓ Enabled" if config.gamemode else "✗ Disabled")
    table.add_row("MangoHud", "✓ Enabled" if config.mangohud else "✗ Disabled")
    table.add_row("vkBasalt", "✓ Enabled" if config.vkbasalt else "✗ Disabled")
    table.add_row("FSR", "✓ Enabled" if config.fsr else "✗ Disabled")
    table.add_row("FPS Limit", str(config.fps_limit) if config.fps_limit > 0 else "Unlimited")
    table.add_row("", "")
    table.add_row("CPU Affinity", config.cpu_affinity or "All cores")
    table.add_row("CPU Priority (nice)", str(config.cpu_priority))
    table.add_row("", "")
    
    if config.launch_options:
        table.add_row("Launch Options", "")
        for opt in config.launch_options:
            table.add_row("  ", opt)
    
    console.print(table)


def main():
    """Main CLI entry point."""
    if len(sys.argv) < 2:
        show_help()
        return
    
    command = sys.argv[1]
    
    try:
        if command == "detect":
            detect_hardware()
        elif command == "recommend":
            show_recommendations()
        elif command == "optimize":
            category = sys.argv[2] if len(sys.argv) > 2 else None
            if category and category.startswith("--category="):
                category = category.split("=")[1]
            run_optimizations(category)
        elif command == "scan":
            scan_games()
        elif command == "list":
            list_games()
        elif command == "launch":
            if len(sys.argv) < 3:
                console.print("[red]Error: Game ID required[/red]")
                return
            launch_game(sys.argv[2])
        elif command == "config":
            if len(sys.argv) < 3:
                console.print("[red]Error: Game ID required[/red]")
                return
            show_game_config(sys.argv[2])
        elif command == "tui":
            from .main import main as tui_main
            tui_main()
        elif command in ("help", "--help", "-h"):
            show_help()
        else:
            console.print(f"[red]Unknown command: {command}[/red]")
            show_help()
            sys.exit(1)
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted[/yellow]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def show_help():
    """Show help message."""
    console.print(Panel(
        "[bold magenta]CachyOS Game Optimizer - CLI v1.0.0[/bold magenta]\n"
        "[dim]Futuristic Gaming Performance Suite[/dim]",
        border_style="magenta"
    ))
    
    console.print("\n[bold]Usage:[/bold] cgo <command> [options]\n")
    
    commands = [
        ("detect", "Detect hardware and show profile"),
        ("recommend", "Show optimization recommendations"),
        ("optimize [--category=CAT]", "Run optimizations (all or category)"),
        ("  Categories: cpu, gpu, memory, kernel, storage, gaming, wine"),
        ("scan", "Scan all game libraries (Steam, Heroic, Lutris)"),
        ("list", "List all games in library"),
        ("launch <game_id>", "Launch game by ID"),
        ("config <game_id>", "Show game configuration"),
        ("tui", "Launch TUI application"),
        ("help", "Show this help"),
    ]
    
    for cmd, desc in commands:
        console.print(f"  [cyan]{cmd:<35}[/cyan] {desc}")
    
    console.print("\n[bold]Examples:[/bold]")
    console.print("  [dim]cgo detect[/dim]")
    console.print("  [dim]cgo optimize --category=gpu[/dim]")
    console.print("  [dim]cgo scan[/dim]")
    console.print("  [dim]cgo launch steam_730[/dim]")
    console.print("  [dim]cgo tui[/dim]")


if __name__ == "__main__":
    main()