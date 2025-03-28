

# from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton, QListWidget, QTextEdit, QHBoxLayout, QLabel, QLineEdit, QDialog, QScrollArea, QFrame, QComboBox
# from PyQt6.QtGui import QIcon, QColor
# from PyQt6.QtCore import Qt
# import sys

# class AddChannelDialog(QDialog):
#     def __init__(self):
#         super().__init__()
#         self.setWindowTitle("Add Channel")
#         self.setGeometry(200, 200, 300, 150)
        
#         layout = QVBoxLayout()
#         self.channel_name_input = QLineEdit()
#         self.channel_name_input.setPlaceholderText("Enter channel name")
#         layout.addWidget(self.channel_name_input)
        
#         self.create_button = QPushButton("Create")
#         self.create_button.clicked.connect(self.accept)
#         layout.addWidget(self.create_button)
        
#         self.setLayout(layout)
    
#     def get_channel_name(self):
#         return self.channel_name_input.text().strip()

# class DiscordUI(QMainWindow):
#     def __init__(self):
#         super().__init__()
#         self.setWindowTitle("Discord Clone - PyQt6")
#         self.setGeometry(100, 100, 1200, 700)
        
#         self.channels = {"General": [], "Gaming": [], "Music": []}  # Chat history per channel
#         self.current_channel = "General"
        
#         self.initUI()

#     def initUI(self):
#         central_widget = QWidget()
#         self.setCentralWidget(central_widget)
        
#         main_layout = QHBoxLayout()
#         central_widget.setLayout(main_layout)
        
#         # Sidebar (Channel List)
#         sidebar_layout = QVBoxLayout()
        
#         discord_label = QLabel("DISCORD V1.0")
#         discord_label.setStyleSheet("color: white; font-size: 18px; font-weight: bold;")
#         sidebar_layout.addWidget(discord_label, 1, Qt.AlignmentFlag.AlignHCenter)
        
#         self.add_channel_button = QPushButton("+ Create Channel")
#         self.add_channel_button.setStyleSheet("background-color: #5865F2; color: white;")
#         self.add_channel_button.clicked.connect(self.add_channel)
#         sidebar_layout.addWidget(self.add_channel_button, 1)
        
#         self.channel_scroll = QScrollArea()
#         self.channel_scroll.setWidgetResizable(True)
#         self.channel_container = QWidget()
#         self.channel_list_layout = QVBoxLayout(self.channel_container)
        
#         self.channel_list = QListWidget()
#         self.channel_list.setStyleSheet("background-color: #2F3136; color: white;")
#         self.channel_list.addItems(self.channels.keys())
#         self.channel_list.itemClicked.connect(self.switch_channel)
#         self.channel_list_layout.addWidget(self.channel_list)
        
#         self.channel_scroll.setWidget(self.channel_container)
#         sidebar_layout.addWidget(self.channel_scroll, 6)
        
#         # User Info at Bottom Left
#         user_info_frame = QFrame()
#         user_info_layout = QVBoxLayout(user_info_frame)
        
#         self.username_label = QLabel("User: JohnDoe")
#         self.username_label.setStyleSheet("color: white;")
#         self.user_status_label = QLabel("Status: Online")
#         self.user_status_label.setStyleSheet("color: green;")
        
#         self.status_dropdown = QComboBox()
#         self.status_dropdown.addItems(["Online", "Away", "Do Not Disturb", "Offline"])
#         self.status_dropdown.currentTextChanged.connect(self.change_status)
        
#         user_info_layout.addWidget(self.username_label)
#         user_info_layout.addWidget(self.user_status_label)
#         user_info_layout.addWidget(self.status_dropdown)
        
#         sidebar_layout.addWidget(user_info_frame, 2)
        
#         main_layout.addLayout(sidebar_layout, 2)
        
#         # Member List on the right
#         member_list_layout = QVBoxLayout()
#         member_label = QLabel("Members in Channel")
#         member_label.setStyleSheet("color: white; font-weight: bold;")
#         member_list_layout.addWidget(member_label)
        
#         self.member_list = QListWidget()
#         self.member_list.setStyleSheet("background-color: #2F3136; color: white;")
#         member_list_layout.addWidget(self.member_list, 6)
        
#         main_layout.addLayout(member_list_layout, 2)
        
#         # Chat Layout
#         chat_layout = QVBoxLayout()
        
