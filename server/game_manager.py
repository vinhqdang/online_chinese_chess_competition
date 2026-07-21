"""Authoritative game/referee logic for one table (lobby -> match -> result).

The server is the sole judge: it holds the only Board instance, validates
every move against xiangqi.Board's legality rules, enforces the warning
counter for illegal moves, enforces per-move and per-match clocks, and
enforces the no-progress draw rule. Clients (browser players, admin,
bots) only ever see state broadcasts and send intents (move/resign/etc).
"""

import asyncio
import logging
import time

from xiangqi import Board
from xiangqi.board import RED, BLACK, other_color, IllegalMoveError

from .config import GameConfig

logger = logging.getLogger("xiangqi.server")

PHASE_LOBBY = "lobby"
PHASE_IN_PROGRESS = "in_progress"
PHASE_FINISHED = "finished"


class Player:
    def __init__(self, color, name, ws):
        self.color = color
        self.name = name
        self.ws = ws
        self.warnings = 0
        self.remaining_time = 0.0
        self.connected = True

    def to_dict(self):
        return {
            "color": self.color,
            "name": self.name,
            "warnings": self.warnings,
            "connected": self.connected,
            "remaining_time": round(self.remaining_time, 1),
        }


COLOR_NAME = {RED: "red", BLACK: "black"}
NAME_COLOR = {v: k for k, v in COLOR_NAME.items()}


