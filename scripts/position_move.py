import chess
import chess.polyglot
from sqlmodel import Field, SQLModel

from scripts.shakmaty_hasher import ShakmatyHasher

FLAG_REGULAR = 1
FLAG_PUT = 2
_hasher = ShakmatyHasher()


class PositionMove(SQLModel, table=True):
    """Model for a move in a position."""

    hash: int = Field(primary_key=True)
    move: int = Field(primary_key=True)
    white: int
    draw: int
    black: int

    @property
    def decoded_move(self) -> chess.Move:
        """Return the decoded move."""
        from_square = self.move & 0x3F
        to_square = (self.move >> 6) & 0x3F
        promotion = (self.move >> 12) & 0x7
        flag = (self.move >> 15) & 0x3

        if flag == FLAG_PUT:
            return chess.Move(from_square=0, to_square=to_square, drop=promotion)

        if flag != FLAG_REGULAR:
            return chess.Move(from_square, to_square, promotion or None)

        king_square = from_square
        rook_square = to_square
        king_rank = chess.square_rank(king_square)

        if chess.square_file(rook_square) > chess.square_file(king_square):
            dest_square = chess.square(6, king_rank)
        else:
            dest_square = chess.square(2, king_rank)

        return chess.Move(from_square=king_rank, to_square=dest_square)

    @staticmethod
    def get_hash(board: chess.Board) -> int:
        """Return the hash of the given position."""
        zobrist = chess.polyglot.zobrist_hash(board, _hasher=_hasher)

        if zobrist >= (1 << 63):
            zobrist -= 1 << 64
        return zobrist
