# DEVELOP A NETWORK APPLICATION

[![Python](https://img.shields.io/badge/python-3.7%2B-blue)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)


Build a simple segment chat application (Discord-like) with application protocols defined by
each group, using the **TCP/IP** protocol stack.

<p align="center">
<img width=800 src="https://github.com/user-attachments/assets/f0feb615-fd1d-424c-b169-6b142bbc5516"/>
</p>

# Discord Clone – P2P Segment Chat Application

> Ứng dụng mạng mô phỏng Discord mini sử dụng mô hình kết hợp giữa Client-Server và Peer-to-Peer. Được xây dựng nhằm phục vụ học phần **Computer Networks**, Semester 1, 2024-2025.

---

##  Tính Năng Chính

- **Hybrid Architecture**: Kết hợp Client-Server (Tracker) và Peer-to-Peer (Chat, Livestream)
- **Authentication**: Đăng nhập, đăng ký tài khoản, hỗ trợ chế độ Viewer (không cần đăng nhập)
- **Channel Management**: Tạo, gửi tin nhắn, xem lịch sử chat
- **P2P Livestream**: Truyền hình ảnh webcam trực tiếp qua UDP
- **Offline Message Sync**: Lưu tin nhắn khi offline và đồng bộ lại khi kết nối trở lại
- **System Logging**: Ghi log quá trình kết nối và hoạt động

---

##  Yêu Cầu Cài Đặt

### Python

- Phiên bản yêu cầu: **Python 3.7+**

### Thư viện cần cài đặt

```bash
pip install PyQt6 opencv-python pymongo pydantic
```

### MongoDB

- Ứng dụng sử dụng MongoDB Atlas hoặc MongoDB local.
- Đảm bảo bạn đã cài đặt MongoDB và sửa `uri` trong file `db.py`:

```python
# Nếu dùng MongoDB Atlas:
uri = "mongodb+srv://<username>:<password>@<cluster-url>"

# Hoặc dùng MongoDB local:
uri = "mongodb://localhost:27017/"
```

---

##  Cách Chạy Ứng Dụng

### 1. Khởi động Tracker Server

```bash
python tracker.py
```

Tracker sẽ lắng nghe tại `127.0.0.1:5000`.

### 2. Mở Giao Diện Chính

```bash
python Run.py
```

> Lưu ý: Luôn đảm bảo tracker chạy trước khi mở ứng dụng chính.

---

##  Cấu Trúc Thư Mục

```
.
├── Run.py                  # Khởi động giao diện PyQt
├── tracker.py              # Tracker server (TCP server)
├── user.py                 # Peer logic: P2P chat, livestream, offline cache
├── Home.py                 # Giao diện chat chính (giống Discord)
├── Login.py                # Giao diện login/register
│
├── channelService.py       # Business logic xử lý channel
├── authService.py          # Business logic xử lý đăng nhập/đăng ký
├── channelController.py    # Controller cho channel
├── authController.py       # Controller cho auth
├── channelRequest.py       # Xử lý request liên quan đến channel
├── authRequest.py          # Xử lý request liên quan đến auth
│
├── channelModel.py         # Pydantic model cho channel
├── authModel.py            # Pydantic model cho user
├── db.py                   # Kết nối MongoDB
│
└── README.md               # Tài liệu hướng dẫn 
```

---

##  Một Số Tính Năng Nổi Bật

| Tính năng | Mô tả |
|----------|-------|
|  Login / Viewer | Đăng nhập hoặc vào với tư cách người xem |
|  Chat Channel | Tạo và gửi tin nhắn vào kênh |
|  P2P Livestream | Truyền video trực tiếp qua UDP |
|  Offline Sync | Tin nhắn bị mất sẽ được lưu và gửi lại sau |
|  Log File | Ghi vào `system.log` toàn bộ kết nối và tin nhắn |

---





## Installation
Clone this repository:
```bash
git clone https://github.com/Beckversync/Network-Application.git
```


