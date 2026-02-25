"""Minimal pygame UI for Mahjong Solitaire."""

from __future__ import annotations

import time
from dataclasses import dataclass
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
    z_shift_x: int = -10
    z_shift_y: int = -10


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

    def board_to_screen(self, p: Position) -> pygame.Rect:
        x = self.cfg.x0 + (p.x // TILE_W) * self.cfg.tile_w + p.z * self.cfg.z_shift_x
        y = self.cfg.y0 + p.y * (self.cfg.tile_h // 2) + p.z * self.cfg.z_shift_y
        return pygame.Rect(x, y, self.cfg.tile_w, self.cfg.tile_h)

    def tile_under_mouse(self, pos: Tuple[int, int]) -> Optional[Position]:
        ordered = sorted(self.engine.state.tiles.keys(), key=lambda p: (p.z, p.y, p.x), reverse=True)
        for p in ordered:
            if self.board_to_screen(p).collidepoint(pos):
                return p
        return None

    def draw(self) -> None:
        self.screen.fill((28, 45, 58))
        now = time.time()
        for p in sorted(self.engine.state.tiles.keys(), key=lambda p: (p.z, p.y, p.x)):
            rect = self.board_to_screen(p)
            free = is_free_position(p, self.engine.state.tiles)
            base = (232, 224, 204) if free else (190, 188, 176)
            pygame.draw.rect(self.screen, base, rect, border_radius=8)
            border = (60, 60, 60)
            if self.engine.state.selected == p:
                border = (255, 196, 0)
            if self.hint and p in self.hint and now < self.hint_until:
                border = (80, 220, 255)
            pygame.draw.rect(self.screen, border, rect, width=3, border_radius=8)
            label = self.engine.state.tiles[p].tile.face
            surf = self.font.render(label, True, (20, 20, 20))
            self.screen.blit(surf, (rect.x + 8, rect.y + 8))

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
