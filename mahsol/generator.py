"""Deterministic solvable puzzle generation."""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Dict, List, Tuple

from .layout import TILE_W, Layout, is_free_position
from .models import BoardState, PlacedTile, Position, Tile, TileKind
from .tileset import pair_pool_from_standard


@dataclass(frozen=True)
class DifficultyParams:
    name: str
    openness_weight: float


DIFFICULTY = {
    "easy": DifficultyParams("easy", openness_weight=1.0),
    "medium": DifficultyParams("medium", openness_weight=0.0),
    "hard": DifficultyParams("hard", openness_weight=-1.0),
}


def eligible_reverse_positions(layout: Layout, placed: Dict[Position, PlacedTile]) -> List[Position]:
    eligible: List[Position] = []
    for p in layout.positions:
        if p in placed:
            continue
        probe = dict(placed)
        probe[p] = PlacedTile(Tile(-1, "_", "_", TileKind.SUIT))
        if is_free_position(p, probe):
            eligible.append(p)
    return eligible


def build_pair_sequence(pair_count: int, rng: random.Random) -> List[Tuple[Tile, Tile]]:
    pairs = pair_pool_from_standard()
    if pair_count > len(pairs):
        raise ValueError("Layout requires more pairs than standard tileset provides")
    rng.shuffle(pairs)
    return pairs[:pair_count]


def _rectangular_rows(layout: Layout) -> List[List[Position]] | None:
    """Return rows for a one-layer full rectangle layout, else None."""

    if not layout.positions:
        return None
    if any(p.z != 0 for p in layout.positions):
        return None

    by_y: Dict[int, List[Position]] = {}
    for p in layout.positions:
        by_y.setdefault(p.y, []).append(p)

    rows: List[List[Position]] = []
    expected_width = -1
    for y in sorted(by_y):
        row = sorted(by_y[y], key=lambda p: p.x)
        if expected_width == -1:
            expected_width = len(row)
        if len(row) != expected_width:
            return None
        if len(row) < 2 or len(row) % 2 != 0:
            return None
        if any((row[i + 1].x - row[i].x) != TILE_W for i in range(len(row) - 1)):
            return None
        rows.append(row)
    return rows


def _rectangular_rows_for_layer(positions: List[Position]) -> List[List[Position]] | None:
    """Return ordered rows for a rectangular single layer."""

    if not positions:
        return None
    by_y: Dict[int, List[Position]] = {}
    for p in positions:
        by_y.setdefault(p.y, []).append(p)

    rows: List[List[Position]] = []
    expected_width = -1
    for y in sorted(by_y):
        row = sorted(by_y[y], key=lambda p: p.x)
        if expected_width == -1:
            expected_width = len(row)
        if len(row) != expected_width:
            return None
        if len(row) < 2 or len(row) % 2 != 0:
            return None
        if any((row[i + 1].x - row[i].x) != TILE_W for i in range(len(row) - 1)):
            return None
        rows.append(row)
    return rows


def _rectangular_layer_rows(layout: Layout) -> Dict[int, List[List[Position]]] | None:
    """Return rectangular rows for each layer if layout is aligned rectangular layers."""

    by_z: Dict[int, List[Position]] = {}
    for p in layout.positions:
        by_z.setdefault(p.z, []).append(p)
    if not by_z:
        return None

    layers: Dict[int, List[List[Position]]] = {}
    ref_xy: set[tuple[int, int]] | None = None
    for z in sorted(by_z):
        rows = _rectangular_rows_for_layer(by_z[z])
        if rows is None:
            return None
        xy = {(p.x, p.y) for row in rows for p in row}
        if ref_xy is None:
            ref_xy = xy
        elif xy != ref_xy:
            return None
        layers[z] = rows
    return layers