#         self.channel_label = QLabel(f"# {self.current_channel}")
#         self.channel_label.setStyleSheet("color: white; font-size: 20px; font-weight: bold;")
#         chat_layout.addWidget(self.channel_label)
        
#         self.chat_display = QTextEdit()
#         self.chat_display.setReadOnly(True)
#         self.chat_display.setStyleSheet("background-color: #36393F; color: white;")
#         chat_layout.addWidget(self.chat_display, 8)
        
#         message_input_layout = QHBoxLayout()
#         self.message_input = QLineEdit()
#         self.message_input.setStyleSheet("background-color: #40444B; color: white;")
#         self.send_button = QPushButton("Send")
#         self.send_button.setStyleSheet("background-color: #5865F2; color: white;")
#         self.send_button.clicked.connect(self.send_message)
#         message_input_layout.addWidget(self.message_input, 4)
#         message_input_layout.addWidget(self.send_button, 1)
#         chat_layout.addLayout(message_input_layout, 1)
        
#         main_layout.addLayout(chat_layout, 6)
        
#         self.load_chat()
    
#     def send_message(self):
#         message = self.message_input.text().strip()
#         if message:
#             self.channels[self.current_channel].append(f"You: {message}")
#             self.chat_display.append(f"You: {message}")
#             self.message_input.clear()
    
#     def switch_channel(self, item):
#         self.current_channel = item.text()
#         self.channel_label.setText(f"# {self.current_channel}")
#         self.load_chat()
    
#     def load_chat(self):
#         self.chat_display.clear()
#         for msg in self.channels[self.current_channel]:
#             self.chat_display.append(msg)
    
#     def add_channel(self):
#         dialog = AddChannelDialog()
#         if dialog.exec():
#             new_channel = dialog.get_channel_name()
#             if new_channel and new_channel not in self.channels:
#                 self.channels[new_channel] = []
#                 self.channel_list.addItem(new_channel)
    
#     def change_status(self, status):
#         self.user_status_label.setText(f"Status: {status}")
#         color = "green" if status == "Online" else "yellow" if status == "Away" else "red" if status == "Do Not Disturb" else "gray"
#         self.user_status_label.setStyleSheet(f"color: {color};")
    

# if __name__ == "__main__":
#     app = QApplication(sys.argv)
#     login_window = DiscordUI()
#     login_window.show()
#     sys.exit(app.exec())


from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton, QListWidget, QTextEdit, QHBoxLayout, QLabel, QLineEdit, QDialog, QScrollArea, QFrame, QComboBox
from PyQt6.QtGui import QIcon, QColor
from PyQt6.QtCore import Qt
import sys

class AddChannelDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Add Channel")
        self.setGeometry(200, 200, 300, 150)
        
        layout = QVBoxLayout()
        self.channel_name_input = QLineEdit()
        self.channel_name_input.setPlaceholderText("Enter channel name")
        layout.addWidget(self.channel_name_input)
        
        self.create_button = QPushButton("Create")
        self.create_button.clicked.connect(self.accept)
        layout.addWidget(self.create_button)
        
        self.setLayout(layout)
    
    def get_channel_name(self):
        return self.channel_name_input.text().strip()

