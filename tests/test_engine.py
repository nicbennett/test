from mahsol.engine import PlayEngine
from mahsol.models import BoardState, PlacedTile, Position, Tile, TileKind


def test_apply_undo_redo():
    p1 = Position(0, 0, 0)
    p2 = Position(4, 0, 0)
    state = BoardState(
        tiles={
            p1: PlacedTile(Tile(1, "BAM 1", "BAM 1", TileKind.SUIT)),
            p2: PlacedTile(Tile(2, "BAM 1", "BAM 1", TileKind.SUIT)),
        }
    )
    eng = PlayEngine(state)

    eng.click(p1)
    removed = eng.click(p2)
    assert removed
    assert len(state.tiles) == 0

    assert eng.undo()
    assert len(state.tiles) == 2

    assert eng.redo()
    assert len(state.tiles) == 0
