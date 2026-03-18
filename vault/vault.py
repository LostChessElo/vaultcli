import sys
import os
import platform
import argparse
from auth import Auth
from encryption import Encryption 


class Vault:
    def __init__(self):
        self._authenticate = Auth()
        self._encryption = Encryption()
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
                reatempt = input("Retype master password: ")
                if mpwd != reatempt:
                    attempts += 1
                    print("Passwords dont match.")
                else:
                    self._master_pwd = mpwd
                    self._authenticate.set_up(mpwd)
                    return 
                print("Too many failed attempts.")
                break
    
    def menu(self):
        os.system("clear")
        while True:
            try:
                ui = int(input(f"vaultcli@{self.osname}:~$ "))
            except Exception as e:
                continue

    def _args(self):
        pass


    def _validate_password(self, pwd: str) -> bool:
        special_chars = list("!@#$%^&*()[]{}|:;',.<>?/-_+=")
        
        return (len(pwd) >= 8 
                and any(i.isdigit() for i in pwd) 
                and any(i.isalpha() for i in pwd) 
                and any(i in special_chars for i in pwd))

v = Vault()
v.menu()