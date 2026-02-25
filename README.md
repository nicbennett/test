# Mahjong Solitaire (Shanghai) Prototype

A minimal but modular Mahjong Solitaire implementation in Python + Pygame.

## Run

```bash
python -m mahsol --seed 123 --layout brick --difficulty medium
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

- **Covered**: tile at `z+1` overlaps footprint of tile below.
- **Side blocking**: same-layer neighbor touching exact left or right boundary.
- **Free tile**: not covered and at least one side open.

## Generator solvability strategy

The generator uses reverse-build with backtracking:

1. Start empty.
2. Repeatedly place matching pairs onto currently eligible boundary positions (positions that would be free if occupied now).
3. Backtrack on dead ends.

Because each reverse step adds a pair that is immediately removable in forward play, produced boards are solvable by construction.

## Solver high-level

- DFS with memoized transposition table using canonical board hash.
- Legal moves are generated from free tiles grouped by match-group.
- Prunes repeated states and dead ends.
- Hint tries candidate moves that preserve solvability.
- Difficulty score approximates branching + forced-move ratio.
