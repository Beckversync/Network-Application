# file: channelService.py
from config.db import channels_collection, users_collection
from models.channelModel import Channel
import logging
from typing import Dict, Any, List

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s')

def create_channel(host: str, channel_name: str, allow_visitor: bool = True):
    if channels_collection.find_one({"channel_name": channel_name}):
        return {"status": "error", "message": "Channel already exists"}
    new_channel = Channel(
        channel_name=channel_name,
        owner=host,
        members=[host],
        allow_visitor=allow_visitor
    )
    channels_collection.insert_one(new_channel.dict())
    users_collection.update_one(
        {"username": host},
        {"$addToSet": {"hosted_channels": channel_name, "joined_channels": channel_name}}
    )
    logging.info("Channel '%s' created by %s with allow_visitor=%s", channel_name, host, allow_visitor)
    return {"status": "success", "message": f"Channel '{channel_name}' created successfully"}

def join_channel(username: str, channel_name: str):
    channel = channels_collection.find_one({"channel_name": channel_name})
    if not channel:
        return {"status": "error", "message": "Channel not found"}
    if username in channel["members"]:
        return {"status": "error", "message": "User already in channel"}
    channels_collection.update_one(
        {"channel_name": channel_name},
        {"$push": {"members": username}}
    )
    users_collection.update_one(
        {"username": username},
        {"$addToSet": {"joined_channels": channel_name}}
    )
    logging.info("User %s joined channel '%s'", username, channel_name)
    return {"status": "success", "message": f"{username} joined '{channel_name}'"}

def send_message(username: str, channel_name: str, message_text: str):
    channel_data = channels_collection.find_one({"channel_name": channel_name})
    if not channel_data:
        return {"status": "error", "message": "Channel not found"}
    new_message = {"sender": username, "text": message_text}
    channels_collection.update_one(
        {"channel_name": channel_name},
        {"$push": {"messages": new_message}}
    )
    logging.info("Message from %s sent in channel '%s'", username, channel_name)
    return {"status": "success", "message": "Message sent successfully"}

def get_channel_info(channel_name: str) -> dict:
    channel = channels_collection.find_one({"channel_name": channel_name})
    if not channel:
        return {"status": "error", "message": "Channel not found"}
    return {
        "status": "success",
        "channel_name": channel["channel_name"],
        "owner": channel["owner"],
        "members": channel["members"],
        "messages": channel.get("messages", []),
        "allow_visitor": channel.get("allow_visitor", True)
    }

def get_joined_channels(username: str):
    user_data = users_collection.find_one({"username": username}, {"joined_channels": 1, "_id": 0})
    if not user_data:
        return {"status": "error", "message": "User not found"}
    return {"status": "success", "joined_channels": user_data.get("joined_channels", [])}

def get_hosted_channels(username: str):
    user_data = users_collection.find_one({"username": username}, {"hosted_channels": 1, "_id": 0})
    if not user_data:
        return {"status": "error", "message": "User not found"}
    return {"status": "success", "hosted_channels": user_data.get("hosted_channels", [])}

def delete_channel(username: str, channel_name: str):
    channel = channels_collection.find_one({"channel_name": channel_name})
    if not channel:
        return {"status": "error", "message": "Channel not found"}
    if channel["owner"] != username:
        return {"status": "error", "message": "Only the owner can delete the channel"}
    channels_collection.delete_one({"channel_name": channel_name})
    users_collection.update_many(
        {},
        {"$pull": {"hosted_channels": channel_name, "joined_channels": channel_name}}
    )
    logging.info("Channel '%s' deleted by %s", channel_name, username)
    return {"status": "success", "message": f"Channel '{channel_name}' deleted successfully"}

def get_all_channels():
    channels = channels_collection.find({}, {"_id": 0, "channel_name": 1, "owner": 1})
    all_channels = list(channels)
    return {"status": "success", "data": all_channels}

# >>> NEW <<<
def sync_channels(local_channels: Dict[str, Any], username: str) -> dict:
    """
    local_channels có dạng:
      {
        "<channel_name>": {
          "name": "<channel_name>",
          "members": [...],
          "messages": [ { "sender": ..., "text": ... }, ... ]
        },
        ...
      }
    Ta sẽ đồng bộ mỗi channel với DB. Trường 'owner' = username (chủ kênh).
    Nếu channel chưa tồn tại trên server, ta tạo. Nếu đã tồn tại, merge tin nhắn hai chiều.
    Trả về "synced_channels" là phiên bản cuối cùng (danh sách messages, members, …).
    """
    synced_channels = {}

    for ch_name, ch_data in local_channels.items():
        # Kiểm tra kênh trên server
        existing = channels_collection.find_one({"channel_name": ch_name})
        if not existing:
            # Tạo mới
            # Lưu ý: ta giả định host= username
            new_channel = Channel(
                channel_name=ch_name,
                owner=username,
                members=ch_data.get("members", [username]),
                allow_visitor=True  # tuỳ ý
            )
            channels_collection.insert_one(new_channel.dict())
            # Ghi messages local lên server
            local_msgs = ch_data.get("messages", [])
            if local_msgs:
                for msg in local_msgs:
                    channels_collection.update_one(
                        {"channel_name": ch_name},
                        {"$push": {"messages": msg}}
                    )
            logging.info("Created channel '%s' on server from local host '%s'", ch_name, username)

            # Thêm kênh vào hosted_channels của user
            users_collection.update_one(
                {"username": username},
                {"$addToSet": {"hosted_channels": ch_name, "joined_channels": ch_name}}
            )

            # synced_channels[ch_name] = final info
            synced_channels[ch_name] = {
                "owner": username,
                "members": ch_data.get("members", [username]),
                "messages": local_msgs
            }
        else:
            # Kênh đã tồn tại -> merge messages
            server_msgs = existing.get("messages", [])
            local_msgs = ch_data.get("messages", [])

            # 1) Thêm tin từ server vào local nếu local chưa có
            #    (Ở đây so sánh dict msg, thực tế nên so sánh theo id/time)
            for sm in server_msgs:
                if sm not in local_msgs:
                    local_msgs.append(sm)

            # 2) Đẩy tin nhắn local lên server
            for lm in local_msgs:
                if lm not in server_msgs:
                    channels_collection.update_one(
                        {"channel_name": ch_name},
                        {"$push": {"messages": lm}}
                    )

            # 3) Merge members
            server_members = existing.get("members", [])
            local_members = ch_data.get("members", [])
            # Ai chưa có trong server_members thì push
            for mem in local_members:
                if mem not in server_members:
                    server_members.append(mem)
            # Ai chưa có trong local thì thêm
            for mem in server_members:
                if mem not in local_members:
                    local_members.append(mem)

            channels_collection.update_one(
                {"channel_name": ch_name},
                {
                    "$set": {
                        "messages": local_msgs,
                        "members": server_members
                    }
                }
            )
            logging.info("Merged channel '%s' from local <-> server for host '%s'", ch_name, username)

            # Lưu final merged
            synced_channels[ch_name] = {
                "owner": existing["owner"],
                "members": server_members,
                "messages": local_msgs
            }

    return {
        "status": "success",
        "message": "Sync completed",
        "synced_channels": synced_channels
    }
