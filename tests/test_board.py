from xiangqi.board import (
    Board,
    Piece,
    RED,
    BLACK,
    GENERAL,
    ADVISOR,
    ELEPHANT,
    HORSE,
    ROOK,
    CANNON,
    PAWN,
    IllegalMoveError,
)


def empty_board(turn=RED):
    b = Board.__new__(Board)
    b.grid = [[None for _ in range(9)] for _ in range(10)]
    b.turn = turn
    b.move_history = []
    b.halfmove_clock = 0
    return b


def test_initial_position_piece_count():
    board = Board()
    pieces = board.all_pieces()
    assert len(pieces) == 32
    assert len(board.all_pieces(RED)) == 16
    assert len(board.all_pieces(BLACK)) == 16
    assert board.turn == RED


def test_soldier_forward_only_before_river():
    board = empty_board(RED)
    board.set(0, 3, Piece(RED, PAWN))
    dests = board.piece_destinations((0, 3))
    assert dests == [(0, 4)]


def test_soldier_can_move_sideways_after_crossing_river():
    board = empty_board(RED)
    board.set(4, 5, Piece(RED, PAWN))
    dests = set(board.piece_destinations((4, 5)))
    assert dests == {(4, 6), (3, 5), (5, 5)}


def test_soldier_never_moves_backward():
    board = empty_board(BLACK)
    board.set(4, 4, Piece(BLACK, PAWN))
    dests = set(board.piece_destinations((4, 4)))
    assert (4, 5) not in dests
    assert dests == {(4, 3), (3, 4), (5, 4)}


def test_elephant_cannot_cross_river():
    board = empty_board(RED)
    board.set(2, 4, Piece(RED, ELEPHANT))
    dests = set(board.piece_destinations((2, 4)))
    assert (0, 6) not in dests
    assert (4, 6) not in dests
    assert dests == {(0, 2), (4, 2)}


def test_elephant_blocked_by_eye():
    board = empty_board(RED)
    board.set(2, 0, Piece(RED, ELEPHANT))
    board.set(1, 1, Piece(RED, PAWN))  # occupies the eye point
    dests = board.piece_destinations((2, 0))
    assert (0, 2) not in dests


def test_horse_blocked_by_leg():
    board = empty_board(RED)
    board.set(4, 4, Piece(RED, HORSE))
    board.set(4, 5, Piece(BLACK, PAWN))  # blocks the leg for the two northward jumps
    dests = set(board.piece_destinations((4, 4)))
    assert (3, 6) not in dests
    assert (5, 6) not in dests
    assert (3, 2) in dests
    assert (5, 2) in dests


def test_cannon_cannot_capture_without_screen():
    board = empty_board(RED)
    board.set(4, 0, Piece(RED, CANNON))
    board.set(4, 5, Piece(BLACK, ROOK))
    dests = board.piece_destinations((4, 0))
    assert (4, 5) not in dests  # nothing to jump over
    assert (4, 4) in dests  # can slide freely up to just before the target


def test_cannon_captures_by_jumping_exactly_one_screen():
    board = empty_board(RED)
    board.set(4, 0, Piece(RED, CANNON))
    board.set(4, 3, Piece(RED, PAWN))  # screen
    board.set(4, 6, Piece(BLACK, ROOK))
    dests = board.piece_destinations((4, 0))
    assert (4, 6) in dests
    assert (4, 5) not in dests
    assert (4, 1) in dests
    assert (4, 2) in dests


def test_rook_blocked_by_piece_cannot_jump():
    board = empty_board(RED)
    board.set(0, 0, Piece(RED, ROOK))
    board.set(0, 3, Piece(RED, PAWN))
    dests = board.piece_destinations((0, 0))
    assert (0, 3) not in dests
    assert (0, 6) not in dests
    assert (0, 2) in dests


def test_general_confined_to_palace():
    board = empty_board(RED)
    board.set(4, 2, Piece(RED, GENERAL))
    dests = set(board.piece_destinations((4, 2)))
    assert (4, 3) not in dests  # outside the palace
    assert dests == {(3, 2), (5, 2), (4, 1)}


