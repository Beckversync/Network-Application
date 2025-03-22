
from fastapi import HTTPException  # type: ignore
from models.authModel import UserRegister, UserLogin, Visitor
from services.authService import register_user, login_user, visitor_mode
##########################################################
def register(user: UserRegister):
    result = register_user(user)
    
    if result["message"] == "User registered successfully":
        return result
    if result["message"] == "Email already registered":
        raise HTTPException(status_code=409, detail=result["message"])
    if result["message"] == "Username already taken":
        raise HTTPException(status_code=409, detail=result["message"])
    
    raise HTTPException(status_code=500, detail="Failed to process registration")
##########################################################
def login(user: UserLogin):
    result = login_user(user)
    
    if result["message"] == "Login successful":
        return result
    raise HTTPException(status_code=403, detail=result["message"])
##########################################################
def visitor(visitor_data: Visitor):
    result = visitor_mode(visitor_data)
    
    if "message" in result:
        return result
    raise HTTPException(status_code=400, detail="Invalid visitor request")