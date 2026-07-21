# Writing a bot

A bot for this server implements exactly **one function**:

```python
def choose_move(board):
    ...
    return src, dst
```

That's the whole contract:

- **Input**: `board`, a `xiangqi.Board` — the current position, at the
  moment it's your turn to move.
- **Output**: `(src, dst)` — the move you want to make. `src` and `dst`
  are each a `(file, rank)` pair, 0-indexed:
  - `file`: 0-8, left to right from Red's side (0='a' ... 8='i')
  - `rank`: 0-9, where 0 is Red's home rank and 9 is Black's home rank
  - e.g. `((0, 3), (0, 4))` moves the piece at a3 to a4.

Nothing else. You don't open a socket, parse JSON, manage a clock, or
track whose turn it is — the harness (`bots/base_bot.py`) does all of
that and only calls `choose_move(board)` when it is actually your turn
and at least one legal move exists.

## The `board` object

`board` is a real `xiangqi.board.Board` — the same rules engine the
server itself uses to judge the match — reconstructed from the server's
latest broadcast. Useful bits:

- `board.turn` — your color, `'r'` (Red) or `'b'` (Black).
- `board.get(file, rank)` — the `Piece` at a square, or `None`. A `Piece`
  has `.color` (`'r'`/`'b'`) and `.kind` (one of `G` General, `A`
  Advisor, `E` Elephant, `H` Horse, `R` Chariot/Rook, `C` Cannon, `P`
  Soldier/Pawn).
- `board.legal_moves(color)` — every legal `(src, dst)` move for that
  color, already validated against full Xiangqi rules (palace
  confinement, flying-general, blocked legs/eyes, cannon-screen capture,
  etc). The easiest correct bot just picks one of these.
- `board.copy()` — a deep copy, handy for looking one move ahead (see
  `bots/greedy_bot.py` for an example: it simulates each candidate move
  on a copy to check whether it gives check).

You are **not required** to only return moves from `board.legal_moves()`
— you can compute a move however you like. But if you return an illegal
move, the server (the sole judge) rejects it and issues a warning to
your side instead of crashing your bot; three warnings and you lose
automatically. So in practice, always deriving your move from
`board.legal_moves(board.turn)` is the safe default.

## Minimal example

```python
import random

def choose_move(board):
    return random.choice(board.legal_moves(board.turn))
```

This is, verbatim, `bots/random_bot.py`'s entire strategy.

## Running your bot

Drop your `choose_move` into a copy of `bots/random_bot.py` (or import
the harness directly) and run it against a server:

```python
import asyncio
from bots.base_bot import build_arg_parser, run_bot, uri_from_args

def choose_move(board):
    ...  # your logic here

def main():
    parser = build_arg_parser("My bot")
    args = parser.parse_args()
    asyncio.run(run_bot(uri_from_args(args), args.name, choose_move, args.think_delay))

if __name__ == "__main__":
    main()
```

```bash
python -m bots.my_bot --host localhost --port 8000 --name MyBot
```

It joins the lobby exactly like a browser player would (first-come,
first-served for the Red/Black seat), then waits for the admin to start
the match from `/admin`.

See `bots/greedy_bot.py` for a slightly less trivial example (a one-ply
material heuristic) that still fits entirely inside the one required
function.
