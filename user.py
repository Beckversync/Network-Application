import socket
import threading
import json
import os

class USER:
    def __init__(self, TRACKER_IP, TRACKER_PORT):
        self.TRACKER_IP = TRACKER_IP
        self.TRACKER_PORT = TRACKER_PORT
        self.name = input("ENTER YOUR NAME: ")
        self.ip = input("ENTER YOUR IP (Nhấn Enter để dùng mặc định 127.0.0.1): ") or "127.0.0.1"
        self.port = input("ENTER YOUR PORT: ")

        self.tracker_socket = None
        self.connect_to_tracker()

        self.isChatRunning = False

        self.menu()

# ========== TRACKER TASK ==========

    def connect_to_tracker(self):
        """Kết nối và đăng ký với Tracker."""
        try:
            self.tracker_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.tracker_socket.connect((self.TRACKER_IP, self.TRACKER_PORT))

            request = json.dumps({
                "command": "CONNECT",
                "name": self.name,
                "ip": self.ip,
                "port": self.port
            })
            self.tracker_socket.sendall(request.encode('utf-8'))

            response = self.tracker_socket.recv(1024).decode('utf-8')
            response_data = json.loads(response)

            print(f"[INFO] Tracker response: {response_data.get('message', 'Không có phản hồi')}")
        except Exception as e:
            print(f"[ERROR] Không thể kết nối đến Tracker: {e}")
            self.tracker_socket = None

    def get_peer_list(self):
        """Lấy danh sách peer từ Tracker."""
        if self.tracker_socket is None:
            print("[ERROR] Chưa kết nối đến tracker.")
            return []

        try:
            request = json.dumps({"command": "GET_LIST", "name": self.name})
            self.tracker_socket.sendall(request.encode('utf-8'))

            response = self.tracker_socket.recv(1024).decode('utf-8')
            response_data = json.loads(response)

            if response_data.get("status") == "OK":
                peer_list = response_data.get("peer_list", [])
                print("[INFO] Danh sách peer:")
                for peer in peer_list:
                    print(f" - {peer['name']} ({peer['ip']}:{peer['port']})")
                return peer_list
            else:
                print(f"[ERROR] Tracker trả về lỗi: {response_data.get('message', 'Không có thông báo lỗi')}")
                return []

        except Exception as e:
            print(f"[ERROR] Lỗi khi lấy danh sách peer: {e}")
            return []

    def leave_tracker(self):
        """Gửi yêu cầu rời khỏi tracker."""
        if self.tracker_socket is None:
            print("[ERROR] Chưa kết nối đến tracker.")
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
            print(f"[INFO] Tracker response: {response_data.get('message', 'Không có phản hồi')}")

        except Exception as e:
            print(f"[ERROR] Lỗi khi rời khỏi tracker: {e}")

        finally:
            self.tracker_socket.close()
            self.tracker_socket = None

# ========== CHAT TASK ==========

    def send_message(self):
        """Gửi tin nhắn"""
        while self.isChatRunning:
            client_input = input("")
            if client_input.lower() == "\exit":
                self.isChatRunning = False
                self.tracker_socket.sendall("OUTCHAT" .encode('utf-8'))
                break
                #self.leave_tracker()
                #os._exit(0)
            else:
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
                    print(f"[ERROR] Lỗi khi gửi tin nhắn: {e}")
                    break

    def receive_message(self):
        """Nhận tin nhắn từ server"""
        if self.tracker_socket is None:
            print("[ERROR] Không có kết nối socket, không thể nhận tin nhắn.")
            return

        while self.isChatRunning:
            try:
                server_message = self.tracker_socket.recv(1024).decode()
                if not server_message.strip():
                    break
                
                # Parse JSON từ server
                data = json.loads(server_message)
                
                if data.get("command") == "MSG_RECV":
                    print(f"\033[1;34m{data['client_name']} >> {data['message']}\033[0m")

                elif data.get("command") == "NOTIFY":
                    print(f"\033[1;32m[NOTIFY] {data['message']}\033[0m")

            except (json.JSONDecodeError, ConnectionResetError):
                print("[ERROR] Mất kết nối với server.")
                break

    def talk_to_server(self):
        """Bắt đầu chat với server"""
        self.isChatRunning = True
        threading.Thread(target=self.receive_message, daemon=True).start()
        self.send_message()

# ========== CHANNEL ==========








# ========== MENU TASK ==========

    def menu(self):
        """Hiển thị menu tùy chọn"""
        while True:
            print("\n===== MENU =====")
            print("0. Thoát")
            print("1. Lấy danh sách peer")
            print("2. Rời khỏi mạng")
            print("3. Gửi tin nhắn")
            choice = input("Chọn một tùy chọn: ")

            if choice == "0":
                self.leave_tracker()
                break
            elif choice == "1":
                self.get_peer_list()
            elif choice == "2":
                self.leave_tracker()
                break
            elif choice == "3":
                self.talk_to_server()
            else:
                print("[ERROR] Lựa chọn không hợp lệ. Hãy nhập lại.")

if __name__ == '__main__':
    USER("127.0.0.1", 5000)
