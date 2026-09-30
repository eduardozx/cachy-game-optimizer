# CachyOS Game Optimizer 🎮⚡

> **Futuristic Gaming Performance Suite for CachyOS**  
> Maximize gaming performance on older hardware with intelligent, hardware-specific optimizations.

![CachyOS](https://img.shields.io/badge/CachyOS-Arch%20Based-blue?style=for-the-badge&logo=archlinux)
![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)
![Status](https://img.shields.io/badge/Status-Production%20Ready-brightgreen?style=for-the-badge)

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

### 🎮 Game Management
- **Auto-scan**: Steam, Heroic Games Launcher, Lutris, Bottles, Flatpak
- **Per-game config**: Wine/Proton version, DXVK/VKD3D, launch options
- **Launch with optimizations**: GameMode, MangoHud, vkBasalt, FSR, CPU affinity
- **Proton/Wine management**: ESYNC/FSYNC/FUTEX2, DXVK cache, GStreamer

### 🖥️ Three Interfaces
| Interface | Description |
|-----------|-------------|
| **TUI** | Beautiful Textual-based terminal UI with panels (recommended) |
| **CLI** | Full command-line access for scripting/automation |
| **Systemd Service** | Auto-apply optimizations on boot |

---

## 📸 Screenshots

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
- **Dependencies**: `textual`, `rich`, `pyyaml`, `psutil`, `pydantic`

---

## ⚡ Quick Install

```bash
# Clone to standard location
git clone https://github.com/yourusername/cachy-game-optimizer.git ~/.local/share/cachy-game-optimizer
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
# 🖥️ TUI Mode (Recommended - Best Experience)
cachy-game-optimizer
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
│   └── main.py          # TUI application (Textual)
├── scripts/
│   ├── cachy-game-optimizer  # TUI launcher
│   └── cgo                  # CLI wrapper
├── config/
│   └── cachy-game-optimizer.service  # Systemd service
├── themes/              # UI themes (Kali-inspired)
├── games/               # Game library database
├── logs/                # Application logs
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

## 🐛 Troubleshooting

<details>
<summary><b>Permission Errors</b></summary>

```bash
# Run with sudo for system optimizations
sudo cgo optimize
```
</details>

<details>
<summary><b>Game Won't Launch</b></summary>

```bash
# Check dry-run output
cgo launch <game_id> --dry-run

# Check logs
tail -f ~/.local/share/cachy-game-optimizer/logs/*.log
```
</details>

<details>
<summary><b>Hardware Not Detected</b></summary>

```bash
# Refresh detection
cgo detect
# or in TUI press 'r'
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

**Built for CachyOS** • **Optimized for Older Hardware** • **Maximum FPS** 🚀