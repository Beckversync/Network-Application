import socket
import threading
import json
import logging
from request.authRequest import handle_request as auth_request
from request.channelRequest import handle_channel_request
from config.db import users_collection 
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s')


class TRACKER_SERVER:
    def __init__(self, port=5000):
        self.peer_list = []
        self.peer_list_lock = threading.Lock()
        host = self.get_host_default_interface_ip()
        self.start_server(host, port)

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
        # logging.info("New connection from %s:%s", peer_ip, peer_temp_port)

        try:
            while True:
                data = conn.recv(1024).decode('utf-8').strip()
                if not data:
                    break

                try:
                    parsed = json.loads(data)
                except json.JSONDecodeError:
                    conn.sendall(json.dumps({"status": "ERROR", "message": "Invalid JSON"}).encode('utf-8'))
                    continue

                # === TRACKER COMMAND ===
                if "command" in parsed:
                    cmd = parsed["command"]

                    if cmd == "CONNECT":
                        if not all(k in parsed for k in ["name", "ip", "port"]):
                            conn.sendall(json.dumps({"status": "ERROR", "message": "Missing info"}).encode('utf-8'))
                            continue

                        name, ip, port = parsed["name"], parsed["ip"], parsed["port"]

                        user_data = users_collection.find_one({"username": name})
                        if user_data:
                            with self.peer_list_lock:
                                if not any(n == name and i == ip and p == port for n, i, p, _ in self.peer_list):
                                    self.peer_list.append((name, ip, port, conn))

                                    users_collection.update_one(
                                        {"username": name, "sessions.peer_ip": ip},
                                        {"$set": {"sessions.$.peer_port": port}}
                                    )

                                    logging.info("Added peer: %s (%s:%s)", name, ip, port)
                                    response = {"status": "OK", "message": f"Peer {name} ({ip}:{port}) added"}
                                else:
                                    response = {"status": "OK", "message": f"Peer {name} ({ip}:{port}) already exists"}
                            conn.sendall(json.dumps(response).encode('utf-8'))
                        else:
                            conn.sendall(json.dumps({"status": "ERROR", "message": "User not logged in"}).encode('utf-8'))


                    elif cmd == "GET_LIST":
                        with self.peer_list_lock:
                            peer_data = [{"name": n, "ip": i, "port": p} for n, i, p, _ in self.peer_list]
                        response = {"status": "OK", "peer_list": peer_data}
                        conn.sendall(json.dumps(response).encode('utf-8'))
                        logging.info("Sent peer list to %s", parsed.get('name', 'unknown'))

                    elif cmd == "LEAVE":
                        name, ip, port = parsed.get("name"), parsed.get("ip"), parsed.get("port")
                        with self.peer_list_lock:
                            for peer in self.peer_list:
                                if peer[:3] == (name, ip, port):
                                    self.peer_list.remove(peer)
                                    logging.info("Peer %s (%s:%s) left", name, ip, port)
                                    conn.sendall(json.dumps({
                                        "status": "OK", "message": f"Peer {name} ({ip}:{port}) left"
                                    }).encode('utf-8'))
                                    break
                            else:
                                conn.sendall(json.dumps({
                                    "status": "ERROR", "message": "Peer not found"
                                }).encode('utf-8'))

                    elif cmd == "MSG_SEND":
                        name, ip, port, message = parsed.get("name"), parsed.get("ip"), parsed.get("port"), parsed.get("message")
                        logging.info("[CHAT] %s: %s", name, message)

                        with self.peer_list_lock:
                            disconnected = []
                            for n, i, p, peer_conn in self.peer_list:
                                if (i, p) == (ip, port):  # skip sender
                                    continue
                                try:
                                    peer_conn.sendall(json.dumps({
                                        "command": "MSG_RECV",
                                        "client_name": name,
                                        "message": message
                                    }).encode('utf-8'))
                                    logging.info("Sent message to %s (%s:%s)", n, i, p)
                                except:
                                    logging.warning("Disconnected peer: %s (%s:%s)", n, i, p)
                                    disconnected.append((n, i, p, peer_conn))
                            for d in disconnected:
                                self.peer_list.remove(d)

                    else:
                        conn.sendall(json.dumps({"status": "ERROR", "message": "Invalid command"}).encode('utf-8'))

                # === CHANNEL/AUTH ACTION ===
                elif "action" in parsed:
                    action = parsed.get("action")
                    port = parsed.get("port", peer_temp_port)

                    if action in [
                        "create_channel", "join_channel", "get_user_channels",
                        "send_message", "get_channel_info", "delete_channel",
                        "get_all_channels", "start_livestream", "join_livestream",
                        "end_livestream", "approve_join_request", "get_join_requests",
                        "reject_join_request", "get_hosted_channels", "send_message_p2p"
                    ]:
                        response = handle_channel_request(data)
                    else:
                        response = auth_request(data, peer_ip, port)

                    conn.sendall(response.encode('utf-8'))

                else:
                    conn.sendall(json.dumps({"status": "ERROR", "message": "Unknown request"}).encode('utf-8'))

        except Exception as e:
            logging.error("Error handling client %s:%s -> %s", peer_ip, peer_temp_port, e)
        finally:
            conn.close()
            logging.info("Connection with %s:%s closed.", peer_ip, peer_temp_port)

    def start_server(self, host, port):
        serversocket = socket.socket()
        serversocket.bind((host, port))
        serversocket.listen(5)
        logging.info("Tracker-Server is listening on %s:%s", host, port)

        while True:
            conn, addr = serversocket.accept()
            threading.Thread(target=self.handle_client, args=(conn, addr), daemon=True).start()


if __name__ == "__main__":
    TRACKER_SERVER()
