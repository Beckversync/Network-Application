import json
import sys, os, threading, time, socket
import logging
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget,
    QVBoxLayout, QHBoxLayout, QPushButton, QListWidget, QListWidgetItem,
    QTextEdit, QLineEdit, QLabel, QTabWidget,
    QCheckBox, QFrame, QComboBox, QDialog, QMessageBox
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6 import QtGui
from PyQt6.QtGui import QFont
from request import channelRequest
from syncService import SyncManager
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s')
from config.db import channels_collection, users_collection
import time
import datetime
class DiscordUI(QMainWindow):
    def __init__(self, login_window, username, session_info, user_peer=None):
        super().__init__()
        self.login_window = login_window
        self.username = username
        self.session_info = session_info
        self.user_peer = user_peer

        self.setWindowTitle("Discord Clone - Improved UI")
        self.setGeometry(100, 100, 1200, 700)
        
        self.current_mode = None
        self.current_channel = None
        self.current_dm_user = None

        self.channels = {}
        self.hosted_channels = {}      
        self.dm_users = []      
        self.last_message_count = 0  

        self.is_viewer = False

        self.sync_manager = None

        self.initUI()
        self.get_channels_from_server()
        self.get_hosted_channels_from_server()
        self.load_dm_list()

        self.polling_thread = threading.Thread(target=self.poll_loop, daemon=True)
        self.polling_thread.start()

    def initUI(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
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
        
        channel_tab = QWidget()
        channel_tab_layout = QVBoxLayout(channel_tab)
        self.channel_list = QListWidget()
        self.channel_list.setStyleSheet("background-color: #3F4147; color: white;")
        self.channel_list.itemClicked.connect(self.handle_channel_clicked)
        channel_tab_layout.addWidget(self.channel_list)
        tab_widget.addTab(channel_tab, "Channels")

        hosted_channel_tab = QWidget()
        hosted_channel_layout = QVBoxLayout(hosted_channel_tab)
        self.hosted_channel_list = QListWidget()
        self.hosted_channel_list.setStyleSheet("background-color: #3F4147; color: white;")
        self.hosted_channel_list.itemClicked.connect(self.handle_channel_clicked)
        hosted_channel_layout.addWidget(self.hosted_channel_list)
        tab_widget.addTab(hosted_channel_tab, "Hosted Channels")
        
        dm_tab = QWidget()
        dm_tab_layout = QVBoxLayout(dm_tab)
        self.dm_list = QListWidget()
        self.dm_list.setStyleSheet("background-color: #3F4147; color: white;")
        self.dm_list.itemClicked.connect(self.handle_dm_clicked)
        dm_tab_layout.addWidget(self.dm_list)
        tab_widget.addTab(dm_tab, "Direct Msg")
        
        sidebar_layout.addWidget(tab_widget)
        
        self.status_dropdown = QComboBox()
        self.status_dropdown.addItems(["Online", "Offline", "Invisible"])
        self.status_dropdown.currentTextChanged.connect(self.change_status)
        sidebar_layout.addWidget(self.status_dropdown)
        
        main_layout.addWidget(self.sidebar_frame)
        
        self.center_frame = QFrame()
        self.center_frame.setStyleSheet("background-color: #36393F;")
        center_layout = QVBoxLayout(self.center_frame)
        center_layout.setContentsMargins(10, 10, 10, 10)
        center_layout.setSpacing(8)
        
        self.chat_title_label = QLabel("No channel/user selected")
        self.chat_title_label.setStyleSheet("color: white; font-size: 18px; font-weight: bold;")
        center_layout.addWidget(self.chat_title_label)
        
        self.join_button = QPushButton("Join Channel")
        self.join_button.setStyleSheet("background-color: #7289DA; color: white;")
        self.join_button.clicked.connect(self.join_channel)
        center_layout.addWidget(self.join_button)
        
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
        self.message_input.returnPressed.connect(self.send_message)
        self.send_button = QPushButton("Send")
        self.send_button.setStyleSheet("background-color: #5865F2; color: white; padding: 8px;")
        self.send_button.clicked.connect(self.send_message)
        input_layout.addWidget(self.message_input)
        input_layout.addWidget(self.send_button)
        center_layout.addLayout(input_layout)
        
        self.toggle_livestream_button = QPushButton("Start Livestream")
        self.toggle_livestream_button.setStyleSheet("background-color: orange; color: white; padding: 8px;")
        self.toggle_livestream_button.clicked.connect(self.toggle_livestream)
        center_layout.addWidget(self.toggle_livestream_button)
        
        main_layout.addWidget(self.center_frame, 1)
        
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

    def send_message(self):
        message = self.message_input.text().strip()
        if not message:
            return
        self.message_input.clear()
        #self.chat_display.append(message)
        logging.info("Sending message: %s", message)
        if self.current_mode == "channel":
            self.send_message_p2p_api(message)
        elif self.current_mode == "dm":
            if self.user_peer:
                self.user_peer.send_chat_message_via_tracker(f"[DM to {self.current_dm_user}] {message}")
            else:
                self.chat_display.append("[ERROR] No user_peer for DM")
        else:
            self.chat_display.append("[INFO] No channel or DM selected!")
    
    def send_message_p2p_api(self, message):
        if not self.current_channel:
            self.chat_display.append("[ERROR] No channel selected.")
            return
        if not (self.user_peer and self.user_peer.tracker_socket):
            self.chat_display.append("[ERROR] Tracker is offline. Cannot send channel message.")
            logging.error("Tracker offline: cannot send channel message: %s", message)
            return
        try:
            request_data = {
                "action": "send_message_p2p",
                "username": self.username,
                "channel_name": self.current_channel,
                "message": message
            }
            response_str = channelRequest.handle_channel_request(json.dumps(request_data))
            response = json.loads(response_str)
            if response.get("status") != "success":
                self.chat_display.append(f"[ERROR] Send failed: {response.get('message')}")
            else:
                logging.info("Message from %s sent in channel '%s'", self.username, self.current_channel)
        except Exception as e:
            self.chat_display.append(f"[ERROR] {e}")
        
    def send_channel_message_api(self, message):
        if not self.current_channel:
            self.chat_display.append("[ERROR] No channel selected.")
            return
        if not (self.user_peer and self.user_peer.tracker_socket):
            self.chat_display.append("[ERROR] Tracker is offline. Cannot send channel message.")
            logging.error("Tracker offline: cannot send channel message: %s", message)
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
            else:
                logging.info("Message from %s sent in channel '%s'", self.username, self.current_channel)
        except Exception as e:
            self.chat_display.append(f"[ERROR] {e}")

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
                    display_text = f"{user.get('username')} ({user.get('status')})"
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
        # self.load_messages_from_file()
        # Cập nhật active_channel của user_peer
        if self.user_peer:
            self.user_peer.active_channel = self.current_channel
            # Nếu user là chủ kênh, cập nhật livestream_channel
            if self.channels.get(self.current_channel, {}).get("owner") == self.username:
                self.user_peer.livestream_channel = self.current_channel
        if self.channels.get(self.current_channel, {}).get("owner") == self.username:
            if not self.sync_manager:
                # self.sync_manager = SyncManager(self.username, self.current_channel)
                # self.sync_manager.start_periodic_sync(interval=30)
                logging.info("[SYNC] SyncManager started for channel '%s'", self.current_channel)
    

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
            request_data = {
                "action": "get_channel_info",
                "channel_name": self.current_channel,
                "username": self.username
            }
            if self.is_viewer:
                request_data["is_visitor"] = True
            response_str = channelRequest.handle_channel_request(json.dumps(request_data))
            response = json.loads(response_str)
            if response.get("status") == "success":
                members = response.get("members", [])
                self.update_member_list(members)
                if self.username in members:
                    self.join_button.setText("Joined")
                    self.join_button.setEnabled(False)
                else:
                    self.join_button.setText("Join Channel")
                    self.join_button.setEnabled(True)
                owner = response.get("owner")
                self.start_request_timer(owner)

        except Exception as e:
            logging.error("load_channel_messages error: %s", e)
        channel_data = channels_collection.find_one({"channel_name": self.current_channel})
        if not channel_data:
            return {"status": "error", "message": "Channel not found"}
        owner_username = channel_data.get("owner")
        owner_data = users_collection.find_one({"username": owner_username})
        if owner_data and owner_data.get("state") == "offline":
            messages = response.get("messages", [])
            self.last_message_count = len(messages)
            for msg in messages:
                text = msg.get("text")
                self.chat_display.append(f"{text}")
            self.current_channel_info = response
            if response.get("status") != "success":
                self.chat_display.clear()
                self.chat_display.append(f"[ERROR] {response.get('message')}")
        else:
            try:
                file_path = os.path.join("local_sync", f"sync_{self.current_channel}_{owner_username}.txt")
                if not os.path.exists(file_path):
                    self.chat_display.append("[INFO] Do not have mesage.")
                    return

                with open(file_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        self.chat_display.append(line.strip())
                        self.last_message_count += 1

                logging.info("[SYNC LOAD] Save message to file: %s", file_path)
            except Exception as e:
                logging.error("[SYNC LOAD] Error when read file: %s", e)
                self.chat_display.append("[ERROR] Can not load message from file.")
        


    def start_request_timer(self, owner):
        self.owner = owner
        self.request_timer = QTimer()
        self.request_timer.timeout.connect(self.generate_request)
        self.request_timer.start(1000)  # mỗi 1 giây gọi lại

    def generate_request(self):
        if self.username != self.owner:
            self.request_list.clear()
            self.request_list.addItem("You are not the owner")
            return

        req_data = {
            "action": "get_join_requests",
            "channel_name": self.current_channel,
            "owner": self.owner
        }
        try:
            resp_str = channelRequest.handle_channel_request(json.dumps(req_data))
            resp = json.loads(resp_str)
            self.request_list.clear()
            if resp.get("status") == "success":
                join_requests = resp.get("join_requests", [])
                if not join_requests:
                    self.request_list.addItem("No requests")
                for user in join_requests:
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
                self.request_list.addItem("Failed to fetch requests")
        except Exception as e:
            logging.error("generate_request error: %s", e)


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
                QMessageBox.information(self, "Approved", f"{username} approved to join {self.current_channel}")
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
                QMessageBox.information(self, "Rejected", f"{username} rejected from joining {self.current_channel}")
                self.load_channel_messages()
            else:
                QMessageBox.warning(self, "Failed", response.get("message", "Something went wrong"))
        except Exception as e:
            logging.error("reject_user error: %s", e)
            QMessageBox.critical(self, "Error", str(e))
   
    def update_member_list(self, members):
        self.member_list.clear()
        status_map = {}
        try:
            request_data = {"action": "get_all_users"}
            response_str = channelRequest.handle_channel_request(json.dumps(request_data))
            response = json.loads(response_str)
            if response.get("status") == "success":
                all_users = response.get("data", [])
                for u in all_users:
                    user_name = u.get("username")
                    user_status = u.get("status", "Offline")
                    status_map[user_name] = user_status
            else:
                logging.error("Error get_all_users: %s", response.get("message"))
        except Exception as e:
            logging.error("Exception in get_all_users: %s", e)
        
        for m in members:
            user_status = status_map.get(m, "Offline")
            if user_status == "Online":
                display_text = f"🟢 {m}"
                color = QtGui.QColor("lime")
            else:
                display_text = f"⚪ {m}"
                color = QtGui.QColor("gray")
            item = QListWidgetItem(display_text)
            item.setForeground(color)
            self.member_list.addItem(item)
    
    def load_dm_messages(self):
        self.chat_display.clear()
    
    # def sync_offline_channel_messages(self):
    #     filename = f"offline_channel_{self.current_channel}_{self.username}.txt"
    #     try:
    #         if os.path.exists(filename):
    #             with open(filename, "r", encoding="utf-8") as f:
    #                 messages = [line.strip() for line in f if line.strip()]
    #             if messages:
    #                 self.chat_display.append(f"[SYNC] Syncing {len(messages)} offline messages to server...")
    #                 for msg in messages:
    #                     self.send_channel_message_api(msg)
    #                 os.remove(filename)
    #                 self.chat_display.append("[SYNC] Offline messages synced.")
    #                 logging.info("Synced offline messages from file %s", filename)
    #     except Exception as e:
    #         logging.error("Error syncing offline messages: %s", e)
    
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
                self.get_channels_from_server()
                self.get_hosted_channels_from_server()
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
        type_choice = QMessageBox.question(
                self,
                "Channel Type",
                "Do you want to create a Private channel?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        dialog = AddChannelDialog()
        if dialog.exec():
            data = dialog.get_channel_data()
            new_channel = data.get("channel_name")
            if not new_channel:
                return
            is_private = (type_choice == QMessageBox.StandardButton.Yes)
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
                self.get_hosted_channels_from_server()
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

    def get_hosted_channels_from_server(self):
        try:
            request_data = {"action": "get_hosted_channels", "username": self.username}
            response_str = channelRequest.handle_channel_request(json.dumps(request_data))
            response = json.loads(response_str)

            if response.get("status") == "success":
                channels = response.get("data", {}).get("hosted_channels", [])
                self.hosted_channels = {ch: {} for ch in channels}  # tạo dict đơn giản
                self.hosted_channel_list.clear()
                for c in channels:
                    self.hosted_channel_list.addItem(c)
            else:
                logging.error("Error get_hosted_channels: %s", response.get("message"))
        
        except Exception as e:
            logging.error("get_hosted_channels_from_server error: %s", e)
    
    def poll_loop(self):
        while True:
            if self.current_mode == "channel" and self.current_channel:
                channel_data = channels_collection.find_one({"channel_name": self.current_channel})
                owner_username = channel_data.get("owner")
                owner_data = users_collection.find_one({"username": owner_username})
                if owner_data and owner_data.get("state") == "offline":
                    try:
                        request_data = {"action": "get_channel_info", "channel_name": self.current_channel, "username": self.username}
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
                                    # if sender == self.username:
                                    #     continue
                                    self.chat_display.append(f"{text}")
                                self.last_message_count = len(messages)
                        else:
                            logging.error("Polling error: %s", response.get("message"))
                    except Exception as e:
                        logging.error("Error in poll_loop (new messages): %s", e)

                if owner_data and owner_data.get("state") == "online":
                    file_path = os.path.join("local_sync", f"sync_{self.current_channel}_{owner_username}.txt")
                    if os.path.exists(file_path):
                        with open(file_path, 'r', encoding='utf-8') as f:
                            lines = f.readlines()
                            for line in lines[self.last_message_count:]:
                                self.chat_display.append(line.strip())
                                self.last_message_count += 1
                        # logging.info("[SYNC LOAD] Loaded messages from file: %s", file_path)
                    else:
                        logging.warning("[SYNC LOAD] File not found: %s", file_path)
                
            try:
                self.load_dm_list()
                self.get_channels_from_server()
                self.get_hosted_channels_from_server()
                #self.load_channel_messages()
            except Exception as e:
                logging.error("Error updating lists: %s", e)

            time.sleep(0.5)
    
    def toggle_livestream(self):
        if self.current_mode != "channel":
            self.chat_display.append("[INFO] No channel selected or not in channel mode!")
            return
        if not (self.current_channel_info and self.current_channel_info.get("owner") == self.username and self.is_viewer == True):
            self.chat_display.append("[INFO] Only the channel owner can start/stop livestream. Others can only watch.")
            return
        if not self.user_peer:
            self.chat_display.append("[ERROR] user_peer not found!")
            return
        # Nếu livestream chưa chạy, bắt đầu livestream; nếu đang chạy, gọi stop_livestream
        if not self.user_peer.is_livestreaming:
            threading.Thread(target=self.user_peer.start_livestream, daemon=True).start()
            self.toggle_livestream_button.setText("Stop Livestream")
        else:
            self.user_peer.stop_livestream()
            self.toggle_livestream_button.setText("Start Livestream")
    
    def change_status(self, status):
        logging.info("Status changed to %s", status)
        session_id = self.session_info.get("session_id")
        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_ip = '192.168.0.4'
            server_port = 5000
            client_socket.connect((server_ip, server_port))
            if status == "Online":
                request_data = {"action": "update_status", "session_id": session_id, "visible": True}
            elif status == "Invisible":
                request_data = {"action": "update_status", "session_id": session_id, "visible": False}
            elif status == "Offline":
                request_data = {"action": "logout", "session_id": session_id}
            client_socket.send(json.dumps(request_data).encode())
            response_str = client_socket.recv(4096).decode()
            response = json.loads(response_str)
            client_socket.close()
            if response.get("status") != "success":
                logging.error("Status update failed: %s", response.get("message"))
            if status == "Offline":
                QMessageBox.information(self, "Logout", "You have been logged out.")
                self.close()
                self.login_window.show()
        except Exception as e:
            logging.error("Change status error: %s", str(e))
    
    def logout(self):
        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_ip = '192.168.0.4'
            server_port = 5000
            client_socket.connect((server_ip, server_port))
            session_id = self.session_info.get("session_id")
            request_data = {"action": "logout", "session_id": session_id}
            client_socket.send(json.dumps(request_data).encode())
            response_str = client_socket.recv(4096).decode()
            response = json.loads(response_str)
            client_socket.close()

            if response.get("status") == "success":
                sync_folder = "local_sync"
                if os.path.exists(sync_folder):
                    for filename in os.listdir(sync_folder):
                        if filename.startswith("sync_") and filename.endswith(".txt"):
                            file_path = os.path.join(sync_folder, filename)
                            parts = filename.replace("sync_", "").replace(".txt", "").split("_")
                            if len(parts) < 2:
                                continue

                            channel_name = parts[0]
                            channel_owner = parts[1]

                            if channel_owner != self.username:
                                logging.warning("[SYNC SKIPPED] User is not owner of channel: %s", channel_name)
                                continue

                            with open(file_path, "r", encoding="utf-8") as f:
                                for line in f:
                                    line = line.strip()
                                    if not line:
                                        continue
                                    try:
                                        time_part, rest = line.split("] ", 1)
                                        readable_time = time_part[1:]
                                        sender, message_text = rest.split(": ", 1)
                                        message_dict = {
                                            "sender": sender,
                                            "text": f"[{readable_time}] {sender}: {message_text}"
                                        }
                                        channels_collection.update_one(
                                            {"channel_name": channel_name},
                                            {"$push": {"messages": message_dict}}
                                        )
                                    except Exception as e:
                                        logging.error("Error sending line in %s: %s", filename, e)
                            logging.info("[SYNC DONE] Synced file: %s", filename)

                QMessageBox.information(self, "Logout", "You have been logged out.")
                if self.user_peer:
                    self.user_peer.leave_tracker()
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
    from PyQt6.QtWidgets import QApplication, QWidget
    app = QApplication(sys.argv)
    login_window = QWidget()
    username = "UserA"
    session_info = {"session_id": "dummy"}
    window = DiscordUI(login_window, username, session_info)
    window.show()
    sys.exit(app.exec())
