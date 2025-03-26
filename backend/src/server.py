import socket
import threading
from request.authRequest import handle_request  # Import xử lý request từ client
from config.db import client  # Kết nối MongoDB

# Kết nối đến MongoDB
db = client.get_database("chatappp")
collection = db.get_collection("collection")

print("Connected to MongoDB database:", db.name)

def handle_client(conn, addr):
    """ Xử lý kết nối từ client """
    print(f"New connection from {addr}")

    try:
        while True:
            data = conn.recv(1024).decode()
            if not data:
                break

            response = handle_request(data)
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
