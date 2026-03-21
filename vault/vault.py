import sys
import os
import platform
import time 
import pyperclip
import curses
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
            mpwd = curses.wrapper(lambda s: self._input(s, "VaultCLI", "Master password:", secret=True))
        if self._authenticate.check_pwd(mpwd):
            self._master_pwd = mpwd
            return
        else:
            curses.wrapper(lambda s: self._show(s, "VaultCLI", "Incorrect password. Try again."))
            attempts += 1
        print("Too many failed attempts.")

    def _set_up(self):

        while True:
            mpwd = curses.wrapper(lambda s: self._input(s, "VaultCLI", "Set master password:", secret=True))
            if not self._validate_password(mpwd):
                print("Password must be 8 characters long and contain a special character and a number.")
                continue 

            attempts = 0
            while attempts < 3:
                reattempt = curses.wrapper(lambda s: self._input(s, "VaultCLI", "Retype master password:", secret=True))
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
        curses.use_default_colors()
        curses.init_pair(1, curses.COLOR_BLUE, -1)
        curses.init_pair(2, curses.COLOR_WHITE, -1)

        BLUE   = curses.color_pair(1)
        NORMAL = curses.color_pair(2)

        selected = 0

        while True:
            stdscr.clear()
            stdscr.bkgd(' ', curses.color_pair(0))

            top        = f"╭{'─' * (width - 2)}╮"
            bottom     = f"╰{'─' * (width - 2)}╯"
            empty      = f"│{' ' * (width - 2)}│"
            divider    = f"├{'─' * (width - 2)}┤"
            title_line = f"│{title.center(width - 2)}│"

            row = 0
            stdscr.addstr(row, 0, top, BLUE);        row += 1
            stdscr.addstr(row, 0, title_line, BLUE); row += 1
            stdscr.addstr(row, 0, divider, BLUE);    row += 1
            stdscr.addstr(row, 0, empty, BLUE);      row += 1

            for i, option in enumerate(options):
                stdscr.addstr(row, 0, "│", BLUE)
                if i == selected:
                    stdscr.addstr(row, 1, f" → {option:<{width - 4}}", BLUE)
                else:
                    stdscr.addstr(row, 1, f"    {option:<{width - 5}}", NORMAL)
                stdscr.addstr(row, width - 1, "│", BLUE)
                row += 1

            stdscr.addstr(row, 0, empty, BLUE);  row += 1
            stdscr.addstr(row, 0, bottom, BLUE)

            stdscr.refresh()
            key = stdscr.getch()

            if key == curses.KEY_UP and selected > 0:
                selected -= 1
            elif key == curses.KEY_DOWN and selected < len(options) - 1:
                selected += 1
            elif key in (curses.KEY_ENTER, 10, 13):
                return selected
            
    def _input(self, stdscr, title, prompt, secret=False):
        curses.curs_set(1)
        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(1, curses.COLOR_BLUE, -1)

        BLUE   = curses.color_pair(1)
        NORMAL = curses.A_NORMAL

        width  = 50
        top        = f"╭{'─' * (width - 2)}╮"
        bottom     = f"╰{'─' * (width - 2)}╯"
        empty      = f"│{' ' * (width - 2)}│"
        divider    = f"├{'─' * (width - 2)}┤"
        title_line = f"│{title.center(width - 2)}│"
        prompt_line = f"│ {prompt:<{width - 3}}│"

        value = ""

        while True:
            stdscr.clear()

            row = 0
            stdscr.addstr(row, 0, top, BLUE);          row += 1
            stdscr.addstr(row, 0, title_line, BLUE);   row += 1
            stdscr.addstr(row, 0, divider, BLUE);      row += 1
            stdscr.addstr(row, 0, empty, BLUE);        row += 1
            stdscr.addstr(row, 0, prompt_line, BLUE);  row += 1

            display = "*" * len(value) if secret else value
            input_line = f"│ {display:<{width - 3}}│"
            stdscr.addstr(row, 0, "│", BLUE)
            stdscr.addstr(row, 1, f" {display:<{width - 3}}", NORMAL)
            stdscr.addstr(row, width - 1, "│", BLUE)
            row += 1

            stdscr.addstr(row, 0, empty, BLUE);        row += 1
            stdscr.addstr(row, 0, bottom, BLUE)

            stdscr.move(5, 2 + len(display))

            key = stdscr.getch()

            if key in (curses.KEY_ENTER, 10, 13):
                curses.curs_set(0)
                return value.strip()
            elif key in (curses.KEY_BACKSPACE, 127, 8):
                value = value[:-1]
            elif 32 <= key <= 126:
                value += chr(key)

    def ui(self):
        os.system("clear")
        try:
            if self._conf.is_empty():
                self._set_up()
            else:
                self._login()
        except Exception as e:
            print(f"Error: {e}")

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
                print(f"Error: {e}")
                sys.exit()

    def _add_service(self):
        service  = curses.wrapper(lambda s: self._input(s, "Add Service", "Service name:"))
        password = curses.wrapper(lambda s: self._input(s, "Add Service", "Password:", secret=False))
        self._encryption.add_pwd(service.lower(), password, self._master_pwd)
        print(f"Successfully saved {service} password.")

    def _remove_service(self):
        if self._encryption.is_empty():
            print("No services saved.")
            return
        content = self._encryption.get_all()
        curses.wrapper(lambda s: self._show(s, "Services", content))
        service = curses.wrapper(lambda s: self._input(s, "Remove Service", "Service name:"))
        r = self._encryption.remove_pwd(service.strip().lower(), self._master_pwd)
        if r:
            print("Successful.")

    def _get_service(self):
        if self._encryption.is_empty():
            print("No services saved.")
            return
        content = self._encryption.get_all()
        curses.wrapper(lambda s: self._show(s, "Services", content))
        service  = curses.wrapper(lambda s: self._input(s, "Get Service", "Service name:"))
        password = self._encryption.get_pwd(service.strip(), self._master_pwd)
        pyperclip.copy(password)
        print("Password copied to clipboard.")

    def _remove_all(self):
        if self._encryption.is_empty():
            print("No services saved.")
            return
        confirm = curses.wrapper(lambda s: self._input(s, "Remove All", "Type YES to confirm:"))
        if confirm != "YES":
            print("Cancelled.")
            return
        self._encryption.clear()
        print("Removed all services.")

    def _show(self, stdscr, title, content):
        curses.curs_set(0)
        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(1, curses.COLOR_BLUE, -1)

        BLUE   = curses.color_pair(1)
        NORMAL = curses.A_NORMAL

        width  = 50
        lines  = content.splitlines()

        top        = f"╭{'─' * (width - 2)}╮"
        bottom     = f"╰{'─' * (width - 2)}╯"
        empty      = f"│{' ' * (width - 2)}│"
        divider    = f"├{'─' * (width - 2)}┤"
        title_line = f"│{title.center(width - 2)}│"

        stdscr.clear()
        row = 0
        stdscr.addstr(row, 0, top, BLUE);        row += 1
        stdscr.addstr(row, 0, title_line, BLUE); row += 1
        stdscr.addstr(row, 0, divider, BLUE);    row += 1
        stdscr.addstr(row, 0, empty, BLUE);      row += 1

        for line in lines:
            stdscr.addstr(row, 0, "│", BLUE)
            stdscr.addstr(row, 1, f" {line:<{width - 3}}", NORMAL)
            stdscr.addstr(row, width - 1, "│", BLUE)
            row += 1

        stdscr.addstr(row, 0, empty, BLUE);  row += 1
        stdscr.addstr(row, 0, bottom, BLUE); row += 1
        stdscr.addstr(row, 0, "  press any key to continue", BLUE)

        stdscr.getch()


    def _validate_password(self, pwd: str) -> bool:
        special_chars = list("!@#$%^&*()[]{}|:;',.<>?/-_+=")
        
        return (len(pwd) >= 8 
                and any(i.isdigit() for i in pwd) 
                and any(i.isalpha() for i in pwd) 
                and any(i in special_chars for i in pwd))

if __name__ == "__main__":
    vault = Vault()
    vault.ui()