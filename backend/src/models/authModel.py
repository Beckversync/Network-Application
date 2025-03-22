from pydantic import BaseModel  # type: ignore

class UserRegister(BaseModel):
    username: str
    email: str
    password: str

class Visitor(BaseModel):
    name: str

class UserLogin(BaseModel):
    username: str
    password: str
