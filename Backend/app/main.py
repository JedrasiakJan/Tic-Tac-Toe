import logging
import asyncio 
import json
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ValidationError
from .game_logic import TicTacToeGame
from .connection_manager import ConnectionManager
from websockets.exceptions import ConnectionClosed
# --- KONFIGURACJA LOGOWANIA ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

menager = ConnectionManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(menager.clean_empty_rooms())
    logger.info("🔧 Garbage Collector uruchomiony w tle.")
    yield 
    task.cancel()
# Utworzenie głównej instancji aplikacji
app = FastAPI(lifespan=lifespan)

# Zezwolenie na ruch z dowolnego źródła w fazie deweloperskiej
app.add_middleware(
    CORSMiddleware,
    # TODO: W środowisku produkcyjnym ograniczyć do konkretnej domeny ze względów bezpieczeństwa. 
    # Zostawiono "*" dla ułatwienia testów lokalnych z GitHuba.
    allow_origins=["*"],  # Pozwala frontendowi z każdego portu łączyć się z API
    allow_credentials=True,
    allow_methods=["*"],  # Zezwala na wszystkie metody (GET, POST itp.)
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    logger.info("Otrzymano zapytanie do endpointu healthcheck (/)")
    return {"message": "Serwer kółko i krzyżyk działa!"}

class Move(BaseModel):
    index: int


@app.websocket("/ws/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str):
    role, game = await menager.join_room(websocket, room_id)
    if role is None or game is None: 
        return
    await websocket.send_json({"your_role": role})
    try:
        if len(menager.rooms[room_id]["players"]) == 1:
                await websocket.send_json({"message": "Czekamy na przeciwnika..."})
        else:
            logger.info(f"Pokój {room_id} skompletowany. Rozpoczynamy grę.")
            await menager.broadcast({
                "board": game.board,
                "turn": game.current_player,
                "winner": game.check_winner()
            }, room_id)
        while True:
            try:
                game = menager.rooms[room_id]["game"]
                raw_data = await websocket.receive_text()
                try:
                    data_dict = json.loads(raw_data)
                    if not isinstance(data_dict, dict):
                        data_dict = {"index": int(data_dict)}
                    move_data = Move(**data_dict)
                except (json.JSONDecodeError, ValueError):
                    move_data = Move(index=int(raw_data))
                if move_data.index == -1:
                    if game.check_winner() is not None or " " not in game.board:
                        # Gra się skończyła, więc pozwalamy na reset
                        menager.rooms[room_id]["game"] = TicTacToeGame()
                        await menager.broadcast({
                            "message": "Gra zresetowana! Zaczyna X.",
                            "board": [" " for _ in range(9)],
                            "turn": "X",
                            "winner": None
                        }, room_id)
                    continue
                if len(menager.rooms[room_id]["players"]) < 2:
                    await websocket.send_json({"error": "Poczekaj na dołączenie przeciwnika!"})
                    continue
                if game.check_winner() is not None:
                    await websocket.send_json({"error": "Gra się już zakończyła! Odśwież stronę, aby zagrać ponownie."})
                    continue
                if role != game.current_player:
                    await websocket.send_json({"error": "To nie Twój ruch!"})
                    continue
                result = game.make_move(move_data.index)
                if not result:
                    await websocket.send_json({"error": "To pole jest zajęte!"})
                    continue
                await menager.broadcast({
                    "board": game.board,
                    "turn": game.current_player,
                    "winner": game.check_winner()
                }, room_id)
            except ValidationError:
                await websocket.send_json({"error": "Błędny format danych! Oczekiwano cyfry."})
            except (WebSocketDisconnect, ConnectionClosed):
                # To przerywa nieskończoną pętlę i pozwala serwerowi wyczyścić pokój w bloku pod pętlą
                break
            except RuntimeError as e:
                # Obejście błędu ucinania sieci
                if "Unexpected ASGI message" in str(e):
                    break
                logger.error(f"Wyjątek: RuntimeError - {str(e)}")
            except Exception as e:
                logger.error(f"Wyjątek: {type(e).__name__} - {str(e)}")
                try:
                    await websocket.send_json({"error": f"Błędne żądanie: {str(e)}"})
                except:
                    break
    except (WebSocketDisconnect, ConnectionClosed, RuntimeError):
        pass
    finally:
        await menager.disconnect(websocket, room_id)
        if room_id in menager.rooms:
            menager.rooms[room_id]["game"] = TicTacToeGame()
            try:
                await menager.broadcast({
                    "message": "Przeciwnik wyszedł. Gra zresetowana. Czekamy na kogoś nowego!",
                    "board": [" " for _ in range(9)],
                    "turn": "X",
                    "winner": None
                }, room_id)
            except Exception:
                pass