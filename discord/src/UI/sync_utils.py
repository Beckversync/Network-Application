# sync_utils.py
import os
from typing import List, Union, Dict

def dump_messages_to_file(channel: str,
                          username: str,
                          messages: List[Union[str, Dict]]) -> int:
    """
    Ghi thêm các tin nhắn mới vào local_sync/sync_<channel>_<user>.txt
    • Tránh lưu trùng dòng.
    • Trả về số dòng vừa thêm.
    """
    os.makedirs("local_sync", exist_ok=True)
    path = os.path.join("local_sync",
                        f"sync_{channel}_{username}.txt")

    # Đọc các dòng đã có để chống trùng
    existed = set()
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            existed = {line.strip() for line in f if line.strip()}

    added = 0
    with open(path, "a", encoding="utf-8") as f:
        for msg in messages:
            # chấp nhận cả str hoặc dict {"text": "..."}
            line = msg if isinstance(msg, str) else msg.get("text", "")
            line = line.strip()
            if line and line not in existed:
                f.write(line + "\n")
                added += 1
    return added
