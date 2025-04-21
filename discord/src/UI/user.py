import json
import sys
import os
import threading
import time
import logging
import random
import socket
import cv2
import numpy as np
import base64
import datetime

from config.db import users_collection, channels_collection

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s')

class USER:
    def __init__(self, TRACKER_IP, TRACKER_PORT, headless=False, username=None, port=None):
        # Thiết lập tên người dùng và đồng nhất thuộc tính
        if username is not None:
            self.name = username
            self.username = username
        else:
            self.name = input("ENTER YOUR NAME: ")
            self.username = self.name

        # Lấy IP tự động
        self.ip = USER.get_host_default_interface_ip()

        # Thiết lập cổng
        if headless:
            self.port = port if port is not None else self._get_random_port()
        else:
            self.port = int(input("ENTER YOUR PORT (TCP): "))

        self.udp_port = self.port + 1

        # Khởi tạo thư mục sync
        os.makedirs("local_sync", exist_ok=True)

        # Kết nối tracker và server P2P, UDP listener
        self.tracker_socket = None
        self.connect_to_tracker(TRACKER_IP, TRACKER_PORT)
        self.start_p2p_server()
        self.start_udp_listener()

        # Lịch sử chat và trạng thái
        self.chat_history = []
        self.isChatRunning = False

        # File offline caching
        self.offline_file = f"offline_{self.name}.txt"
        self.sync_offline_messages()

        # Thuộc tính livestream
        self._stop_livestream_flag = False
        self.is_livestreaming = False
        self.livestream_channel = None
        self.active_channel = None

        if not headless:
            self.menu()

    @staticmethod
    def get_host_default_interface_ip():
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(('8.8.8.8', 80))
            ip = s.getsockname()[0]
        except Exception as e:
            ip = '127.0.0.1'
            logging.error("Error when getting IP: %s", e)
        finally:
            s.close()
        return ip

    def _get_random_port(self):
        return random.randint(6000, 9000)

    def connect_to_tracker(self, TRACKER_IP, TRACKER_PORT):
        try:
            self.tracker_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.tracker_socket.connect((TRACKER_IP, TRACKER_PORT))
            request = json.dumps({
                "command": "CONNECT",
                "name": self.name,
                "ip": self.ip,
                "port": self.port
            })
            self.tracker_socket.sendall(request.encode('utf-8'))
            response = self.tracker_socket.recv(1024).decode('utf-8')
            response_data = json.loads(response)
            logging.info("Tracker response: %s", response_data.get('message', 'No response'))
        except Exception as e:
            logging.error("Unable to connect to Tracker: %s", e)
            self.tracker_socket = None

    def start_p2p_server(self):
        threading.Thread(target=self.p2p_server, daemon=True).start()

    def p2p_server(self):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            server_socket.bind((self.ip, self.port))
            server_socket.listen(5)
            logging.info("P2P SERVER listening on %s:%s", self.ip, self.port)
            while True:
                conn, addr = server_socket.accept()
                threading.Thread(target=self.handle_p2p_connection, args=(conn, addr), daemon=True).start()
        except Exception as e:
            logging.error("P2P server error: %s", e)
        finally:
            server_socket.close()

    def handle_p2p_connection(self, conn, addr):
        try:
            data = conn.recv(4096)
            if not data:
                logging.warning("No data received from %s", addr)
                return
            try:
                data_str = data.decode('utf-8')
                message_data = json.loads(data_str)
                msg_type = message_data.get("type", "chat")
                sender = message_data.get("sender", "Unknown")
                
                if msg_type == "livestream":
                    msg_channel = message_data.get("channel")
                    if not self.active_channel or self.active_channel != msg_channel:
                        logging.warning("Livestream not matching active channel: %s", msg_channel)
                        return
                    
                    frame_data = message_data.get("message", "")
                    try:
                        img_bytes = base64.b64decode(frame_data)
                        np_arr = np.frombuffer(img_bytes, np.uint8)
                        frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
                        if frame is not None:
                            threading.Thread(target=self.show_frame, args=(frame, sender)).start()
                        else:
                            logging.error("Failed to decode livestream frame from %s", sender)
                    except Exception as e:
                        logging.error("Error decoding livestream frame: %s", e)

                elif msg_type == "chat":
                    text = message_data.get("message", "")
                    readable_time = message_data.get("readable_time", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                    filename = f"sync_{self.active_channel}_{self.name}.txt"
                    filepath = os.path.join("local_sync", filename)
                    os.makedirs(os.path.dirname(filepath), exist_ok=True)
                    if not os.path.exists(filepath):
                        try:
                            with open(filepath, 'w', encoding='utf-8') as f:
                                f.write(f"{filename}\n")
                            logging.info("[INFO] Create new file: %s", filepath)
                        except Exception as e:
                            logging.error("[ERROR] Cannot create file: %s", e)

                    line = f"[{readable_time}] {sender}: {text}\n"
                    print(line)
                    try:
                        with open(filepath, 'a', encoding='utf-8') as f:
                            f.write(line)

                    except Exception as e:
                        logging.error("[SAVE_DOWN] Cannot save message: %s", e)

                    logging.info("[P2P MESSAGE] %s -> %s: %s", sender, self.name, text)

            except (json.JSONDecodeError, UnicodeDecodeError) as e:
                logging.error("Error handling received data from %s: %s", addr, e)

        except Exception as e:
            logging.error("Handling P2P connection error: %s", e)

        finally:
            conn.close()
    # Các method gửi chat qua tracker và P2P giữ nguyên, đảm bảo thêm 'channel' và 'owner' trong payload
    def send_chat_message_via_tracker(self, message):
        if self.tracker_socket is None:
            logging.error("No tracker connection. Chat message not sent: %s", message)
            return
        try:
            request = json.dumps({
                "command": "MSG_SEND",
                "ip": self.ip,
                "port": self.port,
                "name": self.name,
                "message": message
            })
            self.tracker_socket.sendall(request.encode('utf-8'))
            logging.info("Sent chat message via tracker: %s", message)
        except Exception as e:
            logging.error("Error sending chat message via tracker: %s", e)

    def send_message_p2p(self, target_ip, target_port, message, msg_type="chat"):
        payload = {
            "sender": self.name,
            "owner": self.name,
            "type": msg_type,
            "channel": self.active_channel,
            "message": message
        }
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((target_ip, target_port))
            s.sendall(json.dumps(payload).encode('utf-8'))
            s.close()
            logging.info("Sent %s to %s:%s in channel %s", msg_type, target_ip, target_port, self.active_channel)
        except Exception as e:
            logging.error("Failed to send %s to %s:%s: %s", msg_type, target_ip, target_port, e)

    def send_p2p_broadcast(self, message, msg_type="chat"):
        if msg_type == "chat":
            self.send_chat_message_via_tracker(message)
            return
        peers = self.get_peer_list()
        if not peers:
            logging.info("No peers available for P2P broadcast.")
            return
        for peer in peers:
            if peer["ip"] == self.ip and int(peer["port"]) == self.port:
                continue
            target_ip = peer["ip"]
            target_port = int(peer["port"])
            self.send_message_p2p(target_ip, target_port, message, msg_type)

    def send_udp_broadcast(self, message, msg_type="chat", channel=None):
        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            peers = self.get_peer_list()
            for peer in peers:
                if peer["ip"] == self.ip and int(peer["port"]) == self.port:
                    continue
                target_ip = peer["ip"]
                target_udp_port = int(peer["port"]) + 1  # Giả sử UDP port = TCP port + 1
                data_dict = {
                    "sender": self.name,
                    "type": msg_type,
                    "message": message
                }
                if msg_type == "livestream" and channel is not None:
                    data_dict["channel"] = channel
                data = json.dumps(data_dict)
                udp_socket.sendto(data.encode('utf-8'), (target_ip, target_udp_port))
                logging.info("Sent UDP %s message to %s:%s", msg_type, target_ip, target_udp_port)
        except Exception as e:
            logging.error("Error sending UDP broadcast: %s", e)
        finally:
            udp_socket.close()

    def start_livestream(self):
        if self.is_livestreaming:
            logging.info("Livestream already running.")
            return
        self.is_livestreaming = True
        self._stop_livestream_flag = False
        cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
        if not cap.isOpened():
            logging.error("Cannot access webcam for livestream.")
            self.is_livestreaming = False
            return
        logging.info("Starting livestream.")
        # Yêu cầu self.livestream_channel được set từ UI (là tên channel)
        while not self._stop_livestream_flag:
            ret, frame = cap.read()
            if not ret:
                logging.error("Failed to read frame from webcam.")
                break
            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 50]
            ret, buffer = cv2.imencode('.jpg', frame, encode_param)
            if not ret:
                logging.error("Failed to encode frame.")
                continue
            jpg_as_text = base64.b64encode(buffer).decode('utf-8')
            self.send_udp_broadcast(jpg_as_text, msg_type="livestream", channel=self.livestream_channel)
            cv2.imshow('Livestream (Local)', frame)
            cv2.waitKey(1)
            time.sleep(0.1)
        cap.release()
        cv2.destroyAllWindows()
        self.is_livestreaming = False
        logging.info("Livestream stopped.")

    # THÊM: Phương thức stop_livestream để dừng quá trình livestream
    def stop_livestream(self):
        if not self.is_livestreaming:
            logging.info("No livestream is running.")
            return
        logging.info("Stopping livestream.")
        self._stop_livestream_flag = True

    def udp_listener(self):
        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            udp_socket.bind((self.ip, self.udp_port))
            logging.info("UDP LISTENER listening on %s:%s for livestream.", self.ip, self.udp_port)
            while True:
                data, addr = udp_socket.recvfrom(65535)
                try:
                    data_str = data.decode('utf-8')
                    message_data = json.loads(data_str)
                    msg_type = message_data.get("type", "chat")
                    sender = message_data.get("sender", "Unknown")
                    if msg_type == "livestream":
                        msg_channel = message_data.get("channel")
                        if not self.active_channel or self.active_channel != msg_channel:
                            continue
                        frame_data = message_data.get("message", "")
                        img_bytes = base64.b64decode(frame_data)
                        np_arr = np.frombuffer(img_bytes, np.uint8)
                        frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
                        if frame is not None:
                            cv2.imshow(f"UDP Livestream from {sender}", frame)
                            cv2.waitKey(1)
                        else:
                            logging.error("Failed to decode UDP livestream frame from %s", sender)
                    else:
                        logging.info("Received non-livestream UDP message from %s", sender)
                except Exception as e:
                    logging.error("Error handling UDP data from %s: %s", addr, e)
        except Exception as e:
            logging.error("UDP listener error: %s", e)
        finally:
            udp_socket.close()

    def get_peer_list(self):
        if self.tracker_socket is None:
            logging.error("Not connected to tracker.")
            return []
        try:
            request = json.dumps({"command": "GET_LIST", "name": self.name})
            self.tracker_socket.sendall(request.encode('utf-8'))
            response = self.tracker_socket.recv(1024).decode('utf-8')
            response_data = json.loads(response)
            if response_data.get("status") == "OK":
                peer_list = response_data.get("peer_list", [])
                logging.info("Peer list retrieved:")
                for peer in peer_list:
                    logging.info(" - %s (%s:%s)", peer.get('name'), peer.get('ip'), peer.get('port'))
                return peer_list
            else:
                logging.error("Tracker error: %s", response_data.get('message', 'No error message'))
                return []
        except Exception as e:
            logging.error("Error retrieving peer list: %s", e)
            return []

    def leave_tracker(self):
        if self.tracker_socket is None:
            logging.error("Not connected to tracker.")
            return
        try:
            request = json.dumps({
                "command": "LEAVE",
                "name": self.name,
                "ip": self.ip,
                "port": self.port
            })
            self.tracker_socket.sendall(request.encode('utf-8'))
            response = self.tracker_socket.recv(1024).decode('utf-8')
            response_data = json.loads(response)
            logging.info("Tracker response on LEAVE: %s", response_data.get('message', 'No response'))
        except Exception as e:
            logging.error("Error leaving tracker: %s", e)
        finally:
            self.tracker_socket.close()
            self.tracker_socket = None

    def sync_online_message(self):
        user_data = self.users_collection.find_one({"username": self.username})
        
        if user_data:
            if user_data.get("state") == "online":
                logging.info(f"User {self.username} is online. You can now send or sync messages.")
                return True
            else:
                logging.info(f"User {self.username} is not online.")
                return False 
        else:
            logging.error(f"User {self.username} not found.")
            return False

    def sync_offline_messages(self):
        if os.path.exists(self.offline_file):
            try:
                with open(self.offline_file, 'r') as f:
                    lines = f.readlines()
                for line in lines:
                    try:
                        msg_obj = json.loads(line.strip())
                        if msg_obj.get("msg_type") == "chat":
                            continue
                        target_ip = msg_obj.get("target_ip")
                        target_port = msg_obj.get("target_port")
                        message = msg_obj.get("message")
                        msg_type = msg_obj.get("msg_type", "chat")
                        self.send_message_p2p(target_ip, target_port, message, msg_type)
                    except Exception as ex:
                        logging.error("Error syncing a message: %s", ex)
                os.remove(self.offline_file)
                logging.info("Offline messages synced and file removed.")
            except Exception as e:
                logging.error("Error syncing offline messages: %s", e)

    def start_udp_listener(self):
        threading.Thread(target=self.udp_listener, daemon=True).start()

    def menu(self):
        while True:
            print("\n===== MENU =====")
            print("0. Exit")
            print("1. Get Peer List (Client-Server)")
            print("2. Leave Network (Client-Server)")
            print("3. Chat via Tracker (Broadcast, Client-Server)")
            print("4. Send Direct Message via Tracker (One-to-One)")
            print("5. Start Livestream (UDP P2P)")
            choice = input("Choose an option: ")
            if choice == "0":
                self.leave_tracker()
                break
            elif choice == "1":
                self.get_peer_list()
            elif choice == "2":
                self.leave_tracker()
                break
            elif choice == "3":
                self.talk_to_tracker_chat()
            elif choice == "4":
                self.send_direct_message_menu()
            elif choice == "5":
                threading.Thread(target=self.start_livestream, daemon=True).start()
            else:
                logging.error("Invalid option. Please try again.")

    def talk_to_tracker_chat(self):
        if self.chat_history:
            print("==== Chat History ====")
            for msg in self.chat_history:
                print(msg)
            print("======================")
        self.isChatRunning = True
        chat_thread = threading.Thread(target=self.receive_tracker_message, daemon=True)
        chat_thread.start()
        self.send_tracker_message()

    def send_tracker_message(self):
        while self.isChatRunning:
            client_input = input("")
            if client_input.lower() == "\\exit":
                self.isChatRunning = False
                break
            else:
                local_msg = f"{self.name} >> {client_input}"
                self.chat_history.append(local_msg)
                logging.info("Tracker chat: %s", local_msg)
                request = json.dumps({
                    "command": "MSG_SEND",
                    "ip": self.ip,
                    "port": self.port,
                    "name": self.name,
                    "message": client_input
                })
                try:
                    if self.tracker_socket:
                        self.tracker_socket.sendall(request.encode('utf-8'))
                    else:
                        logging.error("Cannot send tracker message: No tracker connection.")
                except Exception as e:
                    logging.error("Error sending tracker message: %s", e)
                    break

    def receive_tracker_message(self):
        if self.tracker_socket is None:
            logging.error("No tracker connection to receive messages.")
            return
        while self.isChatRunning:
            try:
                server_message = self.tracker_socket.recv(1024).decode('utf-8')
                if not server_message.strip():
                    break
                data = json.loads(server_message)
                if data.get("command") == "MSG_RECV":
                    msg = f"{data['client_name']} >> {data['message']}"
                    self.chat_history.append(msg)
                    logging.info("Received tracker message: %s", msg)
                elif data.get("command") == "NOTIFY":
                    msg = f"[NOTIFY] {data['message']}"
                    self.chat_history.append(msg)
                    logging.info("Notification: %s", msg)
            except (json.JSONDecodeError, ConnectionResetError):
                logging.error("Lost connection to tracker.")
                break

    def send_direct_message_menu(self):
        peers = self.get_peer_list()
        if not peers:
            logging.info("No peers available for direct messaging.")
            return
        print("\nSelect a peer to send a direct message:")
        valid_peers = [peer for peer in peers if not (peer["ip"] == self.ip and int(peer["port"]) == self.port)]
        if not valid_peers:
            logging.info("No valid peers found for direct messaging.")
            return
        for idx, peer in enumerate(valid_peers):
            print(f"{idx}. {peer['name']} ({peer['ip']}:{peer['port']})")
        selection = input("Enter the index of the target peer: ")
        try:
            selection = int(selection)
            target = valid_peers[selection]
            message = input("Enter your message: ")
            self.send_chat_message_via_tracker(f"[DM to {target['name']}] {message}")
        except Exception as e:
            logging.error("Invalid selection or error: %s", e)

if __name__ == '__main__':
    # Lấy IP của máy tự động
    tracker_ip = USER.get_host_default_interface_ip()
    tracker_port = 5000  # Hoặc đặt thành biến nếu cần linh động

    USER(tracker_ip, tracker_port)