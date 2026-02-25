from mahsol.layout import blocks_left, blocks_right, covers, is_free_position
from mahsol.models import Position, PlacedTile, Tile, TileKind


def t(i: int) -> PlacedTile:
    return PlacedTile(Tile(i, f"X{i}", f"G{i}", TileKind.SUIT))


def test_cover_and_blocks():
    lower = Position(0, 0, 0)
    upper = Position(0, 0, 1)
    left = Position(-2, 0, 0)
    right = Position(2, 0, 0)

    assert covers(upper, lower)
    assert blocks_left(lower, left)
    assert blocks_right(lower, right)


def test_free_tile_logic():
    p = Position(0, 0, 0)
    left = Position(-2, 0, 0)
    right = Position(2, 0, 0)
    above = Position(0, 0, 1)

    board = {p: t(1), left: t(2)}
    assert is_free_position(p, board)

    board[right] = t(3)
    assert not is_free_position(p, board)

    board.pop(right)
    board[above] = t(4)
    assert not is_free_position(p, board)
