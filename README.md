# VaultCLI

A terminal-based password manager written in Python. Passwords are encrypted using a master password that is never stored in plaintext. The vault must be run with `sudo` — all sensitive files are owned by root and restricted to `600` permissions.

---

## How It Works

VaultCLI stores two types of files:

- **`~/.config/vconf/master.json`** — stores the bcrypt hash of your master password and the salt used to derive the encryption key. Owned by root, `chmod 600`.
- **`~/.vault/pwd.json`** — stores your service passwords encrypted with Fernet (AES-128-CBC). Owned by root, `chmod 600`.

When you add a password, a 256-bit encryption key is derived from your master password using PBKDF2-HMAC-SHA256 with 480,000 iterations and the stored salt. The password is encrypted with that key and written to the vault file. Retrieval reverses the process — the key is re-derived from your master password and used to decrypt.

The master password itself is never stored. Only its bcrypt hash is kept, used solely for login verification.

---

## Project Structure

```
vaultcli/
├── vault/
│   ├── __init__.py
│   ├── vault.py          ← Entry point. UI, menu, input handling
│   ├── auth.py           ← Master password hashing and verification (bcrypt)
│   ├── encryption.py     ← Key derivation, encrypt/decrypt, vault file I/O
│   └── conf.py           ← Config file I/O for master.json
├── tests/
│   ├── test_vault.py
│   ├── test_auth.py
│   ├── test_encryption.py
│   └── test_conf.py
├── vaultenv/             ← Virtual environment (not committed)
├── install.sh            ← Automated installer
├── uninstall.sh          ← Automated uninstaller
├── requirements.txt
├── .gitignore
└── README.md
```

---

## Requirements

- Python 3.12+
- Linux (Wayland or X11)
- `sudo` access
- `wl-clipboard` (Wayland) or `xclip` (X11) for clipboard support

---

## Installation

**1. Clone the repo**
```bash
git clone https://github.com/LostChessElo/vaultcli.git
cd vaultcli
```

**2. Run the installer**
```bash
chmod +x install.sh
./install.sh
```

The installer will:
- Check your Python version
- Create a virtual environment and install dependencies
- Detect your display server and install the correct clipboard backend
- Add the `vault` alias to your shell config

**3. Reload your shell**

**zsh**
```bash
source ~/.zshrc
```
**bash**
```bash
source ~/.bashrc
```

---

### Manual Installation

If you prefer to set up manually:

```bash
python3 -m venv vaultenv
source vaultenv/bin/activate
pip install -r requirements.txt

# Wayland
sudo apt install wl-clipboard

# X11
sudo apt install xclip
```

Add this alias to your `~/.zshrc` or `~/.bashrc`:
```bash
alias vault="sudo --preserve-env=WAYLAND_DISPLAY,XDG_RUNTIME_DIR /home/<user>/vaultcli/vaultenv/bin/python /home/<user>/vaultcli/vault/vault.py"
```

---

## Uninstallation

```bash
chmod +x uninstall.sh
./uninstall.sh
```

The uninstaller will remove the shell alias, config directory, vault data directory, and virtual environment — each with individual confirmation prompts.

---

## Usage

```bash
vault
```

Or without the alias:
```bash
sudo --preserve-env=WAYLAND_DISPLAY,XDG_RUNTIME_DIR /path/to/vaultenv/bin/python vault/vault.py
```

> `--preserve-env` is required on Wayland so the clipboard can reach your display session as root.

---

## First Run

On first launch, VaultCLI detects that no master password has been set and prompts you to create one.

**Master password requirements:**
- Minimum 8 characters
- At least one letter
- At least one number
- At least one special character (`!@#$%^&*` etc.)

You will be asked to retype the password to confirm. Once set, the bcrypt hash and salt are written to `~/.config/vconf/master.json` with root-only permissions.

---

## Menu Options

```
╭────────────────────────────────────────╮
│                VaultCLI                │
├────────────────────────────────────────┤
│                                        │
│  → Add service                         │
│    Get service                         │
│    Remove service                      │
│    Remove all services                 │
│    Log out                             │
│    Quit                                │
│                                        │
╰────────────────────────────────────────╯
```

Navigate with arrow keys, select with Enter.

| Option | Description |
|---|---|
| Add service | Save an encrypted password for a named service |
| Get service | Retrieve and copy a password to clipboard |
| Remove service | Delete a single saved password |
| Remove all services | Wipe the entire vault (requires confirmation) |
| Log out | Clear the session and return to the login screen |
| Quit | Exit the program |

---

## Security Details

| Property | Value |
|---|---|
| Password hashing | bcrypt (work factor 12) |
| Encryption algorithm | Fernet (AES-128-CBC + HMAC-SHA256) |
| Key derivation | PBKDF2-HMAC-SHA256, 480,000 iterations |
| File permissions | `chmod 600`, owned by root |
| Master password storage | Never stored — bcrypt hash only |
| Clipboard | Password copied on retrieval |

---

## Why sudo?

VaultCLI enforces `sudo` at the application level — `conf.py` and `encryption.py` both call `os.geteuid()` and raise `PermissionError` if not running as root. This ensures:

- Vault files are owned by root and unreadable by other users
- No unprivileged process can read or modify the vault directly
- The permissions are set explicitly on every write (`chmod 600`, `chown 0:0`)

---

## Troubleshooting

**`Pyperclip could not find a copy/paste mechanism`**

You are missing a clipboard backend. Install one:
```bash
sudo apt install wl-clipboard   # Wayland
sudo apt install xclip          # X11
```

And make sure your alias uses `--preserve-env=WAYLAND_DISPLAY,XDG_RUNTIME_DIR`.

**`PermissionError: Vaultcli must be run with sudo permissions`**

You are running without sudo. Use the alias or prefix with `sudo`.

**`ModuleNotFoundError` when running with sudo**

sudo uses the system Python, not your venv. Use the full venv Python path in your alias:
```bash
sudo --preserve-env=WAYLAND_DISPLAY,XDG_RUNTIME_DIR /path/to/vaultenv/bin/python vault/vault.py
```
---

## Dependencies

| Package | Purpose |
|---|---|
| `bcrypt` | Master password hashing and verification |
| `cryptography` | Fernet encryption and PBKDF2 key derivation |
| `pyperclip` | Clipboard access for password retrieval |

---

## Changelog

### v1.0.0
- Full terminal UI built with `curses`
- Master password setup and login with bcrypt verification
- Add, retrieve, remove, and wipe services
- Passwords encrypted with Fernet via PBKDF2-derived key
- Clipboard copy on password retrieval
- Root-owned vault files with `chmod 600` permissions enforced at application level
- Log out without quitting
- Remove all services with confirmation prompt
- Automated `install.sh` and `uninstall.sh`
- 79-test pytest suite

---

## License

Personal project. Not intended for redistribution.