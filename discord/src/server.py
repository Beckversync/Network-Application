import json
import socket
import threading
from request.authRequest import handle_request as auth_request
from request.channelRequest import handle_channel_request  # Import xử lý channel
from config.db import client  # Kết nối MongoDB

# Kết nối đến MongoDB
def handle_client(conn, addr):
    peer_ip, peer_port = addr 
    print(f"New connection from {peer_ip}:{peer_port}")

    try:
        while True:
            data = conn.recv(1024).decode()
            if not data:
                break

            request = json.loads(data)
            action = request.get("action")

            if action in ["create_channel", "join_channel", "get_user_channels", "send_message", "get_channel_info", "delete_channel", "get_all_channels", "start_livestream", "join_livestream", "end_livestream"]:
                response = handle_channel_request(data)
            else:
                response = auth_request(data, peer_ip, peer_port)

            conn.send(response.encode())

    except Exception as e:
        print(f"Error with {peer_ip}:{peer_port} -> {e}")
    finally:
        conn.close()

def server_program(host, port):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen(5)
    print(f"Socket server listening on {host}:{port}")

    while True:
        conn, addr = server_socket.accept()
        threading.Thread(target=handle_client, args=(conn, addr)).start()

if __name__ == "__main__":
    server_program("0.0.0.0", 22236)
