import socket
import threading
import json


class TRACKER:
    def __init__(self, host="127.0.0.1", port=5000):
        self.peer_list = []  # Danh sách các peer đang kết nối
        self.peer_list_lock = threading.Lock()  # Lock để bảo vệ truy cập danh sách
        self.tracker_server(host, port)  # Khởi động server

    def handle_client(self, conn, addr):
        """Xử lý client kết nối đến tracker"""
        print(f"[INFO] Kết nối mới từ {addr}")
    
        try:
            while True:
                data = conn.recv(1024).decode('utf-8').strip()
                if not data:
                    break

                try:
                    command = json.loads(data)  # Giải mã JSON
                except json.JSONDecodeError:
                    conn.sendall(json.dumps({"status": "ERROR", "message": "Dữ liệu không hợp lệ"}).encode('utf-8'))
                    continue

                if "command" not in command:
                    conn.sendall(json.dumps({"status": "ERROR", "message": "Thiếu lệnh"}).encode('utf-8'))
                    continue

                cmd = command["command"]

                if cmd == "CONNECT":
                    if not all(k in command for k in ["name", "ip", "port"]):
                        conn.sendall(json.dumps({"status": "ERROR", "message": "Thiếu thông tin cần thiết"}).encode('utf-8'))
                        continue

                    name, ip, port = command["name"], command["ip"], command["port"]

                    with self.peer_list_lock:
                        if not any(n == name and i == ip and p == port for n, i, p, _ in self.peer_list):
                            self.peer_list.append((name, ip, port, conn))
                            print(f"[INFO] Đã thêm peer: {name} ({ip}:{port})")
                            response = {"status": "OK", "message": f"Peer {name} ({ip}:{port}) đã được thêm"}
                        else:
                            response = {"status": "OK", "message": f"Peer {name} ({ip}:{port}) đã tồn tại"}

                    conn.sendall(json.dumps(response).encode('utf-8'))

                elif cmd == "GET_LIST":
                    if "name" not in command:
                        conn.sendall(json.dumps({"status": "ERROR", "message": "Thiếu thông tin cần thiết"}).encode('utf-8'))
                        continue

                    with self.peer_list_lock:
                        peer_data = [{"name": n, "ip": i, "port": p} for n, i, p, _ in self.peer_list]

                    response = {"status": "OK", "peer_list": peer_data}
                    conn.sendall(json.dumps(response).encode('utf-8'))
                    print(f"[INFO] Gửi danh sách peer đến {command['name']}")

                elif cmd == "LEAVE":
                    if not all(k in command for k in ["name", "ip", "port"]):
                        conn.sendall(json.dumps({"status": "ERROR", "message": "Thiếu thông tin cần thiết"}).encode('utf-8'))
                        continue

                    name, ip, port = command["name"], command["ip"], command["port"]

                    with self.peer_list_lock:
                        for peer in self.peer_list:
                            if peer[:3] == (name, ip, port):  # So sánh 3 phần tử đầu
                                self.peer_list.remove(peer)
                                print(f"[INFO] Peer {name} ({ip}:{port}) đã rời khỏi tracker.")
                                response = {"status": "OK", "message": f"Peer {name} ({ip}:{port}) đã rời đi"}
                                break
                        else:
                            response = {"status": "ERROR", "message": f"Peer {name} ({ip}:{port}) không tồn tại"}

                    conn.sendall(json.dumps(response).encode('utf-8'))

                elif cmd == "MSG_SEND":
                    if not all(k in command for k in ["ip", "port", "name", "message"]):
                        conn.sendall(json.dumps({"status": "ERROR", "message": "Thiếu thông tin cần thiết"}).encode('utf-8'))
                        continue

                    name, ip, port, message = command["name"], command["ip"], command["port"], command["message"]
                    print(f"[CHAT] {name}: {message}")

                    with self.peer_list_lock:
                        disconnected_peers = []
                        for name_list, ip_list, port_list, peer_conn in self.peer_list:
                            if ip == ip_list and port == port_list:
                                continue  # Không gửi lại cho người gửi

                            try:
                                json_message = json.dumps({
                                    "command": "MSG_RECV",
                                    "client_name": name,
                                    "message": message
                                })

                                peer_conn.sendall(json_message.encode('utf-8'))
                                print(f"[INFO] Đã gửi tin nhắn đến {name_list} ({ip_list}:{port_list})")

                            except Exception:
                                print(f"[ERROR] Không thể gửi tin nhắn đến {name_list} ({ip_list}:{port_list})")
                                disconnected_peers.append((name_list, ip_list, port_list, peer_conn))

                        # Xóa các peer đã mất kết nối
                        for peer in disconnected_peers:
                            self.peer_list.remove(peer)
                            print(f"[INFO] Xóa peer không còn kết nối: {peer[0]} ({peer[1]}:{peer[2]})")

                else:
                    conn.sendall(json.dumps({"status": "ERROR", "message": "Lệnh không hợp lệ"}).encode('utf-8'))

        except Exception as e:
            print(f"[ERROR] Lỗi xử lý client: {e}")

        finally:
            conn.close()
            print(f"🔴 Kết nối với {addr} đã đóng.")

    def tracker_server(self, host="127.0.0.1", port=5000):
        """Khởi động tracker server"""
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((host, port))
        server.listen(5)
        print(f"[START] Tracker đang lắng nghe trên {host}:{port}")

        while True:
            conn, addr = server.accept()
            threading.Thread(target=self.handle_client, args=(conn, addr), daemon=True).start()


if __name__ == "__main__":
    TRACKER()
