import socket
import threading
import json
import os
import cv2
import numpy as np
import base64
import time
import random

class USER:
    def __init__(self, TRACKER_IP, TRACKER_PORT, headless=False, username=None, port=None):
        # Nếu đã cung cấp username thì dùng luôn, nếu không thì yêu cầu nhập từ terminal
        if username is not None:
            self.name = username
        else:
            self.name = input("ENTER YOUR NAME: ")
        
        # Dùng IP mặc định
        self.ip = "127.0.0.1"
        
        # Nếu ở chế độ headless, tự động chọn port (nếu chưa được chỉ định)
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
        self.chat_history = []  # Lưu trữ lịch sử chat
        self.isChatRunning = False
        
        # Nếu không ở chế độ headless, hiển thị menu terminal
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
            print(f"[INFO] Tracker response: {response_data.get('message', 'No response')}")
        except Exception as e:
            print(f"[ERROR] Unable to connect to Tracker: {e}")
            self.tracker_socket = None

    def start_p2p_server(self):
        threading.Thread(target=self.p2p_server, daemon=True).start()

    def p2p_server(self):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            server_socket.bind((self.ip, self.port))
            server_socket.listen(5)
            print(f"[P2P SERVER] Listening on {self.ip}:{self.port} for direct P2P connections.")
            while True:
                conn, addr = server_socket.accept()
                threading.Thread(target=self.handle_p2p_connection, args=(conn, addr), daemon=True).start()
        except Exception as e:
            print(f"[ERROR] P2P server error: {e}")
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
                            print(f"[ERROR] Failed to decode livestream frame from {sender}")
                    else:
                        text = message_data.get("message", "")
                        print(f"\033[1;35m[P2P MESSAGE] {sender} -> {self.name}: {text}\033[0m")
                except Exception as e:
                    print(f"[ERROR] Error handling received P2P data: {e}")
        except Exception as e:
            print(f"[ERROR] Handling P2P connection error: {e}")
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
            print(f"[INFO] Sent {msg_type} message to {target_ip}:{target_port}")
        except Exception as e:
            print(f"[ERROR] Failed to send {msg_type} message to {target_ip}:{target_port}: {e}")

    def send_p2p_broadcast(self, message, msg_type="chat"):
        peers = self.get_peer_list()
        if not peers:
            print("[INFO] No peers available for P2P broadcast.")
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
            print(f"[INFO] Sent UDP {msg_type} message to {target_ip}:{target_udp_port}")
        except Exception as e:
            print(f"[ERROR] Failed to send UDP {msg_type} message to {target_ip}:{target_udp_port}: {e}")

    def send_udp_broadcast(self, message, msg_type="livestream"):
        peers = self.get_peer_list()
        if not peers:
            print("[INFO] No peers available for UDP broadcast.")
            return
        for peer in peers:
            if peer["ip"] == self.ip and int(peer["port"]) == self.port:
                continue
            target_ip = peer["ip"]
            target_udp_port = int(peer["port"]) + 1
            self.send_udp_message(target_ip, target_udp_port, message, msg_type)

    def get_peer_list(self):
        if self.tracker_socket is None:
            print("[ERROR] Not connected to tracker.")
            return []
        try:
            request = json.dumps({"command": "GET_LIST", "name": self.name})
            self.tracker_socket.sendall(request.encode('utf-8'))
            response = self.tracker_socket.recv(1024).decode('utf-8')
            response_data = json.loads(response)
            if response_data.get("status") == "OK":
                peer_list = response_data.get("peer_list", [])
                print("[INFO] Peer list:")
                for peer in peer_list:
                    print(f" - {peer['name']} ({peer['ip']}:{peer['port']})")
                return peer_list
            else:
                print(f"[ERROR] Tracker error: {response_data.get('message', 'No error message')}")
                return []
        except Exception as e:
            print(f"[ERROR] Error retrieving peer list: {e}")
            return []

    def leave_tracker(self):
        if self.tracker_socket is None:
            print("[ERROR] Not connected to tracker.")
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
            print(f"[INFO] Tracker response: {response_data.get('message', 'No response')}")
        except Exception as e:
            print(f"[ERROR] Error leaving tracker: {e}")
        finally:
            self.tracker_socket.close()
            self.tracker_socket = None

    def start_udp_listener(self):
        threading.Thread(target=self.udp_listener, daemon=True).start()

    def udp_listener(self):
        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            udp_socket.bind((self.ip, self.udp_port))
            print(f"[UDP LISTENER] Listening on {self.ip}:{self.udp_port} for UDP livestream.")
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
                            print(f"[ERROR] Failed to decode UDP livestream frame from {sender}")
                    else:
                        print(f"[INFO] Received non-livestream UDP message from {sender}")
                except Exception as e:
                    print(f"[ERROR] Error handling UDP data from {addr}: {e}")
        except Exception as e:
            print(f"[ERROR] UDP listener error: {e}")
        finally:
            udp_socket.close()

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
                print("[ERROR] Invalid option. Please try again.")

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
                local_msg = f"\033[1;33m{self.name} >> {client_input}\033[0m"
                self.chat_history.append(local_msg)
                if self.isChatRunning:
                    print(local_msg)
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
                    print(f"[ERROR] Error sending message: {e}")
                    break

    def receive_tracker_message(self):
        if self.tracker_socket is None:
            print("[ERROR] No tracker connection to receive messages.")
            return
        while self.isChatRunning:
            try:
                server_message = self.tracker_socket.recv(1024).decode('utf-8')
                if not server_message.strip():
                    break
                data = json.loads(server_message)
                if data.get("command") == "MSG_RECV":
                    msg = f"\033[1;34m{data['client_name']} >> {data['message']}\033[0m"
                    self.chat_history.append(msg)
                    if self.isChatRunning:
                        print(msg)
                elif data.get("command") == "NOTIFY":
                    msg = f"\033[1;32m[NOTIFY] {data['message']}\033[0m"
                    self.chat_history.append(msg)
                    if self.isChatRunning:
                        print(msg)
            except (json.JSONDecodeError, ConnectionResetError):
                print("[ERROR] Lost connection to tracker.")
                break

    def send_direct_message_menu(self):
        peers = self.get_peer_list()
        if not peers:
            print("[INFO] No peers available for direct messaging.")
            return
        print("\nSelect a peer to send a direct message:")
        valid_peers = []
        for peer in peers:
            if peer["ip"] == self.ip and int(peer["port"]) == self.port:
                continue
            valid_peers.append(peer)
        if not valid_peers:
            print("[INFO] No valid peers found for direct messaging.")
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
            print(f"[ERROR] Invalid selection or error: {e}")

    def start_livestream(self):
        cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
        if not cap.isOpened():
            print("[ERROR] Cannot access webcam for livestream.")
            return
        print("[LIVESTREAM] Starting livestream. Press 'q' in the video window to stop.")
        while True:
            ret, frame = cap.read()
            if not ret:
                print("[ERROR] Failed to read frame from webcam.")
                break
            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 50]
            ret, buffer = cv2.imencode('.jpg', frame, encode_param)
            if not ret:
                print("[ERROR] Failed to encode frame.")
                continue
            jpg_as_text = base64.b64encode(buffer).decode('utf-8')
            self.send_udp_broadcast(jpg_as_text, msg_type="livestream")
            cv2.imshow('Livestream (Local)', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
            time.sleep(0.1)
        cap.release()
        cv2.destroyAllWindows()

if __name__ == '__main__':
    USER("127.0.0.1", 5000)
