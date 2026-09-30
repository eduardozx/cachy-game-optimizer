"""
CachyOS Game Optimizer - Game Manager
Manages game library, launches with optimal settings, handles Wine/Proton prefixes.
"""

import json
import os
import subprocess
from pathlib import Path
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field, asdict
from enum import Enum
import yaml


class GameSource(Enum):
    STEAM = "steam"
    HEROIC = "heroic"
    LUTRIS = "lutris"
    BOTTLES = "bottles"
    FLATPAK = "flatpak"
    NATIVE = "native"
    CUSTOM = "custom"


class WineBackend(Enum):
    PROTON_GE = "proton-ge"
    PROTON_OFFICIAL = "proton-official"
    WINE_GE = "wine-ge"
    WINE_SYSTEM = "wine-system"
    BOX86 = "box86"
    BOX64 = "box64"


@dataclass
class GameConfig:
    """Per-game optimization configuration."""
    # Compatibility tool (Proton/Wine) - single selector for installed tools
    compat_tool: str = ""  # e.g., "GE-Proton9-27", "wine-ge-9.21", "system"
    
    # Component versions (auto-detected from selected tool, but overridable)
    dxvk_version: str = "latest"
    vkd3d_version: str = "latest"

    # Launch options
    launch_options: List[str] = field(default_factory=list)
    env_vars: Dict[str, str] = field(default_factory=dict)

    # Performance
    gamemode: bool = True
    mangohud: bool = True
    vkbasalt: bool = False
    fsr: bool = False
    fps_limit: int = 0

    # CPU affinity
    cpu_affinity: str = ""  # e.g., "0-3" for first 4 cores
    cpu_priority: int = 10  # nice value

    # Memory
    force_dedicated_vram: bool = False
    max_vram_mb: int = 0

    # Custom
    custom_script_pre: str = ""
    custom_script_post: str = ""

    # Backward compatibility - accept old fields and migrate
    def __post_init__(self):
        # Handle legacy fields if passed via **kwargs during from_dict
        pass

    @classmethod
    def from_legacy(cls, data: Dict) -> 'GameConfig':
        """Create GameConfig from legacy data dict with old fields."""
        # Extract new fields
        compat_tool = data.get('compat_tool', '')
        
        # Migrate from legacy fields if compat_tool not set
        if not compat_tool:
            wine_backend = data.get('wine_backend', 'proton-ge')
            proton_version = data.get('proton_version', 'GE-Proton9-20')
            wine_version = data.get('wine_version', '')
            
            if wine_backend in ['proton-ge', 'proton-official'] and proton_version:
                compat_tool = proton_version
            elif wine_backend in ['wine-ge', 'wine-system'] and wine_version:
                compat_tool = wine_version
            elif wine_backend in ['proton-ge', 'proton-official']:
                compat_tool = proton_version or 'GE-Proton9-20'
        
        return cls(
            compat_tool=compat_tool,
            dxvk_version=data.get('dxvk_version', 'latest'),
            vkd3d_version=data.get('vkd3d_version', 'latest'),
            launch_options=data.get('launch_options', []),
            env_vars=data.get('env_vars', {}),
            gamemode=data.get('gamemode', True),
            mangohud=data.get('mangohud', True),
            vkbasalt=data.get('vkbasalt', False),
            fsr=data.get('fsr', False),
            fps_limit=data.get('fps_limit', 0),
            cpu_affinity=data.get('cpu_affinity', ''),
            cpu_priority=data.get('cpu_priority', 10),
            force_dedicated_vram=data.get('force_dedicated_vram', False),
            max_vram_mb=data.get('max_vram_mb', 0),
            custom_script_pre=data.get('custom_script_pre', ''),
            custom_script_post=data.get('custom_script_post', ''),
        )


