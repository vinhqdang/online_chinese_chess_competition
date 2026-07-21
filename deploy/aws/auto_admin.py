"""Demo-mode auto-admin: keeps a bot-vs-bot Xiangqi match running forever.

Used by the AWS demo deployment so that opening the server URL always shows
a live game in progress. A human admin can still open /admin at the same
time -- multiple admin/spectator connections are supported -- and a human
could take over a seat by having the admin kick a bot first.
"""

import argparse
import asyncio
import json
import logging

from websockets.asyncio.client import connect as ws_connect

logger = logging.getLogger("xiangqi.auto_admin")

DEFAULT_CONFIG = {
    "move_time_limit_sec": 20,
    "match_time_limit_sec": 900,
    "max_warnings": 3,
    "draw_no_progress_halfmoves": 60,
}


async def run_loop(uri, pause_between_games):
    while True:
        try:
            await _play_one_cycle(uri, pause_between_games)
        except Exception:
            logger.exception("auto_admin cycle failed, retrying shortly")
            await asyncio.sleep(5)


async def _play_one_cycle(uri, pause_between_games):
    async with ws_connect(uri) as ws:
        logger.info("connected as admin, waiting for both seats to fill")
        while True:
            msg = json.loads(await ws.recv())
            if msg.get("type") == "lobby_update" and len(msg.get("players", {})) == 2:
                break

        await ws.send(json.dumps({"type": "configure", "config": DEFAULT_CONFIG}))
        await ws.recv()
        await ws.send(json.dumps({"type": "start"}))
        await ws.recv()
        logger.info("match started")

        while True:
            msg = json.loads(await ws.recv())
            if msg.get("type") == "game_over":
                logger.info("game over: %s", msg)
                break

        await asyncio.sleep(pause_between_games)
        await ws.send(json.dumps({"type": "reset"}))
        await ws.recv()


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
    parser = argparse.ArgumentParser(description="Keep a bot-vs-bot demo match looping.")
    parser.add_argument("--host", default="localhost")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--pause", type=float, default=8.0, help="Seconds to pause between games.")
    args = parser.parse_args()
    uri = f"ws://{args.host}:{args.port}/ws/admin"
    asyncio.run(run_loop(uri, args.pause))


if __name__ == "__main__":
    main()
