import json
import sys, os, threading
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget,
    QVBoxLayout, QHBoxLayout, QSplitter,
    QPushButton, QListWidget, QListWidgetItem,
    QTextEdit, QLineEdit, QLabel, QTabWidget,
    QCheckBox, QFrame, QComboBox, QDialog
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

# Giả sử bạn có module request
from request import channelRequest

class DiscordUI(QMainWindow):
    def __init__(self, login_window, username, session_info, user_peer=None):
        super().__init__()
        self.login_window = login_window
        self.username = username
        self.session_info = session_info
        self.user_peer = user_peer

        self.setWindowTitle("Discord Clone - Improved UI")
        self.setGeometry(100, 100, 1200, 700)
        
        # Thêm thuộc tính live_mode để tránh lỗi AttributeError
        self.live_mode = False
        
        # Chế độ chat: "channel" hay "dm"
        self.current_mode = None
        self.current_channel = None
        self.current_dm_user = None

        self.channels = {}      # Danh sách channel
        self.dm_users = []      # Danh sách user (sẽ load từ API)

        self.initUI()
        self.get_channels_from_server()
        self.load_dm_list()  # Load DM list sau khi UI được thiết lập

    def initUI(self):
        # Widget trung tâm
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Tạo layout tổng
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0,0,0,0)

        # ─────────────────────────────────────────
        # 1) KHU VỰC TRÁI: Sidebar (Channel + DM)
        # ─────────────────────────────────────────
        self.sidebar_frame = QFrame()
        self.sidebar_frame.setStyleSheet("background-color: #2F3136;")
        self.sidebar_frame.setFixedWidth(200)  # Đặt chiều rộng sidebar
        sidebar_layout = QVBoxLayout(self.sidebar_frame)
        sidebar_layout.setContentsMargins(10,10,10,10)
        sidebar_layout.setSpacing(8)

        # Tiêu đề
        title_label = QLabel("DISCORD V2.0")
        title_label.setStyleSheet("color: white; font-size: 16px; font-weight: bold;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sidebar_layout.addWidget(title_label)

        # Nút tạo channel
        self.add_channel_button = QPushButton("+ Create Channel")
        self.add_channel_button.setStyleSheet("background-color: #5865F2; color: white;")
        self.add_channel_button.clicked.connect(self.add_channel)
        sidebar_layout.addWidget(self.add_channel_button)

        # TabWidget để phân tách Channel & DM
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

        # Live mode
        self.live_checkbox = QCheckBox("Live Mode (P2P)")
        self.live_checkbox.setStyleSheet("color: white;")
        self.live_checkbox.stateChanged.connect(self.toggle_live_mode)
        sidebar_layout.addWidget(self.live_checkbox)

        # Thông tin user
        self.status_dropdown = QComboBox()
        self.status_dropdown.addItems(["Online", "Away", "Do Not Disturb", "Offline"])
        self.status_dropdown.currentTextChanged.connect(self.change_status)
        sidebar_layout.addWidget(self.status_dropdown)

        # Thêm sidebar vào layout
        main_layout.addWidget(self.sidebar_frame)

        # ─────────────────────────────────────────
        # 2) KHU VỰC GIỮA: Chat chính
        # ─────────────────────────────────────────
        self.center_frame = QFrame()
        self.center_frame.setStyleSheet("background-color: #36393F;")
        center_layout = QVBoxLayout(self.center_frame)
        center_layout.setContentsMargins(10,10,10,10)
        center_layout.setSpacing(8)

        # Label hiển thị tên channel / user DM
        self.chat_title_label = QLabel("No channel/user selected")
        self.chat_title_label.setStyleSheet("color: white; font-size: 18px; font-weight: bold;")
        center_layout.addWidget(self.chat_title_label)

        # Khung chat
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setStyleSheet("background-color: #40444B; color: white;")
        center_layout.addWidget(self.chat_display, 1)

        # Hàng nhập tin nhắn
        input_layout = QHBoxLayout()
        self.message_input = QLineEdit()
        self.message_input.setStyleSheet("background-color: #2F3136; color: white; padding: 8px;")
        self.send_button = QPushButton("Send")
        self.send_button.setStyleSheet("background-color: #5865F2; color: white; padding: 8px;")
        self.send_button.clicked.connect(self.send_message)
        input_layout.addWidget(self.message_input)
        input_layout.addWidget(self.send_button)
        center_layout.addLayout(input_layout)

        # Nút livestream
        self.livestream_button = QPushButton("Start Livestream")
        self.livestream_button.setStyleSheet("background-color: orange; color: white; padding: 8px;")
        self.livestream_button.clicked.connect(self.start_livestream)
        center_layout.addWidget(self.livestream_button)

        main_layout.addWidget(self.center_frame, 1)  # Chiếm nhiều không gian

        # ─────────────────────────────────────────
        # 3) KHU VỰC PHẢI: (Tùy ý) - danh sách member
        # ─────────────────────────────────────────
        self.right_frame = QFrame()
        self.right_frame.setStyleSheet("background-color: #2F3136;")
        self.right_frame.setFixedWidth(200)
        right_layout = QVBoxLayout(self.right_frame)
        right_layout.setContentsMargins(10,10,10,10)

        members_label = QLabel("Members")
        members_label.setStyleSheet("color: white; font-size: 14px; font-weight: bold;")
        right_layout.addWidget(members_label)

        self.member_list = QListWidget()
        self.member_list.setStyleSheet("background-color: #3F4147; color: white;")
        right_layout.addWidget(self.member_list)

        # Nút Logout
        self.logout_button = QPushButton("Logout")
        self.logout_button.setStyleSheet("background-color: red; color: white;")
        self.logout_button.clicked.connect(self.logout)
        right_layout.addWidget(self.logout_button)

        main_layout.addWidget(self.right_frame)

        # Sau khi setup xong, ta load DM list tạm
        self.load_dm_list()

    # ─────────────────────────────────────────
    # HÀM HỖ TRỢ
    # ─────────────────────────────────────────
    def toggle_live_mode(self, state):
        self.live_mode = (state == Qt.CheckState.Checked.value)

    def load_dm_list(self):
        """Gọi API để lấy danh sách user và cập nhật vào DM list (loại trừ user đang đăng nhập)."""
        try:
            # Lưu ý: Nếu API không hỗ trợ "get_all_users", hãy thay đổi action này theo đúng yêu cầu.
            request_data = {"action": "get_all_users"}
            response_str = channelRequest.handle_channel_request(json.dumps(request_data))
            response = json.loads(response_str)
            if response.get("status") == "success":
                users = response.get("data", [])
                self.dm_list.clear()
                self.dm_users = []  # Cập nhật danh sách DM
                for user in users:
                    username = user.get("username")
                    if username != self.username:
                        self.dm_users.append(username)
                        item = QListWidgetItem(username)
                        self.dm_list.addItem(item)
            else:
                print("Error getting user list:", response.get("message"))
        except Exception as e:
            print("Exception in load_dm_list:", e)


    def handle_channel_clicked(self, item):
        """Khi click vào 1 channel."""
        self.current_mode = "channel"
        self.current_channel = item.text()
        self.chat_title_label.setText(f"#{self.current_channel}")
        self.load_channel_messages()

    def handle_dm_clicked(self, item):
        """Khi click vào 1 user để chat DM."""
        self.current_mode = "dm"
        self.current_dm_user = item.text()
        self.chat_title_label.setText(f"DM with {self.current_dm_user}")
        self.load_dm_messages()

    def load_channel_messages(self):
        """Load tin nhắn kênh từ server."""
        if not self.current_channel:
            return
        self.chat_display.clear()
        # Gọi API get channel info
        try:
            request_data = {"action": "get_channel_info", "channel_name": self.current_channel}
            response_str = channelRequest.handle_channel_request(json.dumps(request_data))
            response = json.loads(response_str)
            if response.get("status") == "success":
                messages = response.get("messages", [])
                for msg in messages:
                    sender = msg.get("sender")
                    text = msg.get("text")
                    self.chat_display.append(f"{sender}: {text}")
        except Exception as e:
            print("load_channel_messages error:", e)

    def load_dm_messages(self):
        """Load tin nhắn DM (nếu bạn muốn lưu DB). Tạm thời chỉ clear."""
        self.chat_display.clear()
        # Nếu muốn, gọi API / DB để load DM cũ, hoặc hiển thị tạm
        # self.chat_display.append("=== DM HISTORY ===")

    def send_message(self):
        message = self.message_input.text().strip()
        if not message:
            return
        self.message_input.clear()

        # Hiển thị luôn
        self.chat_display.append(f"You: {message}")

        # Phân biệt channel vs dm
        if self.current_mode == "channel":
            if self.live_mode:
                # Gửi P2P broadcast
                if self.user_peer:
                    self.user_peer.send_p2p_broadcast(message)
                else:
                    self.chat_display.append("[ERROR] No user_peer for P2P")
            else:
                # Gửi lên server
                self.send_channel_message_api(message)
        elif self.current_mode == "dm":
            # Gửi tin nhắn trực tiếp (P2P)
            if self.user_peer:
                # Tìm IP, port user kia (cách làm tuỳ bạn)
                # Hoặc broadcast tạm, tuỳ logic DM
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

    def add_channel(self):
        dialog = AddChannelDialog()
        if dialog.exec():
            new_channel = dialog.get_channel_name()
            if new_channel:
                request_data = {"action": "create_channel", "host": self.username, "channel_name": new_channel}
                response_str = channelRequest.handle_channel_request(json.dumps(request_data))
                response = json.loads(response_str)
                if response.get("status") == "success":
                    self.get_channels_from_server()
                else:
                    print("Error creating channel:", response.get("message"))

    def get_channels_from_server(self):
        """Tải danh sách channel từ server."""
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
                print("Error get_channels:", response.get("message"))
        except Exception as e:
            print("get_channels_from_server error:", e)

    def start_livestream(self):
        if self.user_peer:
            threading.Thread(target=self.user_peer.start_livestream, daemon=True).start()
        else:
            self.chat_display.append("[ERROR] user_peer not found!")

    def change_status(self, status):
        print(f"Status changed to {status}")

    def logout(self):
        self.close()
        self.login_window.show()

class AddChannelDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Add Channel")
        self.setGeometry(300, 300, 300, 120)
        layout = QVBoxLayout(self)

        self.channel_name_input = QLineEdit()
        self.channel_name_input.setPlaceholderText("Channel name")
        layout.addWidget(self.channel_name_input)

        create_btn = QPushButton("Create")
        create_btn.clicked.connect(self.accept)
        layout.addWidget(create_btn)

    def get_channel_name(self):
        return self.channel_name_input.text().strip()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    login_window = QWidget()
    username = "UserA"
    session_info = {"session_id": "dummy"}
    window = DiscordUI(login_window, username, session_info)
    window.show()
    sys.exit(app.exec())
