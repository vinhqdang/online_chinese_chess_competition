"""Coordinate notation for the board.

Files are lettered a-i (left to right from Red's side, 0-8).
Ranks are numbered 0-9, where rank 0 is Red's back rank and
rank 9 is Black's back rank. This is the ICCS-style coordinate
system used by international Xiangqi engines, independent of
the Chinese-character move records used in traditional notation.

A square is written as "<file><rank>", e.g. "e3".
A move is written as "<from><to>", e.g. "e3e4".
"""

FILES = "abcdefghi"


def parse_square(text):
    text = text.strip().lower()
    if len(text) != 2:
        raise ValueError(f"Invalid square: {text!r}")
    file_char, rank_char = text[0], text[1]
    if file_char not in FILES:
        raise ValueError(f"Invalid file in square: {text!r}")
    if not rank_char.isdigit():
        raise ValueError(f"Invalid rank in square: {text!r}")
    file_ = FILES.index(file_char)
    rank = int(rank_char)
    if not (0 <= rank <= 9):
        raise ValueError(f"Rank out of range: {text!r}")
    return file_, rank


def format_square(file_, rank):
    if not (0 <= file_ <= 8):
        raise ValueError(f"File out of range: {file_}")
    if not (0 <= rank <= 9):
        raise ValueError(f"Rank out of range: {rank}")
    return f"{FILES[file_]}{rank}"


def parse_move(text):
    """Parse a 4-character move string like 'e3e4' into ((f,r), (f,r))."""
    text = text.strip().lower().replace("-", "").replace(" ", "")
    if len(text) != 4:
        raise ValueError(f"Invalid move string: {text!r}")
    src = parse_square(text[0:2])
    dst = parse_square(text[2:4])
    return src, dst


def format_move(src, dst):
    return format_square(*src) + format_square(*dst)
