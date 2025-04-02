from pydantic import BaseModel # type: ignore
from typing import List

class Channel(BaseModel):
    channel_name: str
    owner: str
    members: List[str] = []
