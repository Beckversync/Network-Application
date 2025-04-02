import sys
from PyQt6.QtWidgets import QApplication
from Login import LoginRegisterUI
from Home import DiscordUI

class AppManager:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.login_window = LoginRegisterUI()
        self.login_window.login_button.clicked.connect(self.open_main_app)
        self.login_window.register_button.clicked.connect(self.open_main_app)
        self.login_window.viewer_button.clicked.connect(self.open_main_app_as_viewer)
        self.main_window = None
    
    def open_main_app(self):
        self.main_window = DiscordUI(self.login_window)
        self.main_window.show()
        self.login_window.close()
    
    def open_main_app_as_viewer(self):
        self.main_window = DiscordUI(self.login_window)
        self.main_window.setWindowTitle("Discord Clone - Viewer Mode")
        self.main_window.send_button.setEnabled(False)
        self.main_window.message_input.setEnabled(False)
        self.main_window.add_channel_button.setEnabled(False)
        self.main_window.status_dropdown.setEnabled(False)
        self.main_window.show()
        self.login_window.close()
    
    def run(self):
        self.login_window.resize(600, 400)  # Điều chỉnh kích thước cho phù hợp web
        self.login_window.show()
        sys.exit(self.app.exec())

if __name__ == "__main__":
    app_manager = AppManager()
    app_manager.run()