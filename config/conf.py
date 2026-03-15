import json 
import os
from pathlib import Path 

class VaultConfig:
    def __init__(self):
        self._base_dir = Path.home() / ".config" / "vconf"
        self._conf_file = self._base_dir / "master.json"
        self._base_dir.mkdir(parents=True, exist_ok=True)

    def conf_dir(self):
        return self._base_dir
    
    def conf_file(self):
        return self._conf_file
    
    def write_to_master(self, data: dict) -> None:
        try:
            with open(self.conf_file(), "w") as f:
                json.dump(data, f)
        except FileNotFoundError:
            return "Main config file missing from ~/.config/vconf"
        except TypeError:
            return "Data must be a valid dictionary"

    def read_master(self) -> dict:
        try:
            with open(self.conf_file(), "r") as f:
                data = json.load(f)
            return data 
        except FileNotFoundError:
            return "Main config file missing from ~/.config/vconf"
        except json.JSONDecodeError:
            return "Error: could not decode json file"
        
    def is_empty(self) -> bool:
        try:
            with open(self.conf_file(), "r") as f:
                data = json.load(f)
            return True if not data else False
        except FileNotFoundError:
            return "Error: main config missing from ~/.config/vconf"
        
    def exists(self) -> bool:
        return self._conf_file.exists()