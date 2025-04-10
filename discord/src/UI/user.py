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

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s')

class USER:
    def __init__(self, TRACKER_IP, TRACKER_PORT, headless=False, username=None, port=None):
        # Nếu không truyền username thì nhập từ bàn phím
        if username is not None:
            self.name = username
        else:
            self.name = input("ENTER YOUR NAME: ")

        self.ip = "127.0.0.1"
        if headless:
            if port is not None:
                self.port = port
            else:
                self.port = self._get_random_port()
        else:
            self.port = int(input("ENTER YOUR PORT (TCP): "))

        self.udp_port = self.port + 1
        self.tracker_socket = None
        self.connect_to_tracker(TRACKER_IP, TRACKER_PORT)
        self.start_p2p_server()
        self.start_udp_listener()
        self.chat_history = []  # Lịch sử chat
        self.isChatRunning = False

        # Offline caching: file lưu tin nhắn chưa đồng bộ (các tin tin P2P không gửi được)
        self.offline_file = f"offline_{self.name}.txt"
        self.sync_offline_messages()

        # Các thuộc tính hỗ trợ livestream:
        self._stop_livestream_flag = False  # Cờ dừng livestream
        self.is_livestreaming = False       # Trạng thái livestream

        if not headless:
            self.menu()

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
            if data:
                try:
                    data_str = data.decode('utf-8')
                    message_data = json.loads(data_str)
                    msg_type = message_data.get("type", "chat")
                    sender = message_data.get("sender", "Unknown")
                    if msg_type == "livestream":
                        frame_data = message_data.get("message", "")
                        img_bytes = base64.b64decode(frame_data)
                        np_arr = np.frombuffer(img_bytes, np.uint8)
                        frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
                        if frame is not None:
                            cv2.imshow(f"Livestream from {sender}", frame)
                            cv2.waitKey(1)
                        else:
                            logging.error("Failed to decode livestream frame from %s", sender)
                    else:
                        text = message_data.get("message", "")
                        logging.info("[P2P MESSAGE] %s -> %s: %s", sender, self.name, text)
                except Exception as e:
                    logging.error("Error handling received P2P data: %s", e)
        except Exception as e:
            logging.error("Handling P2P connection error: %s", e)
        finally:
            conn.close()

    def send_message_p2p(self, target_ip, target_port, message, msg_type="chat"):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((target_ip, target_port))
            message_data = json.dumps({
                "sender": self.name,
                "type": msg_type,
                "message": message
            })
            s.sendall(message_data.encode('utf-8'))
            s.close()
            logging.info("Sent %s message to %s:%s", msg_type, target_ip, target_port)
        except Exception as e:
            logging.error("Failed to send %s message to %s:%s: %s", msg_type, target_ip, target_port, e)
            self.store_offline_message({"target_ip": target_ip, "target_port": target_port, "message": message, "msg_type": msg_type})

    def send_p2p_broadcast(self, message, msg_type="chat"):
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

    def send_udp_message(self, target_ip, target_udp_port, message, msg_type="livestream"):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            message_data = json.dumps({
                "sender": self.name,
                "type": msg_type,
                "message": message
            })
            s.sendto(message_data.encode('utf-8'), (target_ip, target_udp_port))
            s.close()
            logging.info("Sent UDP %s message to %s:%s", msg_type, target_ip, target_udp_port)
        except Exception as e:
            logging.error("Failed to send UDP %s message to %s:%s: %s", msg_type, target_ip, target_udp_port, e)

    def send_udp_broadcast(self, message, msg_type="livestream"):
        peers = self.get_peer_list()
        if not peers:
            logging.info("No peers available for UDP broadcast.")
            return
        for peer in peers:
            if peer["ip"] == self.ip and int(peer["port"]) == self.port:
                continue
            target_ip = peer["ip"]
            target_udp_port = int(peer["port"]) + 1
            self.send_udp_message(target_ip, target_udp_port, message, msg_type)

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

    def start_udp_listener(self):
        threading.Thread(target=self.udp_listener, daemon=True).start()

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

    def store_offline_message(self, msg_obj):
        try:
            with open(self.offline_file, 'a') as f:
                f.write(json.dumps(msg_obj) + "\n")
            logging.info("Stored offline message: %s", msg_obj)
        except Exception as e:
            logging.error("Error storing offline message: %s", e)

    def sync_offline_messages(self):
        if os.path.exists(self.offline_file):
            try:
                with open(self.offline_file, 'r') as f:
                    lines = f.readlines()
                for line in lines:
                    try:
                        msg_obj = json.loads(line.strip())
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

    def menu(self):
        while True:
            print("\n===== MENU =====")
            print("0. Exit")
            print("1. Get Peer List (Client-Server)")
            print("2. Leave Network (Client-Server)")
            print("3. Send Message via Tracker (Broadcast, Client-Server)")
            print("4. Send Direct P2P Message (One-to-One)")
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
                    self.tracker_socket.sendall(request.encode('utf-8'))
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
            target_ip = target["ip"]
            target_port = int(target["port"])
            message = input("Enter your message: ")
            self.send_message_p2p(target_ip, target_port, message, msg_type="chat")
        except Exception as e:
            logging.error("Invalid selection or error: %s", e)

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
            self.send_udp_broadcast(jpg_as_text, msg_type="livestream")
            cv2.imshow('Livestream (Local)', frame)
            cv2.waitKey(1)
            time.sleep(0.1)
        cap.release()
        cv2.destroyAllWindows()
        self.is_livestreaming = False
        logging.info("Livestream stopped.")

    def stop_livestream(self):
        if not self.is_livestreaming:
            logging.info("No livestream to stop.")
            return
        logging.info("Stopping livestream.")
        self._stop_livestream_flag = True

if __name__ == '__main__':
    USER("127.0.0.1", 5000)
