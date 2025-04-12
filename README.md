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




# README – Hybrid Chat Application (Client-Server & P2P)

## Table of Contents
1. [Introduction](#introduction)
2. [System Architecture](#system-architecture)
3. [Assignment Requirements & Implementation](#assignment-requirements--implementation)
   - [1. Hybrid Paradigm (Client-Server + P2P)](#1-hybrid-paradigm-client-server--p2p)
   - [2. Tracker Protocol (Initialization Phase)](#2-tracker-protocol-initialization-phase)
   - [3. Client-Server Paradigm](#3-client-server-paradigm)
   - [4. Peer-to-Peer Paradigm & Livestream](#4-peer-to-peer-paradigm--livestream)
   - [5. Authentication & Visitor Mode](#5-authentication--visitor-mode)
   - [6. Channel (Chat Room) & Functionalities](#6-channel-chat-room--functionalities)
   - [7. Personal Server / Channel Hosting & Synchronization](#7-personal-server--channel-hosting--synchronization)
   - [8. User Access & Notification](#8-user-access--notification)
   - [9. System Log](#9-system-log)
   - [10. Advanced Features & Extensions](#10-advanced-features--extensions)
4. [Installation & Execution Guide](#installation--execution-guide)
5. [Project Structure & File Descriptions](#project-structure--file-descriptions)
6. [Usage Guide](#usage-guide)
7. [Enhancements & Future Development](#enhancements--future-development)
8. [Team Info & Roles](#team-info--roles)

---

## Introduction

This is a Discord-like Chat Application designed to demonstrate a **hybrid architecture** combining **Client-Server** and **Peer-to-Peer (P2P)** paradigms, with additional support for real-time livestreaming. Key features include:

- Authentication-based login and anonymous Visitor access.
- Creating, joining, and chatting in channels.
- P2P-based livestreaming using UDP.
- Centralized server (tracker + MongoDB) ensures data persistence even when the hosting peer is offline.
- System-wide connection and activity logging.

---

## System Architecture

- **Tracker Server**: Centralized component that maintains an updated list of connected peers.
- **Peer**: Each client instance runs its own peer node:
  - TCP socket for server connection.
  - TCP socket listener for incoming P2P messages.
  - UDP socket for receiving P2P livestream data.
- **MongoDB Database**: Stores persistent data including users, channels, messages, and logs.

### System Diagram:
```
Peer A <----> Peer B
   \           /
    \         / (P2P)
     \       /
      Tracker  (Server) -- MongoDB
```


---

## Assignment Requirements & Implementation

### 1. Hybrid Paradigm (Client-Server + P2P)
- **Requirement**: Support both paradigms.
- **Implementation**:
  - `tracker.py` maintains active peers.
  - `user.py` connects to tracker and enables P2P messaging and livestreaming.

### 2. Tracker Protocol (Initialization Phase)
- **Requirement**: Implement `submit_info`, `add_list`, `get_list` commands.
- **Implementation**:
  - `user.py` → `connect_to_tracker()` sends `CONNECT` command.
  - Tracker stores peer info and replies with peer list on `GET_LIST`.

### 3. Client-Server Paradigm
- **Requirement**: Message storage, authentication, and channel data must go through the server.
- **Implementation**:
  - Implemented via `channelRequest.py`, `channelService.py`, and `MongoDB`.

### 4. Peer-to-Peer Paradigm & Livestream
- **Requirement**: Use P2P to broadcast real-time data (chat or livestream).
- **Implementation**:
  - Chat: `send_p2p_broadcast()` via TCP.
  - Livestream: `start_livestream()` → OpenCV + Base64 + UDP broadcasting.

### 5. Authentication & Visitor Mode
- **Requirement**:
  - Visitors: View-only, no registration needed.
  - Authenticated users: Full permissions.
- **Implementation**:
  - `Login.py` handles both modes.
  - `authService.py` validates `@hcmut.edu.vn` emails.

### 6. Channel (Chat Room) & Functionalities
- **Requirement**: Users can create, join, and interact in channels.
- **Implementation**:
  - Create via “+ Create Channel” (UI → `Home.py`).
  - Backend logic: `channelService.py`, `channelController.py`.
  - Visitor view controlled by `allow_visitor`.

### 7. Personal Server / Channel Hosting & Synchronization
- **Requirement**: Each user can host their own channel; synchronization with server is required.
- **Implementation**:
  - Local files: `offline_<username>.txt`, `hosted_<channel>.json`.
  - Sync logic in `user.py` → `sync_local_channels_with_server()` and `channelService.sync_channels()`.

### 8. User Access & Notification
- **Requirement**: Notify users on new messages.
- **Implementation**:
  - 5-second polling via `poll_new_messages()` in UI.
  - Tracker supports “MSG_RECV” command for pushing updates.

### 9. System Log
- **Requirement**: Log all system events in ASCII format.
- **Implementation**:
  - `Run.py` configures logging with `system.log`.
  - Events: login, message sending, livestream toggling, etc.

### 10. Advanced Features & Extensions
- MongoDB for scalable data persistence.
- Invisible Mode in UI status dropdown.
- GUI built with PyQt6.
- Optional: multi-seeding, REST APIs for bot integration.

---

## Installation & Execution Guide

### 1. Environment Setup
- Python 3.8+
- Install dependencies:
  ```bash
  pip install -r requirements.txt


### 2. MongoDB Configuration
- URI configured in db.py. Ensure your MongoDB instance is accessible.
- Expected log: Connected to MongoDB successfully!

### 3. Start Tracker
  ```bash
  python tracker.py
  ```
(default port 5000)

### 4. Start Main Application
- Mở terminal khác, chạy:
  ```bash
  python Run.py
  ```
- (launches local server + UI)

### 5. Register an Account
- Via GUI → Register → Must use @hcmut.edu.vn email

### 6. Login or Use Viewer Mode
- **Login**: Full access
- **Login as Viewer**: View-only if the channel allows

---

## CProject Structure & File Descriptions

```bash
.
├── Run.py                  # Main app entry, starts internal server and GUI
├── tracker.py              # Tracker server (peer registry)
├── user.py                 # Peer class: P2P logic, UDP, livestream, sync
├── system.log              # Log file for all system events
├── authService.py          # User authentication logic
├── channelService.py       # Channel CRUD operations and message sync
├── authRequest.py          # Entry point for login/register requests
├── channelRequest.py       # Channel request handler
├── UI/
│   ├── Login.py            # PyQt login/register window
│   ├── Home.py             # Main chat interface (channels, messages, members)
├── db.py                   # MongoDB connection
├── ...                     # Additional model/controller files
```


---

## Usage Guide

### 1. Basic Usage
1. **Start the Tracker** by running `tracker.py`.
2. **Launch the Main Application** by executing `Run.py`, which opens the login GUI.
3. **Register** an account (if not already registered).
4. **Log in** using your credentials or click **“Login as Viewer”** for read-only access.

### 2. Create Channel & Chat
1. Click **“+ Create Channel”** in the sidebar to create a new channel, with the option to enable/disable visitor access.
2. In the **Channels** tab, select the newly created channel.
3. Click **“Join Channel”** (if you are the owner, you'll be joined automatically).
4. Type your message and click **“Send”** — it will be saved to the central server.

### 3. Send P2P Messages
- You can send direct P2P messages by calling the `send_p2p_broadcast()` function either from the console or from within `user.py`.

### 4. Livestream
- Enable **“Live Mode (P2P)”** or click **“Start Livestream”** in the interface to start broadcasting your webcam.
- Peers currently online will receive the video stream via **UDP**.

### 5. Offline Caching & Synchronization
- If the peer cannot send a message (e.g., due to connectivity loss), it will be saved in a local file (`offline_<username>.txt`).
- When the peer reconnects, `sync_offline_messages()` automatically sends the cached messages.
- Similarly, **hosted channels** store messages locally when offline, and they are synchronized to the server upon reconnection.

### 6. Status Management
- A dropdown allows users to switch between:
  - **Online**: Fully connected and visible to other users.
  - **Offline**: Disconnected from the tracker; no messages sent/received.
  - **Invisible**: Functions like Online but appears Offline to others.



