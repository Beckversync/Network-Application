import json
import sys, os, threading, time
import logging
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget,
    QVBoxLayout, QHBoxLayout, QPushButton,
    QListWidget, QListWidgetItem, QTextEdit,
    QLineEdit, QLabel, QTabWidget, QCheckBox,
    QFrame, QComboBox, QDialog
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from request import channelRequest

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s')

class DiscordUI(QMainWindow):
    def __init__(self, login_window, username, session_info, user_peer=None):
        super().__init__()
        self.login_window = login_window
        self.username = username
        self.session_info = session_info
        self.user_peer = user_peer

        self.setWindowTitle("Discord Clone - Improved UI")
        self.setGeometry(100, 100, 1200, 700)
        
        # Nếu live_mode True thì sử dụng P2P livestream
        self.live_mode = False
        
        # Chế độ chat: "channel" hoặc "dm"
        self.current_mode = None
        self.current_channel = None
        self.current_dm_user = None

        self.channels = {}      # Danh sách channel
        self.dm_users = []      # Danh sách user (để load từ API)
        self.last_message_count = 0  # Dùng để theo dõi tin nhắn mới
        
        # Thuộc tính is_viewer: mặc định False, nếu ở chế độ Visitor sẽ set True
        self.is_viewer = False

        self.initUI()
        self.get_channels_from_server()
        self.load_dm_list()

        # Khởi tạo thread polling tin nhắn mới mỗi 5 giây
        self.polling_thread = threading.Thread(target=self.poll_new_messages, daemon=True)
        self.polling_thread.start()

    def initUI(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Sidebar: chứa danh sách Channels và Direct Message
        self.sidebar_frame = QFrame()
        self.sidebar_frame.setStyleSheet("background-color: #2F3136;")
        self.sidebar_frame.setFixedWidth(200)
        sidebar_layout = QVBoxLayout(self.sidebar_frame)
        sidebar_layout.setContentsMargins(10, 10, 10, 10)
        sidebar_layout.setSpacing(8)

        title_label = QLabel("DISCORD V2.0")
        title_label.setStyleSheet("color: white; font-size: 16px; font-weight: bold;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sidebar_layout.addWidget(title_label)

        self.add_channel_button = QPushButton("+ Create Channel")
        self.add_channel_button.setStyleSheet("background-color: #5865F2; color: white;")
        self.add_channel_button.clicked.connect(self.add_channel)
        sidebar_layout.addWidget(self.add_channel_button)

        tab_widget = QTabWidget()
        tab_widget.setStyleSheet("QTabBar::tab { height: 30px; color: white; }")

        # Tab Channel
        channel_tab = QWidget()
        channel_tab_layout = QVBoxLayout(channel_tab)
        self.channel_list = QListWidget()
        self.channel_list.setStyleSheet("background-color: #3F4147; color: white;")
        self.channel_list.itemClicked.connect(self.handle_channel_clicked)
        channel_tab_layout.addWidget(self.channel_list)
        tab_widget.addTab(channel_tab, "Channels")

        # Tab DM
        dm_tab = QWidget()
        dm_tab_layout = QVBoxLayout(dm_tab)
        self.dm_list = QListWidget()
        self.dm_list.setStyleSheet("background-color: #3F4147; color: white;")
        self.dm_list.itemClicked.connect(self.handle_dm_clicked)
        dm_tab_layout.addWidget(self.dm_list)
        tab_widget.addTab(dm_tab, "Direct Msg")

        sidebar_layout.addWidget(tab_widget)

        self.live_checkbox = QCheckBox("Live Mode (P2P)")
        self.live_checkbox.setStyleSheet("color: white;")
        self.live_checkbox.stateChanged.connect(self.toggle_live_mode)
        sidebar_layout.addWidget(self.live_checkbox)

        # CHỈ SỬ DỤNG 3 TRẠNG THÁI: Online, Offline, Invisible
        # Online: trạng thái online được hiển thị công khai cho các authenticated-user khác.
        # Offline: người dùng không có kết nối đến hệ thống.
        # Invisible: mặc dù user vẫn kết nối và hoạt động như online, nhưng trạng thái hiển thị là offline.
        self.status_dropdown = QComboBox()
        self.status_dropdown.addItems(["Online", "Offline", "Invisible"])
        self.status_dropdown.currentTextChanged.connect(self.change_status)
        sidebar_layout.addWidget(self.status_dropdown)

        main_layout.addWidget(self.sidebar_frame)

        # Khung chat chính
        self.center_frame = QFrame()
        self.center_frame.setStyleSheet("background-color: #36393F;")
        center_layout = QVBoxLayout(self.center_frame)
        center_layout.setContentsMargins(10, 10, 10, 10)
        center_layout.setSpacing(8)

        self.chat_title_label = QLabel("No channel/user selected")
        self.chat_title_label.setStyleSheet("color: white; font-size: 18px; font-weight: bold;")
        center_layout.addWidget(self.chat_title_label)

        # Nút Join cho kênh (chỉ hiển thị khi chế độ chat là channel)
        self.join_button = QPushButton("Join Channel")
        self.join_button.setStyleSheet("background-color: #7289DA; color: white;")
        self.join_button.clicked.connect(self.join_channel)
        center_layout.addWidget(self.join_button)
        # Ban đầu ẩn đi nếu chưa có kênh nào được chọn
        self.join_button.setVisible(False)

        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setStyleSheet("background-color: #40444B; color: white;")
        center_layout.addWidget(self.chat_display, 1)

        input_layout = QHBoxLayout()
        self.message_input = QLineEdit()
        self.message_input.setStyleSheet("background-color: #2F3136; color: white; padding: 8px;")
        # THÊM SIGNAL: Nhấn Enter sẽ gửi tin nhắn
        self.message_input.returnPressed.connect(self.send_message)
        self.send_button = QPushButton("Send")
        self.send_button.setStyleSheet("background-color: #5865F2; color: white; padding: 8px;")
        self.send_button.clicked.connect(self.send_message)
        input_layout.addWidget(self.message_input)
        input_layout.addWidget(self.send_button)
        center_layout.addLayout(input_layout)

        self.livestream_button = QPushButton("Start Livestream")
        self.livestream_button.setStyleSheet("background-color: orange; color: white; padding: 8px;")
        self.livestream_button.clicked.connect(self.start_livestream)
        center_layout.addWidget(self.livestream_button)

        main_layout.addWidget(self.center_frame, 1)

        # Khung danh sách thành viên (các thành viên online trong kênh)
        self.right_frame = QFrame()
        self.right_frame.setStyleSheet("background-color: #2F3136;")
        self.right_frame.setFixedWidth(200)
        right_layout = QVBoxLayout(self.right_frame)
        right_layout.setContentsMargins(10, 10, 10, 10)

        members_label = QLabel("Members")
        members_label.setStyleSheet("color: white; font-size: 14px; font-weight: bold;")
        right_layout.addWidget(members_label)

        self.member_list = QListWidget()
        self.member_list.setStyleSheet("background-color: #3F4147; color: white;")
        right_layout.addWidget(self.member_list)

        self.logout_button = QPushButton("Logout")
        self.logout_button.setStyleSheet("background-color: red; color: white;")
        self.logout_button.clicked.connect(self.logout)
        right_layout.addWidget(self.logout_button)

        main_layout.addWidget(self.right_frame)

        self.load_dm_list()

    def toggle_live_mode(self, state):
        self.live_mode = (state == Qt.CheckState.Checked.value)
        logging.info("Live mode set to %s", self.live_mode)

    def load_dm_list(self):
        try:
            request_data = {"action": "get_all_users"}
            response_str = channelRequest.handle_channel_request(json.dumps(request_data))
            response = json.loads(response_str)
            if response.get("status") == "success":
                users = response.get("data", [])
                self.dm_list.clear()
                self.dm_users = []
                for user in users:
                    display_text = f"{user.get('username')} ({user.get('peer_ip')}:{user.get('peer_port')}, {user.get('session_id')})"
                    self.dm_users.append(user)
                    item = QListWidgetItem(display_text)
                    self.dm_list.addItem(item)
            else:
                logging.error("Error getting user list: %s", response.get("message"))
        except Exception as e:
            logging.error("Exception in load_dm_list: %s", e)

    def handle_channel_clicked(self, item):
        self.current_mode = "channel"
        self.current_channel = item.text()
        self.chat_title_label.setText(f"#{self.current_channel}")
        self.join_button.setVisible(True)  # Hiển thị nút Join khi chọn kênh
        self.load_channel_messages()

    def handle_dm_clicked(self, item):
        self.current_mode = "dm"
        self.current_dm_user = item.text()
        self.chat_title_label.setText(f"DM with {self.current_dm_user}")
        self.join_button.setVisible(False)  # Ẩn nút Join khi chuyển sang DM
        self.load_dm_messages()

    def load_channel_messages(self):
        if not self.current_channel:
            return
        self.chat_display.clear()
        try:
            request_data = {"action": "get_channel_info", "channel_name": self.current_channel}
            if self.is_viewer:
                request_data["is_visitor"] = True
            response_str = channelRequest.handle_channel_request(json.dumps(request_data))
            response = json.loads(response_str)
            if response.get("status") == "success":
                messages = response.get("messages", [])
                self.last_message_count = len(messages)
                for msg in messages:
                    sender = msg.get("sender")
                    text = msg.get("text")
                    self.chat_display.append(f"{sender}: {text}")
                # Cập nhật danh sách thành viên từ dữ liệu trả về
                members = response.get("members", [])
                self.update_member_list(members)
                # Cập nhật trạng thái nút Join: nếu người dùng đã có trong thành viên, disable nút Join
                if self.username in members:
                    self.join_button.setText("Joined")
                    self.join_button.setEnabled(False)
                else:
                    self.join_button.setText("Join Channel")
                    self.join_button.setEnabled(True)
            else:
                self.chat_display.append(f"[ERROR] {response.get('message')}")
                logging.error("Error loading channel messages: %s", response.get("message"))
        except Exception as e:
            logging.error("load_channel_messages error: %s", e)

    def update_member_list(self, members):
        self.member_list.clear()
        for m in members:
            self.member_list.addItem(m)

    def load_dm_messages(self):
        self.chat_display.clear()
        # Nếu có tích hợp DM history, load tại đây

    def send_message(self):
        message = self.message_input.text().strip()
        if not message:
            return
        self.message_input.clear()

        # Hiển thị tin nhắn ngay (chỉ nội dung, không có tiền tố "You:")
        self.chat_display.append(message)
        logging.info("Sending message: %s", message)

        if self.current_mode == "channel":
            if self.live_mode:
                if self.user_peer:
                    self.user_peer.send_p2p_broadcast(message)
                else:
                    self.chat_display.append("[ERROR] No user_peer for P2P")
            else:
                self.send_channel_message_api(message)
        elif self.current_mode == "dm":
            if self.user_peer:
                self.user_peer.send_p2p_broadcast(f"[DM to {self.current_dm_user}] {message}")
            else:
                self.chat_display.append("[ERROR] No user_peer for DM")
        else:
            self.chat_display.append("[INFO] No channel or DM selected!")

    def send_channel_message_api(self, message):
        if not self.current_channel:
            self.chat_display.append("[ERROR] No channel selected.")
            return
        try:
            request_data = {
                "action": "send_message",
                "username": self.username,
                "channel_name": self.current_channel,
                "message": message
            }
            response_str = channelRequest.handle_channel_request(json.dumps(request_data))
            response = json.loads(response_str)
            if response.get("status") != "success":
                self.chat_display.append(f"[ERROR] Send failed: {response.get('message')}")
        except Exception as e:
            self.chat_display.append(f"[ERROR] {e}")

    def join_channel(self):
        if not self.current_channel:
            return
        try:
            request_data = {
                "action": "join_channel",
                "username": self.username,
                "channel_name": self.current_channel
            }
            response_str = channelRequest.handle_channel_request(json.dumps(request_data))
            response = json.loads(response_str)
            if response.get("status") == "success":
                self.chat_display.append("[INFO] Joined channel successfully.")
                # Reload thông tin kênh để cập nhật danh sách thành viên và trạng thái nút Join
                self.load_channel_messages()
            else:
                self.chat_display.append(f"[ERROR] {response.get('message')}")
        except Exception as e:
            self.chat_display.append(f"[ERROR] {e}")

    def add_channel(self):
        dialog = AddChannelDialog()
        if dialog.exec():
            data = dialog.get_channel_data()
            new_channel = data.get("channel_name")
            allow_visitor = data.get("allow_visitor", True)
            if new_channel:
                request_data = {
                    "action": "create_channel",
                    "host": self.username,
                    "channel_name": new_channel,
                    "allow_visitor": allow_visitor
                }
                response_str = channelRequest.handle_channel_request(json.dumps(request_data))
                response = json.loads(response_str)
                if response.get("status") == "success":
                    self.get_channels_from_server()
                else:
                    logging.error("Error creating channel: %s", response.get("message"))

    def get_channels_from_server(self):
        try:
            request_data = {"action": "get_all_channels"}
            response_str = channelRequest.handle_channel_request(json.dumps(request_data))
            response = json.loads(response_str)
            if response.get("status") == "success":
                channels = response.get("data", [])
                self.channels = {ch["channel_name"]: ch for ch in channels}
                self.channel_list.clear()
                for c in channels:
                    self.channel_list.addItem(c["channel_name"])
            else:
                logging.error("Error get_channels: %s", response.get("message"))
        except Exception as e:
            logging.error("get_channels_from_server error: %s", e)

    def poll_new_messages(self):
        while True:
            if self.current_mode == "channel" and self.current_channel:
                try:
                    request_data = {"action": "get_channel_info", "channel_name": self.current_channel}
                    if self.is_viewer:
                        request_data["is_visitor"] = True
                    response_str = channelRequest.handle_channel_request(json.dumps(request_data))
                    response = json.loads(response_str)
                    if response.get("status") == "success":
                        messages = response.get("messages", [])
                        if len(messages) > self.last_message_count:
                            new_msgs = messages[self.last_message_count:]
                            for msg in new_msgs:
                                sender = msg.get("sender")
                                text = msg.get("text")
                                # Nếu tin nhắn do chính bạn gửi, bỏ qua (để không lặp)
                                if sender == self.username:
                                    continue
                                self.chat_display.append(f"{sender}: {text}")
                            self.last_message_count = len(messages)
                    else:
                        logging.error("Polling error: %s", response.get("message"))
                except Exception as e:
                    logging.error("Error in poll_new_messages: %s", e)
            time.sleep(5)

    def start_livestream(self):
        if self.user_peer:
            threading.Thread(target=self.user_peer.start_livestream, daemon=True).start()
        else:
            self.chat_display.append("[ERROR] user_peer not found!")

    def change_status(self, status):
        logging.info("Status changed to %s", status)
        # Có thể gửi request cập nhật trạng thái lên server nếu cần

    def logout(self):
        self.close()
        self.login_window.show()

class AddChannelDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Add Channel")
        self.setGeometry(300, 300, 300, 150)
        layout = QVBoxLayout(self)

        self.channel_name_input = QLineEdit()
        self.channel_name_input.setPlaceholderText("Channel name")
        layout.addWidget(self.channel_name_input)

        self.allow_visitor_checkbox = QCheckBox("Allow Visitors to View")
        self.allow_visitor_checkbox.setChecked(True)
        layout.addWidget(self.allow_visitor_checkbox)

        create_btn = QPushButton("Create")
        create_btn.clicked.connect(self.accept)
        layout.addWidget(create_btn)

    def get_channel_data(self):
        channel_name = self.channel_name_input.text().strip()
        allow_visitor = self.allow_visitor_checkbox.isChecked()
        return {"channel_name": channel_name, "allow_visitor": allow_visitor}

if __name__ == "__main__":
    app = QApplication(sys.argv)
    login_window = QWidget()  # Cửa sổ login giả lập
    username = "UserA"        # Ví dụ tên user cố định (thay đổi theo nhu cầu)
    session_info = {"session_id": "dummy"}
    window = DiscordUI(login_window, username, session_info)
    window.show()
    sys.exit(app.exec())
