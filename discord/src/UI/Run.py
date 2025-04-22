import sys
import os
import logging
import threading

# Cấu hình logging tập trung: ghi log vào file system.log (ASCII text file) và console
logger = logging.getLogger()
logger.setLevel(logging.INFO)
formatter = logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s')

# Handler ghi log vào file (mode append)
file_handler = logging.FileHandler('system.log', mode='a', encoding='utf-8')
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# Handler ghi log ra console (có thể bỏ nếu chỉ muốn ghi file)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(BASE_DIR)

from PyQt6.QtWidgets import QApplication
from UI.Login import LoginRegisterUI
from UI.Home import DiscordUI

from tracker import TRACKER_SERVER  # Tracker server, chạy riêng (python tracker.py)
from user import USER

class AppManager:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.login_window = LoginRegisterUI()
        self.login_window.login_success.connect(self.open_main_app)
        self.login_window.viewer_login_success.connect(self.open_main_app_as_viewer)
        self.main_window = None
        self.user_peer = None

    def open_main_app(self, username, session_info):
        logging.info("User '%s' logging in (authenticated mode).", username)
        # Khởi tạo USER ở chế độ headless để thực hiện các thao tác P2P.
        self.user_peer = USER("172.20.10.2", 5000, headless=True, username=username)
        self.main_window = DiscordUI(self.login_window, username, session_info, self.user_peer)
        self.main_window.show()
        self.login_window.close()
    
    def open_main_app_as_viewer(self, username, session_info):
        logging.info("User '%s' logging in (visitor mode).", username)
        self.user_peer = USER("172.20.10.2", 5000, headless=True, username=username)
        self.main_window = DiscordUI(self.login_window, username, session_info, self.user_peer)
        self.main_window.setWindowTitle("Discord Clone - Viewer Mode")
        self.main_window.send_button.setEnabled(False)
        self.main_window.message_input.setEnabled(False)
        self.main_window.add_channel_button.setEnabled(False)
        self.main_window.status_dropdown.setEnabled(False)
        self.main_window.is_viewer = True
        self.main_window.show()
        self.login_window.close()
    
    def run(self):
        self.login_window.resize(600, 400)
        self.login_window.show()
        sys.exit(self.app.exec())

if __name__ == "__main__":
    # server_thread = threading.Thread(target=server_program, args=("192.168.110.96", 22236), daemon=True)
    # server_thread.start()
    app_manager = AppManager()
    app_manager.run()
