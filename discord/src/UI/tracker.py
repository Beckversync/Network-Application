import socket
import threading
import json
import logging

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s')


class TRACKER:
    def __init__(self, host="127.0.0.1", port=5000):
        self.peer_list = []  # Danh sách các peer đang kết nối
        self.peer_list_lock = threading.Lock()  # Lock cho việc truy cập danh sách
        self.tracker_server(host, port)  # Khởi động server

    def handle_client(self, conn, addr):
        logging.info("New connection from %s", addr)

        try:
            while True:
                data = conn.recv(1024).decode('utf-8').strip()
                if not data:
                    break

                try:
                    command = json.loads(data)
                except json.JSONDecodeError:
                    conn.sendall(json.dumps({"status": "ERROR", "message": "Invalid data"}).encode('utf-8'))
                    continue

                if "command" not in command:
                    conn.sendall(json.dumps({"status": "ERROR", "message": "Missing command"}).encode('utf-8'))
                    continue

                cmd = command["command"]

                if cmd == "CONNECT":
                    if not all(k in command for k in ["name", "ip", "port"]):
                        conn.sendall(json.dumps({"status": "ERROR", "message": "Missing information"}).encode('utf-8'))
                        continue

                    name, ip, port = command["name"], command["ip"], command["port"]

                    with self.peer_list_lock:
                        if not any(n == name and i == ip and p == port for n, i, p, _ in self.peer_list):
                            self.peer_list.append((name, ip, port, conn))
                            logging.info("Added peer: %s (%s:%s)", name, ip, port)
                            response = {"status": "OK", "message": f"Peer {name} ({ip}:{port}) added"}
                        else:
                            response = {"status": "OK", "message": f"Peer {name} ({ip}:{port}) already exists"}

                    conn.sendall(json.dumps(response).encode('utf-8'))

                elif cmd == "GET_LIST":
                    if "name" not in command:
                        conn.sendall(json.dumps({"status": "ERROR", "message": "Missing information"}).encode('utf-8'))
                        continue

                    with self.peer_list_lock:
                        peer_data = [{"name": n, "ip": i, "port": p} for n, i, p, _ in self.peer_list]

                    response = {"status": "OK", "peer_list": peer_data}
                    conn.sendall(json.dumps(response).encode('utf-8'))
                    logging.info("Sent peer list to %s", command['name'])

                elif cmd == "LEAVE":
                    if not all(k in command for k in ["name", "ip", "port"]):
                        conn.sendall(json.dumps({"status": "ERROR", "message": "Missing information"}).encode('utf-8'))
                        continue

                    name, ip, port = command["name"], command["ip"], command["port"]

                    with self.peer_list_lock:
                        for peer in self.peer_list:
                            if peer[:3] == (name, ip, port):
                                self.peer_list.remove(peer)
                                logging.info("Peer %s (%s:%s) left tracker.", name, ip, port)
                                response = {"status": "OK", "message": f"Peer {name} ({ip}:{port}) left"}
                                break
                        else:
                            response = {"status": "ERROR", "message": f"Peer {name} ({ip}:{port}) not found"}

                    conn.sendall(json.dumps(response).encode('utf-8'))

                elif cmd == "MSG_SEND":
                    if not all(k in command for k in ["ip", "port", "name", "message"]):
                        conn.sendall(json.dumps({"status": "ERROR", "message": "Missing information"}).encode('utf-8'))
                        continue

                    name, ip, port, message = command["name"], command["ip"], command["port"], command["message"]
                    logging.info("[CHAT] %s: %s", name, message)

                    with self.peer_list_lock:
                        disconnected_peers = []
                        for name_list, ip_list, port_list, peer_conn in self.peer_list:
                            if ip == ip_list and port == port_list:
                                continue
                            try:
                                json_message = json.dumps({
                                    "command": "MSG_RECV",
                                    "client_name": name,
                                    "message": message
                                })
                                peer_conn.sendall(json_message.encode('utf-8'))
                                logging.info("Sent message to %s (%s:%s)", name_list, ip_list, port_list)
                            except Exception:
                                logging.error("Cannot send message to %s (%s:%s)", name_list, ip_list, port_list)
                                disconnected_peers.append((name_list, ip_list, port_list, peer_conn))

                        for peer in disconnected_peers:
                            self.peer_list.remove(peer)
                            logging.info("Removed disconnected peer: %s (%s:%s)", peer[0], peer[1], peer[2])
                else:
                    conn.sendall(json.dumps({"status": "ERROR", "message": "Invalid command"}).encode('utf-8'))

        except Exception as e:
            logging.error("Error handling client: %s", e)
        finally:
            conn.close()
            logging.info("Connection with %s closed.", addr)

    def tracker_server(self, host="127.0.0.1", port=5000):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((host, port))
        server.listen(5)
        logging.info("Tracker is listening on %s:%s", host, port)

        while True:
            conn, addr = server.accept()
            threading.Thread(target=self.handle_client, args=(conn, addr), daemon=True).start()


if __name__ == "__main__":
    TRACKER()