class DiscordUI(QMainWindow):
    def __init__(self, login_window):
        super().__init__()
        self.login_window = login_window
        self.setWindowTitle("Discord Clone - PyQt6")
        self.setGeometry(100, 100, 1200, 700)
        
        self.channels = {"General": [], "Gaming": [], "Music": []}  # Chat history per channel
        self.current_channel = "General"
        
        self.initUI()

    def initUI(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout()
        central_widget.setLayout(main_layout)
        
        # Sidebar (Channel List)
        sidebar_layout = QVBoxLayout()
        
        discord_label = QLabel("DISCORD V1.0")
        discord_label.setStyleSheet("color: white; font-size: 18px; font-weight: bold;")
        sidebar_layout.addWidget(discord_label, 1, Qt.AlignmentFlag.AlignHCenter)
        
        self.add_channel_button = QPushButton("+ Create Channel")
        self.add_channel_button.setStyleSheet("background-color: #5865F2; color: white;")
        self.add_channel_button.clicked.connect(self.add_channel)
        sidebar_layout.addWidget(self.add_channel_button, 1)
        
        self.channel_scroll = QScrollArea()
        self.channel_scroll.setWidgetResizable(True)
        self.channel_container = QWidget()
        self.channel_list_layout = QVBoxLayout(self.channel_container)
        
        self.channel_list = QListWidget()
        self.channel_list.setStyleSheet("background-color: #2F3136; color: white;")
        self.channel_list.addItems(self.channels.keys())
        self.channel_list.itemClicked.connect(self.switch_channel)
        self.channel_list_layout.addWidget(self.channel_list)
        
        self.channel_scroll.setWidget(self.channel_container)
        sidebar_layout.addWidget(self.channel_scroll, 6)
        
        # User Info at Bottom Left
        user_info_frame = QFrame()
        user_info_layout = QVBoxLayout(user_info_frame)
        
        self.username_label = QLabel("User: JohnDoe")
        self.username_label.setStyleSheet("color: white;")
        self.user_status_label = QLabel("Status: Online")
        self.user_status_label.setStyleSheet("color: green;")
        
        self.status_dropdown = QComboBox()
        self.status_dropdown.addItems(["Online", "Away", "Do Not Disturb", "Offline"])
        self.status_dropdown.currentTextChanged.connect(self.change_status)
        
        user_info_layout.addWidget(self.username_label)
        user_info_layout.addWidget(self.user_status_label)
        user_info_layout.addWidget(self.status_dropdown)
        
        sidebar_layout.addWidget(user_info_frame, 2)
        
        main_layout.addLayout(sidebar_layout, 2)
        
        # Member List on the right
        member_list_layout = QVBoxLayout()
        member_label = QLabel("Members in Channel")
        member_label.setStyleSheet("color: white; font-weight: bold;")
        member_list_layout.addWidget(member_label)
        
        self.member_list = QListWidget()
        self.member_list.setStyleSheet("background-color: #2F3136; color: white;")
        member_list_layout.addWidget(self.member_list, 6)
        
        main_layout.addLayout(member_list_layout, 2)
        
        # Chat Layout
        chat_layout = QVBoxLayout()
        
        self.channel_label = QLabel(f"# {self.current_channel}")
        self.channel_label.setStyleSheet("color: white; font-size: 20px; font-weight: bold;")
        chat_layout.addWidget(self.channel_label)
        
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setStyleSheet("background-color: #36393F; color: white;")
        chat_layout.addWidget(self.chat_display, 8)
        
        message_input_layout = QHBoxLayout()
        self.message_input = QLineEdit()
        self.message_input.setStyleSheet("background-color: #40444B; color: white;")
        self.send_button = QPushButton("Send")
        self.send_button.setStyleSheet("background-color: #5865F2; color: white;")
        self.send_button.clicked.connect(self.send_message)
        message_input_layout.addWidget(self.message_input, 4)
        message_input_layout.addWidget(self.send_button, 1)
        chat_layout.addLayout(message_input_layout, 1)
        
        # Logout Button
        self.logout_button = QPushButton("Logout")
        self.logout_button.setStyleSheet("background-color: red; color: white;")
        self.logout_button.clicked.connect(self.logout)
        chat_layout.addWidget(self.logout_button, 1, Qt.AlignmentFlag.AlignRight)
        
        main_layout.addLayout(chat_layout, 6)
        
        self.load_chat()
    
    def send_message(self):
        message = self.message_input.text().strip()
        if message:
            self.channels[self.current_channel].append(f"You: {message}")
            self.chat_display.append(f"You: {message}")
            self.message_input.clear()
    
    def switch_channel(self, item):
        self.current_channel = item.text()
        self.channel_label.setText(f"# {self.current_channel}")
        self.load_chat()
    
    def load_chat(self):
        self.chat_display.clear()
        for msg in self.channels[self.current_channel]:
            self.chat_display.append(msg)
    
    def add_channel(self):
        dialog = AddChannelDialog()
        if dialog.exec():
            new_channel = dialog.get_channel_name()
            if new_channel and new_channel not in self.channels:
                self.channels[new_channel] = []
                self.channel_list.addItem(new_channel)
    
    def change_status(self, status):
        self.user_status_label.setText(f"Status: {status}")
        color = "green" if status == "Online" else "yellow" if status == "Away" else "red" if status == "Do Not Disturb" else "gray"
        self.user_status_label.setStyleSheet(f"color: {color};")
    
    def logout(self):
        self.close()
        self.login_window.show()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    login_window = QWidget()
    discord_ui = DiscordUI(login_window)
    discord_ui.show()
    sys.exit(app.exec())
