"""Solver and analyzer for Mahjong Solitaire boards."""

from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from typing import Dict, List, Optional, Tuple

from .layout import is_free_position
from .models import BoardState, Move, Position
from .tileset import can_match


@dataclass
class SolverResult:
    solvable: bool
    solution: List[Tuple[Position, Position]]
    explored_states: int


class Solver:
    """Depth-first solver with memoization."""

    def __init__(self) -> None:
        self.memo: Dict[Tuple[Tuple[int, int, int, str], ...], bool] = {}
        self.explored_states = 0

    def legal_moves(self, state: BoardState) -> List[Tuple[Position, Position]]:
        free = [p for p in state.tiles if is_free_position(p, state.tiles)]
        by_group: dict[str, list[Position]] = {}
        for p in free:
            by_group.setdefault(state.tiles[p].tile.group, []).append(p)

        moves: List[Tuple[Position, Position]] = []
        for positions in by_group.values():
            for p1, p2 in combinations(positions, 2):
                if can_match(state.tiles[p1].tile, state.tiles[p2].tile):
                    moves.append((p1, p2))

        def score(move: Tuple[Position, Position]) -> int:
            p1, p2 = move
            return p1.z + p2.z

        moves.sort(key=score, reverse=True)
        return moves

    def _search(
        self,
        tiles: Dict[Position, object],
        path: List[Tuple[Position, Position]],
        max_states: int,
    ) -> Optional[List[Tuple[Position, Position]]]:
        state = BoardState(tiles=tiles)
        key = state.canonical_key()
        if key in self.memo:
            return None
        self.memo[key] = True
        self.explored_states += 1
        if self.explored_states > max_states:
            return None
        if not tiles:
            return list(path)

        moves = self.legal_moves(state)
        if not moves:
            return None

        for p1, p2 in moves:
            next_tiles = dict(tiles)
            del next_tiles[p1]
            del next_tiles[p2]
            path.append((p1, p2))
            result = self._search(next_tiles, path, max_states)
            path.pop()
            if result is not None:
                return result
        return None

    def solve(self, state: BoardState, max_states: int = 200_000) -> SolverResult:
        self.memo.clear()
        self.explored_states = 0
        solution = self._search(state.clone_tiles(), [], max_states)
        return SolverResult(solution is not None, solution or [], self.explored_states)

    def hint(self, state: BoardState, max_states: int = 30_000) -> Optional[Tuple[Position, Position]]:
        moves = self.legal_moves(state)
        for move in moves:
            next_tiles = state.clone_tiles()
            del next_tiles[move[0]]
            del next_tiles[move[1]]
            result = self.solve(BoardState(tiles=next_tiles), max_states=max_states)
            if result.solvable:
                return move
        return moves[0] if moves else None

    def difficulty_score(self, state: BoardState, sample_depth: int = 20) -> float:
        """Rough score based on average branching and forced moves."""

        tiles = state.clone_tiles()
        branches: List[int] = []
        forced = 0
        for _ in range(sample_depth):
            cur = BoardState(tiles=tiles)
            moves = self.legal_moves(cur)
            if not moves:
                break
            branches.append(len(moves))
            if len(moves) == 1:
                forced += 1
            m = moves[0]
            del tiles[m[0]]
            del tiles[m[1]]
            if not tiles:
                break
        if not branches:
            return 0.0
        avg_branch = sum(branches) / len(branches)
        forced_ratio = forced / len(branches)
        return round(avg_branch + forced_ratio * 3.0, 2)
