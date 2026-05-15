# 🎮 Tic-Tac-Toe (FastAPI + WebSockets)

A full-stack, real-time multiplayer Tic-Tac-Toe game built as a personal project to practice and showcase backend development skills. Rather than trying to solve a real-world problem, this project was an excuse to dive deep into WebSockets, asynchronous Python, and clean architecture principles. 

It was built with a focus on writing solid, decoupled code, handling real-time network quirks, and learning how to properly structure a FastAPI application.

## 🚀 What I Learned / Key Features

* **Real-time Communication:** Implementing instant bidirectional communication between clients and the server using WebSockets.
* **Smart Garbage Collection:** Writing a background `asyncio` task (`lifespan`) that runs periodically to clean up abandoned rooms and free up server memory.
* **Fail-Fast Data Validation:** Using **Pydantic** to strictly validate incoming payloads, protecting the game logic from bad data or malformed JSONs.
* **Handling Edge Cases:** Dealing with common WebSocket issues, like race conditions during page refreshes and gracefully handling sudden client disconnections without crashing the server.
* **Dockerization:** Containerizing the backend and frontend (Nginx) using Docker Compose for an isolated, easy-to-run environment.


## 🛠️ Tech Stack

* **Backend:** Python 3.14.4
* **Framework:** FastAPI (v0.136.1)
* **WebSockets:** Uvicorn (v0.46.0) + websockets (v16.0)
* **Data Validation:** Pydantic (v2.13.4)
* **Frontend:** HTML5, CSS3, Vanilla JavaScript
* **Infrastructure:** Docker & Docker Compose

## 🏗️ Architecture

The backend code is divided into three distinct layers to maintain clean code principles (Separation of Concerns):

### 1. `main.py` (Routing & Validation)
* The entry point for the FastAPI application.
* Handles WebSocket endpoints and raw text receiving.
* Uses Pydantic (`Move` model) to validate incoming JSON payloads.
* Catches and handles network exceptions (`WebSocketDisconnect`, `RuntimeError`) to prevent server crashes.

### 2. `connection_manager.py` (State Management)
* Manages active WebSocket connections and organizes players into rooms.
* Handles broadcasting messages to specific rooms.
* Runs a background `asyncio` task (Garbage Collector) to periodically remove abandoned rooms and free up memory.

### 3. `game_logic.py` (Game Engine)
* Contains only the pure Python logic for Tic-Tac-Toe (checking turns, updating the board, verifying winners).
* Completely decoupled from the network layer — it has no dependencies on FastAPI or WebSockets, making it easily testable and reusable.

## 🧠 Challenges & Solutions

Building a stable real-time game requires handling edge cases that don't exist in standard REST APIs. Here are the main technical hurdles I solved during development:

### 1. The "Page Refresh" Race Condition
**Problem:** Initially, players had to refresh the page to start a new game. If Player A refreshed their page a millisecond before Player B, the server state would reset, but Player B's frontend would still display the old board. This caused queue desynchronization and server crashes.
**Solution:** I eliminated the need for manual browser refreshes entirely. I implemented a seamless "Restart Game" payload (`{"index": -1}`). When triggered, the server instantly resets the `TicTacToeGame` instance and broadcasts a `"winner": null` payload. Both clients intercept this, wipe their UI boards, and start the next round simultaneously without dropping the socket connection.

### 2. Aggressive Handling of Disconnections & Ghost Sockets
**Problem:** In mobile environments, refreshing a browser or closing a tab instantly severs the WebSocket connection. If the server was attempting to `broadcast()` a game state at that exact microsecond, Python would throw a fatal `RuntimeError: Unexpected ASGI message 'websocket.send' after 'websocket.close'`. 
**Solution:** I implemented a robust `try-except-finally` wrapper inside the main game loop and the `ConnectionManager`. The server now:
* Silently catches `RuntimeError` and `ConnectionClosed` when broadcasting to a disconnected player.
* Uses a `finally` block to guarantee that whenever a loop breaks (due to network failure or manual exit), the player is wiped from the active `room` dict, preventing memory leaks and allowing new players to join cleanly.

### 3. Client-Side Cache vs Pydantic Serialization
**Problem:** While refactoring the payload structure from raw strings (`"4"`) to JSON (`{"index": 4}`), cached mobile browsers continued sending old string formats, crashing the Pydantic parser with `JSONDecodeError`.
**Solution:** Instead of forcing `websocket.receive_json()`, the server deliberately uses `websocket.receive_text()`. It then attempts to manually parse the JSON. If it catches a bare string (due to a cached client), it gracefully repackages it into a dictionary (`{"index": int(raw_data)}`) before handing it off to Pydantic for final validation.

## 💻 How to Run (Locally)

1. Clone the repository:
   ```bash
   git clone https://github.com/JedrasiakJan/Tic-Tac-Toe.git
   cd your-repo-name
   ```
2. Start the application using Docker Compose:
   ```bash
   docker-compose up --build
   ```
3. Open your browser and go to `http://localhost`. Open the same link on your phone (using your local IPv4 address, e.g., `http://192.168.0.x`) to play against yourself!