"""CLI entrypoint: python -m mahsol."""

from __future__ import annotations

import argparse

from .generator import generate_puzzle
from .layout import brick_layout
from .solver import Solver


def main() -> None:
    parser = argparse.ArgumentParser(description="Mahjong Solitaire prototype")
    parser.add_argument("--seed", type=int, default=123)
    parser.add_argument("--layout", type=str, default="brick")
    parser.add_argument("--difficulty", type=str, default="medium", choices=["easy", "medium", "hard"])
    parser.add_argument("--no-ui", action="store_true", help="Generate and analyze only")
    args = parser.parse_args()

    if args.layout != "brick":
        raise ValueError("Only 'brick' layout is currently implemented")

    layout = brick_layout(width=4, height=2, layers=1)
    state = generate_puzzle(layout=layout, seed=args.seed, difficulty=args.difficulty)

    solver = Solver()
    result = solver.solve(state, max_states=20_000)
    difficulty_score = solver.difficulty_score(state)

    print(f"seed={args.seed} layout={layout.name} difficulty={args.difficulty}")
    print(f"tiles={len(state.tiles)} solvable={result.solvable} explored={result.explored_states}")
    print(f"difficulty_score={difficulty_score}")

    if not args.no_ui:
        from .ui_pygame import MahjongUI

        MahjongUI(state).run()


if __name__ == "__main__":
    main()
