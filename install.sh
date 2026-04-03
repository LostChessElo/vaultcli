#!/bin/bash

BLUE='\033[34m'
GREEN='\033[32m'
RED='\033[31m'
YELLOW='\033[33m'
RESET='\033[0m'
BOLD='\033[1m'

info()    { echo -e "${BLUE}${BOLD}[•]${RESET} $1"; }
success() { echo -e "${GREEN}${BOLD}[✓]${RESET} $1"; }
warn()    { echo -e "${YELLOW}${BOLD}[!]${RESET} $1"; }
error()   { echo -e "${RED}${BOLD}[✗]${RESET} $1"; }

confirm() {
    echo -e "${YELLOW}${BOLD}[?]${RESET} $1 ${BOLD}(y/n)${RESET}: \c"
    read -r answer
    [[ "$answer" =~ ^[Yy]$ ]]
}

divider() {
    echo -e "${BLUE}────────────────────────────────────────────────${RESET}"
}

clear
divider
echo -e "${BLUE}${BOLD}"
echo "        VaultCLI Installer"
echo -e "${RESET}"
divider
echo ""

#install dir
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VAULT_ENTRY="$SCRIPT_DIR/project.py"

if [[ ! -f "$VAULT_ENTRY" ]]; then
    error "Cannot find project.py in $SCRIPT_DIR"
    error "Run this script from the root of the vaultcli repo."
    exit 1
fi

info "Install directory: $SCRIPT_DIR"
echo ""


divider
info "Checking Python version..."
divider

if ! command -v python3 &>/dev/null; then
    error "python3 is not installed. Install it with: sudo apt install python3"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
REQUIRED="3.10"

if python3 -c "import sys; exit(0 if sys.version_info >= (3,10) else 1)"; then
    success "Python $PYTHON_VERSION found."
else
    error "Python $REQUIRED+ required. Found $PYTHON_VERSION."
    exit 1
fi
echo ""
# venv
divider
info "Setting up virtual environment..."
divider

VENV_DIR="$SCRIPT_DIR/vaultenv"

if [[ -d "$VENV_DIR" ]]; then
    warn "Virtual environment already exists at $VENV_DIR."
    if confirm "Recreate it?"; then
        rm -rf "$VENV_DIR"
        python3 -m venv "$VENV_DIR"
        success "Virtual environment recreated."
    else
        info "Keeping existing virtual environment."
    fi
else
    python3 -m venv "$VENV_DIR"
    success "Virtual environment created at $VENV_DIR."
fi
echo ""

# ── step 3: install dependencies ─────────────────────────────
divider
info "Installing dependencies from requirements.txt..."
divider

REQUIREMENTS="$SCRIPT_DIR/requirements.txt"

if [[ ! -f "$REQUIREMENTS" ]]; then
    error "requirements.txt not found in $SCRIPT_DIR"
    exit 1
fi

"$VENV_DIR/bin/pip" install --quiet --upgrade pip
"$VENV_DIR/bin/pip" install --quiet -r "$REQUIREMENTS"

if [[ $? -eq 0 ]]; then
    success "Dependencies installed."
else
    error "Failed to install dependencies."
    exit 1
fi
echo ""

#clipboard
divider
info "Checking clipboard backend..."
divider

if [[ -n "$WAYLAND_DISPLAY" ]]; then
    DISPLAY_SERVER="wayland"
    CLIPBOARD_PKG="wl-clipboard"
    CLIPBOARD_BIN="wl-copy"
else
    DISPLAY_SERVER="x11"
    CLIPBOARD_PKG="xclip"
    CLIPBOARD_BIN="xclip"
fi

info "Display server detected: $DISPLAY_SERVER"

if command -v "$CLIPBOARD_BIN" &>/dev/null; then
    success "$CLIPBOARD_PKG is already installed."
else
    warn "$CLIPBOARD_PKG not found — required for clipboard support."
    if confirm "Install $CLIPBOARD_PKG with sudo apt?"; then
        sudo apt install -y "$CLIPBOARD_PKG"
        if [[ $? -eq 0 ]]; then
            success "$CLIPBOARD_PKG installed."
        else
            error "Failed to install $CLIPBOARD_PKG."
            warn "You can install it manually: sudo apt install $CLIPBOARD_PKG"
        fi
    else
        warn "Skipping clipboard install. Clipboard copy will not work."
    fi
fi
echo ""

#set up alias
divider
info "Setting up shell alias..."
divider

PYTHON_BIN="$VENV_DIR/bin/python"
ALIAS_CMD="alias vault=\"sudo --preserve-env=WAYLAND_DISPLAY,XDG_RUNTIME_DIR,XDG_SESSION_TYPE $PYTHON_BIN $VAULT_ENTRY\""

CURRENT_SHELL="$(basename "$SHELL")"
info "Detected shell: $CURRENT_SHELL"
echo ""

setup_alias() {
    local RC_FILE="$1"
    local SHELL_NAME="$2"

    if [[ ! -f "$RC_FILE" ]]; then
        warn "$RC_FILE not found, skipping $SHELL_NAME."
        return
    fi

    if grep -q "alias vault=" "$RC_FILE"; then
        warn "Alias already exists in $RC_FILE."
        if confirm "Overwrite it?"; then
            sed -i '/# VaultCLI/{N;/alias vault=/d}' "$RC_FILE"
            sed -i '/alias vault=/d' "$RC_FILE"
        else
            info "Keeping existing alias in $RC_FILE."
            return
        fi
    fi

    if confirm "Add vault alias to $RC_FILE?"; then
        echo "" >> "$RC_FILE"
        echo "# VaultCLI" >> "$RC_FILE"
        echo "$ALIAS_CMD" >> "$RC_FILE"
        success "Alias added to $RC_FILE."
    else
        warn "Skipping alias for $SHELL_NAME."
    fi
}

if [[ "$CURRENT_SHELL" == "zsh" ]]; then
    setup_alias "$HOME/.zshrc" "zsh"
    if confirm "Also add alias to bash (~/.bashrc)?"; then
        setup_alias "$HOME/.bashrc" "bash"
    fi
elif [[ "$CURRENT_SHELL" == "bash" ]]; then
    setup_alias "$HOME/.bashrc" "bash"
    if confirm "Also add alias to zsh (~/.zshrc)?"; then
        setup_alias "$HOME/.zshrc" "zsh"
    fi
else
    warn "Unrecognised shell: $CURRENT_SHELL"
    if confirm "Add alias to ~/.bashrc?"; then
        setup_alias "$HOME/.bashrc" "bash"
    fi
    if confirm "Add alias to ~/.zshrc?"; then
        setup_alias "$HOME/.zshrc" "zsh"
    fi
fi
echo ""

divider
success "VaultCLI installation complete."
divider
echo ""
echo -e "  Reload your shell to use the alias:"
echo -e "  ${BOLD}source ~/.bashrc${RESET}  or  ${BOLD}source ~/.zshrc${RESET}"
echo ""
echo -e "  Then run:"
echo -e "  ${BOLD}vault${RESET}"
echo ""
divider