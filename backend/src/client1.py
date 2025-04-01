import socket
import sys
import json
import keyboard # type: ignore
TRACKER_IP = "127.0.0.1"
TRACKER_PORT = 22236

def connect_to_tracker(peer_ip, peer_port):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((TRACKER_IP, TRACKER_PORT))
        return s
    except Exception as e:
        print(f"[ERROR] Không thể kết nối đến Tracker: {e}")
        return None

session_id = None
response_list = None
status_login = None
username_login = None
all_channelist = None
#username = None
def send_to_tracker(sock, message):
    global session_id
    global response_list
    global status_login
    global all_channelist
    try:
        parts = message.split()
        action = parts[0].lower()
        data = {"action": action}

        if action == "login":
            if len(parts) < 3:
                return "[ERROR] Cần nhập username và password!"
            data["username"] = parts[1]
            data["password"] = parts[2]
        elif action == "register":
            if len(parts) < 4:
                return "[ERROR] Cần nhập username, password và email!"
            data["username"] = parts[1]
            data["password"] = parts[2]
            data["email"] = parts[3]
        elif action == "visitor":
            if len(parts) < 2:
                return "[ERROR] Cần nhập tên visitor!"
            data["name"] = parts[1]
        elif action == "logout":
            data["session_id"] = session_id
        elif action == "create_channel":
            data["host"] = parts[1]
            data["channel_name"] = parts[2]
        elif action == "join_channel":
            data["username"] = parts[1]
            data["channel_name"] = parts[2]
        elif action == "get_user_channels":
            data["username"] = parts[1]
        elif action == "send_message":
            data["username"] = parts[1]
            data["channel_name"] = parts[2]
            data["message"] = parts[3]
        elif action == "get_channel_info":
            data["channel_name"] = parts[1]
        elif action == "get_all_channels":
            pass
        elif action == "delete_channel":
            data["username"] = parts[1]
            data["channel_name"] = parts[2]
        elif action == "data":
            if len(parts) < 4:
                return "[ERROR] Cần nhập IP, Port và tin nhắn!"
            data["target_ip"] = parts[1]
            data["target_port"] = parts[2]
            data["message"] = " ".join(parts[3:])

        json_message = json.dumps(data)
        sock.sendall(json_message.encode('utf-8'))

        response = sock.recv(1024)
        if not response:
            return "[ERROR] Không nhận được phản hồi từ server."

        response_data = response.decode('utf-8')
        if action == "get_user_channels":
            response_list = response_data
        elif action == "get_all_channels":
            all_channelist = response_data
        #print(response_list)
        #print(type(response_list))
        print(f"[DEBUG] Phản hồi từ Tracker: {response_data}")
        #print(type(response_data))
        #print(f"[DEBUG] Dữ liệu nhận được từ server: {response_data}")
        
        try:
            response_dict = json.loads(response_data)
            response_dict = json.loads(response_dict)
            status_login = response_dict.get("status", {})
            print(status_login)
            # print(type(response_dict))
            # print(f"[DEBUG] Phản hồi từ Tracker: {response_dict}")
            user_data = response_dict.get("user", {})
            #print("[DEBUG] user_data:", user_data)
            sessions = user_data.get("sessions", [])
            username_temp = user_data.get("username", {})
            print(username_temp);
            #print("[DEBUG] sessions:", sessions)

            if sessions:
                session_id = sessions[-1]["session_id"]
                print("session ID của phiên đăng nhập hiện tại:", session_id)
            else:
                print("Không tìm thấy session nào!")

        except (json.JSONDecodeError, KeyError, IndexError) as e:
            print("[LỖI] Không thể lấy session_id:", str(e))

        
        return response_data

    except Exception as e:
        return f"[ERROR] Lỗi khi gửi dữ liệu: {e}"

