from conf import VaultConfig
from auth import Auth
from encryption import Encryption 


class Vault:
    def __init__(self):
        self._authenticate = Auth()
        self._encryption = Encryption()
        self._conf = VaultConfig()
        self._master_pwd = None

    @property
    def master_pwd(self):
        return self._master_pwd

    def login(self):
        attempts = 0
        while attempts < 3:
            mpwd = input("Enter master password: ")
            if self._authenticate.check_pwd(mpwd):
                self._master_pwd = mpwd
                return
            else:
                print("Incorrect password, try again.")
                attempts += 1
        print("Too many failed attempts.")

    def _set_up(self):
        while True:
            mpwd = input("Set a master password: ")
            if not self._validate_password(mpwd):
                print("Password must be 8 characters long and contain a special character and a number.")
                continue 

            attempts = 0
            while attempts < 3:
                reattempt = input("Retype master password: ")
                if mpwd != reattempt:
                    attempts += 1
                    print("Passwords dont match.")
                else:
                    self._master_pwd = mpwd
                    self._authenticate.set_up(mpwd)
                    return 
                
            print("Too many failed attempts.")
            break
            

    def ui(self):
        if self._conf.is_empty():
            self._set_up()
        else:
            self.login()
        print("1. Add service")
        print("2. View service")
        print("3. Remove service")
        print("4. Quit")
        while True:
            pass

    def _validate_password(self, pwd: str) -> bool:
        special_chars = list("!@#$%^&*()[]{}|:;',.<>?/-_+=")
        
        return (len(pwd) >= 8 
                and any(i.isdigit() for i in pwd) 
                and any(i.isalpha() for i in pwd) 
                and any(i in special_chars for i in pwd))


