from config.db import users_collection
from models.authModel import UserRegister, UserLogin, Visitor
##########################################################
def register_user(user: UserRegister) -> dict:
    try:
        if users_collection.find_one({"email": user.email}):
            return {"status": "error", "message": "Email already registered"}

        if users_collection.find_one({"username": user.username}):
            return {"status": "error", "message": "Username already taken"}

        new_user = user.model_dump()
        new_user["verified"] = True 

        result = users_collection.insert_one(new_user) 
        return {"status": "success", "message": "User registered successfully", "user_id": str(result.inserted_id)}

    except Exception as e:
        return {"status": "error", "message": f"Database error: {str(e)}"}

##########################################################
def login_user(user: UserLogin) -> dict:
    user_data = users_collection.find_one({"username": user.username, "password": user.password})

    if user_data:
        return {
            "status": "success",
            "message": "Login successful",
            "user": {
                "username": user_data["username"],
                "email": user_data["email"],
                "channels_joined": user_data.get("channels_joined", []),
                "hosted_channels": user_data.get("hosted_channels", [])
            }
        }

    return {"status": "error", "message": "Invalid username or password"}

##########################################################
def visitor_mode(visitor_data: Visitor, ) -> dict:
    if users_collection.find_one({"username": visitor_data.name}):
            return {"status": "error", "message": "Username already taken"}
    if not visitor_data.name:
        return {"status": "error", "message": "Visitor name cannot be empty"}
    
    return {"status": "success", "message": f"Welcome, {visitor_data.name}! You are in visitor mode."}
