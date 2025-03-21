import socket

TRACKER_IP = "127.0.0.1"  # Địa chỉ Tracker
TRACKER_PORT = 5000        # Cổng Tracker

def register_with_tracker(peer_ip, peer_port):
    """Gửi thông tin Peer lên Tracker"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((TRACKER_IP, TRACKER_PORT))
        s.sendall(f"SEND {peer_ip} {peer_port}".encode('utf-8'))
        response = s.recv(1024).decode('utf-8')
        print(f"[INFO] Tracker response: {response}")

def get_peer_list():
    """Nhận danh sách Peer từ Tracker"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((TRACKER_IP, TRACKER_PORT))
        s.sendall(b"GET_LIST")
        response = s.recv(1024).decode('utf-8')
        print(f"[INFO] Peer list: {response}")
        return response.replace("PEER_LIST ", "").split(",")

def peer_client(target_ip, target_port, message):
    """Gửi dữ liệu đến Peer khác"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((target_ip, int(target_port)))
        s.sendall(f"DATA {message}".encode('utf-8'))
        response = s.recv(1024).decode('utf-8')
        print(f"[INFO] Response from Peer: {response}")

if __name__ == "__main__":
    peer_ip = "192.168.1.101"  # Địa chỉ IP của Peer
    peer_port = 8081            # Cổng Peer

    # Đăng ký với Tracker
    register_with_tracker(peer_ip, peer_port)

    # Lấy danh sách Peer
    peer_list = get_peer_list()

    # Kết nối và gửi dữ liệu đến Peer khác
    if peer_list:
        target = peer_list[0].split(":")
        peer_client(target[0], target[1], "Hello from Peer!")
