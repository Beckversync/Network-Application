# client.py
import socket
import argparse

def connect_and_send(server_ip, server_port, message):
    """Kết nối đến server, gửi message và in phản hồi"""
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client_socket.connect((server_ip, server_port))
        client_socket.sendall((message + "\n").encode('utf-8'))
        response = client_socket.recv(4096).decode('utf-8')
        print("Response from server:\n{}".format(response))
    except Exception as e:
        print("Error:", e)
    finally:
        client_socket.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog='Client',
        description='Client gửi lệnh SUBMIT_INFO và GET_LIST đến server'
    )
    parser.add_argument('--server-ip', required=True, help='Địa chỉ IP của server')
    parser.add_argument('--server-port', type=int, required=True, help='Cổng của server')
    parser.add_argument('--username', required=True, help='Tên đăng ký của bạn')
    parser.add_argument('--peer-port', type=int, required=True, help='Cổng mà peer của bạn sẽ lắng nghe (cho kết nối P2P sau này)')
    args = parser.parse_args()

    # Gửi lệnh SUBMIT_INFO: "SUBMIT_INFO <username> <ip> <peer_port>"
    # Ở ví dụ này dùng 127.0.0.1 cho IP của client, có thể thay bằng hàm lấy IP nếu cần.
    submit_message = "SUBMIT_INFO {} {} {}".format(args.username, "127.0.0.1", args.peer_port)
    print("Gửi SUBMIT_INFO đến server...")
    connect_and_send(args.server_ip, args.server_port, submit_message)

    # Gửi lệnh GET_LIST để lấy danh sách các peer
    print("Yêu cầu danh sách peer với GET_LIST...")
    connect_and_send(args.server_ip, args.server_port, "GET_LIST")
