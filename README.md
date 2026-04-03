# VaultCLI

A terminal-based encrypted password manager built in Python. VaultCLI stores your passwords locally in an encrypted file, protected by a master password. There are no cloud accounts, no subscriptions, and no data ever leaves your machine.

#### Video Demo: https://youtu.be/REPLACE_WITH_YOUR_URL

---

## Description

VaultCLI is a command-line password manager that runs entirely in your terminal using a curses-based interface. It encrypts all stored passwords using a key derived from your master password, meaning your vault is useless to anyone who does not know that password — even if they have direct access to your files.

The project was built as a CS50P final project with a focus on real-world security practices: passwords are never stored in plain text, the encryption key is derived at runtime and never written to disk, and file permissions are enforced at the OS level to prevent other users from reading the vault file.

### Features

- Master password authentication with bcrypt hashing
- Per-service password storage with Fernet symmetric encryption
- PBKDF2-HMAC-SHA256 key derivation — the encryption key is derived from your master password at runtime, never stored
- Curses-based terminal UI — no mouse required, fully keyboard-driven
- Clipboard integration with automatic Wayland and X11 detection
- Root-enforced file permissions (`chmod 600`) on the vault file
- Install and uninstall scripts with shell alias setup

---

## Project Structure

```
vaultcli/
├── project.py          # Entry point — main() lives here
├── requirements.txt    # Python dependencies
├── install.sh          # Installer — sets up venv, alias, clipboard backend
├── uninstall.sh        # Removes venv, alias, and optionally vault data
├── README.md
├── vault/
│   ├── __init__.py
│   ├── vault.py        # Vault class — UI and menu logic
│   ├── auth.py         # Auth class — master password hashing and verification
│   ├── encryption.py   # Encryption class — Fernet encrypt/decrypt, PBKDF2 key derivation
│   └── conf.py         # Conf class — file I/O, JSON read/write, permission enforcement
└── test/
    ├── test_vault.py
    ├── test_auth.py
    ├── test_encryption.py
    └── test_conf.py
```

---

## File Descriptions

### `project.py`

The entry point for CS50P submission requirements. Imports the `Vault` class from `vault/vault.py` and calls `main()`, which instantiates and runs the application. CS50P requires that `main()` and at least three independently testable functions live in or be importable from this file — those functions are re-exported here from the submodules.

### `vault/vault.py`

Contains the `Vault` class, which owns the application's runtime state and all menu logic. It holds the master password in memory for the duration of a session (never written to disk) and coordinates between the `Auth`, `Encryption`, and `Conf` classes.

Key methods:

- `run()` — top-level entry point, checks whether the vault is configured and routes to setup or login accordingly, then launches the main menu loop
- `_login()` — prompts for the master password using curses, verifies it against the stored bcrypt hash via `Auth`, allows up to three attempts before exiting
- `_setup()` — runs first-time setup: prompts for a new master password, validates it against the strength rules, then calls `Auth.set_up()` to hash and store it
- `_validate_password(password)` — enforces password strength: minimum 8 characters, at least one letter, one digit, and one special character. Returns `True` or `False`
- `_add_service()` — prompts for a service name and password, then calls `Encryption.add_pwd()` to encrypt and store the entry
- `_get_service()` — retrieves a password for a named service, decrypts it, and copies it to the clipboard using `_copy_to_clipboard()`
- `_remove_service()` — removes a single service entry after prompting for confirmation
- `_remove_all()` — clears the entire vault after requiring the user to type `YES` explicitly
- `_copy_to_clipboard(text)` — detects whether the session is running under Wayland or X11 using `XDG_SESSION_TYPE` and `WAYLAND_DISPLAY`, then routes to `wl-copy` or `xclip` accordingly. Falls back to `pyperclip` if neither binary is found

### `vault/auth.py`

Contains the `Auth` class, which handles all master password logic. It is intentionally decoupled from encryption — its only job is to verify that the person running the program is the vault's owner.

Key methods:

- `is_configured()` — returns `True` if the config file exists and contains a master password hash. Used by `Vault.run()` to decide whether to show setup or login
- `set_up(password)` — generates a bcrypt salt, hashes the password, and writes the hash and salt to the config file via `Conf`
- `check_pwd(password)` — reads the stored hash from the config file and uses `bcrypt.checkpw()` to verify the supplied password. Raises `RuntimeError` if called before setup

**Design decision:** bcrypt is used for the master password separately from the PBKDF2 key derivation in `encryption.py`. These are two different security concerns — bcrypt verifies identity (is this the right password?), while PBKDF2 derives the encryption key (given the right password, produce a consistent key). Conflating them would either weaken the encryption key derivation or slow down login unnecessarily.

