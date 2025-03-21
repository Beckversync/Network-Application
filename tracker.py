import socket
import threading

# Danh sách lưu các peer đang hoạt động
peer_list = []

def handle_client(conn, addr):
    global peer_list
    with conn:
        print(f"[INFO] Kết nối từ {addr}")

        while True:
            try:
                data = conn.recv(1024).decode('utf-8')
                if not data:
                    break

                command = data.split()
                if command[0] == "SEND":
                    # Thêm Peer vào danh sách
                    ip, port = command[1], command[2]
                    peer_list.append((ip, port))
                    conn.sendall(b"OK")

                elif command[0] == "GET_LIST":
                    # Trả danh sách peer về
                    response = "PEER_LIST " + ",".join([f"{ip}:{port}" for ip, port in peer_list])
                    conn.sendall(response.encode('utf-8'))

            except Exception as e:
                print(f"[ERROR] Lỗi: {e}")
                break

def tracker_server(host="0.0.0.0", port=5000):
    """Chạy server Tracker"""
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((host, port))
    server.listen(5)
    print(f"[START] Tracker đang lắng nghe trên {host}:{port}")

    while True:
        conn, addr = server.accept()
        threading.Thread(target=handle_client, args=(conn, addr)).start()

if __name__ == "__main__":
    tracker_server()
