import sys
from PyQt6.QtWidgets import QApplication
from Login import LoginRegisterUI
from Home import DiscordUI

class MainApp:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.login_window = LoginRegisterUI()
        self.login_window.login_button.clicked.connect(self.start_discord_ui)
        self.login_window.viewer_button.clicked.connect(self.start_discord_ui_viewer)
        self.login_window.show()
    
    def start_discord_ui(self):
        username = self.login_window.username_input.text().strip()
        password = self.login_window.password_input.text().strip()
        
        if username and password:
            self.discord_ui = DiscordUI(self.login_window)
            self.discord_ui.username_label.setText(f"User: {username}")
            self.login_window.hide()
            self.discord_ui.show()
    
    def start_discord_ui_viewer(self):
        self.discord_ui = DiscordUI()
        self.discord_ui.username_label.setText("User: Viewer (Read-Only)")
        self.login_window.hide()
        self.discord_ui.show()
    
    def run(self):
        sys.exit(self.app.exec())

if __name__ == "__main__":
    app_instance = MainApp()
    app_instance.run()