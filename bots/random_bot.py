"""Test player: picks a uniformly random legal move each turn."""

import asyncio
import logging
import random

from .base_bot import build_arg_parser, run_bot, uri_from_args


def choose_move(board, color, legal_moves):
    return random.choice(legal_moves)


def main():
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    parser = build_arg_parser("Random-move test player for the Xiangqi server.")
    args = parser.parse_args()
    asyncio.run(run_bot(uri_from_args(args), args.name, choose_move, args.think_delay))


if __name__ == "__main__":
    main()
