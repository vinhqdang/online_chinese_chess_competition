# Online Xiangqi (Chinese Chess) Competition Server

A referee server for online Xiangqi (象棋 / Cờ Tướng) matches. The server is
the **sole judge**: it holds the only copy of the board, validates every
move against international Xiangqi rules, enforces time limits and an
illegal-move warning system, and declares the result (win / loss / draw).

Everything runs through a browser:

- **Admin dashboard** (`/admin`) — see who has connected, configure the
  match (time limits, warning threshold, draw rule), start the match,
  kick a connected player, and spectate the live game.
- **Player page** (`/player`) — join with a name, get seated Red or Black
  on a first-come-first-served basis, then play by clicking pieces on the
  board.

Two simple bot players are included to test the server end to end without
needing two humans.

## Rules implemented

- Standard 9×9-point / 10-rank Xiangqi board, international piece rules:
  General confined to the palace with the "flying general" restriction,
  Advisor diagonal-in-palace, Elephant blocked by its eye point and unable
  to cross the river, Horse blocked by its leg point, Chariot/Cannon
  sliding rules (Cannon requires exactly one screen to capture), Soldier
  forward-only until crossing the river.
- **No stalemate draw**: a side with no legal move on its turn loses,
  whether or not it is in check (this differs from international chess
  and matches Xiangqi rules).
- **Illegal-move warnings**: an illegal move sent by a player earns a
  warning instead of ending the game; reaching the configured maximum
  (default 3) is an automatic loss.
- **Per-move and per-match clocks**: each player has a time budget for the
  whole match (a chess-clock style countdown) and a cap on how long any
  single move may take. Running out of either is an immediate loss.
- **Draw by inactivity**: if a configurable number of moves (default 30)
  pass for *each* side with no capture and no check, the game is a draw.
- **Draw by threefold repetition**: if the exact same position (same
  piece placement, same side to move) occurs three times, the game is a
  draw.
- Disconnection during a match is a forfeit for the disconnected side.
  The admin can also kick a connected player (frees the seat before the
  match starts, or forfeits them if the match is already running).

## Project layout

```
xiangqi/        Rule engine: board, piece movement, check/checkmate, notation
server/         FastAPI app: GameConfig, GameManager (referee), WebSocket routes
static/         Browser UI: index/admin/player pages, canvas board renderer, EN/VI i18n
bots/           Two WebSocket test players (random, greedy-capture)
tests/          pytest unit tests for the rule engine
run_server.py   Entry point
```

## Running locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

python run_server.py --host 0.0.0.0 --port 8000
```

Then open:

- Admin: `http://localhost:8000/admin`
- Player: `http://localhost:8000/player`

The admin page shows the server's LAN address and the exact URL to hand to
competitors (`http://<detected-ip>:8000/player`), so the same server works
for two browsers on your own machine, two machines on a LAN, or two
machines over the internet (as long as the port is reachable — forward
port 8000 on your router, or open it in your cloud provider's firewall,
for internet play).

`--host 0.0.0.0` is what makes the server listen on every network
interface, not just `localhost`; use `--host 127.0.0.1` if you only want
local/same-machine testing.

## Playing a match

1. Two browsers open `/player`, each enters a name and clicks **Join
   match**. First to join is seated Red, second is seated Black (any
   further attempt to join is rejected while the lobby is full or a match
   is running).
2. The admin opens `/admin`, sees both seats filled, optionally adjusts
   **Match configuration** (move time limit, match time limit, warning
   threshold, draw-after-N-moves), then clicks **Start Match**.
3. Each player sees the board oriented with their own side at the bottom,
   clicks a piece to see its legal destinations highlighted, then clicks a
   destination to move. Only the player to move can act; everyone else
   (including spectating admin) sees the position update live.
4. The match ends automatically on checkmate, no-legal-moves, 3 warnings,
   either clock running out, resignation, disconnect, kick, or the
   inactivity draw rule. The admin can then click **New Match** to return
   to the lobby (same connected players can play again, or the admin can
   kick one to let someone else in).

Language: use the dropdown (English / Tiếng Việt) in the top bar of any
page; the choice is remembered per browser.

## Test bots

Two bot players connect over the same WebSocket protocol as a browser
would, so you can test the server without two humans:

```bash
# with the server running on localhost:8000
python -m bots.random_bot --host localhost --port 8000 --name RandomBot
python -m bots.greedy_bot  --host localhost --port 8000 --name GreedyBot
```

Then start the match from `/admin` as usual. `random_bot` picks a
uniformly random legal move; `greedy_bot` prefers capturing the most
valuable piece available (falling back to random), as a slightly less
naive opponent. Both reuse the same `xiangqi` rule engine as the server to
compute legal moves from the state it broadcasts — they never trust their
own judgment about legality, the server still validates every move.

Writing your own bot means implementing exactly one function —
`choose_move(board) -> (src, dst)` — see
[`docs/writing_a_bot.md`](docs/writing_a_bot.md) for the full contract.

## Tests

```bash
pytest tests/
```

Covers piece movement rules (including the trickier ones: elephant eye
blocking, horse leg blocking, cannon screen capture, flying-general
restriction), checkmate detection, the Xiangqi no-stalemate-draw rule,
and the inactivity-draw half-move counter.

## Protocol notes (for building your own client/bot)

All messages are JSON over WebSocket.

- Player connects to `/ws/player`, sends `{"type": "join", "name": "..."}`
  first, gets back `{"type": "joined", "color": "red"|"black", ...}`.
- On your turn, request legal destinations for a square with
  `{"type": "legal_moves", "square": [file, rank]}` (file 0-8 = a-i,
  rank 0-9, rank 0 is Red's home rank), then send a move with
  `{"type": "move", "from": [file, rank], "to": [file, rank]}`.
- `{"type": "resign"}` forfeits immediately.
- Admin connects to `/ws/admin`, can send `{"type": "configure", "config":
  {...}}`, `{"type": "start"}`, `{"type": "kick", "color": "red"|"black"}`,
  `{"type": "reset"}`.
- Both sides receive `{"type": "state", ...}` broadcasts (full board,
  whose turn, per-player warnings/remaining time, last move, in-check
  flag, move-deadline timestamp) and a final `{"type": "game_over",
  "winner": "red"|"black"|null, "reason": "..."}`.
