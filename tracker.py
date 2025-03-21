# import socket
# import threading

# # Danh sách lưu các peer đang hoạt động
# peer_list = []

# def handle_client(conn, addr):
#     global peer_list
#     with conn:
#         print(f"[INFO] Kết nối từ {addr}")

#         while True:
#             try:
#                 data = conn.recv(1024).decode('utf-8')
#                 if not data:
#                     break

#                 command = data.split()
#                 if command[0] == "SEND":
#                     # Thêm Peer vào danh sách
#                     ip, port = command[1], command[2]
#                     peer_list.append((ip, port))
#                     conn.sendall(b"OK")

#                 elif command[0] == "GET_LIST":
#                     # Trả danh sách peer về
#                     response = "PEER_LIST " + ",".join([f"{ip}:{port}" for ip, port in peer_list])
#                     conn.sendall(response.encode('utf-8'))

#             except Exception as e:
#                 print(f"[ERROR] Lỗi: {e}")
#                 break

# def tracker_server(host="0.0.0.0", port=5000):
#     """Chạy server Tracker"""
#     server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#     server.bind((host, port))
#     server.listen(5)
#     print(f"[START] Tracker đang lắng nghe trên {host}:{port}")

#     while True:
#         conn, addr = server.accept()
#         threading.Thread(target=handle_client, args=(conn, addr)).start()

# if __name__ == "__main__":
#     tracker_server()

###***UPDATE***###

import socket
import threading

# Danh sách lưu các peer đang hoạt động và Lock bảo vệ truy cập
peer_list = []
peer_list_lock = threading.Lock()

def handle_client(conn, addr):
    global peer_list
    added_peer = None  # Lưu peer đã được thêm từ lệnh SEND
    with conn:
        print(f"[INFO] Kết nối từ {addr}")
        while True:
            try:
                data = conn.recv(1024).decode('utf-8').strip()
                if not data:
                    break

                command = data.split()
                if not command:
                    continue

                if command[0] == "SEND":
                    if len(command) < 3:
                        conn.sendall("ERROR: Cú pháp SEND <peer_ip> <peer_port>")
                        continue

                    ip, port = command[1], command[2]
                    with peer_list_lock:
                        if (ip, port) not in peer_list:
                            peer_list.append((ip, port))
                            added_peer = (ip, port)
                            print(f"[INFO] Đã thêm peer: {(ip, port)}")
                        else:
                            print(f"[INFO] Peer {(ip, port)} đã tồn tại.")
                    conn.sendall(b"OK")

                elif command[0] == "GET_LIST":
                    with peer_list_lock:
                        response = "PEER_LIST " + ",".join([f"{ip}:{port}" for ip, port in peer_list])
                    conn.sendall(response.encode('utf-8'))

                elif command[0] == "LEAVE":
                    if len(command) < 3:
                        conn.sendall("ERROR: Cú pháp LEAVE <peer_ip> <peer_port>")
                        continue

                    ip, port = command[1], command[2]
                    with peer_list_lock:
                        if (ip, port) in peer_list:
                            peer_list.remove((ip, port))
                            print(f"[INFO] Đã xóa peer: {(ip, port)}")
                    conn.sendall(b"OK")

                else:
                    conn.sendall("ERROR: Lệnh không được hỗ trợ")

            except Exception as e:
                print(f"[ERROR] Lỗi: {e}")
                break

    # Nếu kết nối bị đóng mà peer chưa được xóa thông qua LEAVE, xóa peer đó khỏi danh sách
    if added_peer:
        with peer_list_lock:
            if added_peer in peer_list:
                peer_list.remove(added_peer)
                print(f"[INFO] Kết nối đóng, đã xóa peer: {added_peer}")

def tracker_server(host="0.0.0.0", port=5000):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((host, port))
    server.listen(5)
    print(f"[START] Tracker đang lắng nghe trên {host}:{port}")

    while True:
        conn, addr = server.accept()
        threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()

if __name__ == "__main__":
    tracker_server()
