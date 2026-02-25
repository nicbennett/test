"""Deterministic solvable puzzle generation."""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Dict, List, Tuple

from .layout import Layout, is_free_position
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


def generate_puzzle(layout: Layout, seed: int, difficulty: str = "medium") -> BoardState:
    """Generate a solvable board by reverse-build with backtracking."""

    if len(layout.positions) % 2 != 0:
        raise ValueError("Layout must have even number of positions")

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
