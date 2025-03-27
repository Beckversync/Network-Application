from pydantic import BaseModel # type: ignore
from typing import List

class UserRegister(BaseModel):
    username: str
    email: str
    password: str

class Visitor(BaseModel):
    name: str

class UserLogin(BaseModel):
    username: str
    password: str
    channels_joined: List[str] = []
    hosted_channels: List[str] = []
