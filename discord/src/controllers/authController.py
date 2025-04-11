import json
from models.authModel import UserRegister, UserLogin, Visitor
from services.authService import register_user, login_user, visitor_mode, logout_user

def register(data):
    user = UserRegister(**data)
    result = register_user(user)
    return result

def login(data, peer_ip, peer_port):
    user = UserLogin(**data)
    result = login_user(user, peer_ip, peer_port)
    return result

def visitor(data):
    visitor_data = Visitor(**data)
    result = visitor_mode(visitor_data)
    return result

def logout(data):
    session_id = data.get("session_id")
    if not session_id:
        return {"status": "error", "message": "Session ID is required"}
    result = logout_user(session_id)
    return result

def update_status(data):
    session_id = data.get("session_id")
    visible = data.get("visible")
    if session_id is None or visible is None:
        return {"status": "error", "message": "Missing parameters"}
    from services.authService import update_user_status
    result = update_user_status(session_id, visible)
    return result
