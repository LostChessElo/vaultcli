import json
import os
from pathlib import Path
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
import base64
from conf import VaultConfig


class Encryption:
    def __init__(self):
        self._base_dir = Path.home() / ".vault"
        self._pwd_file = self._base_dir / "pwd.json"
        self._conf = VaultConfig()
        self._base_dir.mkdir(parents=True, exist_ok=True)

    @property
    def base_dir(self):
        return self._base_dir

    @property
    def pwd_file(self):
        return self._pwd_file

    def _get_salt(self):
        if not self._conf.exists() or self._conf.is_empty():
            raise RuntimeError("Missing config")
        data = self._conf.read_master()
        return data["salt"].encode()

    def _encrypt(self, pwd: str, key) -> str:
        return Fernet(key).encrypt(pwd.encode()).decode()

    def _decrypt(self, encrypted_pwd: str, key) -> str:
        return Fernet(key).decrypt(encrypted_pwd.encode()).decode()

    def _derive_key(self, master_pwd: str) -> bytes:
        salt = self._get_salt()
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=480000,
        )
        return base64.urlsafe_b64encode(kdf.derive(master_pwd.encode()))

    def write_to(self, data: dict):
        if os.geteuid() != 0:
            raise PermissionError("Error: you do not have permissions")
        if self._base_dir.exists() and isinstance(data, dict):
            with open(self._pwd_file, "w") as f:
                json.dump(data, f)
            self._pwd_file.chmod(0o600)
            os.chown(self._pwd_file, 0, 0)
        else:
            raise ValueError

    def read_from(self) -> dict:
        try:
            with open(self._pwd_file, "r") as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
        
    def is_empty(self):
        if os.geteuid() != 0:
            raise PermissionError("Error: you do not have permissions")
        try:
            with open(self._pwd_file, "r") as f:
                return not bool(json.load(f))
        except FileNotFoundError:
            return True
            
    def add_pwd(self, service: str, pwd: str, master_pwd: str) -> None:
        k = self._derive_key(master_pwd)
        encrypted = self._encrypt(pwd, k)
        existing = self.read_from()
        existing[service] = encrypted
        self.write_to(existing)

    def get_pwd(self, service: str, master_pwd: str):
        data = self.read_from()
        if not data or service not in data.keys():
            raise KeyError("Service not found.")
        k = self._derive_key(master_pwd)
        return self._decrypt(data[service], k)
    
    def remove_pwd(self, service: str) -> bool:
        data = self.read_from()
        if not data or service not in data:
            raise KeyError("Service not found.")
        del data[service]
        self.write_to(data)
        return service not in data

    def get_all(self):
        data = self.read_from()
        return "\n".join(data.keys())
    
    def clear(self):
        if os.geteuid() != 0:
            raise PermissionError("Vaultcli must be run with sudo permissions.")
        try:
            with open(self.pwd_file, "w") as f:
                json.dump({}, f)
        except FileNotFoundError:
            raise FileNotFoundError("Error: file missing from config dir")