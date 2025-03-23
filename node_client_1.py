import socket
import time

TRACKER_IP = "127.0.0.1"  # Địa chỉ Tracker
TRACKER_PORT = 5000  # Cổng Tracker


def connect_to_tracker(peer_ip, peer_port):
    """Tạo kết nối duy trì với Tracker và đăng ký peer."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((TRACKER_IP, TRACKER_PORT))
    # Đăng ký với Tracker
    s.sendall(f"SEND {peer_ip} {peer_port}".encode('utf-8'))
    response = s.recv(1024).decode('utf-8')
    print(f"[INFO] Tracker response: {response}")
    return s


def get_peer_list(s):
    """Gửi lệnh GET_LIST qua kết nối duy trì và nhận danh sách peer."""
    s.sendall(b"GET_LIST")
    response = s.recv(1024).decode('utf-8')
    print(f"[INFO] Peer list: {response}")
    return response.replace("PEER_LIST ", "").strip().split(",") if response.startswith("PEER_LIST") else []


def leave_tracker(s, peer_ip, peer_port):
    """Gửi lệnh LEAVE để hủy đăng ký và rời tracker."""
    s.sendall(f"LEAVE {peer_ip} {peer_port}".encode('utf-8'))
    response = s.recv(1024).decode('utf-8')
    print(f"[INFO] Tracker response: {response}")


def peer_client(target_ip, target_port, message):
    """Kết nối tới peer khác để gửi dữ liệu."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            print(f"[DEBUG] Connecting to {target_ip}:{target_port}...")
            s.connect((target_ip, int(target_port)))
            s.sendall(f"DATA {message}".encode('utf-8'))
            response = s.recv(1024).decode('utf-8')
            print(f"[INFO] Response from Peer: {response}")
    except Exception as e:
        print(f"[ERROR] Could not connect to {target_ip}:{target_port} - {e}")



if __name__ == "__main__":
    # peer_ip = "192.168.1.101"  # Địa chỉ IP của Peer
    peer_ip="127.0.0.1"
    peer_port = 8081  # Cổng Peer

    # Tạo kết nối duy trì đến Tracker
    tracker_socket = connect_to_tracker(peer_ip, peer_port)

    try:
        while True:
            # Gửi yêu cầu GET_LIST qua kết nối duy trì
            peer_list = get_peer_list(tracker_socket)
            if peer_list and peer_list[0]:
                target = peer_list[0].split(":")
                if len(target) == 2:
                    peer_client(target[0], target[1], "Hello from Peer!")
            time.sleep(10)  # Chờ 10 giây trước khi gửi yêu cầu tiếp
    except KeyboardInterrupt:
        print("\n[INFO] Rời khỏi mạng...")
        leave_tracker(tracker_socket, peer_ip, peer_port)
        tracker_socket.close()
        print("[INFO] Đã thoát.")
