import json
import sys, os, threading, time
import logging
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget,
    QVBoxLayout, QHBoxLayout, QPushButton, QListWidget, QListWidgetItem,
    QTextEdit, QLineEdit, QLabel, QTabWidget,
    QCheckBox, QFrame, QComboBox, QDialog, QMessageBox, QInputDialog
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont
from request import channelRequest
import socket

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
        
        # Thuộc tính live_mode
        self.live_mode = False
        
        # Chế độ chat: "channel" hay "dm"
        self.current_mode = None
        self.current_channel = None
        self.current_dm_user = None

        self.channels = {}      # Danh sách channel
        self.dm_users = []      # Danh sách user (sẽ load từ API)
        self.last_message_count = 0  # Dùng để theo dõi tin nhắn mới
        
        # Thuộc tính is_viewer (mặc định False, được thiết lập lại nếu ở chế độ Visitor)
        self.is_viewer = False

        self.initUI()
        self.get_channels_from_server()
        self.load_dm_list()

        # Polling cập nhật tin nhắn mới mỗi 5 giây
        self.polling_thread = threading.Thread(target=self.poll_new_messages, daemon=True)
        self.polling_thread.start()

    def initUI(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0,0,0,0)

        # Sidebar (Channel + DM)
        self.sidebar_frame = QFrame()
        self.sidebar_frame.setStyleSheet("background-color: #2F3136;")
        self.sidebar_frame.setFixedWidth(200)
        sidebar_layout = QVBoxLayout(self.sidebar_frame)
        sidebar_layout.setContentsMargins(10,10,10,10)
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
        center_layout.setContentsMargins(10,10,10,10)
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
        self.delete_channel_button = QPushButton("Delete Channel")
        self.delete_channel_button.setStyleSheet("background-color: #FF5555; color: white;")
        self.delete_channel_button.clicked.connect(self.delete_channel)
        self.delete_channel_button.setVisible(False)
        center_layout.addWidget(self.delete_channel_button)

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
        right_layout.setContentsMargins(10,10,10,10)

        members_label = QLabel("Members")
        members_label.setStyleSheet("color: white; font-size: 14px; font-weight: bold;")
        right_layout.addWidget(members_label)

        self.member_list = QListWidget()
        self.member_list.setStyleSheet("background-color: #3F4147; color: white;")
        right_layout.addWidget(self.member_list)
        #ui for join request
        request_label = QLabel("Join Requests")
        request_label.setStyleSheet("color: white; font-size: 14px; font-weight: bold;")
        right_layout.addWidget(request_label)

        self.request_list = QListWidget()
        self.request_list.setStyleSheet("background-color: #3F4147; color: white;")
        right_layout.addWidget(self.request_list)

        self.logout_button = QPushButton("Logout")
        self.logout_button.setStyleSheet("background-color: red; color: white;")
        self.logout_button.clicked.connect(self.logout)
        right_layout.addWidget(self.logout_button)

        main_layout.addWidget(self.right_frame)

        self.load_dm_list()

    def toggle_live_mode(self, state):
        self.live_mode = (state == Qt.CheckState.Checked.value)
        logging.info("Live mode set to %s", self.live_mode)

    # Cập nhật danh sách user dựa trên API get_all_users
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
                    # Hiển thị theo định dạng: username (ip:port, session: session_id)
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
        self.join_button.setVisible(True) 
        self.delete_channel_button.setVisible(True)
        self.load_channel_messages()

    def handle_dm_clicked(self, item):
        self.current_mode = "dm"
        self.current_dm_user = item.text()
        self.chat_title_label.setText(f"DM with {self.current_dm_user}")
        self.join_button.setVisible(False)
        self.delete_channel_button.setVisible(False)
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

                # member
                members = response.get("members", [])
                self.update_member_list(members)

                if self.username in members:
                    self.join_button.setText("Joined")
                    self.join_button.setEnabled(False)
                else:
                    self.join_button.setText("Join Channel")
                    self.join_button.setEnabled(True)

                # if owner
                owner = response.get("owner")
                if self.username == owner:
                    request_data = {
                        "action": "get_join_requests",
                        "channel_name": self.current_channel,
                        "owner": owner
                    }
                    response_str = channelRequest.handle_channel_request(json.dumps(request_data))
                    response = json.loads(response_str)
                    print(response)
                    if response.get("status") == "success":
                        join_requests = response.get("join_requests", [])
                        print(join_requests)
                        self.request_list.clear()
                        for user in join_requests:
                            #Viet UI ow day dell bt dc k co j m sua cho t
                            item_widget = QWidget()
                            layout = QHBoxLayout()
                            layout.setContentsMargins(0, 0, 0, 0)

                            label = QLabel(user)
                            approve_btn = QPushButton("✔")
                            reject_btn = QPushButton("✖")

                            approve_btn.setStyleSheet("color: green;")
                            reject_btn.setStyleSheet("color: red;")

                            approve_btn.setFixedSize(30, 25)
                            reject_btn.setFixedSize(30, 25)

                            approve_btn.clicked.connect(lambda _, u=user: self.approve_user(u))
                            reject_btn.clicked.connect(lambda _, u=user: self.reject_user(u))

                            layout.addWidget(label)
                            layout.addWidget(approve_btn)
                            layout.addWidget(reject_btn)

                            item_widget.setLayout(layout)

                            item = QListWidgetItem()
                            item.setSizeHint(item_widget.sizeHint())

                            self.request_list.addItem(item)
                            self.request_list.setItemWidget(item, item_widget)
                    else:
                        self.request_list.clear()
                        self.request_list.addItem("No requests")
                else:
                    self.request_list.clear()
                    self.request_list.addItem("You are not the owner")
            else:
                self.chat_display.append(f"[ERROR] {response.get('message')}")
                logging.error("Error loading channel messages: %s", response.get("message"))

        except Exception as e:
            logging.error("load_channel_messages error: %s", e)
    

    def approve_user(self, username):
        if not self.current_channel:
            return

        request_data = {
            "action": "approve_join_request",
            "channel_name": self.current_channel,
            "owner": self.username,
            "target_user": username
        }

        try:
            response_str = channelRequest.handle_channel_request(json.dumps(request_data))
            response = json.loads(response_str)

            if response.get("status") == "success":
                QMessageBox.information(self, "Approved", f"{username} has been approved to join {self.current_channel}")
                self.load_channel_messages() 
            else:
                QMessageBox.warning(self, "Failed", response.get("message", "Something went wrong"))
        except Exception as e:
            logging.error("approve_user error: %s", e)

            QMessageBox.critical(self, "Error", str(e))
    def reject_user(self, username):
        if not self.current_channel:
            return

        request_data = {
            "action": "reject_join_request",
            "channel_name": self.current_channel,
            "owner": self.username,
            "target_user": username
        }

        try:
            response_str = channelRequest.handle_channel_request(json.dumps(request_data))
            response = json.loads(response_str)

            if response.get("status") == "success":
                QMessageBox.information(self, "Rejected", f"{username} has been rejected from joining {self.current_channel}")
                self.load_channel_messages()  # reload để cập nhật danh sách yêu cầu
            else:
                QMessageBox.warning(self, "Failed", response.get("message", "Something went wrong"))
        except Exception as e:
            logging.error("reject_user error: %s", e)
            QMessageBox.critical(self, "Error", str(e))

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
        # self.chat_display.append(f"You: {message}")
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


    def delete_channel(self):
        if not self.current_channel:
            return
        try:
            confirm = QMessageBox.question(
                self,
                "Confirm Deletion",
                f"Are you sure you want to delete the channel '{self.current_channel}'?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            if confirm != QMessageBox.StandardButton.Yes:
                return

            request_data = {
                "action": "delete_channel",
                "username": self.username,
                "channel_name": self.current_channel
            }
            response_str = channelRequest.handle_channel_request(json.dumps(request_data))
            response = json.loads(response_str)
            
            if response.get("status") == "success":
                self.chat_display.append(f"[INFO] {response.get('message')}")
                self.get_channels_from_server()  # Reload danh sách kênh
                self.chat_display.clear()
                self.chat_title_label.setText("No channel/user selected")
                self.join_button.setVisible(False)
                self.current_channel = None
            else:
                self.chat_display.append(f"[ERROR] {response.get('message')}")
        except Exception as e:
            self.chat_display.append(f"[ERROR] {e}")

    def join_channel(self):
        if not self.current_channel:
            self.chat_display.append("[ERROR] No channel selected.")
            return

        # if member existed
        if hasattr(self, 'is_member') and self.is_member:
            self.chat_display.append("[INFO] You have already joined this channel.")
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
                self.chat_display.append(f"[INFO] Joined channel '{self.current_channel}' successfully.")
                self.load_channel_messages()
                self.is_member = True 
                if hasattr(self, 'join_button'):
                    self.join_button.setEnabled(False)
            else:
                error_msg = response.get('message', 'Unknown error')
                self.chat_display.append(f"[INFO] '{self.current_channel}': {error_msg}")
        except Exception as e:
            self.chat_display.append(f"[ERROR] Exception: {e}")

    def add_channel(self):
        dialog = AddChannelDialog()
        if dialog.exec():
            data = dialog.get_channel_data()
            new_channel = data.get("channel_name")
            
            if not new_channel:
                return
            
            type_choice = QMessageBox.question(
                self,
                "Channel Type",
                "Do you want to create a Private channel?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            is_private = type_choice == QMessageBox.StandardButton.Yes
            print(is_private)
            allow_visitor = False if is_private else True

            request_data = {
                "action": "create_channel",
                "host": self.username,
                "channel_name": new_channel,
                "is_private": is_private,
                "allow_visitor": allow_visitor,
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
        # Polling mỗi 5 giây nếu có channel được chọn
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
                            # # Thông báo nếu có tin nhắn mới
                            # self.chat_display.append(f"[Notification] {len(new_msgs)} new message(s) received.")
                            for msg in new_msgs:
                                sender = msg.get("sender")
                                text = msg.get("text")
                                #Nếu tin nhắn do chính bạn gửi, bỏ qua (để không lặp)
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
        # Có thể gửi request cập nhật status lên server

    def logout(self):
        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_ip = "127.0.0.1"
            server_port = 22236
            client_socket.connect((server_ip, server_port))
            session_id = self.session_info.get("session_id")
            request_data = {"action": "logout", "session_id": session_id}
            client_socket.send(json.dumps(request_data).encode())

            response_str = client_socket.recv(4096).decode()
            response = json.loads(response_str)
            client_socket.close()

            if response.get("status") == "success":
                QMessageBox.information(self, "Logout", "You have been logged out.")
            else:
                QMessageBox.warning(self, "Logout Failed", response.get("message", "Unknown error"))

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Logout error: {str(e)}")

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
    login_window = QWidget()
    username = "UserA"
    session_info = {"session_id": "dummy"}
    window = DiscordUI(login_window, username, session_info)
    window.show()
    sys.exit(app.exec())
