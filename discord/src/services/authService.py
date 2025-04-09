import uuid
from datetime import datetime, timezone
from models.authModel import UserRegister, UserLogin, Visitor
from config.db import users_collection
import logging
import re

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s')


def clean_sessions(sessions):
    """
    Lọc ra các session hợp lệ (chỉ lấy các entry là dict và có đầy đủ các key: 
    "peer_ip", "peer_port", "session_id", "login_time").
    """
    valid_sessions = []
    for session in sessions:
        if isinstance(session, dict) and all(key in session for key in ["peer_ip", "peer_port", "session_id", "login_time"]):
            valid_sessions.append(session)
    return valid_sessions


def limit_sessions(sessions, max_sessions=5):
    """
    Sắp xếp các session theo thời gian đăng nhập và chỉ giữ lại max_sessions phiên mới nhất.
    """
    try:
        sorted_sessions = sorted(sessions, key=lambda s: datetime.fromisoformat(s["login_time"]))
    except Exception as e:
        # Nếu chuyển đổi datetime thất bại, sắp xếp dựa trên chuỗi
        sorted_sessions = sorted(sessions, key=lambda s: s["login_time"])
    if len(sorted_sessions) > max_sessions:
        sorted_sessions = sorted_sessions[-max_sessions:]
    return sorted_sessions


def login_user(user: UserLogin, peer_ip: str, peer_port: int) -> dict:
    user_data = users_collection.find_one({"username": user.username, "password": user.password})
    if user_data:
        # Tạo phiên đăng nhập mới
        session_id = str(uuid.uuid4())
        new_session = {
            "peer_ip": peer_ip,
            "peer_port": peer_port,
            "session_id": session_id,
            "login_time": datetime.now(timezone.utc).isoformat()
        }
        # Thêm phiên mới vào mảng sessions trong DB
        users_collection.update_one(
            {"username": user.username},
            {"$push": {"sessions": new_session}}
        )
        user_data = users_collection.find_one({"username": user.username})
        # Lấy lại mảng sessions, làm sạch và giới hạn số lượng phiên
        sessions = user_data.get("sessions", [])
        valid_sessions = clean_sessions(sessions)
        limited_sessions = limit_sessions(valid_sessions, max_sessions=5)
        # Cập nhật lại mảng sessions hợp lệ vào DB
        users_collection.update_one(
            {"username": user.username},
            {"$set": {"sessions": limited_sessions}}
        )

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
                "channels_joined": user_data.get("channels_joined", []),
                "hosted_channels": user_data.get("hosted_channels", []),
                "sessions": [{**session, "login_time": serialize(session["login_time"])}
                             for session in limited_sessions]
            }
        }
    return {"status": "error", "message": "Invalid username or password"}


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
        users_collection.update_one(
            {"_id": user["_id"]},
            {"$pull": {"sessions": {"session_id": session_id}}}
        )
        logging.info("User %s logged out", user["username"])
        return {"status": "success", "message": "Logout successful"}
    except Exception as e:
        logging.error("Database error during logout: %s", e)
        return {"status": "error", "message": f"Database error: {str(e)}"}
