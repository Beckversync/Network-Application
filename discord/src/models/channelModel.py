from pydantic import BaseModel
from typing import List

class Channel(BaseModel):
    channel_name: str
    owner: str
    members: List[str] = []
    is_private: bool = False
    join_requests: List[str] = []
