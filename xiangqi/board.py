"""Xiangqi (Chinese Chess) board representation and rule engine.

Implements international/standard Xiangqi rules (as opposed to any local
regional variant):
  - 9x10 point grid, pieces sit on intersections.
  - General confined to the palace, cannot face the enemy general on an
    open file ("flying general" rule).
  - Advisor confined to the palace, moves one point diagonally.
  - Elephant cannot cross the river and is blocked by an occupied eye point.
  - Horse is blocked by an occupied leg point ("hobbling the horse").
  - Chariot/Rook moves like a rook, cannot jump.
  - Cannon moves like a rook when not capturing; must jump exactly one
    screening piece to capture.
  - Soldier/Pawn moves forward only until crossing the river, after which
    it may also move sideways; it never moves backward or diagonally.
  - A side with no legal moves on its turn loses immediately, whether or
    not its general is in check (there is no stalemate draw in Xiangqi).

The draw-by-inactivity rule (30 moves each side with no capture and no
check) is enforced by the caller via ``Board.halfmove_clock``.
"""

from copy import deepcopy

RED = "r"
BLACK = "b"

GENERAL = "G"
ADVISOR = "A"
ELEPHANT = "E"
HORSE = "H"
ROOK = "R"
CANNON = "C"
PAWN = "P"

PIECE_VALUES = {
    GENERAL: 10000,
    ROOK: 90,
    CANNON: 45,
    HORSE: 40,
    ELEPHANT: 20,
    ADVISOR: 20,
    PAWN: 10,
}

PALACE_FILES = (3, 4, 5)
RED_PALACE_RANKS = (0, 1, 2)
BLACK_PALACE_RANKS = (7, 8, 9)


def other_color(color):
    return BLACK if color == RED else RED


class Piece:
    __slots__ = ("color", "kind")

    def __init__(self, color, kind):
        self.color = color
        self.kind = kind

    def __repr__(self):
        return f"Piece({self.color}, {self.kind})"

    def __eq__(self, other):
        return (
            isinstance(other, Piece)
            and self.color == other.color
            and self.kind == other.kind
        )

    def to_dict(self):
        return {"color": self.color, "type": self.kind}

    @staticmethod
    def from_dict(data):
        if data is None:
            return None
        return Piece(data["color"], data["type"])


class Move:
    def __init__(self, src, dst, piece, captured=None, gives_check=False):
        self.src = src
        self.dst = dst
        self.piece = piece
        self.captured = captured
        self.gives_check = gives_check

    def to_dict(self):
        return {
            "from": list(self.src),
            "to": list(self.dst),
            "piece": self.piece.to_dict(),
            "captured": self.captured.to_dict() if self.captured else None,
            "check": self.gives_check,
        }


class IllegalMoveError(ValueError):
    pass


