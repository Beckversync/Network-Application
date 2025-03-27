from services.channelService import create_channel, join_channel, send_message, get_messages

##############################################################################################
def create_channel_controller(data):
    host = data.get("host")
    channel_name = data.get("channel_name")

    if not host or not channel_name:
        return {"status": "error", "message": "Missing parameters"}

    result = create_channel(host, channel_name)
    return result

##############################################################################################
def join_channel_controller(data):
    username = data.get("username")
    channel_name = data.get("channel_name")

    if not username or not channel_name:
        return {"status": "error", "message": "Missing parameters"}

    result = join_channel(username, channel_name)
    return result

##############################################################################################
# def get_channel_info_controller(data):
#     channel_name = data.get("channel_name")

#     if not channel_name:
#         return {"status": "error", "message": "Missing parameters"}

#     result = get_channel_info(channel_name)
#     return result

##############################################################################################
def send_message_controller(data):
    username = data.get("username")
    channel_name = data.get("channel_name")
    message_text = data.get("message")

    if not username or not channel_name or not message_text:
        return {"status": "error", "message": "Missing parameters"}

    result = send_message(username, channel_name, message_text)
    return result

##############################################################################################
def get_messages_controller(data):
    """Controller để lấy danh sách tin nhắn của kênh."""
    
    channel_name = data.get("channel_name")

    if not channel_name:
        return {"status": "error", "message": "Missing parameters"}

    result = get_messages(channel_name)
    return result
