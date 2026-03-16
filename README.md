# Mahjong Solitaire (Shanghai) Prototype

A minimal but modular Mahjong Solitaire implementation in Python + Pygame.

## Run

```bash
python -m mahsol --seed 123 --layout brick --difficulty medium
```

Default brick size is `--width 8 --height 9 --layers 2` (144 tiles).
For quick iteration, use:

```bash
python -m mahsol --debug-32 --no-ui
```

You can still tune dimensions manually:

```bash
python -m mahsol --seed 123 --width 8 --height 4 --layers 1 --no-ui
```

If `pygame` fails to install with `fatal error: Python.h: No such file or directory`,
install Python development headers and SDL2 development packages first.
On Fedora:

```bash
sudo dnf install python3-devel SDL2-devel SDL2_image-devel SDL2_mixer-devel SDL2_ttf-devel
python -m pip install --user pygame
```

Headless generation/analyze only:

```bash
python -m mahsol --seed 123 --no-ui
```

## Controls

- Left click: select tile / attempt match
- `U`: undo
- `R`: redo
- `H`: hint (solver-backed)
- `Esc`: quit

## Graphics Assets

If `Assets/` is present, the pygame UI auto-loads tile PNGs and renders them instead of text labels.
Current mapping assumes Mahjong pack indices:
`1-9 BAM`, `10-18 DOT`, `19-27 CRK`, `28-31 winds`, `32-34 dragons`, `35-38 flowers`, `39-42 seasons`.

## Architecture

- `mahsol/models.py`: dataclasses and shared state models.
- `mahsol/layout.py`: layout geometry and free-tile rules.
- `mahsol/engine.py`: move legality, selection behavior, undo/redo.
- `mahsol/tileset.py`: standard 144 tiles and matching groups.
- `mahsol/generator.py`: reverse-build solvable puzzle generator.
- `mahsol/solver.py`: DFS + memo solver, hints, difficulty scoring.
- `mahsol/ui_pygame.py`: rendering/input.
- `mahsol/__main__.py`: CLI entry point.

## Coordinate system and footprint

`Position(x, y, z)` uses integer half-units in x/y.
Each tile footprint is `2x1` half-units, represented as `[x, x+2) x [y, y+1)`.

Rules:

- **Covered**: any higher tile that overlaps footprint blocks the tile below.
- **Side blocking**: same-layer neighbor touching exact left or right boundary.
- **Free tile**: not covered and at least one side open.

## Generator solvability strategy

The generator has two solvable-by-construction paths:

1. Fast path for aligned rectangular layouts (for example default `8x9x2`): repeatedly remove two currently free tiles using seeded randomness, then assign matching pairs to those removed slots.
2. General fallback: reverse-build with backtracking onto currently eligible boundary positions.

Both strategies produce solvable boards by construction.

## Solver high-level

- DFS with memoized transposition table using canonical board hash.
- Legal moves are generated from free tiles grouped by match-group.
- Prunes repeated states and dead ends.
- Hint tries candidate moves that preserve solvability.
- Difficulty score approximates branching + forced-move ratio.
