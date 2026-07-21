from dataclasses import dataclass, asdict


@dataclass
class GameConfig:
    """Configurable rules for a match.

    move_time_limit_sec: max seconds a player has to submit a single move.
    match_time_limit_sec: total seconds a player has across the whole game
        (a chess-clock style budget). Reaching either limit is an immediate
        loss for that player.
    max_warnings: number of illegal-move warnings before the offending
        player loses automatically.
    draw_no_progress_halfmoves: if this many consecutive half-moves pass
        with no capture and no check, the game is declared a draw
        (default 60 == 30 full moves for each side).
    """

    move_time_limit_sec: int = 60
    match_time_limit_sec: int = 1800
    max_warnings: int = 3
    draw_no_progress_halfmoves: int = 60

    def to_dict(self):
        return asdict(self)

    @staticmethod
    def from_dict(data):
        allowed = {f: data[f] for f in GameConfig.__dataclass_fields__ if f in data}
        return GameConfig(**allowed)

    def validate(self):
        if self.move_time_limit_sec < 1:
            raise ValueError("move_time_limit_sec must be >= 1")
        if self.match_time_limit_sec < self.move_time_limit_sec:
            raise ValueError("match_time_limit_sec must be >= move_time_limit_sec")
        if self.max_warnings < 1:
            raise ValueError("max_warnings must be >= 1")
        if self.draw_no_progress_halfmoves < 2:
            raise ValueError("draw_no_progress_halfmoves must be >= 2")
