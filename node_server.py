import socket
import threading

def peer_server(port):
    """Peer mở server để nhận dữ liệu"""
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("0.0.0.0", port))
    server.listen(5)
    print(f"[START] Peer server running on port {port}")

    while True:
        conn, addr = server.accept()
        with conn:
            print(f"[NEW CONNECTION] from {addr}")
            data = conn.recv(1024).decode('utf-8')
            if data.startswith("DATA"):
                print(f"[RECEIVED] {data[5:]}")
                conn.sendall(b"RECEIVED")

if __name__ == "__main__":
    peer_port = 8081  # Cổng Peer server
    threading.Thread(target=peer_server, args=(peer_port,)).start()
