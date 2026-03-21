import sys
import os
import platform
from simple_term_menu import TerminalMenu
from auth import Auth
from encryption import Encryption 
from conf import VaultConfig


class Vault:
    def __init__(self):
        self._authenticate = Auth()
        self._encryption = Encryption()
        self._conf = VaultConfig()
        self._master_pwd = None
        self.osname = platform.freedesktop_os_release()["NAME"]

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
        while True:
            print("1. Add service")
            print("2. View service")
            print("3. Remove service")
            print("4. Quit")
            try:
                ui = int(input("Please select an option (1-4): "))
                if ui == 1:
                    service = input("Please enter service name: ").strip()
                    password = input("Enter service password: ").strip()
                    self._encryption.add_pwd(service, password, self._master_pwd)
                elif ui == 2:
                    print("=" * 6)
                    print(self._encryption.get_all())
                    print("=" * 6)
                    service = input("Enter service name: ").strip()
                    password = self._encryption.get_pwd(service, self._master_pwd)
                    print(password)
                elif ui == 3:
                    service = input("Emter service to be removed: ").strip()
                    r = self._encryption.remove_pwd(service, self._master_pwd)
                    if r:
                        print(("Successful."))
                elif ui == 4:
                    sys.exit()
            except Exception as e:
                print(f"Error occured: {e}")
                continue

    def _add_service(self):
        pass

    def _view_service(self):
        pass

    def _remove_service(self):
        pass


    def _validate_password(self, pwd: str) -> bool:
        special_chars = list("!@#$%^&*()[]{}|:;',.<>?/-_+=")
        
        return (len(pwd) >= 8 
                and any(i.isdigit() for i in pwd) 
                and any(i.isalpha() for i in pwd) 
                and any(i in special_chars for i in pwd))

