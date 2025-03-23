# DEVELOP A NETWORK APPLICATION

[![Python](https://img.shields.io/badge/python-3.7%2B-blue)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)


Build a simple segment chat application (Discord-like) with application protocols defined by
each group, using the **TCP/IP** protocol stack.

<p align="center">
<img width=800 src="https://github.com/user-attachments/assets/f0feb615-fd1d-424c-b169-6b142bbc5516"/>
</p>

## Application overview
● Hybrid paradigm: This application uses both client-server paradigm and peer-to-peer
paradigm.

● The application performs the client-server during the initialization time to submit the
information of upcoming new peers.

● The application leverages peer-to-peer to broadcast the content from one peer to all
other peers (as a live streaming session).

● The application supports client-server when the live streamer is offline which is in low
traffic conditions.

● Hosts: there are two types of hosts in this system: a centralized server and several
normal PCs


## Table of Contents
- [Installation](#installation)
- [Usage](#usage)
  - [Start the Tracker](#start-the-tracker)
  - [Start Peer Servers](#start-peer-servers)
  - [Start Peer Clients](#start-peer-clients)
  - [Interacting with Peers](#interacting-with-peers)
- [Stopping the System](#stopping-the-system)
- [Notes](#notes)
- [Contact](#contact)

## Installation
Clone this repository:
```bash
git clone https://github.com/Beckversync/Network-Application.git
```