def _random_rowwise_pairs(rows: List[List[Position]], rng: random.Random) -> List[Tuple[Position, Position]] | None:
    """Random legal pair-removal sequence for one rectangular layer."""

    occupied: set[Position] = {p for row in rows for p in row}
    left_of: Dict[Position, Position] = {}
    right_of: Dict[Position, Position] = {}
    for row in rows:
        for i, p in enumerate(row):
            if i > 0:
                left_of[p] = row[i - 1]
            if i + 1 < len(row):
                right_of[p] = row[i + 1]

    sequence: List[Tuple[Position, Position]] = []
    while occupied:
        free = [
            p
            for p in occupied
            if (left_of.get(p) not in occupied) or (right_of.get(p) not in occupied)
        ]
        if len(free) < 2:
            return None
        p1 = rng.choice(free)
        pool = [p for p in free if p != p1]
        if not pool:
            return None
        p2 = rng.choice(pool)
        occupied.remove(p1)
        occupied.remove(p2)
        sequence.append((p1, p2))
    return sequence


def _generate_random_rect(layout: Layout, seed: int) -> BoardState | None:
    """Fast seeded-random solvable generation for aligned rectangular layers."""

    layer_rows = _rectangular_layer_rows(layout)
    if layer_rows is None:
        return None
    rng = random.Random(seed)
    pair_slots: List[Tuple[Position, Position]] = []
    for z in sorted(layer_rows.keys(), reverse=True):
        layer_pairs = _random_rowwise_pairs(layer_rows[z], rng)
        if layer_pairs is None:
            return None
        pair_slots.extend(layer_pairs)

    pairs = build_pair_sequence(len(pair_slots), rng)
    placed: Dict[Position, PlacedTile] = {}
    for (p1, p2), pair in zip(pair_slots, pairs, strict=True):
        placed[p1] = PlacedTile(pair[0])
        placed[p2] = PlacedTile(pair[1])
    return BoardState(tiles=placed)


def generate_puzzle(layout: Layout, seed: int, difficulty: str = "medium") -> BoardState:
    """Generate a solvable board by reverse-build with backtracking."""

    if len(layout.positions) % 2 != 0:
        raise ValueError("Layout must have even number of positions")

    fast_board = _generate_random_rect(layout, seed)
    if fast_board is not None:
        return fast_board

    rng = random.Random(seed)
    params = DIFFICULTY.get(difficulty, DIFFICULTY["medium"])
    pair_sequence = build_pair_sequence(len(layout.positions) // 2, rng)
    placed: Dict[Position, PlacedTile] = {}
    visited = 0

    def openness_score(pos: Position, board: Dict[Position, PlacedTile]) -> int:
        probe = dict(board)
        probe[pos] = PlacedTile(Tile(-1, "_", "_", TileKind.SUIT))
        return sum(1 for p in probe if is_free_position(p, probe))

    def backtrack(step: int) -> bool:
        nonlocal visited
        visited += 1
        if visited > 200_000:
            return False
        if step == len(pair_sequence):
            return True

        eligible = eligible_reverse_positions(layout, placed)
        if len(eligible) < 2:
            return False

        rng.shuffle(eligible)
        eligible.sort(
            key=lambda p: params.openness_weight * openness_score(p, placed),
            reverse=True,
        )

        pair = pair_sequence[step]
        # Limit branching by selecting from the best boundary candidates.
        candidates = eligible[: min(12, len(eligible))]
        for i in range(len(candidates) - 1):
            for j in range(i + 1, len(candidates)):
                p1, p2 = candidates[i], candidates[j]
                probe = dict(placed)
                probe[p1] = PlacedTile(pair[0])
                probe[p2] = PlacedTile(pair[1])
                if not (is_free_position(p1, probe) and is_free_position(p2, probe)):
                    continue
                placed[p1] = PlacedTile(pair[0])
                placed[p2] = PlacedTile(pair[1])
                if backtrack(step + 1):
                    return True
                del placed[p1]
                del placed[p2]
        return False

    if not backtrack(0):
        raise RuntimeError("Failed to generate puzzle with reverse-build")

    return BoardState(tiles=placed)
