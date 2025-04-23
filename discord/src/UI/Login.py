import sys
import logging
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QLineEdit, QDialog, QMessageBox
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt, pyqtSignal
from request import authRequest
import json
import socket
import os
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s')
from user import USER
from config.db import channels_collection, users_collection
from request import channelRequest
class RegisterDialog(QDialog):
    def __init__(self, client_socket): 
        super().__init__()
        self.client_socket = client_socket

        self.setWindowTitle("Register")
        self.setGeometry(200, 200, 400, 300)
        self.setStyleSheet("background-color: #36393F; color: white;")

        layout = QVBoxLayout()

        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Enter email")
        self.email_input.setStyleSheet("background-color: #40444B; color: white; padding: 8px; border-radius: 5px;")
        layout.addWidget(self.email_input)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Enter username")
        self.username_input.setStyleSheet("background-color: #40444B; color: white; padding: 8px; border-radius: 5px;")
        layout.addWidget(self.username_input)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Enter password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setStyleSheet("background-color: #40444B; color: white; padding: 8px; border-radius: 5px;")
        layout.addWidget(self.password_input)

        self.confirm_button = QPushButton("Register")
        self.confirm_button.setStyleSheet("background-color: #5865F2; color: white; padding: 10px; border-radius: 5px;")
        self.confirm_button.clicked.connect(self.validate_registration)
        layout.addWidget(self.confirm_button)

        self.setLayout(layout)
    
    def validate_registration(self):
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()
        email = self.email_input.text().strip()

        if not username or not password or not email:
            QMessageBox.warning(self, "Registration Failed", "Username, password, and email cannot be empty!")
            return

        if not email.endswith("@hcmut.edu.vn"):
            QMessageBox.warning(self, "Invalid Email", "Email must end with @hcmut.edu.vn")
            return

        request_data = {
            "action": "register",
            "username": username,
            "password": password,
            "email": email
        }

        try:
            # Gửi request đăng ký tới server
            self.client_socket.sendall(json.dumps(request_data).encode())
            response = self.client_socket.recv(4096).decode()
            response_data = json.loads(response)

            if response_data["status"] == "success":
                logging.info("Registration successful for user: %s", username)
                QMessageBox.information(self, "Registration Successful", f"User '{username}' has been registered successfully!")
                self.accept()
            else:
                QMessageBox.warning(self, "Registration Failed", response_data.get("message", "Unknown error"))
        except Exception as e:
            logging.error("Registration error: %s", str(e))
            QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")
    
    def get_credentials(self):
        return self.username_input.text().strip(), self.password_input.text().strip()

class ViewerLoginDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Viewer Login")
        self.setStyleSheet("background-color: #2C2F33; color: white;")
        self.setFixedSize(300, 150)

        layout = QVBoxLayout()
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Enter viewer username")
        self.username_input.setStyleSheet("background-color: #40444B; color: white; padding: 8px; border-radius: 5px;")
        layout.addWidget(self.username_input)

        self.login_button = QPushButton("Continue")
        self.login_button.setStyleSheet("background-color: #7289DA; color: white; padding: 8px; border-radius: 5px;")
        self.login_button.clicked.connect(self.accept)
        layout.addWidget(self.login_button)

        self.setLayout(layout)

    def get_username(self):
        return self.username_input.text().strip()
    