class Board:
    def __init__(self):
        self.grid = [[None for _ in range(9)] for _ in range(10)]
        self.turn = RED
        self.move_history = []
        self.halfmove_clock = 0
        self._setup_initial_position()

    # ------------------------------------------------------------------
    # Setup / basic accessors
    # ------------------------------------------------------------------
    def _setup_initial_position(self):
        back_rank = [ROOK, HORSE, ELEPHANT, ADVISOR, GENERAL, ADVISOR, ELEPHANT, HORSE, ROOK]
        for file_, kind in enumerate(back_rank):
            self.grid[0][file_] = Piece(RED, kind)
            self.grid[9][file_] = Piece(BLACK, kind)
        for file_ in (1, 7):
            self.grid[2][file_] = Piece(RED, CANNON)
            self.grid[7][file_] = Piece(BLACK, CANNON)
        for file_ in (0, 2, 4, 6, 8):
            self.grid[3][file_] = Piece(RED, PAWN)
            self.grid[6][file_] = Piece(BLACK, PAWN)

    def copy(self):
        new_board = Board.__new__(Board)
        new_board.grid = [row[:] for row in self.grid]
        new_board.turn = self.turn
        new_board.move_history = list(self.move_history)
        new_board.halfmove_clock = self.halfmove_clock
        return new_board

    def in_bounds(self, file_, rank):
        return 0 <= file_ <= 8 and 0 <= rank <= 9

    def get(self, file_, rank):
        if not self.in_bounds(file_, rank):
            return None
        return self.grid[rank][file_]

    def set(self, file_, rank, piece):
        self.grid[rank][file_] = piece

    def find_general(self, color):
        for rank in range(10):
            for file_ in range(9):
                p = self.grid[rank][file_]
                if p and p.color == color and p.kind == GENERAL:
                    return (file_, rank)
        return None

    def all_pieces(self, color=None):
        result = []
        for rank in range(10):
            for file_ in range(9):
                p = self.grid[rank][file_]
                if p and (color is None or p.color == color):
                    result.append(((file_, rank), p))
        return result

    def is_own_side(self, color, rank):
        return rank <= 4 if color == RED else rank >= 5

    def in_palace(self, color, file_, rank):
        if file_ not in PALACE_FILES:
            return False
        ranks = RED_PALACE_RANKS if color == RED else BLACK_PALACE_RANKS
        return rank in ranks

    # ------------------------------------------------------------------
    # Pseudo-legal move generation (piece movement rules only)
    # ------------------------------------------------------------------
    def _slide_moves(self, src, directions, cannon=False):
        file_, rank = src
        piece = self.get(file_, rank)
        moves = []
        for df, dr in directions:
            f, r = file_ + df, rank + dr
            screen_found = False
            while self.in_bounds(f, r):
                target = self.get(f, r)
                if not cannon:
                    if target is None:
                        moves.append((f, r))
                    else:
                        if target.color != piece.color:
                            moves.append((f, r))
                        break
                else:
                    if not screen_found:
                        if target is None:
                            moves.append((f, r))
                        else:
                            screen_found = True
                    else:
                        if target is not None:
                            if target.color != piece.color:
                                moves.append((f, r))
                            break
                f, r = f + df, r + dr
        return moves

    def _general_moves(self, src):
        file_, rank = src
        piece = self.get(file_, rank)
        moves = []
        for df, dr in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            f, r = file_ + df, rank + dr
            if self.in_palace(piece.color, f, r):
                target = self.get(f, r)
                if target is None or target.color != piece.color:
                    moves.append((f, r))
        return moves

    def _advisor_moves(self, src):
        file_, rank = src
        piece = self.get(file_, rank)
        moves = []
        for df, dr in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
            f, r = file_ + df, rank + dr
            if self.in_palace(piece.color, f, r):
                target = self.get(f, r)
                if target is None or target.color != piece.color:
                    moves.append((f, r))
        return moves

    def _elephant_moves(self, src):
        file_, rank = src
        piece = self.get(file_, rank)
        moves = []
        for df, dr in ((2, 2), (2, -2), (-2, 2), (-2, -2)):
            f, r = file_ + df, rank + dr
            eye = (file_ + df // 2, rank + dr // 2)
            if not self.in_bounds(f, r):
                continue
            if not self.is_own_side(piece.color, r):
                continue
            if self.get(*eye) is not None:
                continue
            target = self.get(f, r)
            if target is None or target.color != piece.color:
                moves.append((f, r))
        return moves

    def _horse_moves(self, src):
        file_, rank = src
        piece = self.get(file_, rank)
        moves = []
        candidates = [
            (1, 2, 0, 1), (1, -2, 0, -1), (-1, 2, 0, 1), (-1, -2, 0, -1),
            (2, 1, 1, 0), (2, -1, 1, 0), (-2, 1, -1, 0), (-2, -1, -1, 0),
        ]
        for df, dr, lf, lr in candidates:
            f, r = file_ + df, rank + dr
            leg = (file_ + lf, rank + lr)
            if not self.in_bounds(f, r):
                continue
            if self.get(*leg) is not None:
                continue
            target = self.get(f, r)
            if target is None or target.color != piece.color:
                moves.append((f, r))
        return moves

    def _pawn_moves(self, src):
        file_, rank = src
        piece = self.get(file_, rank)
        moves = []
        forward = 1 if piece.color == RED else -1
        crossed = not self.is_own_side(piece.color, rank)
        candidates = [(0, forward)]
        if crossed:
            candidates += [(1, 0), (-1, 0)]
        for df, dr in candidates:
            f, r = file_ + df, rank + dr
            if not self.in_bounds(f, r):
                continue
            target = self.get(f, r)
            if target is None or target.color != piece.color:
                moves.append((f, r))
        return moves

    def piece_destinations(self, src):
        piece = self.get(*src)
        if piece is None:
            return []
        if piece.kind == GENERAL:
            return self._general_moves(src)
        if piece.kind == ADVISOR:
            return self._advisor_moves(src)
        if piece.kind == ELEPHANT:
            return self._elephant_moves(src)
        if piece.kind == HORSE:
            return self._horse_moves(src)
        if piece.kind == ROOK:
            return self._slide_moves(src, [(1, 0), (-1, 0), (0, 1), (0, -1)])
        if piece.kind == CANNON:
            return self._slide_moves(src, [(1, 0), (-1, 0), (0, 1), (0, -1)], cannon=True)
        if piece.kind == PAWN:
            return self._pawn_moves(src)
        return []

    def pseudo_legal_moves(self, color):
        moves = []
        for src, piece in self.all_pieces(color):
            for dst in self.piece_destinations(src):
                moves.append((src, dst))
        return moves

    # ------------------------------------------------------------------
    # Check / legality
    # ------------------------------------------------------------------
    def is_square_attacked(self, square, by_color):
        for src, piece in self.all_pieces(by_color):
            if square in self.piece_destinations(src):
                return True
        return False

    def generals_facing(self):
        red_pos = self.find_general(RED)
        black_pos = self.find_general(BLACK)
        if red_pos is None or black_pos is None:
            return False
        if red_pos[0] != black_pos[0]:
            return False
        file_ = red_pos[0]
        lo, hi = sorted((red_pos[1], black_pos[1]))
        for r in range(lo + 1, hi):
            if self.get(file_, r) is not None:
                return False
        return True

    def is_in_check(self, color):
        general_pos = self.find_general(color)
        if general_pos is None:
            return False
        return self.is_square_attacked(general_pos, other_color(color))

    def _would_be_legal(self, src, dst):
        piece = self.get(*src)
        board_copy = self.copy()
        board_copy.set(dst[0], dst[1], piece)
        board_copy.set(src[0], src[1], None)
        if board_copy.is_in_check(piece.color):
            return False
        if board_copy.generals_facing():
            return False
        return True

    def legal_moves(self, color=None):
        color = color or self.turn
        legal = []
        for src, dst in self.pseudo_legal_moves(color):
            if self._would_be_legal(src, dst):
                legal.append((src, dst))
        return legal

    def is_legal_move(self, src, dst):
        piece = self.get(*src)
        if piece is None:
            return False, "no_piece_at_source"
        if piece.color != self.turn:
            return False, "not_your_piece"
        if dst not in self.piece_destinations(src):
            return False, "illegal_piece_movement"
        if not self._would_be_legal(src, dst):
            return False, "leaves_general_in_check"
        return True, None

    # ------------------------------------------------------------------
    # Applying moves
    # ------------------------------------------------------------------
    def apply_move(self, src, dst):
        ok, reason = self.is_legal_move(src, dst)
        if not ok:
            raise IllegalMoveError(reason)
        piece = self.get(*src)
        captured = self.get(*dst)
        self.set(dst[0], dst[1], piece)
        self.set(src[0], src[1], None)
        mover_color = piece.color
        opponent = other_color(mover_color)
        gives_check = self.is_in_check(opponent)
        move = Move(src, dst, piece, captured, gives_check)
        self.move_history.append(move)
        if captured is not None or gives_check:
            self.halfmove_clock = 0
        else:
            self.halfmove_clock += 1
        self.turn = opponent
        return move

    def game_status(self):
        """Return (status, winner_color_or_None) evaluated for the side to move.

        status is one of: 'ongoing', 'checkmate', 'no_moves'.
        Xiangqi has no stalemate draw: a side with no legal moves loses,
        whether or not it is in check.
        """
        side = self.turn
        moves = self.legal_moves(side)
        if moves:
            return "ongoing", None
        winner = other_color(side)
        if self.is_in_check(side):
            return "checkmate", winner
        return "no_moves", winner

    # ------------------------------------------------------------------
    # Serialization / rendering
    # ------------------------------------------------------------------
    def to_matrix(self):
        return [
            [self.grid[rank][file_].to_dict() if self.grid[rank][file_] else None for file_ in range(9)]
            for rank in range(10)
        ]

    @staticmethod
    def from_matrix(matrix, turn=RED, halfmove_clock=0):
        board = Board.__new__(Board)
        board.grid = [[Piece.from_dict(cell) for cell in row] for row in matrix]
        board.turn = turn
        board.move_history = []
        board.halfmove_clock = halfmove_clock
        return board

    def render_ascii(self):
        kind_symbols = {
            (RED, GENERAL): "G", (RED, ADVISOR): "A", (RED, ELEPHANT): "E",
            (RED, HORSE): "H", (RED, ROOK): "R", (RED, CANNON): "C", (RED, PAWN): "P",
            (BLACK, GENERAL): "g", (BLACK, ADVISOR): "a", (BLACK, ELEPHANT): "e",
            (BLACK, HORSE): "h", (BLACK, ROOK): "r", (BLACK, CANNON): "c", (BLACK, PAWN): "p",
        }
        lines = []
        for rank in range(9, -1, -1):
            row = []
            for file_ in range(9):
                p = self.grid[rank][file_]
                row.append(kind_symbols[(p.color, p.kind)] if p else ".")
            lines.append(f"{rank:2d}  " + " ".join(row))
        lines.append("    " + " ".join("abcdefghi"))
        return "\n".join(lines)
