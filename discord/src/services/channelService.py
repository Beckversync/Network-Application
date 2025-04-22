from config.db import channels_collection, users_collection
from models.channelModel import Channel
import logging
import time
import datetime
import socket
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s')
import json

def create_channel(host: str, channel_name: str, is_private: bool, allow_visitor: bool):
    if channels_collection.find_one({"channel_name": channel_name}):
        return {"status": "error", "message": "Channel already exists"}
    
    new_channel = Channel(
        channel_name=channel_name,
        owner=host,
        members=[], 
        is_private=is_private,
        join_requests=[],
        allow_visitor=allow_visitor
    )
    
    channels_collection.insert_one(new_channel.dict())
    
    users_collection.update_one(
        {"username": host},
        {"$addToSet": {"hosted_channels": channel_name, "joined_channels": channel_name}}
    )
    
    logging.info("Channel '%s' created by %s (is_private=%s)", channel_name, host, is_private)
    
    return {"status": "success", "message": f"Channel '{channel_name}' created successfully"}

def join_channel(username: str, channel_name: str):
    channel = channels_collection.find_one({"channel_name": channel_name})
    if not channel:
        return {"status": "error", "message": "Channel not found"}

    if username in channel.get("members", []):
        return {"status": "error", "message": "User already in channel"}

    if not channel.get("is_private", False):  # public channel
        channels_collection.update_one(
            {"channel_name": channel_name},
            {"$push": {"members": username}}
        )
        users_collection.update_one(
            {"username": username},
            {"$addToSet": {"joined_channels": channel_name}}
        )
        logging.info("User %s joined public channel '%s'", username, channel_name)
        return {"status": "success", "message": f"{username} joined public channel '{channel_name}'"}
    
    else:  # private channel
        if username in channel.get("join_requests", []):
            return {"status": "info", "message": "Join request already sent"}
        
        channels_collection.update_one(
            {"channel_name": channel_name},
            {"$addToSet": {"join_requests": username}}
        )
        logging.info("User %s requested to join private channel '%s'", username, channel_name)
        return {"status": "info", "message": "Join request sent to channel owner"}
    
def approve_join_request(owner: str, channel_name: str, target_user: str):
    channel = channels_collection.find_one({"channel_name": channel_name})
    if not channel or channel["owner"] != owner:
        return {"status": "error", "message": "Only the channel owner can approve requests"}

    if target_user not in channel.get("join_requests", []):
        return {"status": "error", "message": "No join request from this user"}

    channels_collection.update_one(
        {"channel_name": channel_name},
        {
            "$addToSet": {"members": target_user},
            "$pull": {"join_requests": target_user}
        }
    )
    users_collection.update_one(
        {"username": target_user},
        {"$addToSet": {"joined_channels": channel_name}}
    )
    logging.info("User %s approved to join channel '%s' by %s", target_user, channel_name, owner)
    return {"status": "success", "message": f"{target_user} approved to join '{channel_name}'"}

def reject_join_request(owner: str, channel_name: str, target_user: str):
    channel = channels_collection.find_one({"channel_name": channel_name})
    if not channel or channel["owner"] != owner:
        return {"status": "error", "message": "Only the channel owner can reject requests"}

    if target_user not in channel.get("join_requests", []):
        return {"status": "error", "message": "No join request from this user"}

    channels_collection.update_one(
        {"channel_name": channel_name},
        {"$pull": {"join_requests": target_user}}
    )
    logging.info("User %s rejected from channel '%s' by %s", target_user, channel_name, owner)
    return {"status": "success", "message": f"{target_user} has been rejected from '{channel_name}'"}

def get_join_requests(owner: str, channel_name: str):
    channel = channels_collection.find_one({"channel_name": channel_name})
    
    if not channel:
        return {"status": "error", "message": "Channel not found"}

    if channel["owner"] != owner:
        return {"status": "error", "message": "Only the channel owner can view join requests"}

    join_requests = channel.get("join_requests", [])
    return {
        "status": "success",
        "join_requests": join_requests
    }
