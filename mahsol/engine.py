"""Game play engine."""

from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from typing import List, Optional, Tuple

from .layout import is_free_position
from .models import BoardState, Move, Position
from .tileset import can_match


@dataclass
class PlayEngine:
    """Stateful play interactions and move history."""

    state: BoardState

    def legal_moves(self) -> List[Tuple[Position, Position]]:
        free = [p for p in self.state.tiles if is_free_position(p, self.state.tiles)]
        moves: List[Tuple[Position, Position]] = []
        for p1, p2 in combinations(free, 2):
            if can_match(self.state.tiles[p1].tile, self.state.tiles[p2].tile):
                moves.append((p1, p2))
        return moves

    def click(self, pos: Optional[Position]) -> bool:
        """Handle click. Returns True if a pair was removed."""

        if pos is None or pos not in self.state.tiles or not is_free_position(pos, self.state.tiles):
            self.state.selected = None
            return False

        if self.state.selected is None:
            self.state.selected = pos
            return False

        prev = self.state.selected
        if prev == pos:
            self.state.selected = None
            return False

        if (
            prev in self.state.tiles
            and is_free_position(prev, self.state.tiles)
            and is_free_position(pos, self.state.tiles)
            and can_match(self.state.tiles[prev].tile, self.state.tiles[pos].tile)
        ):
            move = Move(prev, pos, self.state.tiles[prev], self.state.tiles[pos])
            del self.state.tiles[prev]
            del self.state.tiles[pos]
            self.state.undo_stack.append(move)
            self.state.redo_stack.clear()
            self.state.selected = None
            return True

        self.state.selected = pos
        return False

    def undo(self) -> bool:
        if not self.state.undo_stack:
            return False
        move = self.state.undo_stack.pop()
        self.state.tiles[move.p1] = move.t1
        self.state.tiles[move.p2] = move.t2
        self.state.redo_stack.append(move)
        self.state.selected = None
        return True

    def redo(self) -> bool:
        if not self.state.redo_stack:
            return False
        move = self.state.redo_stack.pop()
        if move.p1 not in self.state.tiles or move.p2 not in self.state.tiles:
            return False
        del self.state.tiles[move.p1]
        del self.state.tiles[move.p2]
        self.state.undo_stack.append(move)
        self.state.selected = None
        return True


    def shuffle_remaining(self) -> bool:
        """Optional shuffle hook; intentionally conservative stub."""

        return False
    def is_win(self) -> bool:
        return not self.state.tiles

    def is_loss(self) -> bool:
        return bool(self.state.tiles) and not self.legal_moves()
