import socket

TRACKER_IP = "127.0.0.1"
TRACKER_PORT = 5000


def connect_to_tracker(peer_ip, peer_port):
    """Kết nối và đăng ký với Tracker."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((TRACKER_IP, TRACKER_PORT))
    s.sendall(f"SEND {peer_ip} {peer_port}".encode('utf-8'))
    response = s.recv(1024).decode('utf-8')
    print(f"[INFO] Tracker response: {response}")
    return s


def get_peer_list(s):
    """Lấy danh sách peer từ Tracker."""
    s.sendall(b"GET_LIST")
    response = s.recv(1024).decode('utf-8')
    print(f"[INFO] Peer list: {response}")
    return response.replace("PEER_LIST ", "").strip().split(",") if response.startswith("PEER_LIST") else []


def peer_client(target_ip, target_port, message):
    """Kết nối và gửi tin nhắn đến peer khác."""
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
    peer_ip = "127.0.0.1"
    peer_port = 8081

    tracker_socket = connect_to_tracker(peer_ip, peer_port)

    try:
        while True:
            print("\n=== MENU ===")
            print("1. Xem danh sách peer")
            print("2. Gửi tin nhắn đến peer")
            print("3. Thoát")

            choice = input("Chọn một hành động: ")

            if choice == "1":
                peer_list = get_peer_list(tracker_socket)
                if not peer_list or peer_list[0] == "":
                    print("[INFO] Không có peer nào đang online.")
                else:
                    for i, peer in enumerate(peer_list):
                        print(f"{i + 1}. {peer}")

            elif choice == "2":
                peer_list = get_peer_list(tracker_socket)
                if not peer_list or peer_list[0] == "":
                    print("[INFO] Không có peer nào để gửi tin nhắn.")
                    continue

                print("Nhập tin nhắn để gửi đến tất cả peers:")
                message = input("> ")

                for peer in peer_list:
                    try:
                        target = peer.split(":")
                        if len(target) == 2:
                            peer_client(target[0], target[1], message)
                    except Exception as e:
                        print(f"[ERROR] Không thể gửi đến {peer} - {e}")


            elif choice == "3":
                print("[INFO] Đang thoát...")
                tracker_socket.sendall(f"LEAVE {peer_ip} {peer_port}".encode('utf-8'))
                tracker_socket.close()
                break

            else:
                print("[ERROR] Vui lòng nhập số từ 1 đến 3.")

    except KeyboardInterrupt:
        print("\n[INFO] Rời khỏi mạng...")
        tracker_socket.sendall(f"LEAVE {peer_ip} {peer_port}".encode('utf-8'))
        tracker_socket.close()
        print("[INFO] Đã thoát.")