def send_message(username: str, channel_name: str, message_text: str):
    channel_data = channels_collection.find_one({"channel_name": channel_name})
    if not channel_data:
        return {"status": "error", "message": "Channel not found"}

    if channel_data.get("is_private", False) and username not in channel_data.get("members", []):
        return {
            "status": "error",
            "message": "You do not have permission to send messages in this private channel"
        }
    timestamp = time.time()
    readable_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    new_message = {
        "sender": username,
        "text": f"[{readable_time}] {username}: {message_text}"
    }
    channels_collection.update_one(
            {"channel_name": channel_name},
            {"$push": {"messages": new_message}}
    )
    return {"status": "success", "message": "Message sent successfully"}

def send_to_p2p_server(peer_ip, peer_port, message_text, sender="Unknown", channel=None, owner=None):
    try:
        data_dict = {
            "type": "chat",
            "sender": sender,
            "message": message_text
        }
        # thêm thông tin kênh và chủ kênh
        if channel is not None:
            data_dict["channel"] = channel
        if owner is not None:
            data_dict["owner"] = owner

        json_str = json.dumps(data_dict)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((peer_ip, peer_port))
            s.sendall(json_str.encode('utf-8'))
        logging.info("Sent P2P chat to %s:%s – %s", peer_ip, peer_port, json_str)
        return {"status": "success"}
    except Exception as e:
        logging.error("P2P send error: %s", e)
        return {"status": "error", "message": str(e)}


def send_message_p2p(username: str, channel_name: str, message_text: str):
    from config.db import channels_collection, users_collection
    from services.channelService import send_message  # để backup vào DB
    import logging

    channel_data = channels_collection.find_one({"channel_name": channel_name})
    if not channel_data:
        return {"status": "error", "message": "Không tìm thấy kênh"}

    # Kiểm quyền gửi trong kênh riêng tư
    if channel_data.get("is_private", False) and username not in channel_data.get("members", []):
        return {
            "status": "error",
            "message": "Bạn không có quyền gửi tin nhắn trong kênh riêng tư này"
        }

    owner_username = channel_data.get("owner")
    owner_data     = users_collection.find_one({"username": owner_username})

    success_count, sent_targets = 0, set()

    # ❶ Nếu chủ kênh đang online → gửi P2P tới các peer online
    if owner_data and owner_data.get("state") == "online":
        for member in channel_data.get("members", []):
            user = users_collection.find_one({"username": member})
            if not user or user.get("state") != "online":
                continue
            for sess in user.get("sessions", []):
                peer_ip   = sess.get("peer_ip")
                peer_port = sess.get("peer_port")
                target    = f"{peer_ip}:{peer_port}"
                if peer_ip and peer_port and target not in sent_targets:
                    send_to_p2p_server(
                        peer_ip, peer_port,
                        message_text,
                        sender=username,
                        channel=channel_name,
                        owner=owner_username
                    )
                    sent_targets.add(target)
                    success_count += 1

        logging.info(
            "Tin nhắn từ %s đã gửi tới %d peer online trong kênh '%s'",
            username, success_count, channel_name
        )

    # ❷ LUÔN backup tin nhắn vào MongoDB để peer offline có thể lấy về
    send_message(username, channel_name, message_text)

    # Trả về thông báo
    if success_count:
        return {
            "status": "success",
            "message": f"Đã gửi tới {success_count} peer online và backup vào kênh"
        }
    else:
        return {
            "status": "success",
            "message": "Chủ kênh offline – tin nhắn đã lưu vào kênh"
        }




def get_channel_info(channel_name: str, username: str) -> dict:
    channel = channels_collection.find_one({"channel_name": channel_name})
    if not channel:
        return {"status": "error", "message": "Channel not found"}
    
    # Nếu channel là private và user không nằm trong members, trả về lỗi
    if channel.get("is_private", False) and username not in channel.get("members", []):
        return {
            "status": "error",
            "message": "This is a private channel. You do not have permission to see old messages."
        }
    
    elif channel.get("is_private", True):
        return {
            "status": "success",
            "channel_name": channel["channel_name"],
            "owner": channel["owner"],
            "members": channel["members"],
            "messages": channel.get("messages", []),
            "allow_visitor": channel.get("allow_visitor", True),
            "is_private": channel.get("is_private", False)
        }
    
    return {
        "status": "success",
        "channel_name": channel["channel_name"],
        "owner": channel["owner"],
        "members": channel["members"],
        "messages": channel.get("messages", []),
        "allow_visitor": channel.get("allow_visitor", True),
        "is_private": channel.get("is_private", False)
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
