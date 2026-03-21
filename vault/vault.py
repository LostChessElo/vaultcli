import sys
import os
import platform
import time 
import pyperclip
import curses
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

    def _login(self):
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
    
    def _menu(self, stdscr, title, options, width=40):
        curses.curs_set(0)
        curses.start_color()
        curses.init_pair(1, curses.COLOR_BLUE, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_BLUE)

        BLUE  = curses.color_pair(1)
        SELECTED = curses.color_pair(2)

        selected = 0

        while True:
            stdscr.clear()

            top     = f"╭{'━' * (width - 2)}╮"
            bottom  = f"╰{'━' * (width - 2)}╯"
            empty   = f"│{' ' * (width - 2)}│"
            divider = f"├{'━' * (width - 2)}┤"
            title_line = f"│{title.center(width - 2)}│"

            row = 0
            stdscr.addstr(row, 0, top, BLUE);         row += 1
            stdscr.addstr(row, 0, title_line, BLUE);  row += 1
            stdscr.addstr(row, 0, divider, BLUE);     row += 1
            stdscr.addstr(row, 0, empty, BLUE);       row += 1

            for i, option in enumerate(options):
                label = f"  {option}"
                line  = f"│{label:<{width - 2}}│"
                if i == selected:
                    stdscr.addstr(row, 0, "│", BLUE)
                    stdscr.addstr(row, 1, f"→ {option:<{width - 4}}", SELECTED)
                    stdscr.addstr(row, width - 1, "│", BLUE)
                else:
                    stdscr.addstr(row, 0, line, BLUE)
                row += 1

            stdscr.addstr(row, 0, empty, BLUE);  row += 1
            stdscr.addstr(row, 0, bottom, BLUE)

            key = stdscr.getch()

            if key == curses.KEY_UP and selected > 0:
                selected -= 1
            elif key == curses.KEY_DOWN and selected < len(options) - 1:
                selected += 1
            elif key in (curses.KEY_ENTER, 10, 13):
                return selected

    def ui(self):
        os.system("clear")
        if self._conf.is_empty():
            self._set_up()
        else:
            self._login()

        options = ["Add service", "Get service", "Remove service", "Remove all services", "Log out", "Quit"]

        while True:
            try:
                chosen = curses.wrapper(lambda stdscr: self._menu(stdscr, "VaultCLI", options))

                if chosen == 5:
                    print("Exiting")
                    time.sleep(1)
                    sys.exit()
                elif chosen == 0:
                    os.system("clear")
                    self._add_service()
                    time.sleep(1.5)
                elif chosen == 1:
                    os.system("clear")
                    self._get_service()
                    time.sleep(1.5)
                elif chosen == 2:
                    os.system("clear")
                    self._remove_service()
                    time.sleep(1.5)
                elif chosen == 3:
                    os.system("clear")
                    self._remove_all()
                    time.sleep(1.5)
                elif chosen == 4:
                    self._master_pwd = None
                    os.system("clear")
                    time.sleep(1)
                    self._login()

            except Exception as e:
                return f"Error: {e}"

    def _add_service(self):
        service = input("Service: ").strip().lower()
        password = input("Password: ")
        self._encryption.add_pwd(service, password, self._master_pwd)
        print(f"Successfully saved {service} password.")

    def _get_service(self):
        if self._encryption.is_empty():
            print("No services saved.")
            return
        content = self._encryption.get_all()
        self._display("Services", content)
        service = input("Enter service name: ").strip()
        password = self._encryption.get_pwd(service, self._master_pwd)
        pyperclip.copy(password)
        print("Password copied to clipboard.")

    def _remove_service(self):
        if self._encryption.is_empty():
            print("No services saved.")
            return
        service = input("Emter service to be removed: ").strip()
        r = self._encryption.remove_pwd(service, self._master_pwd)
        if r:
            print("Successful.")

    def _remove_all(self):
        if self._encryption.is_empty():
            print("No services saved.")
            return
        self._encryption.clear()
        print("Removed all services.")

    def _display(self, title, content, width=50):
        BLUE  = "\033[34m"
        RESET = "\033[0m"
        top        = f"╭{'─' * (width - 2)}╮"
        bottom     = f"╰{'─' * (width - 2)}╯"
        empty      = f"│{' ' * (width - 2)}│"
        title_line = f"│{title.center(width - 2)}│"
        divider    = f"├{'─' * (width - 2)}┤"

        lines = content.splitlines()
        content_lines = []
        for line in lines:
            padded = f"│ {line:<{width - 3}}│"
            content_lines.append(padded)

        print(BLUE + top)
        print(title_line)
        print(divider)
        for line in content_lines:
            print(line)
        print(empty)
        print(bottom + RESET)


    def _validate_password(self, pwd: str) -> bool:
        special_chars = list("!@#$%^&*()[]{}|:;',.<>?/-_+=")
        
        return (len(pwd) >= 8 
                and any(i.isdigit() for i in pwd) 
                and any(i.isalpha() for i in pwd) 
                and any(i in special_chars for i in pwd))

v = Vault()
v.ui()