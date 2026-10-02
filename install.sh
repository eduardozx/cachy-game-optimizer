#!/bin/bash
# CachyOS Game Optimizer - One-Click Installer
# Downloads, installs and sets up the AppImage automatically

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m' # No Color

# Configuration
APP_NAME="cachy-game-optimizer"
APPIMAGE_URL="https://github.com/eduardozx/cachy-game-optimizer/releases/latest/download/${APP_NAME}.AppImage"
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

print_step() {
    echo -e "${CYAN}[STEP]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[OK]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_dependencies() {
    print_step "Checking dependencies..."
    
    # Check for FUSE2
    if ! command -v fusermount &> /dev/null && ! command -v fusermount3 &> /dev/null; then
        print_warning "FUSE2 not found. AppImage requires FUSE2 to run."
        echo "Attempting to install..."
        
        if command -v pacman &> /dev/null; then
            sudo pacman -S --noconfirm fuse2
        elif command -v apt &> /dev/null; then
            sudo apt update && sudo apt install -y fuse
        elif command -v dnf &> /dev/null; then
            sudo dnf install -y fuse
        elif command -v zypper &> /dev/null; then
            sudo zypper install -y fuse
        else
            print_error "Could not install FUSE2 automatically. Please install it manually:"
            echo "  Arch/CachyOS: sudo pacman -S fuse2"
            echo "  Ubuntu/Debian: sudo apt install fuse"
            echo "  Fedora: sudo dnf install fuse"
            echo "  openSUSE: sudo zypper install fuse"
            exit 1
        fi
        print_success "FUSE2 installed"
    else
        print_success "FUSE2 found"
    fi
    
    # Check for wget or curl
    if ! command -v wget &> /dev/null && ! command -v curl &> /dev/null; then
        print_error "Neither wget nor curl found. Please install one of them."
        exit 1
    fi
}

create_directories() {
    print_step "Creating directories..."
    mkdir -p "$INSTALL_DIR"
    mkdir -p "$DESKTOP_DIR"
    mkdir -p "$ICON_DIR"
    print_success "Directories created"
}

download_appimage() {
    print_step "Downloading AppImage..."
    
    # Try to download from GitHub releases
    if command -v wget &> /dev/null; then
        wget -q --show-progress -O "$APPIMAGE_PATH" "$APPIMAGE_URL" 2>&1 || {
            print_warning "Failed to download from GitHub releases."
            print_step "Trying alternative: building from source..."
            build_from_source
            return
        }
    else
        curl -L --progress-bar -o "$APPIMAGE_PATH" "$APPIMAGE_URL" 2>&1 || {
            print_warning "Failed to download from GitHub releases."
            print_step "Trying alternative: building from source..."
            build_from_source
            return
        }
    fi
    
    chmod +x "$APPIMAGE_PATH"
    print_success "AppImage downloaded to $APPIMAGE_PATH"
}

build_from_source() {
    print_step "Building from source using existing project..."
    
    # Use the already working project directory
    PROJECT_DIR="/home/kasher/.local/share/cachy-game-optimizer"
    cd "$PROJECT_DIR"
    
    # Create entry_point.py
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

    # Build using the project's venv pyinstaller binary directly
    /home/kasher/.local/share/cachy-game-optimizer/venv/bin/pyinstaller --clean --onefile --name cachy-game-optimizer \
      --add-data "config:config" \
      --add-data "games:games" \
      --add-data "scripts:scripts" \
      --add-data "compat:compat" \
      --hidden-import PyQt6.QtCore \
      --hidden-import PyQt6.QtWidgets \
      --hidden-import PyQt6.QtGui \
      --hidden-import textual \
      --hidden-import textual.widgets \
      --hidden-import textual.widgets._tab_pane \
      --hidden-import textual.widgets._data_table \
      --hidden-import rich \
      --hidden-import psutil \
      --hidden-import yaml \
      --hidden-import tomli \
      --hidden-import requests \
      --hidden-import cachy_game_optimizer.hardware \
      --hidden-import cachy_game_optimizer.optimizer \
      --hidden-import cachy_game_optimizer.games \
      --hidden-import cachy_game_optimizer.cli \
      --hidden-import cachy_game_optimizer.main \
      --hidden-import cachy_game_optimizer.gui \
      --hidden-import cachy_game_optimizer.error_analyzer \
      --hidden-import cachy_game_optimizer.gui_wine_tab \
      --hidden-import cachy_game_optimizer.wine_downloader \
      --hidden-import cachy_game_optimizer.workers \
      --hidden-import cachy_game_optimizer.privileged_helper \
      entry_point.py
    
    # Copy built binary
    cp dist/cachy-game-optimizer "$APPIMAGE_PATH"
    chmod +x "$APPIMAGE_PATH"
    
    print_success "Built from source and installed"
}