@dataclass
class Game:
    """Game entry in library."""
    id: str
    name: str
    source: GameSource
    source_id: str = ""  # Steam AppID, Heroic ID, etc.
    install_path: str = ""
    exe_path: str = ""
    exe_args: str = ""

    # Configuration
    config: GameConfig = field(default_factory=GameConfig)

    # Metadata
    hours_played: float = 0.0
    last_played: str = ""
    icon_path: str = ""
    tags: List[str] = field(default_factory=list)

    # Proton/Wine prefix
    prefix_path: str = ""

    def to_dict(self) -> Dict:
        data = asdict(self)
        data['source'] = self.source.value
        data['config'] = asdict(self.config)
        return data

    @classmethod
    def from_dict(cls, data: Dict) -> 'Game':
        data['source'] = GameSource(data['source'])
        if 'config' in data:
            # Use from_legacy for backward compatibility with old config fields
            data['config'] = GameConfig.from_legacy(data['config'])
        return cls(**data)


class GameManager:
    """Manages game library and launching."""

    def __init__(self, library_path: Optional[Path] = None):
        self.library_path = library_path or Path.home() / '.local' / 'share' / 'cachy-game-optimizer' / 'games'
        self.library_path.mkdir(parents=True, exist_ok=True)

        self.games_file = self.library_path / 'library.json'
        self.games: Dict[str, Game] = {}
        self.load_library()

    def load_library(self):
        """Load game library from disk."""
        if self.games_file.exists():
            try:
                with open(self.games_file, 'r') as f:
                    data = json.load(f)
                    for game_data in data.get('games', []):
                        game = Game.from_dict(game_data)
                        self.games[game.id] = game
            except Exception as e:
                print(f"Error loading library: {e}")

    def save_library(self):
        """Save game library to disk."""
        try:
            data = {
                'version': 1,
                'games': [game.to_dict() for game in self.games.values()]
            }
            with open(self.games_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving library: {e}")

    def add_game(self, game: Game) -> Game:
        """Add game to library."""
        self.games[game.id] = game
        self.save_library()
        return game

    def remove_game(self, game_id: str) -> bool:
        """Remove game from library."""
        if game_id in self.games:
            del self.games[game_id]
            self.save_library()
            return True
        return False

    def get_game(self, game_id: str) -> Optional[Game]:
        """Get game by ID."""
        return self.games.get(game_id)

    def list_games(self, source: Optional[GameSource] = None) -> List[Game]:
        """List all games, optionally filtered by source."""
        games = list(self.games.values())
        if source:
            games = [g for g in games if g.source == source]
        return sorted(games, key=lambda g: g.name.lower())

    def scan_steam_library(self) -> List[Game]:
        """Scan Steam library for games."""
        games = []

        # Find Steam library folders
        steam_paths = [
            Path.home() / '.steam' / 'steam',
            Path.home() / '.local' / 'share' / 'Steam',
            Path('/mnt') / 'Games' / 'SteamLibrary',
        ]

        library_folders = []
        for steam_path in steam_paths:
            if steam_path.exists():
                # Read libraryfolders.vdf
                vdf_path = steam_path / 'steamapps' / 'libraryfolders.vdf'
                if vdf_path.exists():
                    content = vdf_path.read_text()
                    # Simple VDF parsing for paths
                    import re
                    for match in re.finditer(r'"path"\s+"([^"]+)"', content):
                        library_folders.append(Path(match.group(1)))
                library_folders.append(steam_path)

        # Scan each library for appmanifest files
        for lib_folder in library_folders:
            steamapps = lib_folder / 'steamapps'
            if not steamapps.exists():
                continue

            for manifest in steamapps.glob('appmanifest_*.acf'):
                try:
                    content = manifest.read_text()
                    # Parse ACF
                    appid_match = re.search(r'"appid"\s+"(\d+)"', content)
                    name_match = re.search(r'"name"\s+"([^"]+)"', content)
                    installdir_match = re.search(r'"installdir"\s+"([^"]+)"', content)

                    if appid_match and name_match:
                        appid = appid_match.group(1)
                        name = name_match.group(1)
                        installdir = installdir_match.group(1) if installdir_match else ""

                        # Find exe
                        exe_path = ""
                        if installdir:
                            game_dir = steamapps / 'common' / installdir
                            if game_dir.exists():
                                # Look for .exe files
                                for exe in game_dir.rglob('*.exe'):
                                    if not any(x in exe.name.lower() for x in ['uninstall', 'setup', 'install', 'crash', 'report']):
                                        exe_path = str(exe)
                                        break

                        game = Game(
                            id=f"steam_{appid}",
                            name=name,
                            source=GameSource.STEAM,
                            source_id=appid,
                            install_path=str(steamapps / 'common' / installdir) if installdir else "",
                            exe_path=exe_path,
                            prefix_path=str(Path.home() / '.steam' / 'steam' / 'steamapps' / 'compatdata' / appid),
                        )
                        games.append(game)
                except Exception:
                    continue

        return games

    def scan_heroic_library(self) -> List[Game]:
        """Scan Heroic Games Launcher library."""
        games = []

        # Heroic config
        heroic_config = Path.home() / '.config' / 'heroic' / 'heroicGamesLauncher' / 'config.json'
        if not heroic_config.exists():
            return games

        try:
            with open(heroic_config, 'r') as f:
                config = json.load(f)

            # Get library paths
            library_paths = config.get('libraryPaths', [])
            for lib_path in library_paths:
                lib = Path(lib_path)
                if not lib.exists():
                    continue

                # Scan for games
                for game_dir in lib.iterdir():
                    if game_dir.is_dir():
                        # Look for .exe
                        exe_files = list(game_dir.rglob('*.exe'))
                        if exe_files:
                            game = Game(
                                id=f"heroic_{game_dir.name}",
                                name=game_dir.name,
                                source=GameSource.HEROIC,
                                source_id=game_dir.name,
                                install_path=str(game_dir),
                                exe_path=str(exe_files[0]),
                                prefix_path=str(game_dir / 'prefix'),
                            )
                            games.append(game)
        except Exception:
            pass

        return games

    def scan_lutris_library(self) -> List[Game]:
        """Scan Lutris library."""
        games = []

        # Lutris games database
        lutris_db = Path.home() / '.local' / 'share' / 'lutris' / 'pga.db'
        if not lutris_db.exists():
            return games

        try:
            import sqlite3
            conn = sqlite3.connect(lutris_db)
            cursor = conn.cursor()
            cursor.execute("SELECT slug, name, exe, installer_path FROM games")
            for row in cursor.fetchall():
                slug, name, exe, installer = row
                if exe:
                    game = Game(
                        id=f"lutris_{slug}",
                        name=name,
                        source=GameSource.LUTRIS,
                        source_id=slug,
                        exe_path=exe,
                        install_path=str(Path(exe).parent) if exe else "",
                    )
                    games.append(game)
            conn.close()
        except Exception:
            pass

        return games

    def scan_all_sources(self) -> Dict[GameSource, List[Game]]:
        """Scan all game sources."""
        results = {}

        results[GameSource.STEAM] = self.scan_steam_library()
        results[GameSource.HEROIC] = self.scan_heroic_library()
        results[GameSource.LUTRIS] = self.scan_lutris_library()

        # Add scanned games to library
        for source, games in results.items():
            for game in games:
                if game.id not in self.games:
                    self.add_game(game)

        return results

    def launch_game(self, game_id: str, dry_run: bool = False, capture_output: bool = False) -> Dict[str, Any]:
        """Launch game with optimized environment."""
        game = self.get_game(game_id)
        if not game:
            return {'success': False, 'error': 'Game not found'}

        config = game.config
        env = os.environ.copy()

        # Build environment
        # Gamemode
        if config.gamemode:
            env['GAMEMODERUNEXEC'] = '1'

        # MangoHud
        if config.mangohud:
            env['MANGOHUD'] = '1'
            env['MANGOHUD_CONFIGFILE'] = str(Path.home() / '.config' / 'MangoHud' / 'MangoHud.conf')

        # vkBasalt
        if config.vkbasalt:
            env['ENABLE_VKBASALT'] = '1'

        # Wine/Proton
        if game.source in [GameSource.STEAM, GameSource.HEROIC, GameSource.LUTRIS, GameSource.BOTTLES, GameSource.CUSTOM]:
            # Determine which compat tool to use
            compat_tool = config.compat_tool or ""
            
            if compat_tool and compat_tool != 'system':
                # Find the specific tool
                proton = self._find_compat_tool(compat_tool)
                if proton:
                    env['STEAM_COMPAT_CLIENT_INSTALL_PATH'] = str(Path.home() / '.steam' / 'steam')
                    env['STEAM_COMPAT_DATA_PATH'] = game.prefix_path or str(Path.home() / '.steam' / 'steam' / 'steamapps' / 'compatdata' / game.source_id)
            else:
                # Fallback to auto-detect
                proton_paths = [
                    Path.home() / '.steam' / 'steam' / 'steamapps' / 'common' / 'Proton - Experimental',
                    Path.home() / '.steam' / 'steam' / 'steamapps' / 'common' / 'Proton 9.0',
                    Path('/usr') / 'share' / 'steam' / 'compatibilitytools.d',
                    Path.home() / '.local' / 'share' / 'Steam' / 'compatibilitytools.d',
                    Path.home() / '.local' / 'share' / 'cachy-game-optimizer' / 'compat' / 'tools',
                ]
                
                proton_path = ""
                for pp in proton_paths:
                    if pp.exists():
                        proton_path = str(pp)
                        break
                
                if proton_path:
                    env['STEAM_COMPAT_CLIENT_INSTALL_PATH'] = str(Path.home() / '.steam' / 'steam')
                    env['STEAM_COMPAT_DATA_PATH'] = game.prefix_path or str(Path.home() / '.steam' / 'steam' / 'steamapps' / 'compatdata' / game.source_id)

            # DXVK/VKD3D
            env['DXVK_STATE_CACHE'] = '1'
            env['DXVK_STATE_CACHE_PATH'] = str(Path.home() / '.cache' / 'dxvk')
            env['VKD3D_CONFIG'] = 'dxr11,multi_queue'

        # Custom env vars
        env.update(config.env_vars)

        # CPU affinity
        if config.cpu_affinity:
            env['taskset'] = config.cpu_affinity

        # FPS limit via mangohud
        if config.fps_limit > 0 and config.mangohud:
            env['MANGOHUD_CONFIG'] = f"fps_limit={config.fps_limit}"

        # FSR
        if config.fsr:
            env['WINE_FULLSCREEN_FSR'] = '1'
            env['WINE_FULLSCREEN_FSR_STRENGTH'] = '2'

        # ===== FPS BOOST / STUTTER REDUCTION =====
        if game.source in [GameSource.STEAM, GameSource.HEROIC, GameSource.LUTRIS, GameSource.BOTTLES, GameSource.CUSTOM]:
            # DXVK Async - reduces shader compile stutter
            if getattr(config, 'dxvk_async', False):
                env['DXVK_ASYNC'] = '1'
            
            # VKD3D Async
            if getattr(config, 'vkd3d_async', False):
                env['VKD3D_ASYNC'] = '1'
            
            # Disable ESYNC/FSYNC - fixes some stutter/crashes
            if getattr(config, 'disable_esync', False):
                env['PROTON_NO_ESYNC'] = '1'
            if getattr(config, 'disable_fsync', False):
                env['PROTON_NO_FSYNC'] = '1'
            
            # Disable NVAPI - fixes crashes on AMD/Intel
            if getattr(config, 'nvapi_disable', False):
                env['PROTON_DISABLE_NVAPI'] = '1'
            
            # Force D3D11 - more stable than D3D12
            if getattr(config, 'prefer_d3d11', False):
                env['PROTON_FORCE_D3D11'] = '1'
            
            # Disable GStreamer - fixes video playback crashes
            if getattr(config, 'gst_disable', False):
                env['PROTON_NO_GSTREAMER'] = '1'
            
            # Wine fullscreen FSR
            if getattr(config, 'wine_fullscreen_hack', False):
                env['WINE_FULLSCREEN_FSR'] = '1'
                env['WINE_FULLSCREEN_FSR_STRENGTH'] = '2'
            
            # High priority
            if getattr(config, 'high_priority', False):
                env['SCHED_PRIORITY'] = '10'  # Will be handled by taskset/nice
            
            # Force CPU threads
            if getattr(config, 'force_cores', ''):
                force_cores = config.force_cores.strip()
                if force_cores.isdigit():
                    env['WINE_CPU_TOPOLOGY'] = f"{force_cores}:1:1"  # threads:cores:sockets
            
            # Large Address Aware for 32-bit games
            if getattr(config, 'large_address_aware', True):
                env['WINE_LARGE_ADDRESS_AWARE'] = '1'

        # Custom env vars
        env.update(config.env_vars)

        # Build command
        if game.source == GameSource.STEAM:
            cmd = ['steam', f'steam://rungameid/{game.source_id}']
        elif game.exe_path and Path(game.exe_path).exists():
            compat_tool = config.compat_tool or ""
            
            if compat_tool and compat_tool != 'system':
                # Use specific compat tool
                proton = self._find_compat_tool(compat_tool)
                if proton:
                    # Ensure prefix directory exists
                    if game.prefix_path:
                        Path(game.prefix_path).mkdir(parents=True, exist_ok=True)
                    
                    cmd = [
                        'env',
                        f'STEAM_COMPAT_DATA_PATH={game.prefix_path}',
                        f'STEAM_COMPAT_CLIENT_INSTALL_PATH={Path.home() / ".steam" / "steam"}',
                        str(proton / 'proton'), 'run', game.exe_path
                    ] + config.launch_options
                else:
                    # Tool not found, fallback to wine
                    cmd = ['wine', game.exe_path] + config.launch_options
            else:
                # Auto-detect proton or use wine
                proton = self._find_proton(config.proton_version or "GE-Proton9-20")
                if proton and game.exe_path.endswith('.exe'):
                    cmd = [
                        'env',
                        f'STEAM_COMPAT_DATA_PATH={game.prefix_path}',
                        f'STEAM_COMPAT_CLIENT_INSTALL_PATH={Path.home() / ".steam" / "steam"}',
                        str(proton / 'proton'), 'run', game.exe_path
                    ] + config.launch_options
                else:
                    cmd = ['wine', game.exe_path] + config.launch_options
        else:
            return {'success': False, 'error': 'No executable found'}

        # Pre-launch script
        if config.custom_script_pre:
            try:
                subprocess.run(config.custom_script_pre, shell=True, check=True)
            except Exception:
                pass

        if dry_run:
            return {
                'success': True,
                'command': cmd,
                'env': {k: v for k, v in env.items() if k not in os.environ or os.environ[k] != v}
            }

        try:
            # Launch with output capture if requested
            if capture_output:
                proc = subprocess.Popen(
                    cmd,
                    env=env,
                    start_new_session=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    bufsize=1,  # Line buffered
                )
                return {'success': True, 'pid': proc.pid, 'process': proc}
            else:
                # Original detached launch
                proc = subprocess.Popen(
                    cmd,
                    env=env,
                    start_new_session=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )

                return {'success': True, 'pid': proc.pid}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _find_compat_tool(self, tool_name: str) -> Optional[Path]:
        """Find a specific compatibility tool (Proton or Wine) by name."""
        search_paths = [
            Path.home() / '.steam' / 'steam' / 'steamapps' / 'common',
            Path('/usr') / 'share' / 'steam' / 'compatibilitytools.d',
            Path.home() / '.local' / 'share' / 'Steam' / 'compatibilitytools.d',
            Path.home() / '.local' / 'share' / 'wine',
            Path('/opt') / 'wine',
            # Custom downloads from Wine/Proton tab
            Path.home() / '.local' / 'share' / 'cachy-game-optimizer' / 'compat' / 'tools',
        ]

        for base in search_paths:
            if base.exists():
                # Exact match first
                exact = base / tool_name
                if exact.exists():
                    if tool_name.lower().startswith('proton') or 'proton' in tool_name.lower():
                        proton_bin = exact / 'proton'
                        if proton_bin.exists():
                            return exact
                    else:
                        # Wine - check for wine binary
                        wine_bin = exact / 'bin' / 'wine'
                        if wine_bin.exists():
                            return exact
                
                # Fuzzy match
                for item in base.iterdir():
                    if tool_name.lower() in item.name.lower() or item.name.lower() in tool_name.lower():
                        if tool_name.lower().startswith('proton') or 'proton' in tool_name.lower():
                            proton_bin = item / 'proton'
                            if proton_bin.exists():
                                return item
                        else:
                            wine_bin = item / 'bin' / 'wine'
                            if wine_bin.exists():
                                return item

        return None

    def _find_proton(self, version: str) -> Optional[Path]:
        """Find Proton installation (legacy fallback)."""
        search_paths = [
            Path.home() / '.steam' / 'steam' / 'steamapps' / 'common',
            Path('/usr') / 'share' / 'steam' / 'compatibilitytools.d',
            Path.home() / '.local' / 'share' / 'Steam' / 'compatibilitytools.d',
            # Custom downloads from Wine/Proton tab
            Path.home() / '.local' / 'share' / 'cachy-game-optimizer' / 'compat' / 'tools',
        ]

        for base in search_paths:
            if base.exists():
                for item in base.iterdir():
                    if version.lower() in item.name.lower() or 'proton' in item.name.lower():
                        proton_bin = item / 'proton'
                        if proton_bin.exists():
                            return item

        return None

    def get_proton_versions(self) -> List[str]:
        """Get available Proton versions."""
        versions = []
        search_paths = [
            Path.home() / '.steam' / 'steam' / 'steamapps' / 'common',
            Path('/usr') / 'share' / 'steam' / 'compatibilitytools.d',
            Path.home() / '.local' / 'share' / 'Steam' / 'compatibilitytools.d',
            # Custom downloads from Wine/Proton tab
            Path.home() / '.local' / 'share' / 'cachy-game-optimizer' / 'compat' / 'tools',
        ]

        for base in search_paths:
            if base.exists():
                for item in base.iterdir():
                    if item.is_dir() and 'proton' in item.name.lower():
                        versions.append(item.name)

        return sorted(set(versions))

    def get_wine_versions(self) -> List[str]:
        """Get available Wine versions."""
        versions = ['system']

        # Check for wine-ge
        wine_paths = [
            Path.home() / '.local' / 'share' / 'wine',
            Path('/opt') / 'wine',
            # Custom downloads from Wine/Proton tab
            Path.home() / '.local' / 'share' / 'cachy-game-optimizer' / 'compat' / 'tools',
        ]

        for base in wine_paths:
            if base.exists():
                for item in base.iterdir():
                    if item.is_dir():
                        name = item.name.lower()
                        if 'wine' in name or 'proton' not in name:  # Wine or generic
                            versions.append(f"wine-{item.name}" if not name.startswith('wine') else item.name)

        return sorted(set(versions))

    def get_compat_tools(self) -> List[str]:
        """Get all available compatibility tools (Proton + Wine) for game config."""
        tools = []
        
        # Proton versions
        for ver in self.get_proton_versions():
            tools.append(ver)
        
        # Wine versions (skip 'system' as it's the fallback)
        for ver in self.get_wine_versions():
            if ver != 'system':
                tools.append(ver)
        
        # Add system wine as fallback
        tools.append('system')
        
        return sorted(set(tools))


def get_game_manager(library_path: Optional[Path] = None) -> GameManager:
    return GameManager(library_path)