def login_or_register(sock):
    global username_login
    while True:
        print("\n=== ĐĂNG NHẬP / ĐĂNG KÝ / VISITOR ===")
        print("1. Đăng nhập")
        print("2. Đăng ký")
        print("3. Vào với tư cách visitor")
        print("4. Thoát chương trình")

        choice = input("Chọn: ").strip()
        if choice == "1":
            username = input("Tên đăng nhập: ").strip()
            password = input("Mật khẩu: ").strip()
            response = send_to_tracker(sock, f"LOGIN {username} {password}")
            if username and status_login == "success":
                menu(tracker_socket, username)
            else:
                print("[ERROR] Đăng nhập thất bại, thoát chương trình.")
            return username
        
        elif choice == "2":
            username = input("Tên đăng ký: ").strip()
            password = input("Mật khẩu: ").strip()
            email = input("Email: ").strip()
            response = send_to_tracker(sock, f"REGISTER {username} {password} {email}")
        
        elif choice == "3":
            visitor_name = input("Tên của bạn: ").strip()
            response = send_to_tracker(sock, f"VISITOR {visitor_name}")
            print("[INFO]", response)
            if visitor_name and status_login == "success":
                menu(tracker_socket, visitor_name)
            else:
                print("[ERROR] Đăng nhập thất bại, thoát chương trình.")
            #return visitor_name
        
        elif choice == "4":
            print("[INFO] Thoát chương trình.")
            sys.exit()
        else:
            print("[ERROR] Vui lòng chọn 1, 2, 3, 4")

def logout(sock):
    global session_id
    global response_list
    print("Session ID của phiên đăng nhập hiện tại:", session_id)
    if session_id:
        send_to_tracker(sock, "LOGOUT")
        print("[INFO] Đã đăng xuất. Quay lại màn hình đăng nhập...")
        session_id = None
        response_list = None
    else:
        print("[ERROR] Bạn chưa đăng nhập hoặc session đã hết hạn!")



