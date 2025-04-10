from config.db import channels_collection, users_collection
from models.channelModel import Channel
import logging

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s')

def create_channel(host: str, channel_name: str, is_private: bool):
    if channels_collection.find_one({"channel_name": channel_name}):
        return {"status": "error", "message": "Channel already exists"}
    
    new_channel = Channel(
        channel_name=channel_name,
        owner=host,
        members=[host],
        is_private=is_private,
        join_requests=[] 
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
    # Trả về cả trường allow_visitor để kiểm tra trong trường hợp yêu cầu của visitor
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
