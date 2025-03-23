import socket
import threading

def peer_server(port):
    """Peer mở server để nhận dữ liệu"""
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("0.0.0.0", port))  # Lắng nghe trên tất cả các IP
    server.listen(5)
    print(f"[START] Peer server running on port {port}")

    while True:
        try:
            conn, addr = server.accept()
            print(f"[NEW CONNECTION] from {addr}")
            with conn:
                data = conn.recv(1024).decode('utf-8')
                print(f"[DEBUG] Received data: {data}")
                if data.startswith("DATA"):
                    print(f"[RECEIVED] {data[5:]}")
                    conn.sendall(b"RECEIVED")
                else:
                    print("[DEBUG] Unexpected data format")
        except Exception as e:
            print(f"[ERROR] {e}")


if __name__ == "__main__":
    peer_port = 8081  # Cổng Peer server
    threading.Thread(target=peer_server, args=(peer_port,)).start()
