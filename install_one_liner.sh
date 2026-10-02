#!/bin/bash
# CachyOS Game Optimizer - One-Liner Installer
# Run with: curl -fsSL https://raw.githubusercontent.com/eduardozx/cachy-game-optimizer/main/install.sh | bash
# Or: wget -qO- https://raw.githubusercontent.com/eduardozx/cachy-game-optimizer/main/install.sh | bash

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m'

APP_NAME="cachy-game-optimizer"
INSTALL_DIR="$HOME/.local/bin"
DESKTOP_DIR="$HOME/.local/share/applications"
ICON_DIR="$HOME/.local/share/icons/hicolor/256x256/apps"
APPIMAGE_PATH="$INSTALL_DIR/${APP_NAME}.AppImage"

print_header() {
    echo -e "${MAGENTA}"
    echo "╔══════════════════════════════════════════════════════════════════════╗"
    echo "║          CachyOS Game Optimizer - One-Click Installer               ║"
    echo "║          Futuristic Gaming Performance Suite                        ║"
    echo "╚══════════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

print_step() { echo -e "${CYAN}[STEP]${NC} $1"; }
print_success() { echo -e "${GREEN}[OK]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[WARN]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }

check_fuse() {
    print_step "Checking FUSE2..."
    if ! command -v fusermount &> /dev/null && ! command -v fusermount3 &> /dev/null; then
        print_warning "FUSE2 not found. Installing..."
        if command -v pacman &> /dev/null; then
            sudo pacman -S --noconfirm fuse2
        elif command -v apt &> /dev/null; then
            sudo apt update && sudo apt install -y fuse
        elif command -v dnf &> /dev/null; then
            sudo dnf install -y fuse
        elif command -v zypper &> /dev/null; then
            sudo zypper install -y fuse
        else
            print_error "Please install FUSE2 manually for your distro"
            exit 1
        fi
        print_success "FUSE2 installed"
    else
        print_success "FUSE2 found"
    fi
}

create_dirs() {
    print_step "Creating directories..."
    mkdir -p "$INSTALL_DIR" "$DESKTOP_DIR" "$ICON_DIR"
    print_success "Directories created"
}

download_appimage() {
    print_step "Downloading AppImage..."
    
    # Try GitHub releases first
    RELEASE_URL="https://github.com/eduardozx/cachy-game-optimizer/releases/latest/download/cachy-game-optimizer.AppImage"
    
    if command -v wget &> /dev/null; then
        wget -q --show-progress -O "$APPIMAGE_PATH" "$RELEASE_URL" 2>&1 || return 1
    else
        curl -L --progress-bar -o "$APPIMAGE_PATH" "$RELEASE_URL" 2>&1 || return 1
    fi
    
    chmod +x "$APPIMAGE_PATH"
    print_success "AppImage downloaded"
    return 0
}

build_from_source() {
    print_step "Building from source (fallback)..."
    
    REPO_DIR="/tmp/cachy-game-optimizer-build-$$"
    git clone --depth 1 https://github.com/eduardozx/cachy-game-optimizer.git "$REPO_DIR"
    cd "$REPO_DIR"
    
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip -q
    pip install -e . -q
    pip install pyinstaller -q
    
    # Build with pyinstaller
    cat > entry_point.py << 'PYEOF'
#!/usr/bin/env python3
import sys, os
if getattr(sys, 'frozen', False):
    sys.path.insert(0, sys._MEIPASS)
    sys.path.insert(0, os.path.dirname(sys.executable))

def main():
    if len(sys.argv) > 1 and sys.argv[1] in ('--gui', '--tui'):
        if sys.argv[1] == '--gui':
            from cachy_game_optimizer.gui import main as gui_main
            return gui_main()
        else:
            from cachy_game_optimizer.main import main as tui_main
            return tui_main()
    else:
        from cachy_game_optimizer.cli import main as cli_main
        if len(sys.argv) == 1:
            sys.argv = ['cgo', 'help']
        elif sys.argv[0].endswith(('cachy-game-optimizer', 'cachy-game-optimizer.AppImage')):
            sys.argv = ['cgo'] + sys.argv[1:]
        return cli_main()

if __name__ == '__main__':
    sys.exit(main())
PYEOF

    pyinstaller --clean --onefile --name cachy-game-optimizer       --add-data "config:config"       --add-data "games:games"       --add-data "scripts:scripts"       --add-data "compat:compat"       --hidden-import PyQt6.QtCore       --hidden-import PyQt6.QtWidgets       --hidden-import PyQt6.QtGui       --hidden-import textual       --hidden-import textual.widgets       --hidden-import textual.widgets._tab_pane       --hidden-import textual.widgets._data_table       --hidden-import rich       --hidden-import psutil       --hidden-import yaml       --hidden-import tomli       --hidden-import requests       --hidden-import cachy_game_optimizer.hardware       --hidden-import cachy_game_optimizer.optimizer       --hidden-import cachy_game_optimizer.games       --hidden-import cachy_game_optimizer.cli       --hidden-import cachy_game_optimizer.main       --hidden-import cachy_game_optimizer.gui       --hidden-import cachy_game_optimizer.error_analyzer       --hidden-import cachy_game_optimizer.gui_wine_tab       --hidden-import cachy_game_optimizer.wine_downloader       --hidden-import cachy_game_optimizer.workers       --hidden-import cachy_game_optimizer.privileged_helper       entry_point.py
    
    cp dist/cachy-game-optimizer "$APPIMAGE_PATH"
    chmod +x "$APPIMAGE_PATH"
    print_success "Built from source"
}

create_desktop_and_icon() {
    print_step "Creating desktop entry and icon..."
    mkdir -p "$DESKTOP_DIR" "$ICON_DIR"
    
    cat > "$DESKTOP_DIR/cachy-game-optimizer.desktop" << EOF
[Desktop Entry]
Name=CachyOS Game Optimizer
Comment=Futuristic Gaming Performance Suite for CachyOS
Exec=$APPIMAGE_PATH --gui
Icon=cachy-game-optimizer
Terminal=false
Type=Application
Categories=Game;System;Utility;
Keywords=game;optimizer;gaming;performance;proton;wine;gamescope;
StartupNotify=true
EOF
    
    cat > "$ICON_DIR/cachy-game-optimizer.svg" << 'EOF'
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256" width="256" height="256">
  <rect width="256" height="256" rx="32" fill="#0d0d0d"/>
  <circle cx="128" cy="128" r="80" fill="none" stroke="#00ff88" stroke-width="8"/>
  <path d="M80 128 L115 163 L176 95" fill="none" stroke="#00ff88" stroke-width="12" stroke-linecap="round" stroke-linejoin="round"/>
  <circle cx="128" cy="128" r="40" fill="#00ff88"/>
  <text x="128" y="140" text-anchor="middle" fill="#0d0d0d" font-family="monospace" font-size="24" font-weight="bold">FPS</text>
</svg>
EOF
    
    # Try to create PNG
    if command -v magick &> /dev/null; then
        magick "$ICON_DIR/cachy-game-optimizer.svg" "$ICON_DIR/cachy-game-optimizer.png" 2>/dev/null || true
    elif command -v convert &> /dev/null; then
        convert "$ICON_DIR/cachy-game-optimizer.svg" "$ICON_DIR/cachy-game-optimizer.png" 2>/dev/null || true
    fi
    
    print_success "Desktop entry and icon created"
}

update_databases() {
    print_step "Updating desktop database..."
    command -v update-desktop-database &> /dev/null && update-desktop-database "$HOME/.local/share/applications" 2>/dev/null || true
    command -v gtk-update-icon-cache &> /dev/null && gtk-update-icon-cache -f -t "$HOME/.local/share/icons/hicolor" 2>/dev/null || true
    print_success "Desktop database updated"
}

main() {
    print_header() {
        echo -e "${MAGENTA}"
        echo "╔══════════════════════════════════════════════════════════════════════╗"
        echo "║          CachyOS Game Optimizer - One-Click Installer               ║"
        echo "║          Futuristic Gaming Performance Suite                        ║"
        echo "╚══════════════════════════════════════════════════════════════════════╝"
        echo -e "${NC}"
    }
    print_header
    
    check_fuse
    create_dirs
    
    # Try to download, fallback to building
    if ! download_appimage; then
        print_warning "Download failed, building from source..."
        build_from_source
    fi
    
    create_desktop_and_icon
    update_databases
    
    # Test
    if "$APPIMAGE_PATH" --help &> /dev/null; then
        print_success "Installation verified!"
    else
        print_error "Installation test failed"
        exit 1
    fi
    
    # Show usage
    echo ""
    echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}  Installation complete! 🎮${NC}"
    echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
    echo ""
    echo -e "${CYAN}AppImage:${NC} $APPIMAGE_PATH"
    echo ""
    echo -e "${CYAN}Usage:${NC}"
    echo "  cachy-game-optimizer.AppImage --gui      # Launch GUI"
    echo "  cachy-game-optimizer.AppImage --tui      # Launch TUI"
    echo "  cachy-game-optimizer.AppImage detect     # Detect hardware"
    echo "  cachy-game-optimizer.AppImage recommend  # Show optimizations"
    echo "  cachy-game-optimizer.AppImage scan       # Scan games"
    echo "  cachy-game-optimizer.AppImage list       # List games"
    echo "  cachy-game-optimizer.AppImage launch <id> # Launch game"
    echo "  cachy-game-optimizer.AppImage optimize   # Run optimizations"
    echo ""
    echo -e "${CYAN}From menu:${NC} Search 'CachyOS Game Optimizer'"
    echo ""
    echo -e "${YELLOW}Note:${NC} Some optimizations need sudo"
    echo -e "${YELLOW}Note:${NC} GameScope presets: Borderless, Exclusive, Windowed, 1080p/60, 1440p/144, Steam Deck, Competitive"
    echo ""
}

print_step() { echo -e "${CYAN}[STEP]${NC} $1"; }
print_success() { echo -e "${GREEN}[OK]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[WARN]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }

main "$@"
