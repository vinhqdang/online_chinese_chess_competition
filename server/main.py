import logging
from pathlib import Path

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .config import GameConfig
from .game_manager import GameManager
from .net import get_local_ip

logging.basicConfig(level=logging.INFO)

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"

app = FastAPI(title="Online Xiangqi Competition Server")
manager = GameManager(GameConfig())


@app.get("/")
async def index():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/admin")
async def admin_page():
    return FileResponse(STATIC_DIR / "admin.html")


@app.get("/player")
async def player_page():
    return FileResponse(STATIC_DIR / "player.html")


@app.get("/api/server-info")
async def server_info(request: Request):
    port = request.url.port or (443 if request.url.scheme == "https" else 80)
    return {
        "local_ip": get_local_ip(),
        "port": port,
        "requested_host": request.url.hostname,
    }


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.websocket("/ws/player")
async def ws_player(ws: WebSocket):
    await ws.accept()
    color = None
    try:
        join_msg = await ws.receive_json()
        name = (join_msg or {}).get("name", "") if isinstance(join_msg, dict) else ""
        color = await manager.join_player(ws, name)
        if color is None:
            await ws.close()
            return
        while True:
            data = await ws.receive_json()
            msg_type = data.get("type")
            if msg_type == "move":
                await manager.handle_move(color, data.get("from"), data.get("to"))
            elif msg_type == "resign":
                await manager.handle_resign(color)
            elif msg_type == "legal_moves":
                targets = await manager.legal_destinations(color, tuple(data.get("square")))
                await ws.send_json({"type": "legal_destinations", "square": data.get("square"), "targets": targets})
            else:
                await ws.send_json({"type": "error", "message": "unknown_message_type"})
    except WebSocketDisconnect:
        pass
    except Exception:
        logging.exception("player websocket error")
    finally:
        await manager.handle_disconnect(ws)


@app.websocket("/ws/admin")
async def ws_admin(ws: WebSocket):
    await ws.accept()
    await manager.join_admin(ws)
    try:
        while True:
            data = await ws.receive_json()
            msg_type = data.get("type")
            if msg_type == "configure":
                result = await manager.configure(data.get("config", {}))
                await ws.send_json({"type": "configure_result", **result})
            elif msg_type == "start":
                result = await manager.start_game()
                await ws.send_json({"type": "start_result", **result})
            elif msg_type == "kick":
                result = await manager.kick(data.get("color"))
                await ws.send_json({"type": "kick_result", **result})
            elif msg_type == "reset":
                result = await manager.reset()
                await ws.send_json({"type": "reset_result", **result})
            else:
                await ws.send_json({"type": "error", "message": "unknown_message_type"})
    except WebSocketDisconnect:
        pass
    except Exception:
        logging.exception("admin websocket error")
    finally:
        manager.leave_admin(ws)
