"""Shared WebSocket client harness for test-bot players.

A bot connects to the server's /ws/player endpoint exactly like a browser
would, reconstructs a xiangqi.Board from each state broadcast, and calls a
strategy function of exactly one argument -- the current board -- to get
the next move. The server remains the sole judge: the bot never applies
its own move locally, it only proposes one, and the server validates it.

See docs/writing_a_bot.md for the function contract bot authors implement.
"""

import argparse
import asyncio
import logging

import websockets
from websockets.asyncio.client import connect as ws_connect

from xiangqi.board import Board, RED, BLACK

logger = logging.getLogger("xiangqi.bot")

COLOR_CODE = {"red": RED, "black": BLACK}


async def run_bot(uri, name, choose_move, think_delay=0.5):
    async with ws_connect(uri) as ws:
        await ws.send(_json({"type": "join", "name": name}))
        my_color = None
        while True:
            raw = await ws.recv()
            msg = _loads(raw)
            msg_type = msg.get("type")
            if msg_type == "joined":
                my_color = COLOR_CODE[msg["color"]]
                logger.info("%s joined as %s", name, msg["color"])
            elif msg_type == "join_rejected":
                logger.error("%s join rejected: %s", name, msg.get("reason"))
                return
            elif msg_type == "kicked":
                logger.info("%s was kicked", name)
                return
            elif msg_type == "game_over":
                logger.info("%s: game over — winner=%s reason=%s", name, msg.get("winner"), msg.get("reason"))
                return
            elif msg_type == "state":
                if msg.get("phase") != "in_progress" or msg.get("board") is None:
                    continue
                if msg.get("turn") != msg.get("your_color"):
                    continue
                board = Board.from_matrix(msg["board"], turn=my_color)
                if not board.legal_moves(my_color):
                    continue
                await asyncio.sleep(think_delay)
                src, dst = choose_move(board)
                await ws.send(_json({"type": "move", "from": list(src), "to": list(dst)}))
            elif msg_type == "invalid_move":
                logger.warning("%s: invalid move warning %s/%s (%s)", name, msg["warnings"], msg["max_warnings"], msg.get("reason"))
            elif msg_type == "error":
                logger.warning("%s: server error: %s", name, msg.get("message"))


def _json(obj):
    import json
    return json.dumps(obj)


def _loads(raw):
    import json
    return json.loads(raw)


def build_arg_parser(description):
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("--host", default="localhost")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--name", default="Bot")
    parser.add_argument("--think-delay", type=float, default=0.5, help="Seconds to 'think' before moving, for visibility.")
    return parser


def uri_from_args(args):
    return f"ws://{args.host}:{args.port}/ws/player"
