from mahsol.engine import PlayEngine
from mahsol.generator import generate_puzzle
from mahsol.layout import brick_layout
from mahsol.solver import Solver


def test_generated_boards_solvable_multiple_seeds():
    layout = brick_layout(width=4, height=2, layers=1)
    for seed in [1, 2, 7, 42, 99]:
        board = generate_puzzle(layout, seed=seed, difficulty="medium")
        result = Solver().solve(board, max_states=5000)
        assert result.solvable


def test_determinism_same_seed_same_board():
    layout = brick_layout(width=4, height=2, layers=1)
    a = generate_puzzle(layout, seed=123, difficulty="hard")
    b = generate_puzzle(layout, seed=123, difficulty="hard")
    assert a.canonical_key() == b.canonical_key()


def test_generate_144_tile_board():
    layout = brick_layout(width=8, height=9, layers=2)
    board = generate_puzzle(layout, seed=123, difficulty="medium")
    assert len(board.tiles) == 144
    assert PlayEngine(board).legal_moves()


def test_144_tile_board_is_seed_deterministic():
    layout = brick_layout(width=8, height=9, layers=2)
    a = generate_puzzle(layout, seed=123, difficulty="medium")
    b = generate_puzzle(layout, seed=123, difficulty="medium")
    c = generate_puzzle(layout, seed=124, difficulty="medium")
    assert a.canonical_key() == b.canonical_key()
    assert a.canonical_key() != c.canonical_key()
