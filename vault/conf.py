import json 
import os
from pathlib import Path 

class VaultConfig:
    def __init__(self):
        self._base_dir = Path.home() / ".config" / "vconf"
        self._conf_file = self._base_dir / "master.json"
        self._base_dir.mkdir(parents=True, exist_ok=True)

    @property
    def conf_dir(self):
        return self._base_dir
    
    @property
    def conf_file(self):
        return self._conf_file
    
    def write_to_master(self, data: dict) -> None:
        if os.geteuid() != 0:
            raise PermissionError("Vaultcli must be run with sudo permissions.")
        try:
            with open(self.conf_file, "w") as f:
                json.dump(data, f)
            self._conf_file.chmod(0o600) 
            os.chown(self._conf_file, 0,0)
        except FileNotFoundError:
            raise FileNotFoundError("Error: file missing from config dir")

    def read_master(self) -> dict:
        if os.geteuid() != 0:
            raise PermissionError("Vaultcli must be run with sudo permissions.")
        try:
            with open(self.conf_file, "r") as f:
                data = json.load(f)
            return data 
        except FileNotFoundError:
            raise FileNotFoundError("Error: file missing from config dir")
        
    def clear(self):
        if os.geteuid() != 0:
            raise PermissionError("Vaultcli must be run with sudo permissions.")
        try:
            with open(self.conf_file, "w") as f:
                json.dump({}, f)
        except FileNotFoundError:
            raise FileNotFoundError("Error: file missing from config dir")
        
        
    def is_empty(self) -> bool:
        try:
            with open(self.conf_file, "r") as f:
                return not bool(json.load(f))
        except FileNotFoundError:
            raise FileNotFoundError("Error: file missing from config dir")
        
    def exists(self) -> bool:
        return self._conf_file.exists()
    