class GameManager:
    def __init__(self, config=None):
        self.config = config or GameConfig()
        self.phase = PHASE_LOBBY
        self.players = {}  # color -> Player
        self.admin_sockets = set()
        self.board = None
        self.turn_started_at = None
        self.watchdog_task = None
        self.result = None  # {"winner": "red"/"black"/None, "reason": "..."}
        self.lock = asyncio.Lock()
        self.move_log = []

    # ------------------------------------------------------------------
    # Connection lifecycle
    # ------------------------------------------------------------------
    async def join_player(self, ws, name):
        async with self.lock:
            if self.phase != PHASE_LOBBY:
                reason = "game_in_progress" if self.phase == PHASE_IN_PROGRESS else "game_finished"
                await ws.send_json({"type": "join_rejected", "reason": reason})
                return None
            for color in (RED, BLACK):
                if color not in self.players:
                    player = Player(color, name or COLOR_NAME[color].title(), ws)
                    self.players[color] = player
                    logger.info("player joined as %s: %s", color, name)
                    await ws.send_json({
                        "type": "joined",
                        "color": COLOR_NAME[color],
                        "config": self.config.to_dict(),
                    })
                    await self._broadcast_lobby()
                    return color
            await ws.send_json({"type": "join_rejected", "reason": "lobby_full"})
            return None

    async def join_admin(self, ws):
        self.admin_sockets.add(ws)
        await ws.send_json({"type": "server_info", "config": self.config.to_dict()})
        await self._send_lobby(ws)
        if self.phase != PHASE_LOBBY:
            await ws.send_json(self._state_message(viewer_color=None))

    def leave_admin(self, ws):
        self.admin_sockets.discard(ws)

    async def handle_disconnect(self, ws):
        async with self.lock:
            for color, player in list(self.players.items()):
                if player.ws is ws:
                    player.connected = False
                    if self.phase == PHASE_IN_PROGRESS:
                        await self._finish_game(other_color(color), "disconnect")
                    else:
                        del self.players[color]
                    await self._broadcast_lobby()

    # ------------------------------------------------------------------
    # Admin actions
    # ------------------------------------------------------------------
    async def configure(self, data):
        async with self.lock:
            if self.phase != PHASE_LOBBY:
                return {"ok": False, "error": "cannot_configure_while_in_progress"}
            try:
                new_config = GameConfig.from_dict(data)
                new_config.validate()
            except (ValueError, TypeError, KeyError) as exc:
                return {"ok": False, "error": str(exc)}
            self.config = new_config
            await self._broadcast_lobby()
            return {"ok": True}

    async def start_game(self):
        async with self.lock:
            if self.phase != PHASE_LOBBY:
                return {"ok": False, "error": "already_started"}
            if RED not in self.players or BLACK not in self.players:
                return {"ok": False, "error": "need_two_players"}
            self.board = Board()
            self.move_log = []
            self.result = None
            for player in self.players.values():
                player.warnings = 0
                player.remaining_time = float(self.config.match_time_limit_sec)
            self.phase = PHASE_IN_PROGRESS
            for color, player in self.players.items():
                await player.ws.send_json({"type": "game_started", "config": self.config.to_dict()})
            await self._start_turn()
            await self._broadcast_state()
            return {"ok": True}

    async def kick(self, color_name):
        async with self.lock:
            color = NAME_COLOR.get(color_name)
            if color is None or color not in self.players:
                return {"ok": False, "error": "no_such_player"}
            player = self.players[color]
            try:
                await player.ws.send_json({"type": "kicked"})
                await player.ws.close()
            except Exception:
                pass
            if self.phase == PHASE_IN_PROGRESS:
                await self._finish_game(other_color(color), "kicked")
            del self.players[color]
            await self._broadcast_lobby()
            return {"ok": True}

    async def reset(self):
        async with self.lock:
            if self.watchdog_task:
                self.watchdog_task.cancel()
                self.watchdog_task = None
            self.phase = PHASE_LOBBY
            self.board = None
            self.result = None
            self.move_log = []
            for player in self.players.values():
                player.warnings = 0
                player.remaining_time = float(self.config.match_time_limit_sec)
            await self._broadcast_lobby()
            return {"ok": True}

    # ------------------------------------------------------------------
    # Player actions
    # ------------------------------------------------------------------
    async def handle_move(self, color, src, dst):
        async with self.lock:
            if self.phase != PHASE_IN_PROGRESS:
                await self._send_error(color, "game_not_in_progress")
                return
            if self.board.turn != color:
                await self._send_error(color, "not_your_turn")
                return
            src_t, dst_t = tuple(src), tuple(dst)
            ok, reason = self.board.is_legal_move(src_t, dst_t)
            if not ok:
                await self._register_warning(color, reason)
                return
            await self._commit_move(color, src_t, dst_t)

    async def handle_resign(self, color):
        async with self.lock:
            if self.phase != PHASE_IN_PROGRESS:
                return
            await self._finish_game(other_color(color), "resign")

    async def legal_destinations(self, color, square):
        async with self.lock:
            if self.phase != PHASE_IN_PROGRESS or self.board.turn != color:
                return []
            piece = self.board.get(*square)
            if piece is None or piece.color != color:
                return []
            return [list(dst) for src, dst in self.board.legal_moves(color) if src == tuple(square)]

    # ------------------------------------------------------------------
    # Internal move/clock/game-end machinery (all called with lock held)
    # ------------------------------------------------------------------
    async def _register_warning(self, color, reason):
        player = self.players[color]
        player.warnings += 1
        payload = {
            "type": "invalid_move",
            "reason": reason,
            "warnings": player.warnings,
            "max_warnings": self.config.max_warnings,
        }
        await player.ws.send_json(payload)
        await self._broadcast_admin({**payload, "color": COLOR_NAME[color]})
        if player.warnings >= self.config.max_warnings:
            await self._finish_game(other_color(color), "warnings_exceeded")

    async def _commit_move(self, color, src, dst):
        if self.watchdog_task:
            self.watchdog_task.cancel()
            self.watchdog_task = None
        elapsed = time.monotonic() - self.turn_started_at
        player = self.players[color]
        player.remaining_time = max(0.0, player.remaining_time - elapsed)
        if player.remaining_time <= 0:
            await self._finish_game(other_color(color), "match_time_exceeded")
            return
        move = self.board.apply_move(src, dst)
        self.move_log.append(move.to_dict())

        status, winner = self.board.game_status()
        if status == "checkmate":
            await self._finish_game(winner, "checkmate")
            return
        if status == "no_moves":
            await self._finish_game(winner, "no_legal_moves")
            return
        if self.board.halfmove_clock >= self.config.draw_no_progress_halfmoves:
            await self._finish_game(None, "draw_no_progress")
            return

        await self._start_turn()
        await self._broadcast_state()

    async def _start_turn(self):
        self.turn_started_at = time.monotonic()
        color = self.board.turn
        player = self.players[color]
        delay = min(self.config.move_time_limit_sec, player.remaining_time)
        self.watchdog_task = asyncio.create_task(self._watchdog(color, delay))

    async def _watchdog(self, color, delay):
        try:
            await asyncio.sleep(delay)
        except asyncio.CancelledError:
            return
        async with self.lock:
            if self.phase != PHASE_IN_PROGRESS or self.board.turn != color:
                return
            player = self.players[color]
            if self.config.move_time_limit_sec <= player.remaining_time:
                reason = "move_time_exceeded"
            else:
                reason = "match_time_exceeded"
            player.remaining_time = 0.0
            await self._finish_game(other_color(color), reason)

    async def _finish_game(self, winner, reason):
        if self.phase == PHASE_FINISHED:
            return
        if self.watchdog_task:
            self.watchdog_task.cancel()
            self.watchdog_task = None
        self.phase = PHASE_FINISHED
        self.result = {"winner": COLOR_NAME.get(winner), "reason": reason}
        await self._broadcast_state(game_over=True)

    # ------------------------------------------------------------------
    # Broadcasting
    # ------------------------------------------------------------------
    def _state_message(self, viewer_color):
        board_state = None
        in_check = None
        if self.board is not None:
            board_state = self.board.to_matrix()
            for c in (RED, BLACK):
                if self.board.is_in_check(c):
                    in_check = COLOR_NAME[c]
        msg = {
            "type": "state",
            "phase": self.phase,
            "board": board_state,
            "turn": COLOR_NAME[self.board.turn] if self.board else None,
            "your_color": COLOR_NAME.get(viewer_color) if viewer_color else None,
            "in_check": in_check,
            "players": {COLOR_NAME[c]: p.to_dict() for c, p in self.players.items()},
            "last_move": self.move_log[-1] if self.move_log else None,
            "move_count": len(self.move_log),
            "halfmove_clock": self.board.halfmove_clock if self.board else 0,
            "draw_no_progress_halfmoves": self.config.draw_no_progress_halfmoves,
            "turn_deadline_epoch_ms": None,
            "result": self.result,
        }
        if self.phase == PHASE_IN_PROGRESS and self.turn_started_at is not None:
            player = self.players[self.board.turn]
            delay = min(self.config.move_time_limit_sec, player.remaining_time)
            remaining_wall = delay - (time.monotonic() - self.turn_started_at)
            msg["turn_deadline_epoch_ms"] = int((time.time() + max(0.0, remaining_wall)) * 1000)
        return msg

    async def _broadcast_state(self, game_over=False):
        for color, player in self.players.items():
            try:
                await player.ws.send_json(self._state_message(color))
            except Exception:
                pass
        await self._broadcast_admin(self._state_message(None))
        if game_over:
            for color, player in self.players.items():
                try:
                    await player.ws.send_json({"type": "game_over", **self.result})
                except Exception:
                    pass
            await self._broadcast_admin({"type": "game_over", **self.result})

    async def _send_lobby(self, ws):
        await ws.send_json(self._lobby_message())

    def _lobby_message(self):
        return {
            "type": "lobby_update",
            "phase": self.phase,
            "config": self.config.to_dict(),
            "players": {COLOR_NAME[c]: p.to_dict() for c, p in self.players.items()},
        }

    async def _broadcast_lobby(self):
        msg = self._lobby_message()
        for player in self.players.values():
            try:
                await player.ws.send_json(msg)
            except Exception:
                pass
        await self._broadcast_admin(msg)

    async def _broadcast_admin(self, msg):
        dead = []
        for ws in self.admin_sockets:
            try:
                await ws.send_json(msg)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.admin_sockets.discard(ws)

    async def _send_error(self, color, message):
        try:
            await self.players[color].ws.send_json({"type": "error", "message": message})
        except Exception:
            pass
