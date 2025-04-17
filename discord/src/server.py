import socket
import threading
import json
import logging
from request.authRequest import handle_request as auth_request
from request.channelRequest import handle_channel_request
# from config.db import client
# from user import USER

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s')

class SERVER:
    def __init__(self, port=22236):
        host = self.get_host_default_interface_ip()
        self.server_start(host, port)

    def get_host_default_interface_ip(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(('8.8.8.8', 1))
            ip = s.getsockname()[0]
        except Exception:
            ip = '127.0.0.1'
        finally:
            s.close()
        return ip

    def handle_client(self, conn, addr):
        peer_ip, peer_temp_port = addr
        logging.info("New connection from %s:%s", peer_ip, peer_temp_port)

        try:
            while True:
                data = conn.recv(1024).decode('utf-8').strip()
                if not data:
                    break

                try:
                    request = json.loads(data)
                except json.JSONDecodeError:
                    response = {"status": "ERROR", "message": "Invalid JSON"}
                    conn.sendall(json.dumps(response).encode('utf-8'))
                    continue

                action = request.get("action")
                peer_port = request.get("port", peer_temp_port)

                if action in [
                    "create_channel", "join_channel", "get_user_channels",
                    "send_message", "get_channel_info", "delete_channel",
                    "get_all_channels", "start_livestream", "join_livestream",
                    "end_livestream", "approve_join_request", "get_join_requests",
                    "reject_join_request"
                ]:
                    response = handle_channel_request(data)
                else:
                    response = auth_request(data, peer_ip, peer_port)

                conn.sendall(response.encode('utf-8'))

        except Exception as e:
            logging.error("Error with %s:%s -> %s", peer_ip, peer_temp_port, e)
        finally:
            conn.close()
            logging.info("Connection with %s:%s closed.", peer_ip, peer_temp_port)

    def server_start(self, host, port):
        serversocket = socket.socket()
        serversocket.bind((host, port))
        serversocket.listen(5)
        logging.info("Server is listening on %s:%s", host, port)

        while True:
            conn, addr = serversocket.accept()
            threading.Thread(target=self.handle_client, args=(conn, addr), daemon=True).start()


if __name__ == "__main__":
    SERVER()
