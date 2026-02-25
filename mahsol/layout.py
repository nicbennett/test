"""Layout geometry and free-tile logic."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Set

from .models import Position, PlacedTile

TILE_W = 2
TILE_H = 1


@dataclass(frozen=True)
class Layout:
    """Collection of valid positions for a puzzle."""

    name: str
    positions: Set[Position]


def footprint(p: Position) -> tuple[int, int, int, int]:
    """Return rectangle [x0,x1) x [y0,y1) in half-unit grid."""

    return p.x, p.x + TILE_W, p.y, p.y + TILE_H


def overlaps(a: Position, b: Position) -> bool:
    """Whether two tile footprints overlap in x/y."""

    ax0, ax1, ay0, ay1 = footprint(a)
    bx0, bx1, by0, by1 = footprint(b)
    return ax0 < bx1 and bx0 < ax1 and ay0 < by1 and by0 < ay1


def covers(a: Position, b: Position) -> bool:
    """Tile at a (higher layer) covers b (lower layer)."""

    return a.z == b.z + 1 and overlaps(a, b)


def blocks_left(p: Position, q: Position) -> bool:
    """Whether q blocks the left side of p at same z."""

    if p.z != q.z:
        return False
    px0, _, py0, py1 = footprint(p)
    _, qx1, qy0, qy1 = footprint(q)
    y_overlap = py0 < qy1 and qy0 < py1
    return qx1 == px0 and y_overlap


def blocks_right(p: Position, q: Position) -> bool:
    """Whether q blocks the right side of p at same z."""

    if p.z != q.z:
        return False
    _, px1, py0, py1 = footprint(p)
    qx0, _, qy0, qy1 = footprint(q)
    y_overlap = py0 < qy1 and qy0 < py1
    return qx0 == px1 and y_overlap


def is_free_position(p: Position, tiles: Dict[Position, PlacedTile]) -> bool:
    """Check if position is currently free according to Mahjong Solitaire rules."""

    if p not in tiles:
        return False

    for q in tiles:
        if covers(q, p):
            return False

    left_blocked = any(blocks_left(p, q) for q in tiles if q != p)
    right_blocked = any(blocks_right(p, q) for q in tiles if q != p)
    return (not left_blocked) or (not right_blocked)


def free_positions(tiles: Dict[Position, PlacedTile]) -> List[Position]:
    """Return all free tile positions."""

    return [p for p in tiles if is_free_position(p, tiles)]


def brick_layout(width: int = 12, height: int = 8, layers: int = 3) -> Layout:
    """Create a simple shrinking brick layout.

    x advances by TILE_W, y by TILE_H, each higher layer shrinks and offsets inward.
    """

    positions: Set[Position] = set()
    for z in range(layers):
        w = width - 2 * z
        h = height - 2 * z
        if w <= 0 or h <= 0:
            break
        x_off = z
        y_off = z
        for iy in range(h):
            for ix in range(w):
                positions.add(Position((ix + x_off) * TILE_W, iy + y_off, z))
    return Layout(name="brick", positions=positions)
