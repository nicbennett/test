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
