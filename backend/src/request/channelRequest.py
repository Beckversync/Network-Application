import json
from controllers.channelController import (
    create_channel_controller,
    join_channel_controller,
    get_messages_controller,
    send_message_controller
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
        elif action == "get_messages":
            response = get_messages_controller(request)
        elif action == "send_message":
            response = send_message_controller(request)
        else:
            response = {"status": "error", "message": "Invalid action"}

        return json.dumps(response)

    except json.JSONDecodeError:
        return json.dumps({"status": "error", "message": "Invalid JSON format"})
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})
