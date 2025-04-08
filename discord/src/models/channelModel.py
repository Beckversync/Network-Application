from pydantic import BaseModel
from typing import List

class Channel(BaseModel):
    channel_name: str
    owner: str
    members: List[str] = []
    allow_visitor: bool = True  # Thêm trường này để thiết lập quyền cho visitor xem nội dung của channel