### `vault/encryption.py`

Contains the `Encryption` class, which handles all cryptographic operations on stored service passwords.

Key methods:

- `_derive_key(master_pwd, salt)` — derives a 32-byte Fernet-compatible key from the master password using PBKDF2-HMAC-SHA256 with 480,000 iterations. The key is never stored — it is derived fresh each time from the master password held in memory
- `add_pwd(service, password, master_pwd)` — encrypts the service password using the derived key and writes it to the vault JSON file
- `get_pwd(service, master_pwd)` — retrieves and decrypts a stored password for the given service name
- `remove_pwd(service)` — removes a service entry from the vault JSON without needing the master password (the entry is deleted, not decrypted)
- `get_all()` — returns a formatted string of all stored service names, used by the UI to display the service list
- `is_empty()` — returns `True` if the vault contains no entries

**Design decision:** The encryption salt is stored separately from the master password salt in `auth.py`. The auth salt is used only by bcrypt for password verification. The encryption salt is used only by PBKDF2 to derive the Fernet key. Keeping them separate means a compromise of one does not affect the other. The salt is stored in plain text alongside the encrypted data — this is correct and expected behaviour. A salt is not a secret; its purpose is to prevent two users with the same master password from producing the same key.

**Design decision:** PBKDF2 uses 480,000 iterations, matching OWASP's 2023 recommended minimum for HMAC-SHA256. This makes brute-force attacks against the key derivation computationally expensive even if an attacker obtains the vault file and salt.

### `vault/conf.py`

Contains the `Conf` class, which handles all file system operations. It is the only class that reads from or writes to disk, keeping I/O concerns isolated from the rest of the application.

Key methods:

- `exists()` — returns `True` if the config file exists on disk
- `is_empty()` — returns `True` if the config file exists but contains no data
- `read_master()` — reads and returns the master password hash and auth salt from the config file
- `write_to_master(data)` — writes data to the config file and enforces `chmod 600` permissions so only the file owner can read it
- `read_vault()` — reads and returns all encrypted service entries from the vault JSON file
- `write_to_vault(data)` — writes updated vault data to disk and re-applies `chmod 600`

**Design decision:** File permissions are enforced on every write, not just at creation time. This means that even if permissions are manually changed while the program is not running, they are restored the next time anything is written. `chmod 600` is applied using `os.chmod()` rather than relying on the shell's umask, making the enforcement explicit and auditable.

---

## Installation

### Requirements

- Python 3.10 or higher
- `wl-clipboard` (Wayland) or `xclip` (X11) for clipboard support

### Using the installer

```bash
git clone https://github.com/LostChessElo/vaultcli.git
cd vaultcli
chmod +x install.sh
./install.sh
```

The installer will:

1. Check your Python version
2. Create a virtual environment at `vaultenv/`
3. Install all dependencies from `requirements.txt`
4. Detect your display server (Wayland or X11) and offer to install the appropriate clipboard backend
5. Add a `vault` shell alias to your `.bashrc` and/or `.zshrc`

After installation, reload your shell:

```bash
source ~/.bashrc   # or source ~/.zshrc
```

Then run:

```bash
vault
```

The alias runs VaultCLI via `sudo --preserve-env` to enforce root-level file permissions while preserving the Wayland environment variables needed for clipboard access.

### Manual installation

```bash
python3 -m venv vaultenv
source vaultenv/bin/activate
pip install -r requirements.txt
python project.py
```

---

## Uninstallation

```bash
chmod +x uninstall.sh
./uninstall.sh
```

The uninstaller removes the virtual environment, the shell alias from `.bashrc` and `.zshrc`, and optionally your stored vault data. It will ask before deleting the vault data and warn that deletion is irreversible.

---

## Running Tests

From the project root:

```bash
pytest test/ -v
```

Tests use `unittest.mock` to patch file system operations and subprocess calls so no files are read from or written to disk during the test run. Each class is tested in isolation with mocked dependencies.

---

## Dependencies

| Package | Purpose |
|---|---|
| `bcrypt` | Master password hashing and verification |
| `cryptography` | Fernet symmetric encryption and PBKDF2 key derivation |
| `pyperclip` | Clipboard fallback when `wl-copy` and `xclip` are unavailable |

All dependencies are listed in `requirements.txt` and installed by the installer.

---

## Security Notes

- Your master password is held in memory only for the duration of a session and is never written to disk
- The encryption key is derived from the master password at runtime and is never stored
- All vault files are created with `chmod 600` — readable only by the file owner
- Passwords are encrypted individually so a partial file read reveals nothing about other entries
- There is no password recovery mechanism — if the master password is forgotten, the vault cannot be decrypted