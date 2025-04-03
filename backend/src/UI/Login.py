import sys
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QLineEdit, QDialog, QMessageBox
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt, pyqtSignal

class RegisterDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Register")
        self.setGeometry(200, 200, 400, 300)
        self.setStyleSheet("background-color: #36393F; color: white;")
        
        layout = QVBoxLayout()
        
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
        
        if not username or not password:
            QMessageBox.warning(self, "Registration Failed", "Username and password cannot be empty!")
        else:
            QMessageBox.information(self, "Registration Successful", "You have successfully registered!")
            self.accept()
    
    def get_credentials(self):
        return self.username_input.text().strip(), self.password_input.text().strip()

class LoginRegisterUI(QWidget):
    login_success = pyqtSignal(str, dict)
    viewer_login_success = pyqtSignal(str, dict)
    
    def __init__(self):
        super().__init__()
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
        dialog = RegisterDialog()
        if dialog.exec():
            username, _ = dialog.get_credentials()
            QMessageBox.information(self, "Registration Successful", f"User '{username}' has been registered successfully!")
    
    def login(self):
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()
        
        if not username or not password:
            QMessageBox.warning(self, "Login Failed", "Username and password cannot be empty!")
            return
        
        print(f"Logged in as: {username}")
        QMessageBox.information(self, "Login Successful", "You have successfully logged in!")
        
        self.username = username
        self.session_info = {"session_id": "dummy-session-id"}
        
        self.login_success.emit(self.username, self.session_info)
    
    def login_as_viewer(self):
        username = self.username_input.text().strip() or "Viewer"
        QMessageBox.information(self, "Viewer Mode", "You are now in viewer mode. You cannot interact with the chat.")
        print("Logged in as Viewer")
        
        self.username = username
        self.session_info = {"session_id": "dummy-session-id"}
        
        self.viewer_login_success.emit(self.username, self.session_info)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    login_register_ui = LoginRegisterUI()
    login_register_ui.show()
    sys.exit(app.exec())
