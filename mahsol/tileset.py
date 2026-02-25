"""Mahjong tile set definitions."""

from __future__ import annotations

from typing import List, Tuple

from .models import Tile, TileKind


def standard_tiles_144() -> List[Tile]:
    """Return canonical 144 Mahjong Solitaire tiles."""

    tiles: List[Tile] = []
    tile_id = 0

    for suit in ["BAM", "DOT", "CRK"]:
        for rank in range(1, 10):
            face = f"{suit} {rank}"
            for _ in range(4):
                tiles.append(Tile(tile_id=tile_id, face=face, group=face, kind=TileKind.SUIT))
                tile_id += 1

    for wind in ["E", "S", "W", "N"]:
        for _ in range(4):
            tiles.append(Tile(tile_id=tile_id, face=wind, group=wind, kind=TileKind.HONOR))
            tile_id += 1

    for dragon in ["RD", "GD", "WD"]:
        for _ in range(4):
            tiles.append(Tile(tile_id=tile_id, face=dragon, group=dragon, kind=TileKind.HONOR))
            tile_id += 1

    for flower in ["FLW1", "FLW2", "FLW3", "FLW4"]:
        tiles.append(Tile(tile_id=tile_id, face=flower, group="flower", kind=TileKind.FLOWER))
        tile_id += 1

    for season in ["SEA1", "SEA2", "SEA3", "SEA4"]:
        tiles.append(Tile(tile_id=tile_id, face=season, group="season", kind=TileKind.SEASON))
        tile_id += 1

    return tiles


def pair_pool_from_standard() -> List[Tuple[Tile, Tile]]:
    """Build all legal matching pairs available from standard 144 set."""

    tiles = standard_tiles_144()
    by_group: dict[str, list[Tile]] = {}
    for t in tiles:
        by_group.setdefault(t.group, []).append(t)

    pairs: List[Tuple[Tile, Tile]] = []
    for group, gtiles in by_group.items():
        if group in {"flower", "season"}:
            gtiles_sorted = sorted(gtiles, key=lambda t: t.face)
            for i in range(0, len(gtiles_sorted), 2):
                pairs.append((gtiles_sorted[i], gtiles_sorted[i + 1]))
        else:
            for i in range(0, len(gtiles), 2):
                pairs.append((gtiles[i], gtiles[i + 1]))
    return pairs


def can_match(a: Tile, b: Tile) -> bool:
    """Whether two tiles can be removed as a pair."""

    if a.group in {"flower", "season"} and b.group == a.group:
        return True
    return a.face == b.face
