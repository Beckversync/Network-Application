import json
from models.authModel import UserRegister, UserLogin, Visitor
from services.authService import register_user, login_user, visitor_mode

def register(data):
    user = UserRegister(**data)
    result = register_user(user)

    return json.dumps(result)

def login(data):
    user = UserLogin(**data)
    result = login_user(user)

    return json.dumps(result)


def visitor(data):
    visitor_data = Visitor(**data)
    result = visitor_mode(visitor_data)

    return json.dumps(result)