create_desktop_entry() {
    print_step "Creating desktop entry..."
    
    cat > "$DESKTOP_DIR/${APP_NAME}.desktop" << EOF
[Desktop Entry]
Name=CachyOS Game Optimizer
Comment=Futuristic Gaming Performance Suite for CachyOS
Exec=${APPIMAGE_PATH} --gui
Icon=${APP_NAME}
Terminal=false
Type=Application
Categories=Game;System;Utility;
Keywords=game;optimizer;gaming;performance;proton;wine;gamescope;
StartupNotify=true
StartupWMClass=CachyOS Game Optimizer
EOF
    
    print_success "Desktop entry created"
}

create_icon() {
    print_step "Creating application icon..."
    
    # Create a simple SVG icon
    cat > "$ICON_DIR/${APP_NAME}.svg" << 'EOF'
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256" width="256" height="256">
  <rect width="256" height="256" rx="32" fill="#0d0d0d"/>
  <circle cx="128" cy="128" r="80" fill="none" stroke="#00ff88" stroke-width="8"/>
  <path d="M80 128 L115 163 L176 95" fill="none" stroke="#00ff88" stroke-width="12" stroke-linecap="round" stroke-linejoin="round"/>
  <circle cx="128" cy="128" r="40" fill="#00ff88"/>
  <text x="128" y="140" text-anchor="middle" fill="#0d0d0d" font-family="monospace" font-size="24" font-weight="bold">FPS</text>
</svg>
EOF
    
    # Try to convert to PNG if imagemagick/inkscape available
    if command -v magick &> /dev/null; then
        magick "$ICON_DIR/${APP_NAME}.svg" "$ICON_DIR/${APP_NAME}.png" 2>/dev/null || true
    elif command -v convert &> /dev/null; then
        convert "$ICON_DIR/${APP_NAME}.svg" "$ICON_DIR/${APP_NAME}.png" 2>/dev/null || true
    elif command -v inkscape &> /dev/null; then
        inkscape "$ICON_DIR/${APP_NAME}.svg" --export-png="$ICON_DIR/${APP_NAME}.png" 2>/dev/null || true
    fi
    
    print_success "Icon created"
}

update_desktop_database() {
    print_step "Updating desktop database..."
    if command -v update-desktop-database &> /dev/null; then
        update-desktop-database "$HOME/.local/share/applications" 2>/dev/null || true
    fi
    if command -v gtk-update-icon-cache &> /dev/null; then
        gtk-update-icon-cache -f -t "$HOME/.local/share/icons/hicolor" 2>/dev/null || true
    fi
    print_success "Desktop database updated"
}

test_installation() {
    print_step "Testing installation..."
    
    if [ -f "$APPIMAGE_PATH" ] && [ -x "$APPIMAGE_PATH" ]; then
        # Test CLI
        if "$APPIMAGE_PATH" --help &> /dev/null; then
            print_success "AppImage runs correctly"
        else
            print_warning "AppImage test failed, but file exists"
        fi
    else
        print_error "AppImage not found or not executable"
        exit 1
    fi
}

show_usage() {
    echo ""
    echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}  Installation complete! 🎮${NC}"
    echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
    echo ""
    echo -e "${CYAN}AppImage location:${NC} $APPIMAGE_PATH"
    echo ""
    echo -e "${CYAN}Usage:${NC}"
    echo "  ${APP_NAME}.AppImage --gui          # Launch GUI (recommended)"
    echo "  ${APP_NAME}.AppImage --tui          # Launch TUI"
    echo "  ${APP_NAME}.AppImage detect         # Detect hardware"
    echo "  ${APP_NAME}.AppImage recommend      # Show optimizations"
    echo "  ${APP_NAME}.AppImage scan           # Scan game libraries"
    echo "  ${APP_NAME}.AppImage list           # List games"
    echo "  ${APP_NAME}.AppImage launch <id>    # Launch game"
    echo "  ${APP_NAME}.AppImage optimize       # Run optimizations"
    echo ""
    echo -e "${CYAN}From application menu:${NC} Search for 'CachyOS Game Optimizer'"
    echo ""
    echo -e "${CYAN}GameScope presets included:${NC}"
    echo "  🖥️ Borderless Fullscreen (Recommended)"
    echo "  🎯 Exclusive Fullscreen (Lowest Latency)"
    echo "  🪟 Windowed (Streaming/Recording)"
    echo "  📺 1080p @ 60Hz Upscale (Low-end GPU)"
    echo "  📺 1440p @ 144Hz (High Refresh)"
    echo "  🎮 Steam Deck Style (720p/800p Upscale)"
    echo "  ⚡ Competitive (Low Latency + FPS Limit)"
    echo ""
    echo -e "${YELLOW}Note:${NC} Requires FUSE2 (already checked/installed)"
    echo -e "${YELLOW}Note:${NC} Some optimizations need sudo: sudo ${APP_NAME}.AppImage optimize"
    echo ""
}

main() {
    print_header
    
    check_dependencies
    create_directories
    download_appimage
    create_desktop_entry
    create_icon
    update_desktop_database
    test_installation
    show_usage
}

print_header() {
    echo -e "${MAGENTA}"
    echo "╔══════════════════════════════════════════════════════════════════════╗"
    echo "║          CachyOS Game Optimizer - One-Click Installer               ║"
    echo "║          Futuristic Gaming Performance Suite                        ║"
    echo "╚══════════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

# Run main
main "$@"
