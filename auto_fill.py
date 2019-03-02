import ctypes
import getpass
import time

from beanfun import BeanfunClient

class AutoFiller:
    TAB = 9
    ENTER = 13
    CAPITAL = 20

    F1 = 112
    F2 = 113
    F3 = 114
    F4 = 115
    F5 = 116

    def __init__(self, username, password):
        self.beanfunClient = BeanfunClient()
        self.beanfunClient.login(username, password)
        self.accounts = self.beanfunClient.get_accounts()
        self.beanfunClient.show_accounts()
        self.next_account = None
    
    def wait_for_input(self):
        user32 = ctypes.windll.user32
        while True:
            if user32.GetAsyncKeyState(AutoFiller.F1) and 0 < len(self.accounts):
                self.next_account = self.accounts[0]
            if user32.GetAsyncKeyState(AutoFiller.F2) and 1 < len(self.accounts):
                self.next_account = self.accounts[1]
            if user32.GetAsyncKeyState(AutoFiller.F3) and 2 < len(self.accounts):
                self.next_account = self.accounts[2]
            if user32.GetAsyncKeyState(AutoFiller.F4) and 3 < len(self.accounts):
                self.next_account = self.accounts[3]
            if user32.GetAsyncKeyState(AutoFiller.F5) and 4 < len(self.accounts):
                self.next_account = self.accounts[4]

            if self.next_account:
                otp = self.beanfunClient.get_account_otp(self.next_account)
                self.login(self.next_account.acc, otp)

            time.sleep(1)
            
    def login(self, account, password):
        user32 = ctypes.windll.user32
        for key in account:
            if key.isupper() and not user32.GetKeyState(AutoFiller.CAPITAL):
                user32.keybd_event(AutoFiller.CAPITAL, 0, 1, 0)
                user32.keybd_event(AutoFiller.CAPITAL, 0, 2, 0)
            if key.islower() and user32.GetKeyState(AutoFiller.CAPITAL):
                user32.keybd_event(AutoFiller.CAPITAL, 0, 1, 0)
                user32.keybd_event(AutoFiller.CAPITAL, 0, 2, 0)
            if key.islower():
                key = key.upper()
            user32.keybd_event(ord(key), 0, 0, 0)
        user32.keybd_event(AutoFiller.TAB, 0, 0, 0)

        for key in password:
            user32.keybd_event(ord(key), 0, 0, 0)
        time.sleep(0.2)
        user32.keybd_event(AutoFiller.ENTER, 0, 0, 0)

        self.next_account = None

def main():
    username = input("Username: ")
    password = getpass.getpass("Password: ")
    auto_filler = AutoFiller(username, password)
    auto_filler.wait_for_input()

if __name__ == '__main__':
    main()