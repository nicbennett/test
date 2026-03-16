"""Minimal pygame UI for Mahjong Solitaire."""

from __future__ import annotations

import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple

import pygame

from .engine import PlayEngine
from .layout import TILE_H, TILE_W, is_free_position
from .models import BoardState, Position
from .solver import Solver


@dataclass
class UiConfig:
    width: int = 1200
    height: int = 800
    tile_w: int = 64
    tile_h: int = 84
    x0: int = 120
    y0: int = 120
    z_shift_x: int = 0
    z_shift_y: int = 0
    depth_px: int = 8


class MahjongUI:
    def __init__(self, state: BoardState) -> None:
        pygame.init()
        self.cfg = UiConfig()
        self.screen = pygame.display.set_mode((self.cfg.width, self.cfg.height))
        pygame.display.set_caption("Mahjong Solitaire Prototype")
        self.clock = pygame.time.Clock()
        self.engine = PlayEngine(state)
        self.solver = Solver()
        self.hint: Optional[Tuple[Position, Position]] = None
        self.hint_until = 0.0
        self.font = pygame.font.SysFont("arial", 16)
        self.tile_ratio = self.cfg.tile_h / self.cfg.tile_w
        self.apply_asset_tile_aspect()
        self.fit_board_to_window()
        self.tile_images = self.load_tile_images()
        self.blocked_tile_images = {face: self.to_grayscale(img) for face, img in self.tile_images.items()}

    @staticmethod
    def to_grayscale(src: pygame.Surface) -> pygame.Surface:
        out = src.copy()
        w, h = out.get_size()
        for x in range(w):
            for y in range(h):
                r, g, b, a = out.get_at((x, y))
                gray = int(0.299 * r + 0.587 * g + 0.114 * b)
                out.set_at((x, y), (gray, gray, gray, a))
        return out

    @staticmethod
    def _asset_index_for_face(face: str) -> int:
        if face.startswith("BAM "):
            return int(face.split()[1])
        if face.startswith("DOT "):
            return 9 + int(face.split()[1])
        if face.startswith("CRK "):
            return 18 + int(face.split()[1])
        if face in {"E", "S", "W", "N"}:
            return {"E": 28, "S": 29, "W": 30, "N": 31}[face]
        if face in {"RD", "GD", "WD"}:
            return {"RD": 32, "GD": 33, "WD": 34}[face]
        if face.startswith("FLW"):
            return 34 + int(face[-1])
        if face.startswith("SEA"):
            return 38 + int(face[-1])
        return -1

    def _discover_asset_pngs(self) -> dict[int, Path]:
        root = Path(__file__).resolve().parent.parent / "Assets"
        if not root.exists():
            return {}

        indexed: dict[int, Path] = {}
        for p in root.rglob("*.png"):
            m = re.search(r"\((\d+)\)\.png$", p.name)
            if not m:
                continue
            idx = int(m.group(1))
            # Keep first hit for stable behavior if duplicates ever appear.
            indexed.setdefault(idx, p)
        return indexed

    def apply_asset_tile_aspect(self) -> None:
        assets = self._discover_asset_pngs()
        if not assets:
            return
        first = assets[sorted(assets.keys())[0]]
        try:
            surf = pygame.image.load(str(first)).convert_alpha()
        except pygame.error:
            return
        bounds = surf.get_bounding_rect()
        if bounds.width <= 0 or bounds.height <= 0:
            return
        self.tile_ratio = bounds.height / bounds.width

    def fit_board_to_window(self) -> None:
        if not self.engine.state.tiles:
            return

        xs = [p.x // TILE_W for p in self.engine.state.tiles]
        ys = [p.y for p in self.engine.state.tiles]
        zs = [p.z for p in self.engine.state.tiles]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        max_z = max(zs)
        board_cols = (max_x - min_x) + 1
        board_rows = (max_y - min_y) + 1

        # Reserve space for HUD and keep consistent margins.
        margin_x = 24
        margin_top = 56
        margin_bottom = 24
        avail_w = max(1, self.cfg.width - (2 * margin_x))
        avail_h = max(1, self.cfg.height - margin_top - margin_bottom)

        depth_ratio = 0.12
        # Include stack lift and prism depth in fit calculations.
        max_tile_w_by_w = int(avail_w / (board_cols + depth_ratio * (max_z + 1)))
        max_tile_w_by_h = int(avail_h / ((board_rows * self.tile_ratio) + depth_ratio * (max_z + 1)))
        tile_w = max(16, min(max_tile_w_by_w, max_tile_w_by_h))
        tile_h = max(16, int(tile_w * self.tile_ratio))
        depth_px = max(4, int(tile_w * depth_ratio))

        self.cfg.tile_w = tile_w
        self.cfg.tile_h = tile_h
        self.cfg.depth_px = depth_px
        self.cfg.z_shift_x = depth_px
        self.cfg.z_shift_y = -depth_px

        board_px_w = board_cols * tile_w + depth_px * (max_z + 1)
        board_px_h = board_rows * tile_h + depth_px * (max_z + 1)
        self.cfg.x0 = (self.cfg.width - board_px_w) // 2 - (min_x * tile_w) + depth_px
        self.cfg.y0 = margin_top + ((avail_h - board_px_h) // 2) - (min_y * tile_h) + (max_z * depth_px)

    def load_tile_images(self) -> dict[str, pygame.Surface]:
        assets = self._discover_asset_pngs()
        images: dict[str, pygame.Surface] = {}

        for tile in self.engine.state.tiles.values():
            face = tile.tile.face
            if face in images:
                continue
            idx = self._asset_index_for_face(face)
            src = assets.get(idx)
            if src is None:
                continue
            try:
                surf = pygame.image.load(str(src)).convert_alpha()
            except pygame.error:
                continue
            # Source PNGs are large canvases; crop alpha bounds before scaling.
            bounds = surf.get_bounding_rect()
            if bounds.width > 0 and bounds.height > 0:
                surf = surf.subsurface(bounds).copy()
            images[face] = pygame.transform.smoothscale(surf, (self.cfg.tile_w, self.cfg.tile_h))
        return images

    def board_to_screen(self, p: Position) -> pygame.Rect:
        x = self.cfg.x0 + (p.x // TILE_W) * self.cfg.tile_w + p.z * self.cfg.z_shift_x
        y = self.cfg.y0 + p.y * self.cfg.tile_h + p.z * self.cfg.z_shift_y
        return pygame.Rect(x, y, self.cfg.tile_w, self.cfg.tile_h)

    def tile_under_mouse(self, pos: Tuple[int, int]) -> Optional[Position]:
        ordered = sorted(self.engine.state.tiles.keys(), key=lambda p: (p.z, p.y, p.x), reverse=True)
        for p in ordered:
            if self.board_to_screen(p).collidepoint(pos):
                return p
            rect = self.board_to_screen(p)
            prism = pygame.Rect(rect.x - self.cfg.depth_px, rect.y, rect.w + self.cfg.depth_px, rect.h + self.cfg.depth_px)
            if prism.collidepoint(pos):
                return p
        return None

    def draw_prism(self, rect: pygame.Rect, face: str, free: bool) -> None:
        d = self.cfg.depth_px
        top = rect
        ex, ey = -d, d
        left = [(top.left, top.top), (top.left + ex, top.top + ey), (top.left + ex, top.bottom + ey), (top.left, top.bottom)]
        bottom = [(top.left, top.bottom), (top.right, top.bottom), (top.right + ex, top.bottom + ey), (top.left + ex, top.bottom + ey)]

        left_col = (176, 166, 150) if free else (128, 128, 128)
        bottom_col = (198, 188, 172) if free else (142, 142, 142)
        pygame.draw.polygon(self.screen, left_col, left)
        pygame.draw.polygon(self.screen, bottom_col, bottom)

        img = self.tile_images.get(face)
        if img is not None:
            draw_img = img if free else self.blocked_tile_images.get(face, img)
            self.screen.blit(draw_img, top)
        else:
            base = (232, 224, 204) if free else (165, 178, 192)
            pygame.draw.rect(self.screen, base, top, border_radius=8)
            surf = self.font.render(face, True, (20, 20, 20))
            self.screen.blit(surf, (top.x + 8, top.y + 8))

        # Emboss/groove edges between stacked tiles/layers.
        groove = (78, 78, 78)
        groove_soft = (108, 108, 108)
        highlight = (245, 245, 245)
        pygame.draw.line(self.screen, groove, (top.left, top.top), (top.left + ex, top.top + ey), 1)
        pygame.draw.line(self.screen, groove, (top.left, top.bottom), (top.left + ex, top.bottom + ey), 1)
        pygame.draw.line(self.screen, groove_soft, (top.left + ex, top.bottom + ey), (top.right + ex, top.bottom + ey), 1)
        pygame.draw.line(self.screen, highlight, (top.left, top.top), (top.right, top.top), 1)
        pygame.draw.line(self.screen, highlight, (top.right, top.top), (top.right, top.bottom), 1)

    def draw(self) -> None:
        self.screen.fill((28, 45, 58))
        for p in sorted(self.engine.state.tiles.keys(), key=lambda p: (p.z, p.y, p.x)):
            rect = self.board_to_screen(p)
            free = is_free_position(p, self.engine.state.tiles)
            face = self.engine.state.tiles[p].tile.face
            self.draw_prism(rect, face, free)
            border = (60, 60, 60)
            if self.engine.state.selected == p:
                border = (255, 196, 0)
            if self.hint and p in self.hint and now < self.hint_until:
                border = (80, 220, 255)
            pygame.draw.rect(self.screen, border, rect, width=3, border_radius=8)

        info = (
            "LMB select/match | U undo | R redo | H hint | Esc quit | "
            f"Remaining: {len(self.engine.state.tiles)}"
        )
        self.screen.blit(self.font.render(info, True, (245, 245, 245)), (20, 20))
        pygame.display.flip()

    def run(self) -> None:
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_u:
                        self.engine.undo()
                    elif event.key == pygame.K_r:
                        self.engine.redo()
                    elif event.key == pygame.K_h:
                        self.hint = self.solver.hint(self.engine.state)
                        self.hint_until = time.time() + 1.0
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    p = self.tile_under_mouse(event.pos)
                    self.engine.click(p)

            self.draw()
            if self.engine.is_win():
                running = False
            self.clock.tick(60)

        pygame.quit()
