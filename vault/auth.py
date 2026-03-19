import bcrypt 
from conf import VaultConfig


class Auth:
    def __init__(self):
        self._config = VaultConfig()
        
    def check_pwd(self, password: str) -> bool:
        if not self.is_configured():
            raise RuntimeError("Error: config missing in ~/.config/vconf")
        
        data = self._config.read_master() # -> dict
        return bcrypt.checkpw(password.encode(), data["master_pwd"].encode())
        
    def set_up(self, pwd: str):
        salt = bcrypt.gensalt()
        hashed_pwd = bcrypt.hashpw(pwd.encode(), salt)
        self._config.write_to_master({"master_pwd": hashed_pwd.decode(), "salt": salt.decode()})

    def is_configured(self):
        return self._config.exists() and not self._config.is_empty()
    
