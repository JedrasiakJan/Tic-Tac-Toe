import logging
import asyncio
import time
from fastapi import WebSocket
from .game_logic import TicTacToeGame

logger = logging.getLogger(__name__)

class ConnectionManager:

    def __init__(self):
        self.active_connections = set()
        self.rooms = {}

    async def join_room(self, websocket, room_id):
        if room_id not in self.rooms:
            logger.info(f"Tworzenie nowego pokoju: {room_id}")
            self.rooms[room_id] = {
                "players": {},
                "game": TicTacToeGame(),
                "created_at": time.time()
            }
        room = self.rooms[room_id]
        if len(room["players"]) >= 2:
            logger.warning(f"Odrzucono połączenie do pokoju {room_id} - pokój jest pełny.")
            await websocket.close(code=1088)
            return None, None
        await websocket.accept()
        role = "X" if "X" not in room["players"] else "O"
        room["players"][role] = websocket
        logger.info(f"Nowy gracz dołączył do pokoju {room_id} jako {role}")
        return role, room["game"]

    async def disconnect(self, websocket: WebSocket, room_id: str):
        if room_id in self.rooms:
            room = self.rooms[room_id]
            for role, ws in list(room["players"].items()):
                if ws == websocket:
                    del room["players"][role]
                    logger.info(f"Gracz {role} opuścił pokój {room_id}")
                    
            if not room["players"]:
                del self.rooms[room_id]
                logger.info(f"Pokój {room_id} został usunięty (brak graczy).")

    async def broadcast(self, message: dict, room_id : str):
        if room_id in self.rooms:
            for connection in self.rooms[room_id]["players"].values():
                try:
                    await connection.send_json(message)
                except RuntimeError:
                    pass

    async def clean_empty_rooms(self):
        """Funkcja działająca w tle, czyszcząca 'porzucone' pokoje po 30 minutach"""
        while True:
            await asyncio.sleep(1800)
            current_time = time.time()
            for room_id in list(self.rooms.keys()):
                room = self.rooms[room_id]
                if len(room["players"]) < 2 and (current_time - room.get("created_at", current_time)) > 1800:
                    del self.rooms[room_id]
                    logger.info(f"🗑️ Garbage Collector usunął nieaktywny pokój: {room_id}")