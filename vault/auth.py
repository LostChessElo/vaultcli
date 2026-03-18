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

    def _validate_password(self, pwd: str) -> bool:
        special_chars = list("!@#$%^&*()[]{}|:;',.<>?/-_+=")
        
        return (len(pwd) >= 8 
                and any(i.isdigit() for i in pwd) 
                and any(i.isalpha() for i in pwd) 
                and any(i in special_chars for i in pwd))
    
    def is_configured(self):
        return self._config.exists() and not self._config.is_empty()
    
a = Auth()
c = VaultConfig()
print(c.clear())
print(c.read_master())
