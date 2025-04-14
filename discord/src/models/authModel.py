from pydantic import BaseModel
from typing import List, Dict
from typing import Optional

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
    sessions: List[Dict[str, str]] = []
    state: Optional[str] = "offline"
