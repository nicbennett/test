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
    parser.add_argument("--width", type=int, default=8, help="Brick layout width in tiles")
    parser.add_argument("--height", type=int, default=9, help="Brick layout height in tiles")
    parser.add_argument("--layers", type=int, default=2, help="Brick layout layers")
    parser.add_argument("--debug-32", action="store_true", help="Use 32-tile debug brick layout (8x4x1)")
    parser.add_argument("--no-ui", action="store_true", help="Generate and analyze only")
    args = parser.parse_args()

    if args.layout != "brick":
        raise ValueError("Only 'brick' layout is currently implemented")

    width, height, layers = args.width, args.height, args.layers
    if args.debug_32:
        width, height, layers = 8, 4, 1

    layout = brick_layout(width=width, height=height, layers=layers)
    state = generate_puzzle(layout=layout, seed=args.seed, difficulty=args.difficulty)

    solver = Solver()
    result = solver.solve(state, max_states=20_000)
    difficulty_score = solver.difficulty_score(state)

    print(f"seed={args.seed} layout={layout.name} difficulty={args.difficulty}")
    print(f"tiles={len(state.tiles)} solvable={result.solvable} explored={result.explored_states}")
    print(f"difficulty_score={difficulty_score}")

    if not args.no_ui:
        try:
            from .ui_pygame import MahjongUI
        except ModuleNotFoundError as exc:
            if exc.name == "pygame":
                print(
                    "UI disabled: 'pygame' is not installed.\n"
                    "Run headless with --no-ui, or install pygame.\n"
                    "Fedora example:\n"
                    "  sudo dnf install python3-devel SDL2-devel SDL2_image-devel "
                    "SDL2_mixer-devel SDL2_ttf-devel\n"
                    "  python -m pip install --user pygame"
                )
                raise SystemExit(2) from exc
            raise

        MahjongUI(state).run()


if __name__ == "__main__":
    main()
