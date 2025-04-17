import json
import os
import time
import threading
import logging
from request import channelRequest

class SyncManager:
    def __init__(self, username: str, channel_name: str, local_sync_file: str = None):
        self.username = username
        self.channel_name = channel_name
        # File dùng để lưu các message cục bộ khi chưa sync
        self.local_sync_file = local_sync_file or f"sync_{channel_name}_{username}.txt"
        self.last_sync_time = 0  # Sử dụng timestamp (epoch seconds) để đánh dấu lần sync cuối
    
    def save_down(self, message_data: dict):
        """
        Lưu tin nhắn được gửi đến vào file local_sync_file dưới dạng:
        [HH:MM:SS YYYY-MM-DD] sender: text
        """
        try:
            # Đảm bảo định dạng có đủ các trường cần thiết
            readable_time = message_data.get("readable_time", "unknown_time")
            sender = message_data.get("sender", "unknown_sender")
            text = message_data.get("text", "")
            line = f"[{readable_time}] {sender}: {text}\n"

            # Ghi vào file
            with open(self.local_sync_file, 'a', encoding='utf-8') as f:
                f.write(line)

            logging.info("[SAVE_DOWN] Đã lưu tin nhắn: %s", line.strip())

        except Exception as e:
            logging.error("[SAVE_DOWN] Lỗi khi lưu tin nhắn: %s", e)

    def sync_up(self):
        """
        Đọc các message cục bộ từ file và gửi lên server thông qua API send_message.
        Sau khi gửi thành công, file sẽ được xóa.
        """
        if os.path.exists(self.local_sync_file):
            try:
                with open(self.local_sync_file, 'r', encoding='utf-8') as f:
                    messages = [line.strip() for line in f if line.strip()]
                if messages:
                    logging.info("[SYNC] Syncing %d local messages for channel '%s'", len(messages), self.channel_name)
                    for msg in messages:
                        request_data = {
                            "action": "send_message",
                            "username": self.username,
                            "channel_name": self.channel_name,
                            "message": msg
                        }
                        response_str = channelRequest.handle_channel_request(json.dumps(request_data))
                        response = json.loads(response_str)
                        if response.get("status") != "success":
                            logging.error("[SYNC] Failed to sync message: %s", msg)
                        else:
                            logging.info("[SYNC] Synced message: %s", msg)
                    # Sau khi sync xong, xóa file cục bộ
                    os.remove(self.local_sync_file)
                    logging.info("[SYNC] Local sync file cleared.")
            except Exception as e:
                logging.error("[SYNC] Error syncing local messages: %s", e)

    def sync_down(self):
        """
        Lấy danh sách message từ Centralized Server của channel bằng API get_channel_info.
        So sánh dựa trên timestamp (nếu có) để tìm tin mới mà chưa được đồng bộ và cập nhật.
        """
        request_data = {
            "action": "get_channel_info",
            "channel_name": self.channel_name,
            "username": self.username
        }
        try:
            response_str = channelRequest.handle_channel_request(json.dumps(request_data))
            response = json.loads(response_str)
            if response.get("status") == "success":
                messages = response.get("messages", [])
                new_messages = []
                for msg in messages:
                    # Giả định message có trường "timestamp" để so sánh; nếu chưa có, ta có thể bổ sung khi gửi message.
                    try:
                        timestamp = float(msg.get("timestamp", 0))
                    except:
                        timestamp = 0
                    if timestamp > self.last_sync_time:
                        new_messages.append(msg)
                if new_messages:
                    logging.info("[SYNC] Found %d new messages from server for channel '%s'", len(new_messages), self.channel_name)
                    self.last_sync_time = max(float(msg.get("timestamp", 0)) for msg in new_messages)
                    for msg in new_messages:
                        logging.info("[SYNC] New message: %s: %s", msg.get("sender"), msg.get("text"))
                    # Sau khi lấy tin mới, bạn có thể cập nhật lại giao diện hoặc lưu vào file cục bộ.
            else:
                logging.error("[SYNC] Sync down failed: %s", response.get("message"))
        except Exception as e:
            logging.error("[SYNC] Error syncing down: %s", e)

    def start_periodic_sync(self, interval: int = 30):
        """
        Bắt đầu một luồng background tiến hành đồng bộ lên (sync_up) và đồng bộ xuống (sync_down)
        theo khoảng thời gian interval (giây).
        """
        def sync_loop():
            while True:
                self.sync_up()
                self.sync_down()
                time.sleep(interval)
        threading.Thread(target=sync_loop, daemon=True).start()
