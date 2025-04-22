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

        new_user=user.dict()
        new_user["verified"] = True 
        result = users_collection.insert_one(new_user) 
        logging.info("User %s registered successfully", user.username)
        return {"status": "success", "message": "User registered successfully", "user_id": str(result.inserted_id)}
    except Exception as e:
        logging.error("Database error during registration: %s", e)
        return {"status": "error", "message": f"Database error: {str(e)}"}

def login_user(user: UserLogin, peer_ip: str, peer_port: int) -> dict:
    user_data = users_collection.find_one({"username": user.username, "password": user.password})
    if user_data:
        session_id = str(uuid.uuid4()) 
        new_session = {
            "peer_ip": peer_ip,
            "peer_port": peer_port,
            "session_id": session_id,
            "login_time": datetime.now(timezone.utc).isoformat(),
            "visible": True 
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
                "sessions": [{**session, "login_time": serialize(session["login_time"])}
                             for session in user_data.get("sessions", [])]
            }
        }
    return {"status": "error", "message": "Invalid username or password"}

def update_user_status(session_id: str, visible: bool) -> dict:
    try:
        user = users_collection.find_one({"sessions.session_id": session_id})
        if not user:
            return {"status": "error", "message": "Invalid session_id"}

        result = users_collection.update_one(
            {"_id": user["_id"], "sessions.session_id": session_id},
            {"$set": {"sessions.$.visible": visible}}
        )

        if result.modified_count == 0:
            logging.warning("No session updated for session_id: %s", session_id)
            return {"status": "error", "message": "Failed to update visibility status"}

        logging.info("Updated visibility of session %s to %s", session_id, visible)
        return {"status": "success", "message": "User status updated"}
    
    except Exception as e:
        logging.error("Database error during status update: %s", e)
        return {"status": "error", "message": f"Database error: {str(e)}"}

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
        users_collection.update_one(
            {"_id": user["_id"]},
            {"$pull": {"sessions": {"session_id": session_id}}}
        )

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
