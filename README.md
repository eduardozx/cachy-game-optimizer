# CachyOS Game Optimizer 🎮⚡

> **Futuristic Gaming Performance Suite for CachyOS**  
> Maximize gaming performance on older hardware with intelligent, hardware-specific optimizations.

![CachyOS](https://img.shields.io/badge/CachyOS-Arch%20Based-blue?style=for-the-badge&logo=archlinux)
![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)
![Status](https://img.shields.io/badge/Status-Production%20Ready-brightgreen?style=for-the-badge)
![GUI](https://img.shields.io/badge/GUI-PyQt6%20%2B%20Textual-41CD52?style=for-the-badge)
![GameScope](https://img.shields.io/badge/GameScope-Supported-FF6B35?style=for-the-badge)

---

## 🌟 Overview

Built specifically for **older hardware** (tested on **i5-4440S + RX 580 2GB + 16GB DDR3**), this optimizer applies kernel-level, GPU, memory, and Wine/Proton optimizations to squeeze maximum FPS from your system.

### 🎯 Target Hardware
| Component | Spec | Optimizations Applied |
|-----------|------|----------------------|
| **CPU** | Intel i5-4440S (4C/4T @ 2.8GHz) | Performance governor, `intel_pstate=active`, `mitigations=off` |
| **GPU** | AMD RX 580 2048SP (2GB VRAM) | `RADV_PERFTEST=aco,nggc`, texture compression, VRAM optimization |
| **RAM** | 16GB DDR3-1333 | ZRAM (8GB), 1GB hugepages, `swappiness=10`, earlyoom |
| **Kernel** | CachyOS 7.2+ (BORE scheduler) | BORE, NVMe scheduler=none, THP=madvise |
| **Wine/Proton** | GE-Proton / Wine-GE | ESYNC/FSYNC/FUTEX2, DXVK async cache, VKD3D multi-queue |

---

## 🚀 Features

### 🔧 20+ Hardware-Specific Optimizations
| Category | Key Optimizations |
|----------|-------------------|
| **CPU** | Governor tuning, mitigations control, pstate driver |
| **GPU (AMD)** | RADV_PERFTEST, power profiles, VRAM optimization, PP feature mask |
| **Memory** | ZRAM, hugepages, swappiness, earlyoom, THP tuning |
| **Kernel** | BORE scheduler, I/O schedulers, transparent hugepages |
| **Storage** | NVMe write cache, scheduler tuning, power management |
| **Gaming** | GameMode, MangoHud, vkBasalt, FSR |
| **Wine/Proton** | ESYNC/FSYNC, DXVK cache, GStreamer, Proton-GE management |

### 🎮 GameScope Integration (NEW!)
- **Native GameScope support** per-game configuration
- **8 Ready-to-use presets** (one-click setup):
  - 🖥️ **Borderless Fullscreen** (Recommended)
  - 🎯 **Exclusive Fullscreen** (Lowest Latency)
  - 🪟 **Windowed** (Streaming/Recording)
  - 📺 **1080p @ 60Hz Upscale** (Low-end GPU)
  - 📺 **1440p @ 144Hz** (High Refresh)
  - 🎮 **Steam Deck Style** (720p/800p Upscale)
  - ⚡ **Competitive** (Low Latency + FPS Limit)
  - 🔧 **Custom** (Manual configuration)
- **Per-game configuration**: Resolution, refresh rate, FPS limit, scaler (FSR1/FSR2/NIS), filter, HDR/ITM
- Works with **Wine/Proton** and **native Linux games**
- Provides: VRR/FreeSync/G-Sync, HDR, Upscaling (FSR/NIS), FPS limiting, better frame pacing

### 🎮 Game Management
- **Auto-scan**: Steam, Heroic Games Launcher, Lutris, Bottles, Flatpak
- **Per-game config**: Wine/Proton version, DXVK/VKD3D, launch options
- **Launch with optimizations**: GameMode, MangoHud, vkBasalt, FSR, CPU affinity
- **Proton/Wine management**: ESYNC/FSYNC/FUTEX2, DXVK cache, GStreamer

### 🖥️ Four Interfaces
| Interface | Description |
|-----------|-------------|
| **GUI** | PyQt6 with Kali-inspired dark green theme (NEW!) |
| **TUI** | Beautiful Textual-based terminal UI with panels |
| **CLI** | Full command-line access for scripting/automation |
| **Systemd Service** | Auto-apply optimizations on boot |

---

## 📸 Screenshots

### GUI Interface (Kali Dark Green Theme)
```
┌─────────────────────────────────────────────────────────────┐
│ CachyOS Game Optimizer    ┌─────────────────────────────┐  │
│ ┌───────────────────────┐ │ Hardware Profile            │  │
│ │ Games              ▼  │ │ CPU: i5-4440S (4C/4T)     │  │
│ │ ┌───────────────────┐ │ │ GPU: RX 580 8GB           │  │
│ │ │ 🎮 Cyberpunk 2077 │ │ │ RAM: 16GB DDR3            │  │
│ │ │ 🎮 Elden Ring     │ │ │ Kernel: CachyOS 7.2       │  │
│ │ │ 🎮 Baldur's Gate 3│ │ └───────────────────────────┘  │
│ │ │ 🎮 Counter-Strike │ ┌───────────────────────────┐  │
│ │ └───────────────────┘ │ GameScope Presets          │  │
│ └───────────────────────┘ │ [🖥️ Borderless] ▼         │  │
│                           │ [🎯 Exclusive]             │  │
│ [🚀 Launch] [⚙️ Config]   │ [🪟 Windowed]              │  │
│ [🎮 GameScope] [📊 Perf]  │ [📺 1080p/60 Upscale]      │  │
└───────────────────────────┘ [⚡ Competitive]             │
```

### TUI Interface (Kali Dark Green Theme)
```
┌─────────────────────────────────────────────────────────────┐
│  CachyOS Game Optimizer          ┌───────────────────────┐  │
│  ┌─────────────────────────────┐ │  Hardware Profile     │  │
│  │ Games                    ▼  │ │  CPU: i5-4440S (4C/4T)│  │
│  │ ┌─────────────────────────┐ │ │  GPU: RX 580 2GB      │  │
│  │ │ 🎮 Cyberpunk 2077       │ │ │  RAM: 16GB DDR3       │  │
│  │ │ 🎮 Elden Ring           │ │ │  Kernel: CachyOS 7.2  │  │
│  │ │ 🎮 Baldur's Gate 3      │ │ └───────────────────────┘  │
│  │ │ 🎮 Counter-Strike 2     │ ┌───────────────────────┐  │
│  │ └─────────────────────────┘ │  Optimizations         │  │
│  └─────────────────────────────┘ │  [●] CPU Governor     │  │
│                                 │  [●] GPU RADV         │  │
│  [o] Optimize  [s] Scan  [l]    │  [●] Memory ZRAM      │  │
│  Launch      [c] Config  [q]    │  [●] Kernel BORE      │  │
│  Quit                           │  [●] Wine ESYNC       │  │
└─────────────────────────────────┘ └───────────────────────┘
```

---

## 📋 Requirements

- **CachyOS** (or Arch-based with CachyOS repos enabled)
- **Python 3.10+**
- **Root access** (for system optimizations via pkexec)
- **FUSE2** (for AppImage - auto-installed by installer)
- **Dependencies**: `textual`, `rich`, `pyyaml`, `psutil`, `pydantic`, `PyQt6` (for GUI)

---

## ⚡ Quick Install

### 🚀 One-Liner Install (Recommended)
```bash
# Using curl
curl -fsSL https://raw.githubusercontent.com/eduardozx/cachy-game-optimizer/main/install.sh | bash

# Using wget
wget -qO- https://raw.githubusercontent.com/eduardozx/cachy-game-optimizer/main/install.sh | bash
```

**The installer automatically:**
- ✅ Checks/installs FUSE2 (required for AppImage)
- ✅ Downloads AppImage from GitHub Releases (or builds from source)
- ✅ Creates desktop entry (appears in application menu)
- ✅ Creates themed icon (Kali green FPS icon)
- ✅ Updates desktop database
- ✅ Tests installation

### 📦 Manual Install (Development)
```bash
# Clone to standard location
git clone https://github.com/eduardozx/cachy-game-optimizer.git ~/.local/share/cachy-game-optimizer
cd ~/.local/share/cachy-game-optimizer

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install in development mode
pip install -e .

# Optional: Install globally (requires root)
sudo pip install -e .
```

### Quick Start
```bash
# 🖥️ GUI Mode (Recommended - Best Experience)
cachy-game-optimizer.AppImage --gui
# or from menu: "CachyOS Game Optimizer"

# 🖥️ TUI Mode
cachy-game-optimizer.AppImage --tui
# or
cgo tui

# ⚡ CLI Mode (Scripting/Automation)
cgo detect          # Detect hardware
cgo recommend       # Show recommendations
cgo optimize        # Run ALL optimizations
cgo optimize-gpu    # GPU only
cgo optimize-mem    # Memory only
cgo scan            # Scan game libraries
cgo list            # List games
cgo launch steam_730  # Launch game with optimizations
```

---

## ⌨️ TUI Keybindings

| Key | Action |
|-----|--------|
| `q` / `Ctrl+C` | Quit |
| `r` | Refresh hardware & games |
| `o` | Run all optimizations |
| `s` | Scan game libraries |
| `l` | Launch selected game |
| `c` | Configure selected game |
| `↑/↓` | Navigate game list |
| `Enter` | Select game |
| `Tab` | Switch panels |

---

## 🎮 Supported Game Sources

- ✅ **Steam** (native + Proton)
- ✅ **Heroic Games Launcher** (Epic, GOG, Amazon, etc.)
- ✅ **Lutris** (Wine, custom runners)
- ✅ **Bottles** (Wine prefixes)
- ✅ **Flatpak** (Steam, Heroic, etc.)
- ✅ **Native Linux** games
- ✅ **Custom** executables

---

## 🛠️ Systemd Service (Auto-optimize on Boot)

```bash
# Install service
sudo cp config/cachy-game-optimizer.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now cachy-game-optimizer.service
```

---

## 📊 Expected Performance Gains

*For i5-4440S / RX 580 2GB / 16GB DDR3 on CachyOS:*

| Game Type | Before | After | Gain | Primary Optimizations |
|-----------|--------|-------|------|----------------------|
| **Native Linux** | Baseline | +15-30% FPS | 🟢 | CPU governor + kernel |
| **Proton (DXVK)** | Baseline | +20-40% FPS | 🟢 | ESYNC + RADV + DXVK cache |
| **Low VRAM games** | Crashes/Stutter | **Playable** | 🟢 | Texture compression + ZRAM |
| **1% Lows** | Unstable | **Stable** | 🟢 | GameMode + earlyoom + hugepages |

---

## 📁 Project Structure

```
~/.local/share/cachy-game-optimizer/
├── cachy_game_optimizer/
│   ├── __init__.py
│   ├── hardware.py      # Hardware detection & profiling
│   ├── optimizer.py     # Optimization engine (20+ optimizations)
│   ├── games.py         # Game library management (Steam, Heroic, Lutris, etc.)
│   ├── cli.py           # Command-line interface
│   ├── main.py          # TUI application (Textual)
│   ├── gui.py           # GUI application (PyQt6) - NEW!
│   ├── error_analyzer.py # Auto-fix game errors
│   ├── gui_wine_tab.py  # Wine/Proton downloads tab
│   ├── wine_downloader.py # Proton-GE/Wine-GE downloader
│   └── workers.py       # Background workers
├── scripts/
│   ├── cachy-game-optimizer  # TUI launcher
│   ├── cgo                  # CLI wrapper
│   └── cgo-gui              # GUI launcher
├── config/
│   └── cachy-game-optimizer.service  # Systemd service
├── themes/              # UI themes (Kali-inspired)
├── games/               # Game library database
├── logs/                # Application logs
├── install.sh           # One-click installer
├── entry_point.py       # PyInstaller entry point
├── pyproject.toml
└── README.md
```

---

## 🔧 Configuration

| File | Purpose |
|------|---------|
| `~/.config/cachy-game-optimizer/config.yaml` | User preferences |
| `~/.local/share/cachy-game-optimizer/games/library.json` | Game database |
| `/etc/environment` | Global env vars (RADV_PERFTEST, WINEESYNC, etc.) |
| `/etc/sysctl.d/99-cachy-gaming.conf` | Kernel parameters |

---

## 🎮 GameScope Configuration (Per-Game)

In GUI: Select game → **Config** → **🎮 GameScope** tab

| Preset | Mode | Resolution | FPS Limit | Scaler | Best For |
|--------|------|------------|-----------|--------|----------|
| 🖥️ Borderless | borderless | Native | Unlimited | auto | General gaming |
| 🎯 Exclusive | exclusive | Native | Unlimited | auto | Lowest latency |
| 🪟 Windowed | windowed | 1920x1080 | 60 | auto | Streaming/Recording |
| 📺 1080p/60 | borderless | 1920x1080 | 60 | fsr1 | Low-end GPU |
| 📺 1440p/144 | borderless | 2560x1440 | 144 | auto | High refresh |
| 🎮 Steam Deck | borderless | 1280x800 | 60 | fsr1 | Deck-like experience |
| ⚡ Competitive | exclusive | Native | 144 | auto | Esports/Competitive |
| 🔧 Custom | Manual | Manual | Manual | Manual | Advanced users |

---

## 🐛 Troubleshooting

<details>
<summary><b>Permission Errors</b></summary>

```bash
# Run with sudo for system optimizations
sudo cachy-game-optimizer.AppImage optimize
```
</details>

<details>
<summary><b>Game Won't Launch</b></summary>

```bash
# Check dry-run output
cachy-game-optimizer.AppImage launch <game_id> --dry-run

# Check logs
tail -f ~/.local/share/cachy-game-optimizer/logs/*.log
```
</details>

<details>
<summary><b>Hardware Not Detected</b></summary>

```bash
# Refresh detection
cachy-game-optimizer.AppImage detect
# or in TUI press 'r'
```
</details>

<details>
<summary><b>AppImage Won't Run</b></summary>

```bash
# Install FUSE2
# Arch/CachyOS: sudo pacman -S fuse2
# Ubuntu/Debian: sudo apt install fuse
# Fedora: sudo dnf install fuse

# Make executable
chmod +x cachy-game-optimizer.AppImage
```
</details>

---

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-optimization`)
3. Commit your changes (`git commit -m 'Add amazing optimization'`)
4. Push to branch (`git push origin feature/amazing-optimization`)
5. Open a Pull Request

---

## 📄 License

**MIT License** - Free for personal and commercial use.

---

## ⚠️ Disclaimer

- Some optimizations (`mitigations=off`) reduce security for performance
- Always test stability after applying optimizations
- Reboot required for kernel parameter changes
- Backup important data before running system modifications

---

## 📝 Changelog

### v1.1.0 (Latest) - Major GUI & GameScope Release
- ✅ **New PyQt6 GUI** with Kali-inspired dark green theme
- ✅ **GameScope integration** with 8 ready-to-use presets
- ✅ **Per-game GameScope configuration** in GUI
- ✅ **One-click installer** (`install.sh`) with AppImage support
- ✅ **AppImage distribution** (~541 MB, portable)
- ✅ **Desktop integration** (menu entry, icon, mime types)
- ✅ **GameScope presets**: Borderless, Exclusive, Windowed, 1080p/60, 1440p/144, Steam Deck, Competitive
- ✅ **GameScope in launch pipeline** (works with Wine/Proton + native)
- ✅ Fixed TUI markup rendering issues
- ✅ Fixed PyInstaller bundling for all interfaces
- ✅ One-click installer script with GitHub Releases fallback

### v1.0.0 - Initial Release
- Core optimization engine (CPU, GPU, Memory, Kernel, Wine/Proton)
- TUI interface (Textual)
- CLI interface
- Game library management (Steam, Heroic, Lutris, Bottles, Flatpak)
- Systemd service for auto-optimization
- Per-game optimization profiles

---

**Built for CachyOS** • **Optimized for Older Hardware** • **Maximum FPS** 🚀