import json
import socket
import threading
from request.authRequest import handle_request as auth_request
from request.channelRequest import handle_channel_request  # Import xử lý channel
# from config.db import client  # Kết nối MongoDB

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

            if action in ["create_channel", "join_channel", "get_user_channels", "send_message", "get_channel_info", "delete_channel", "get_all_channels", "start_livestream", "join_livestream", "end_livestream", "approve_join_request", "get_join_requests", "reject_join_request"]:
                response = handle_channel_request(data)
            else:
                response = auth_request(data, peer_ip, peer_port)

            conn.send(response.encode())

    except Exception as e:
        print(f"Error with {peer_ip}:{peer_port} -> {e}")
    finally:
        conn.close()

def get_host_default_interface_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
       s.connect(('8.8.8.8',1))
       ip = s.getsockname()[0]
    except Exception:
       ip = '127.0.0.1'
    finally:
       s.close()
    return ip

def server_program(host, port):
    serversocket = socket.socket()
    serversocket.bind((host, port))
    serversocket.listen(5)
    print(f"Socket server listening on {host}:{port}")

    while True:
        conn, addr = serversocket.accept()
        threading.Thread(target=handle_client, args=(conn, addr)).start()

if __name__ == "__main__":
    #hostname = socket.gethostname()
    hostip = get_host_default_interface_ip()
    port = 22236
    print("Listening on: {}:{}".format(hostip,port))
    server_program(hostip, port)

