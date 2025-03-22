from email.message import EmailMessage
from config.db import users_collection 
from models.authModel import UserRegister, UserLogin, Visitor  # Import models
##########################################################
def register_user(user: UserRegister) -> dict:
    if users_collection.find_one({"email": user.email}):
        return {"message": "Email already registered"}

    if users_collection.find_one({"username": user.username}):
        return {"message": "Username already taken"}

    users_collection.insert_one(user.dict() | {"verified": True})
    
    return {"message": "User registered successfully"}
##########################################################
def login_user(user: UserLogin) -> dict:
    user_data = users_collection.find_one({"username": user.username, "password": user.password})
    
    if user_data:
        return {"message": "Login successful"}
    
    return {"message": "Invalid username or password"}
##########################################################
def visitor_mode(visitor_data: Visitor) -> dict:
    if not visitor_data.name:
        return {"message": "Visitor name cannot be empty"}
    
    return {"message": f"Welcome, {visitor_data.name}! You are in visitor mode."}
