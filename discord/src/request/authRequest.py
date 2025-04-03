import json
from controllers.authController import register, login, visitor, logout

def handle_request(data: str, peer_ip: str, peer_port: int) -> str:
    try:
        request = json.loads(data)
        action = request.get("action")

        if action == "register":
            response = register(request)
        elif action == "login":
            response = login(request, peer_ip, peer_port)
        elif action == "visitor":
            response = visitor(request)
        elif action == "logout":
            response = logout(request)
        else:
            response = {"status": "error", "message": "Invalid action"}

        return json.dumps(response)

    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})
