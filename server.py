# server.py
import socket
import threading

# Danh sách lưu thông tin các peer (mỗi phần tử là dict: username, ip, port, addr)
peer_list = []
peer_list_lock = threading.Lock()

def handle_client(conn, addr):
    """Xử lý kết nối đến từ client"""
    print("Accepted connection from {}".format(addr))
    try:
        while True:
            # Nhận dữ liệu (giả sử mỗi message kết thúc bằng '\n')
            data = conn.recv(1024).decode('utf-8')
            if not data:
                break
            # Có thể nhận được nhiều lệnh trong 1 lần, tách theo newline
            messages = data.split('\n')
            for message in messages:
                if message.strip() == "":
                    continue
                print("Received from {}: {}".format(addr, message))
                response = process_command(message.strip(), addr)
                if response:
                    conn.sendall((response + "\n").encode('utf-8'))
    except Exception as e:
        print("Error with {}: {}".format(addr, e))
    finally:
        print("Closing connection from {}".format(addr))
        conn.close()

def process_command(message, addr):
    """Phân tích và xử lý các lệnh từ client"""
    parts = message.split()
    if len(parts) == 0:
        return "ERROR 400 'Bad Request'"
    command = parts[0]
    if command == "SUBMIT_INFO":
        if len(parts) < 4:
            return "ERROR SUBMIT_INFO 400 'Missing parameters'"
        username = parts[1]
        ip = parts[2]
        try:
            port = int(parts[3])
        except ValueError:
            return "ERROR SUBMIT_INFO 400 'Invalid port'"
        peer_info = {"username": username, "ip": ip, "port": port, "addr": addr}
        with peer_list_lock:
            # Thêm peer mới vào danh sách (có thể kiểm tra trùng lặp nếu cần)
            peer_list.append(peer_info)
        return "OK SUBMIT_INFO"
    elif command == "GET_LIST":
        with peer_list_lock:
            response_lines = ["OK GET_LIST {}".format(len(peer_list))]
            for peer in peer_list:
                # Mỗi dòng: <username> <ip> <port>
                response_lines.append("{} {} {}".format(peer["username"], peer["ip"], peer["port"]))
            return "\n".join(response_lines)
    elif command == "QUIT":
        return "OK QUIT"
    else:
        return "ERROR 501 'Not Implemented'"

def get_host_default_interface_ip():
    """Lấy IP của giao diện mặc định (dùng để server hiển thị IP công khai)"""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 1))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip

def server_program(host, port):
    serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serversocket.bind((host, port))
    serversocket.listen(10)
    print("Server listening on {}:{}".format(host, port))
    try:
        while True:
            conn, addr = serversocket.accept()
            client_thread = threading.Thread(target=handle_client, args=(conn, addr))
            client_thread.daemon = True
            client_thread.start()
    except KeyboardInterrupt:
        print("Server shutting down...")
    finally:
        serversocket.close()

if __name__ == "__main__":
    hostip = get_host_default_interface_ip()
    port = 22236  # Cổng cho server, bạn có thể thay đổi nếu cần
    server_program(hostip, port)
