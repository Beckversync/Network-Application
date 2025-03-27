from config.db import channels_collection, users_collection
from models.channelModel import Channel

##############################################################################################
def create_channel(host: str, channel_name: str):
    if channels_collection.find_one({"channel_name": channel_name}):
        return {"status": "error", "message": "Channel already exists"}

    new_channel = Channel(
        channel_name=channel_name,
        owner=host,
        members=[host]
    )

    channels_collection.insert_one(new_channel.dict())

    users_collection.update_one(
        {"username": host},
        {"$addToSet": {"hosted_channels": channel_name, "joined_channels": channel_name}}
    )

    return {"status": "success", "message": f"Channel '{channel_name}' created successfully"}

##############################################################################################
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

    return {"status": "success", "message": f"{username} joined '{channel_name}'"}

##############################################################################################
def send_message(username: str, channel_name: str, message_text: str):
    channel_data = channels_collection.find_one({"channel_name": channel_name})
    if not channel_data:
        return {"status": "error", "message": "Channel not found"}

    if username not in channel_data["members"]:
        return {"status": "error", "message": "Only registered users can send messages"}

    new_message = {"sender": username, "text": message_text}

    channels_collection.update_one(
        {"channel_name": channel_name},
        {"$push": {"messages": new_message}}
    )

    return {"status": "success", "message": "Message sent successfully"}

##############################################################################################
def get_messages(channel_name: str):
    channel_data = channels_collection.find_one({"channel_name": channel_name}, {"messages": 1, "_id": 0})
    if not channel_data:
        return {"status": "error", "message": "Channel not found"}

    return {"status": "success", "messages": channel_data.get("messages", [])}
