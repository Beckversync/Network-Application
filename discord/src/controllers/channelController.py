# file: channelController.py
from services.channelService import (
    create_channel, join_channel, send_message, get_channel_info,
    get_joined_channels, get_hosted_channels, delete_channel, get_all_channels,
    sync_channels
)

def create_channel_controller(data):
    host = data.get("host")
    channel_name = data.get("channel_name")
    allow_visitor = data.get("allow_visitor", True)
    if not host or not channel_name:
        return {"status": "error", "message": "Missing parameters"}
    result = create_channel(host, channel_name, allow_visitor)
    return result

def join_channel_controller(data):
    username = data.get("username")
    channel_name = data.get("channel_name")
    if not username or not channel_name:
        return {"status": "error", "message": "Missing parameters"}
    result = join_channel(username, channel_name)
    return result

def get_user_channels_controller(data):
    username = data.get("username")
    if not username:
        return {"status": "error", "message": "Missing parameters"}
    joined_result = get_joined_channels(username)
    hosted_result = get_hosted_channels(username)
    if joined_result["status"] == "error" or hosted_result["status"] == "error":
        return {"status": "error", "message": "User not found"}
    return {
        "status": "success",
        "data": {
            "joined_channels": joined_result.get("joined_channels", []),
            "hosted_channels": hosted_result.get("hosted_channels", [])
        }
    }

def send_message_controller(data):
    username = data.get("username")
    channel_name = data.get("channel_name")
    message_text = data.get("message")
    if not username or not channel_name or not message_text:
        return {"status": "error", "message": "Missing parameters"}
    result = send_message(username, channel_name, message_text)
    return result

def get_channel_info_controller(data):
    channel_name = data.get("channel_name")
    if not channel_name:
        return {"status": "error", "message": "Missing parameters"}
    result = get_channel_info(channel_name)
    is_visitor = data.get("is_visitor", False)
    if result.get("status") == "success" and is_visitor and not result.get("allow_visitor", True):
         return {"status": "error", "message": "This channel does not allow visitor viewing operation"}
    return result

def delete_channel_controller(data):
    username = data.get("username")
    channel_name = data.get("channel_name")
    if not username or not channel_name:
        return {"status": "error", "message": "Missing parameters"}
    result = delete_channel(username, channel_name)
    return result

def get_all_channels_controller(data):
    result = get_all_channels()
    return result

def get_all_users_controller(data):
    from services.authService import get_all_users
    return get_all_users()

# >>> NEW <<<
def sync_channels_controller(data):
    username = data.get("username")
    local_channels = data.get("local_channels")
    if not username or not local_channels:
        return {"status": "error", "message": "Missing username or local_channels"}
    result = sync_channels(local_channels, username)
    return result