def menu(sock, username):
    global response_list
    try:
        while True:
            print("\n=== MENU ===")
            print("1. User channel list")
            print("2. Gửi tin nhắn đến peer")
            print("3. Create channel")
            print("4. Join channel")
            print("5. All Channel")
            print("6. Đăng xuất")

            choice = input("Chọn một hành động: ").strip()
            if choice == "1":
                # response_list = json.dumps(response_list)
                # print(type(response_list))
                send_to_tracker(sock, f"GET_USER_CHANNELS {username}")
                #print(response_list)
                #print(type(response_list))
                try:
                    channel_info = json.loads(response_list)
                    #print(channel_info)
                    #print(type(channel_info))
                    joined_channels = channel_info["data"].get("joined_channels", [])
                        
                    hosted_channels = channel_info["data"].get("hosted_channels", [])
                    print("\n=== DANH SÁCH KÊNH ===")
                    if joined_channels:
                        print("Joined Channels:")
                        for idx, channel in enumerate(joined_channels, 1):
                            print(f"{idx}. {channel}")
                    else:
                        print("[INFO] Bạn chưa tham gia kênh nào.")
                    
                    if hosted_channels:
                        print("Hosted Channels:")
                        for idx, channel in enumerate(hosted_channels, 1):
                            print(f"{idx}. {channel}")
                    else:
                        print("[INFO] Bạn chưa tạo kênh nào.")

                    #Select channel
                    channels = joined_channels + hosted_channels

                    selected_channel = input("Nhập tên kênh để vào (hoặc Enter để quay lại): ").strip()
                    if selected_channel in channels:
                        print(f"[INFO] Đang vào kênh: {selected_channel}")
                        print(f"\n=== {selected_channel} ===")
                        print("1. Channel_Info")
                        print("2. Delete channel")
                        print("3. Send Message (Not P2P)")
                        print("ENTER to back")
                        option = input("Chon: ").strip()
                        if option == "1":
                            send_to_tracker(sock, f"GET_CHANNEL_INFO {selected_channel}")
                        elif option == "2":
                            send_to_tracker(sock, f"DELETE_CHANNEL {username} {selected_channel}")
                        elif option == "3":
                            while True:
                                print("Nhập tin nhắn (Nhấn ENTER để quay lại màn hình trước): ")
                                text = input("Message: ").strip()
                                if text == "":
                                    break
                                else:
                                    send_to_tracker(sock, f"SEND_MESSAGE {username} {selected_channel} {text}")
                        else:
                            break
                    else:
                        print("[ERROR] Tên kênh không hợp lệ.")
                except Exception as e:
                    print(f"[ERROR] Không thể lấy danh sách kênh: {e}")
            elif choice == "2":
                target_ip = input("Nhập IP của Peer: ").strip()
                target_port = input("Nhập Port của Peer: ").strip()
                message = input("Nhập tin nhắn: ").strip()
                send_to_tracker(sock, f"DATA {target_ip} {target_port} {message}")
            elif choice == "3":
                channel_name = input("Name of channel: ").strip()
                host = username
                send_to_tracker(sock, f"CREATE_CHANNEL {host} {channel_name}")
            elif choice == "4":
                channel_name = input("Name of channel: ").strip()
                send_to_tracker(sock, f"JOIN_CHANNEL {username} {channel_name}")
            elif choice == "5":
                print("\n=== All Channels ===")
                
                send_to_tracker(sock, "GET_ALL_CHANNELS")
                
                try:
                    channel_info = json.loads(all_channelist)
                    
                    all_channels = channel_info["data"]
                    
                    print("\n=== DANH SÁCH TẤT CẢ CÁC KÊNH ===")
                    if all_channels:
                        for idx, channel in enumerate(all_channels, 1):
                            print(f"{idx}. {channel['channel_name']} (Chủ kênh: {channel['owner']})")
                    else:
                        print("[INFO] Hiện tại không có kênh nào.")
                    
                    # Chọn kênh để tham gia
                    selected_channel = input("Nhập tên kênh để vào (hoặc Enter để quay lại): ").strip()
                    
                    # Kiểm tra nếu kênh hợp lệ
                    valid_channels = [c["channel_name"] for c in all_channels]
                    if selected_channel in valid_channels:
                        print(f"[INFO] Đang vào kênh: {selected_channel}")
                        print(f"\n=== {selected_channel} ===")
                        print("1. Channel_Info")
                        print("2. Send Message (Not P2P)")
                        print("ENTER để quay lại")
                        
                        option = input("Chọn: ").strip()
                        
                        if option == "1":
                            send_to_tracker(sock, f"GET_CHANNEL_INFO {selected_channel}")
                        elif option == "2":
                            while True:
                                print("Nhập tin nhắn (Nhấn ENTER để quay lại): ")
                                text = input("Message: ").strip()
                                if text == "":
                                    break
                                else:
                                    send_to_tracker(sock, f"SEND_MESSAGE {username} {selected_channel} {text}")
                        else:
                            print("[INFO] Quay lại menu chính.")
                    
                    else:
                        print("[ERROR] Tên kênh không hợp lệ.")
                
                except Exception as e:
                    print(f"[ERROR] Không thể lấy danh sách kênh: {e}")
            elif choice == "6":
                logout(sock)
                #username = None
                login_or_register(sock)
            else:
                print("[ERROR] Vui lòng chọn từ 1 đến 3.")
    except KeyboardInterrupt:
        print("\n[INFO] Thoát chương trình...")
        logout(sock, username)
        sock.close()
        sys.exit()


if __name__ == "__main__":
    peer_ip = "127.0.0.1"
    peer_port = 8081
    while(1):
        tracker_socket = connect_to_tracker(peer_ip, peer_port)
        if not tracker_socket:
            sys.exit(1)
        login_or_register(tracker_socket)
        # print(username)
        # if username and status_login == "success":
        #     menu(tracker_socket, username)
        # else:
        #     print("[ERROR] Đăng nhập thất bại, thoát chương trình.")
