from fastapi import APIRouter, HTTPException  # type: ignore
from models.authModel import UserRegister, UserLogin, Visitor
from controllers.authController import register, login, visitor

router = APIRouter()
##########################################################
@router.post("/register", status_code=201)
def register_endpoint(user: UserRegister):
    return register(user)
##########################################################
@router.post("/login", status_code=200)
def login_endpoint(user: UserLogin):
    return login(user)
##########################################################
@router.post("/visitor", status_code=200)
def visitor_endpoint(visitor_data: Visitor):
    return visitor(visitor_data)
