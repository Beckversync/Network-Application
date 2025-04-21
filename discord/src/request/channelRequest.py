import json
from controllers.channelController import (
    create_channel_controller,
    join_channel_controller,
    get_channel_info_controller,
    send_message_controller,
    get_user_channels_controller,
    delete_channel_controller,
    get_all_channels_controller,
    get_all_users_controller,
    approve_join_request_controller, 
    get_join_requests_controller, 
    reject_join_request_controller, 
    get_hosted_channels_controller,
    send_message_p2p_controller
)

def handle_channel_request(data: str) -> str:
    try:
        if not data:
            return json.dumps({"status": "error", "message": "No data provided"})
        request = json.loads(data)
        if not isinstance(request, dict):
            return json.dumps({"status": "error", "message": "Invalid request format"})
        action = request.get("action")
        if action == "create_channel":
            response = create_channel_controller(request)
        elif action == "join_channel":
            response = join_channel_controller(request)
        elif action == "get_channel_info":
            response = get_channel_info_controller(request)
        elif action == "send_message":
            response = send_message_controller(request)
        elif action == "get_user_channels":
            response = get_user_channels_controller(request)
        elif action == "delete_channel":
            response = delete_channel_controller(request)
        elif action == "get_all_channels":
            response = get_all_channels_controller(request)
        elif action == "get_all_users":
            response = get_all_users_controller(request)
        elif action == "approve_join_request":
            response = approve_join_request_controller(request)
        elif action == "get_join_requests":
            response = get_join_requests_controller(request)
        elif action == "reject_join_request":
            response = reject_join_request_controller(request)
        elif action == "get_hosted_channels":
            response = get_hosted_channels_controller(request)
        elif action == "send_message_p2p":
            response = send_message_p2p_controller(request)
        else:
            response = {"status": "error", "message": "Invalid action"}
        return json.dumps(response)
    except json.JSONDecodeError:
        return json.dumps({"status": "error", "message": "Invalid JSON format"})
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})
