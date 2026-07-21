"""Test player: greedily prefers capturing the most valuable piece
available, then prefers moves that give check, else moves randomly.
A simple one-ply material heuristic — not meant to be strong, just to
exercise the server with a slightly less naive opponent than random_bot.
"""

import asyncio
import logging
import random

from xiangqi.board import PIECE_VALUES, other_color

from .base_bot import build_arg_parser, run_bot, uri_from_args


def _score_move(board, color, src, dst):
    captured = board.get(*dst)
    score = PIECE_VALUES[captured.kind] if captured else 0
    board_copy = board.copy()
    board_copy.set(dst[0], dst[1], board_copy.get(*src))
    board_copy.set(src[0], src[1], None)
    if board_copy.is_in_check(other_color(color)):
        score += 5
    return score


def choose_move(board, color, legal_moves):
    scored = [(_score_move(board, color, src, dst), src, dst) for src, dst in legal_moves]
    best_score = max(s for s, _, _ in scored)
    best_moves = [(src, dst) for s, src, dst in scored if s == best_score]
    return random.choice(best_moves)


def main():
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    parser = build_arg_parser("Greedy-capture test player for the Xiangqi server.")
    args = parser.parse_args()
    asyncio.run(run_bot(uri_from_args(args), args.name, choose_move, args.think_delay))


if __name__ == "__main__":
    main()
