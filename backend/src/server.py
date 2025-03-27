import json
import socket
import threading
from request.authRequest import handle_request as auth_request
from request.channelRequest import handle_channel_request  # Import xử lý channel
from config.db import client  # Kết nối MongoDB

# Kết nối đến MongoDB
def handle_client(conn, addr):
    """ Xử lý kết nối từ client """
    print(f"New connection from {addr}")

    try:
        while True:
            data = conn.recv(1024).decode()
            if not data:
                break

            request = json.loads(data)
            action = request.get("action")

            if action in ["create_channel", "join_channel", "get_messages", "send_message"]:
                response = handle_channel_request(data)  # Xử lý channel
            else:
                response = auth_request(data)  # Xử lý auth

            conn.send(response.encode())

    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

def server_program(host, port):
    """ Khởi động server """
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen(5)
    print(f"Socket server listening on {host}:{port}")

    while True:
        conn, addr = server_socket.accept()
        threading.Thread(target=handle_client, args=(conn, addr)).start()

if __name__ == "__main__":
    server_program("0.0.0.0", 22236)