def test_advisor_confined_to_diagonal_palace_points():
    board = empty_board(RED)
    board.set(4, 1, Piece(RED, ADVISOR))
    dests = set(board.piece_destinations((4, 1)))
    assert dests == {(3, 0), (5, 0), (3, 2), (5, 2)}


def test_flying_generals_cannot_face_each_other():
    board = empty_board(RED)
    board.set(4, 0, Piece(RED, GENERAL))
    board.set(4, 9, Piece(BLACK, GENERAL))
    board.set(4, 1, Piece(RED, ADVISOR))
    # Moving the advisor out of the way would expose the generals face to face.
    ok, reason = board.is_legal_move((4, 1), (3, 0))
    assert not ok
    assert reason == "leaves_general_in_check"


def test_move_into_own_check_is_illegal():
    board = empty_board(RED)
    board.set(4, 0, Piece(RED, GENERAL))
    board.set(4, 9, Piece(BLACK, GENERAL))
    board.set(0, 0, Piece(RED, ROOK))
    board.set(4, 5, Piece(BLACK, ROOK))
    # General is already in check along the e-file; moving an unrelated
    # piece elsewhere does nothing to resolve it.
    ok, reason = board.is_legal_move((0, 0), (0, 1))
    assert not ok
    assert reason == "leaves_general_in_check"


def test_apply_move_switches_turn_and_records_history():
    board = Board()
    move = board.apply_move((0, 3), (0, 4))
    assert board.turn == BLACK
    assert len(board.move_history) == 1
    assert move.piece.kind == PAWN


def test_illegal_move_raises():
    board = Board()
    try:
        board.apply_move((0, 0), (0, 5))
        assert False, "expected IllegalMoveError"
    except IllegalMoveError:
        pass


def test_checkmate_detected():
    board = empty_board(BLACK)
    board.set(4, 9, Piece(BLACK, GENERAL))
    board.set(4, 0, Piece(RED, GENERAL))
    board.set(4, 5, Piece(RED, ROOK))  # checks along the e-file
    board.set(3, 1, Piece(RED, ROOK))  # controls the d-file, denies d9
    board.set(5, 1, Piece(RED, ROOK))  # controls the f-file, denies f9
    assert board.is_in_check(BLACK)
    status, winner = board.game_status()
    assert status == "checkmate"
    assert winner == RED


def test_no_legal_moves_without_check_is_a_loss():
    # Xiangqi has no stalemate draw: a side with zero legal moves loses
    # even if its general is not currently in check.
    board = empty_board(BLACK)
    board.set(3, 9, Piece(BLACK, GENERAL))  # d9
    board.set(4, 0, Piece(RED, GENERAL))
    board.set(4, 5, Piece(RED, ROOK))  # denies e9
    board.set(5, 7, Piece(RED, HORSE))  # denies d8
    assert not board.is_in_check(BLACK)
    status, winner = board.game_status()
    assert status == "no_moves"
    assert winner == RED


def test_halfmove_clock_resets_on_capture():
    board = empty_board(RED)
    board.set(4, 0, Piece(RED, GENERAL))
    board.set(3, 9, Piece(BLACK, GENERAL))
    board.set(0, 3, Piece(RED, PAWN))
    board.set(0, 4, Piece(BLACK, PAWN))
    board.halfmove_clock = 5
    board.apply_move((0, 3), (0, 4))
    assert board.halfmove_clock == 0


def test_halfmove_clock_increments_on_quiet_move():
    board = empty_board(RED)
    board.set(4, 0, Piece(RED, GENERAL))
    board.set(3, 9, Piece(BLACK, GENERAL))
    board.set(0, 0, Piece(RED, ROOK))
    board.apply_move((0, 0), (0, 1))
    assert board.halfmove_clock == 1


def test_halfmove_clock_resets_on_check():
    board = empty_board(RED)
    board.set(4, 0, Piece(RED, GENERAL))
    board.set(3, 9, Piece(BLACK, GENERAL))
    board.set(3, 5, Piece(RED, ROOK))
    board.halfmove_clock = 7
    board.apply_move((3, 5), (3, 8))  # slides up the d-file, checking black
    assert board.halfmove_clock == 0
    assert board.is_in_check(BLACK)
