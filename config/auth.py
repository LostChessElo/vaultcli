import bcrypt 
from conf import VaultConfig


class Auth:
    def __init__(self):
        self._config = VaultConfig()
                
    def login(self, password: str):
        if self._config.exists() and not self._config.is_empty():
            data = self._config.read_master()
            return bcrypt.checkpw(password.encode(), data["master_pwd"].encode())
        
    def set_up(self, pwd: str):
        salt = bcrypt.gensalt()
        hashed_pwd = bcrypt.hashpw(pwd.encode(), salt)
        self._config.write_to_master({"master_pwd": hashed_pwd.decode(), "salt": salt.decode()})



    