class LoginRegisterUI(QWidget):
    login_success = pyqtSignal(str, dict)
    viewer_login_success = pyqtSignal(str, dict)
    
    def __init__(self):
        super().__init__()
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_ip = '172.20.10.2'
        server_port = 5000
        try:
            self.client_socket.connect((server_ip, server_port))
            print("Connected to server from LoginRegisterUI")
        except Exception as e:
            print(f"Failed to connect: {e}")
        self.setWindowTitle("Login / Register")
        self.setGeometry(100, 100, 800, 500)
        self.setStyleSheet("background-color: #2C2F33; color: white;")
        
        self.username = None
        self.session_info = None
        
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.label = QLabel("Welcome to Discord Clone")
        self.label.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.label)
        
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Enter username")
        self.username_input.setStyleSheet("background-color: #40444B; color: white; padding: 8px; border-radius: 5px;")
        layout.addWidget(self.username_input)
        
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Enter password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setStyleSheet("background-color: #40444B; color: white; padding: 8px; border-radius: 5px;")
        layout.addWidget(self.password_input)
        
        self.login_button = QPushButton("Login")
        self.login_button.setStyleSheet("background-color: #7289DA; color: white; padding: 12px; border-radius: 8px;")
        self.login_button.clicked.connect(self.login)
        layout.addWidget(self.login_button)
        
        self.register_button = QPushButton("Register")
        self.register_button.setStyleSheet("background-color: #7289DA; color: white; padding: 12px; border-radius: 8px;")
        self.register_button.clicked.connect(self.open_register_dialog)
        layout.addWidget(self.register_button)
        
        self.viewer_button = QPushButton("Login as Viewer")
        self.viewer_button.setStyleSheet("background-color: #99AAB5; color: white; padding: 12px; border-radius: 8px;")
        self.viewer_button.clicked.connect(self.login_as_viewer)
        layout.addWidget(self.viewer_button)
        
        self.setLayout(layout)
    
    def open_register_dialog(self):
        dialog = RegisterDialog(self.client_socket)
        if dialog.exec():
            username, _ = dialog.get_credentials()
            QMessageBox.information(self, "Registration Successful", f"User '{username}' has been registered successfully!")
    
    def login(self):
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()

        if not username or not password:
            QMessageBox.warning(self, "Login Failed", "Username and password cannot be empty!")
            return

        try:
            request_data = {
                "action": "login",
                "username": username,
                "password": password
            }

            self.client_socket.send(json.dumps(request_data).encode())
            response_str = self.client_socket.recv(4096).decode()

            try:
                response = json.loads(response_str)
            except json.JSONDecodeError:
                QMessageBox.critical(self, "Error", "Invalid response from server (not JSON)")
                return

            if not isinstance(response, dict):
                QMessageBox.critical(self, "Error", "Unexpected response format from server")
                return

            if response.get("status") != "success":
                QMessageBox.warning(self, "Login Failed", response.get("message", "Unknown error"))
                return

            logging.info("Logged in as: %s", username)
            QMessageBox.information(self, "Login Successful", "You have successfully logged in!")

            self.username = username
            user_data = response.get("user", {})
            sessions = user_data.get("sessions", [])

            if sessions:
                last_session = sessions[-1]
                self.session_info = {"session_id": last_session["session_id"]}
            else:
                self.session_info = {"session_id": "dummy-session-id"}

            # === Phần này cần danh sách các kênh (tự truyền vào nếu không dùng get_hosted_channels) ===
            try:
                request_data = {"action": "get_all_channels"}
                response_str = channelRequest.handle_channel_request(json.dumps(request_data))
                response = json.loads(response_str)
                print(response)
                if response.get("status") == "success":
                    channels = response.get("data", [])

                    channel_list = [ch["channel_name"] for ch in channels]
                    print(channel_list)  # Debug: in ra danh sách tên kênh

                    for channel_name in channel_list:
                        request_messages = {
                            "action": "get_channel_info",
                            "channel_name": channel_name,
                            "username": self.username
                        }
                        response_msg_str = channelRequest.handle_channel_request(json.dumps(request_messages))
                        msg_data = json.loads(response_msg_str)

                        if msg_data.get("status") == "success":
                            members = msg_data.get("members", [])
                            if self.username not in members:
                                logging.info("[SYNC LOGIN] User %s is not a member of channel %s. Skipping sync.", self.username, channel_name)
                                continue

                            messages = msg_data.get("messages", [])
                            sync_filename = f"sync_{channel_name}_{self.username}.txt"
                            sync_path = os.path.join("local_sync", sync_filename)

                            existing_lines = set()
                            if os.path.exists(sync_path):
                                with open(sync_path, "r", encoding="utf-8") as f:
                                    existing_lines = set(line.strip() for line in f if line.strip())

                            with open(sync_path, "a", encoding="utf-8") as f:
                                new_lines_count = 0
                                for msg in messages:
                                    if isinstance(msg, dict):
                                        line = msg.get("text", "").strip()
                                    elif isinstance(msg, str):
                                        line = msg.strip()
                                    else:
                                        logging.warning("[SYNC LOGIN] Unexpected message format: %s", msg)
                                        continue

                                    if line and line not in existing_lines:
                                        f.write(line + "\n")
                                        new_lines_count += 1

                            logging.info("[SYNC LOGIN] Saved %d new messages for %s", new_lines_count, channel_name)
                        else:
                            logging.warning("[SYNC LOGIN] Failed to get messages for channel: %s", channel_name)

                else:
                    logging.warning("[SYNC LOGIN] Failed to fetch all channels: %s", response.get("message"))

            except Exception as sync_e:
                logging.error("Error during login-time sync: %s", sync_e)

            self.login_success.emit(self.username, self.session_info)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")

    
    def login_as_viewer(self):
        dialog = ViewerLoginDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            name = dialog.get_username()
            if not name:
                QMessageBox.warning(self, "Input Error", "Username cannot be empty.")
                return

            request_data = {
                "action": "visitor",
                "name": name
            }

            try:
                self.client_socket.send(json.dumps(request_data).encode())
                response_str = self.client_socket.recv(4096).decode()
                response = json.loads(response_str)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Connection or parsing error: {e}")
                return

            if not isinstance(response, dict):
                QMessageBox.critical(self, "Error", "Unexpected response format from server")
                return

            if response.get("status") != "success":
                QMessageBox.warning(self, "Login Failed", response.get("message", "Unknown error"))
                return

            QMessageBox.information(self, "Viewer Mode", "You are now in viewer mode. You cannot interact with the chat.")
            logging.info("Logged in as Viewer: %s", name)
            self.username = name
            self.session_info = {"session_id": "dummy-session-id"}
            self.viewer_login_success.emit(self.username, self.session_info)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    login_register_ui = LoginRegisterUI()
    login_register_ui.show()
    sys.exit(app.exec())
