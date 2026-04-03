#!/bin/bash

# ── colours ──────────────────────────────────────────────────
BLUE='\033[34m'
GREEN='\033[32m'
RED='\033[31m'
YELLOW='\033[33m'
RESET='\033[0m'
BOLD='\033[1m'

# ── helpers ───────────────────────────────────────────────────
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

# ── banner ────────────────────────────────────────────────────
clear
divider
echo -e "${RED}${BOLD}"
echo "        VaultCLI Uninstaller"
echo -e "${RESET}"
divider
echo ""
warn "This will remove VaultCLI from your system."
echo ""

if ! confirm "Continue with uninstall?"; then
    info "Uninstall cancelled."
    exit 0
fi
echo ""

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/vaultenv"

# ── step 1: remove alias ──────────────────────────────────────
divider
info "Removing shell alias..."
divider

remove_alias() {
    local RC_FILE="$1"
    local SHELL_NAME="$2"

    if [[ ! -f "$RC_FILE" ]]; then
        warn "$RC_FILE not found, skipping."
        return
    fi

    if grep -q "alias vault=" "$RC_FILE"; then
        # remove the comment line and alias line together
        sed -i '/# VaultCLI/{N;s/# VaultCLI\n.*alias vault=.*//}' "$RC_FILE"
        # catch any leftover alias line in case comment wasn't there
        sed -i '/alias vault=/d' "$RC_FILE"
        # remove any double blank lines left behind
        sed -i '/^$/N;/^\n$/d' "$RC_FILE"
        success "Alias removed from $RC_FILE."
    else
        info "No vault alias found in $RC_FILE."
    fi
}

remove_alias "$HOME/.bashrc" "bash"
remove_alias "$HOME/.zshrc"  "zsh"
echo ""

# ── step 2: remove venv ───────────────────────────────────────
divider
info "Removing virtual environment..."
divider

if [[ -d "$VENV_DIR" ]]; then
    rm -rf "$VENV_DIR"
    success "Removed $VENV_DIR."
else
    info "No virtual environment found at $VENV_DIR."
fi
echo ""

# ── step 3: vault data ────────────────────────────────────────
divider
info "Checking for stored vault data..."
divider

# VaultCLI stores its config under ~/.config/vaultcli by default
VAULT_DATA_DIR="$HOME/.config/vaultcli"

if [[ -d "$VAULT_DATA_DIR" ]]; then
    warn "Vault data found at $VAULT_DATA_DIR"
    warn "This contains your encrypted passwords."
    echo ""
    if confirm "Delete vault data? ${RED}${BOLD}This cannot be undone.${RESET}"; then
        rm -rf "$VAULT_DATA_DIR"
        success "Vault data deleted."
    else
        info "Vault data kept at $VAULT_DATA_DIR."
    fi
else
    info "No vault data directory found."
fi
echo ""

# ── step 4: clipboard backend ─────────────────────────────────
divider
info "Clipboard backend..."
divider

if [[ -n "$WAYLAND_DISPLAY" ]]; then
    CLIPBOARD_PKG="wl-clipboard"
    CLIPBOARD_BIN="wl-copy"
else
    CLIPBOARD_PKG="xclip"
    CLIPBOARD_BIN="xclip"
fi

if command -v "$CLIPBOARD_BIN" &>/dev/null; then
    if confirm "Remove $CLIPBOARD_PKG? (only do this if nothing else uses it)"; then
        sudo apt remove -y "$CLIPBOARD_PKG"
        success "$CLIPBOARD_PKG removed."
    else
        info "Keeping $CLIPBOARD_PKG."
    fi
else
    info "$CLIPBOARD_PKG not installed, nothing to remove."
fi
echo ""

# ── done ──────────────────────────────────────────────────────
divider
success "VaultCLI uninstalled."
divider
echo ""
echo -e "  Reload your shell to clear the alias from the current session:"
echo -e "  ${BOLD}source ~/.bashrc${RESET}  or  ${BOLD}source ~/.zshrc${RESET}"
echo ""
divider
