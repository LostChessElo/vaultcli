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
warn "This will remove your vault data, config, and shell alias."
warn "Your saved passwords will be permanently deleted."
echo ""

if ! confirm "Are you sure you want to uninstall VaultCLI?"; then
    info "Uninstall cancelled."
    exit 0
fi
echo ""

# ── step 1: remove alias ──────────────────────────────────────
divider
info "Removing shell alias..."
divider

CURRENT_SHELL="$(basename "$SHELL")"
info "Detected shell: $CURRENT_SHELL"
echo ""

remove_alias() {
    local RC_FILE="$1"
    local SHELL_NAME="$2"

    if [[ ! -f "$RC_FILE" ]]; then
        warn "$RC_FILE not found, skipping $SHELL_NAME."
        return
    fi

    if grep -q "alias vault=" "$RC_FILE"; then
        if confirm "Remove vault alias from $RC_FILE?"; then
            sed -i '/# VaultCLI/d' "$RC_FILE"
            sed -i '/alias vault=/d' "$RC_FILE"
            success "Alias removed from $RC_FILE."
        else
            warn "Skipping alias removal from $RC_FILE."
        fi
    else
        info "No vault alias found in $RC_FILE."
    fi
}

if [[ "$CURRENT_SHELL" == "zsh" ]]; then
    remove_alias "$HOME/.zshrc" "zsh"
    if [[ -f "$HOME/.bashrc" ]] && grep -q "alias vault=" "$HOME/.bashrc"; then
        remove_alias "$HOME/.bashrc" "bash"
    fi
elif [[ "$CURRENT_SHELL" == "bash" ]]; then
    remove_alias "$HOME/.bashrc" "bash"
    if [[ -f "$HOME/.zshrc" ]] && grep -q "alias vault=" "$HOME/.zshrc"; then
        remove_alias "$HOME/.zshrc" "zsh"
    fi
else
    warn "Unrecognised shell: $CURRENT_SHELL"
    remove_alias "$HOME/.bashrc" "bash"
    remove_alias "$HOME/.zshrc" "zsh"
fi
echo ""

# ── step 2: remove config dir ─────────────────────────────────
divider
info "Removing config directory..."
divider

CONFIG_DIR="$HOME/.config/vconf"

if [[ -d "$CONFIG_DIR" ]]; then
    info "Found: $CONFIG_DIR"
    if confirm "Delete $CONFIG_DIR and all contents? (master password hash)"; then
        sudo rm -rf "$CONFIG_DIR"
        if [[ $? -eq 0 ]]; then
            success "Config directory removed."
        else
            error "Failed to remove $CONFIG_DIR — try: sudo rm -rf $CONFIG_DIR"
        fi
    else
        warn "Skipping config directory removal."
    fi
else
    info "Config directory not found, nothing to remove."
fi
echo ""

# ── step 3: remove vault data dir ────────────────────────────
divider
info "Removing vault data directory..."
divider

VAULT_DIR="$HOME/.vault"

if [[ -d "$VAULT_DIR" ]]; then
    info "Found: $VAULT_DIR"
    warn "This contains your encrypted passwords."
    if confirm "Delete $VAULT_DIR and all contents? (cannot be undone)"; then
        sudo rm -rf "$VAULT_DIR"
        if [[ $? -eq 0 ]]; then
            success "Vault data directory removed."
        else
            error "Failed to remove $VAULT_DIR — try: sudo rm -rf $VAULT_DIR"
        fi
    else
        warn "Skipping vault data directory removal."
    fi
else
    info "Vault data directory not found, nothing to remove."
fi
echo ""

# ── step 4: remove venv ───────────────────────────────────────
divider
info "Removing virtual environment..."
divider

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/vaultenv"

if [[ -d "$VENV_DIR" ]]; then
    info "Found: $VENV_DIR"
    if confirm "Delete virtual environment at $VENV_DIR?"; then
        rm -rf "$VENV_DIR"
        success "Virtual environment removed."
    else
        warn "Skipping virtual environment removal."
    fi
else
    info "Virtual environment not found, nothing to remove."
fi
echo ""

# ── done ──────────────────────────────────────────────────────
divider
success "VaultCLI uninstall complete."
divider
echo ""
echo -e "  Reload your shell to apply alias removal:"
echo -e "  ${BOLD}source ~/.zshrc${RESET}  or  ${BOLD}source ~/.bashrc${RESET}"
echo ""
divider
