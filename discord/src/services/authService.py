from config.db import users_collection
import uuid
from datetime import datetime, timezone
from models.authModel import UserRegister, UserLogin, Visitor
import logging
import re
import threading
import socket

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s')

def register_user(user: UserRegister) -> dict:
    try:
        if not re.match(r"^[\w\.-]+@hcmut\.edu\.vn$", user.email):
            return {"status": "error", "message": "Email must be in format '@hcmut.edu.vn'"}

        if users_collection.find_one({"email": user.email}):
            return {"status": "error", "message": "Email already registered"}
        if users_collection.find_one({"username": user.username}):
            return {"status": "error", "message": "Username already taken"}

        new_user = user.model_dump()
        new_user["verified"] = True 
        result = users_collection.insert_one(new_user) 
        logging.info("User %s registered successfully", user.username)
        return {"status": "success", "message": "User registered successfully", "user_id": str(result.inserted_id)}
    except Exception as e:
        logging.error("Database error during registration: %s", e)
        return {"status": "error", "message": f"Database error: {str(e)}"}

running_servers = {}  # Dict[str, int]

def start_user_server(user_username: str, port: int):
    def handle_client(conn, addr):
        print(f"User {user_username} connected from {addr}")
        try:
            while True:
                data = conn.recv(1024)
                if not data:
                    break
                print(f"Received from {user_username}: {data.decode()}")
                conn.send(b"Message received")
        except Exception as e:
            print(f"Error with {user_username}: {e}")
        finally:
            conn.close()

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(("0.0.0.0", port))
    server_socket.listen(5)
    logging.info(f"Server for {user_username} is listening on port {port}...")

    while True:
        conn, addr = server_socket.accept()
        threading.Thread(target=handle_client, args=(conn, addr)).start()


def login_user(user: UserLogin, peer_ip: str, peer_port: int) -> dict:
    user_data = users_collection.find_one({"username": user.username, "password": user.password})
    if user_data:
        session_id = str(uuid.uuid4())
        login_time = datetime.now(timezone.utc)
        if user.username not in running_servers:
            port = 4000 + sum(ord(c) for c in user.username) % 1000
            thread = threading.Thread(target=start_user_server, args=(user.username, port), daemon=True)
            thread.start()
            running_servers[user.username] = port
        else:
            port = running_servers[user.username]

        new_session = {
            "peer_ip": peer_ip,
            "peer_port": peer_port,
            "session_id": session_id,
            "login_time": login_time,
            "visible": True,
            "server_port": port
        }

        users_collection.update_one(
            {"username": user.username},
            {
                "$push": {"sessions": new_session},
                "$set": {"state": "online"}
            }
        )

        user_data = users_collection.find_one({"username": user.username})

        def serialize(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            return obj

        logging.info("User %s logged in successfully", user.username)
        return {
            "status": "success",
            "message": "Login successful",
            "user": {
                "username": user_data["username"],
                "email": user_data.get("email", ""),
                "state": user_data.get("state", "online"),
                "channels_joined": user_data.get("channels_joined", []),
                "hosted_channels": user_data.get("hosted_channels", []),
                "sessions": [
                    {
                        **session,
                        "login_time": serialize(session["login_time"])
                    } for session in user_data.get("sessions", [])
                ]
            }
        }

    return {"status": "error", "message": "Invalid username or password"}

def update_user_status(session_id: str, visible: bool) -> dict:
    user = users_collection.find_one({"sessions.session_id": session_id})
    if not user:
         return {"status": "error", "message": "Session not found"}
    users_collection.update_one(
         {"_id": user["_id"], "sessions.session_id": session_id},
         {"$set": {"sessions.$.visible": visible}}
    )
    logging.info("Updated session %s visible to %s", session_id, visible)
    return {"status": "success", "message": "User status updated"}

def get_all_users():
    try:
        users = list(users_collection.find({}, {"username": 1, "sessions": 1, "_id": 0}))
        result = []
        for user in users:
            username = user.get("username")
            sessions = user.get("sessions", [])
            status = "Offline"
            for session in sessions:
                if session.get("visible", True):
                    status = "Online"
                    break
            result.append({
                "username": username,
                "status": status
            })
        return {"status": "success", "data": result}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def visitor_mode(visitor_data: Visitor) -> dict:
    if users_collection.find_one({"username": visitor_data.name}):
        return {"status": "error", "message": "Username already taken"}
    if not visitor_data.name:
        return {"status": "error", "message": "Visitor name cannot be empty"}
    
    logging.info("Visitor %s entered visitor mode", visitor_data.name)
    return {"status": "success", "message": f"Welcome, {visitor_data.name}! You are in visitor mode."}

def logout_user(session_id: str) -> dict:
    try:
        user = users_collection.find_one({"sessions.session_id": session_id})
        if not user:
            return {"status": "error", "message": "Invalid session_id"}
        
        # Xoá session_id ra khỏi danh sách
        users_collection.update_one(
            {"_id": user["_id"]},
            {"$pull": {"sessions": {"session_id": session_id}}}
        )
        
        # Kiểm tra lại nếu không còn session nào nữa thì set state = offline
        updated_user = users_collection.find_one({"_id": user["_id"]})
        if not updated_user.get("sessions"):  # sessions rỗng hoặc không tồn tại
            users_collection.update_one(
                {"_id": user["_id"]},
                {"$set": {"state": "offline"}}
            )

        logging.info("User %s logged out", user["username"])
        return {"status": "success", "message": "Logout successful"}
    
    except Exception as e:
        logging.error("Database error during logout: %s", e)
        return {"status": "error", "message": f"Database error: {str(e)}"}

