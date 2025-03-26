import json
from controllers.authController import register, login, visitor

def handle_request(data: str) -> str:
    try:
        request = json.loads(data)
        action = request.get("action")

        if action == "register":
            response = register(request)
        elif action == "login":
            response = login(request)
        elif action == "visitor":
            response = visitor(request)
        else:
            response = {"status": "error", "message": "Invalid action"}

        return json.dumps(response)

    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})
