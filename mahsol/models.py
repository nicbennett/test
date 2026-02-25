"""Core data models for Mahjong Solitaire."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple




class TileKind(str, Enum):
    """Broad tile kind."""

    SUIT = "suit"
    HONOR = "honor"
    FLOWER = "flower"
    SEASON = "season"


class MatchGroup(str, Enum):
    """Matching categories for tiles."""

    FLOWER = "flower"
    SEASON = "season"


@dataclass(frozen=True, order=True)
class Position:
    """Tile coordinate on a half-unit grid.

    x and y are expressed in half-tile units. A tile footprint is 2x1 units.
    """

    x: int
    y: int
    z: int


@dataclass(frozen=True)
class Tile:
    """Tile face and matching information."""

    tile_id: int
    face: str
    group: str
    kind: TileKind


@dataclass(frozen=True)
class PlacedTile:
    """A tile placed on a board position."""

    tile: Tile


@dataclass(frozen=True)
class Move:
    """A removed pair of positions and tiles."""

    p1: Position
    p2: Position
    t1: PlacedTile
    t2: PlacedTile


@dataclass
class BoardState:
    """Current board plus history for play engine."""

    tiles: Dict[Position, PlacedTile]
    selected: Optional[Position] = None
    undo_stack: List[Move] = field(default_factory=list)
    redo_stack: List[Move] = field(default_factory=list)

    def clone_tiles(self) -> Dict[Position, PlacedTile]:
        """Copy tile map for solver/generator branching."""

        return dict(self.tiles)

    def canonical_key(self) -> Tuple[Tuple[int, int, int, str], ...]:
        """Stable hashable state key for memoization."""

        items = []
        for pos, placed in self.tiles.items():
            items.append((pos.x, pos.y, pos.z, placed.tile.group + ":" + placed.tile.face))
        items.sort()
        return tuple(items)
