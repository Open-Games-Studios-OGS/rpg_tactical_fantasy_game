"""Dockable palette panel for tileset browsing and drag/drop selection."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Tuple

import pygame

from apps.level_editor.palette_model import PaletteModel, TileEntry


@dataclass
class DragPayload:
    tileset_name: str
    local_id: int
    surface: pygame.Surface
    stamp_mode: bool = False


@dataclass
class PaletteUIConfig:
    tile_render_size: int = 48
    grid_cols: int = 5
    grid_rows: int = 5
    padding: int = 8
    gutter: int = 4
    bg_color: Tuple[int, int, int] = (30, 30, 30)
    grid_color: Tuple[int, int, int] = (45, 45, 45)
    border_color: Tuple[int, int, int] = (70, 70, 70)
    text_color: Tuple[int, int, int] = (220, 220, 220)
    font_name: Optional[str] = None
    font_size: int = 14


class PalettePanel:
    def __init__(
        self,
        model: PaletteModel,
        rect: pygame.Rect,
        on_tileset_menu: Optional[Callable[[], None]] = None,
        config: PaletteUIConfig = PaletteUIConfig(),
    ) -> None:
        self.model = model
        self.rect = rect
        self.config = config
        self.on_tileset_menu = on_tileset_menu

        self.font = pygame.font.SysFont(self.config.font_name, self.config.font_size)
        self.selected: Optional[TileEntry] = None
        self.hovered: Optional[int] = None
        self.drag_payload: Optional[DragPayload] = None

        self._prev_button = pygame.Rect(
            self.rect.x + self.config.padding,
            self.rect.bottom - self.config.padding - 24,
            50,
            24,
        )
        self._next_button = pygame.Rect(
            self.rect.x + self.rect.width - self.config.padding - 50,
            self.rect.bottom - self.config.padding - 24,
            50,
            24,
        )
        self._tileset_button = pygame.Rect(
            self.rect.x + self.config.padding,
            self.rect.y + self.config.padding,
            self.rect.width - 2 * self.config.padding,
            24,
        )

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                if self._tileset_button.collidepoint(event.pos) and self.on_tileset_menu:
                    self.on_tileset_menu()
                    return
                if self._prev_button.collidepoint(event.pos):
                    self.model.prev_page()
                    return
                if self._next_button.collidepoint(event.pos):
                    self.model.next_page()
                    return
                tile_index = self._tile_index_at(event.pos)
                if tile_index is not None:
                    tiles = self.model.page_tiles()
                    if tile_index < len(tiles):
                        tile = tiles[tile_index]
                        self.selected = tile
                        stamp = bool(pygame.key.get_mods() & pygame.KMOD_SHIFT)
                        self.drag_payload = DragPayload(
                            tileset_name=tile.tileset_name,
                            local_id=tile.local_id,
                            surface=tile.surface,
                            stamp_mode=stamp,
                        )
            elif event.button == 4:
                self.model.prev_page()
            elif event.button == 5:
                self.model.next_page()

        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button in (1, 3):
                self.drag_payload = None

        elif event.type == pygame.MOUSEMOTION:
            self.hovered = self._tile_index_at(event.pos)

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_PAGEUP:
                self.model.prev_page()
            elif event.key == pygame.K_PAGEDOWN:
                self.model.next_page()

    def _tile_index_at(self, pos: Tuple[int, int]) -> Optional[int]:
        grid_origin_y = self._grid_origin_y
        grid_origin_x = self.rect.x + self.config.padding
        tw = self.config.tile_render_size
        gh = self.config.gutter
        for row in range(self.config.grid_rows):
            for col in range(self.config.grid_cols):
                idx = row * self.config.grid_cols + col
                x = grid_origin_x + col * (tw + gh)
                y = grid_origin_y + row * (tw + gh)
                cell = pygame.Rect(x, y, tw, tw)
                if cell.collidepoint(pos):
                    return idx
        return None

    @property
    def _grid_origin_y(self) -> int:
        return self.rect.y + self.config.padding + self._tileset_button.height + self.config.gutter

    def draw(self, surface: pygame.Surface) -> None:
        pygame.draw.rect(surface, self.config.bg_color, self.rect)
        pygame.draw.rect(surface, self.config.border_color, self.rect, 1)

        self._draw_tileset_bar(surface)
        self._draw_grid(surface)
        self._draw_paging(surface)

    def _draw_tileset_bar(self, surface: pygame.Surface) -> None:
        pygame.draw.rect(surface, self.config.grid_color, self._tileset_button)
        pygame.draw.rect(surface, self.config.border_color, self._tileset_button, 1)
        name = self.model.state.tileset_name or "Select tileset"
        text = self.font.render(name, True, self.config.text_color)
        surface.blit(
            text,
            (
                self._tileset_button.x + 6,
                self._tileset_button.y + (self._tileset_button.height - text.get_height()) // 2,
            ),
        )

    def _draw_grid(self, surface: pygame.Surface) -> None:
        tiles = self.model.page_tiles()
        tw = self.config.tile_render_size
        gh = self.config.gutter
        origin_x = self.rect.x + self.config.padding
        origin_y = self._grid_origin_y

        for idx in range(self.config.grid_rows * self.config.grid_cols):
            col = idx % self.config.grid_cols
            row = idx // self.config.grid_cols
            x = origin_x + col * (tw + gh)
            y = origin_y + row * (tw + gh)
            cell = pygame.Rect(x, y, tw, tw)
            pygame.draw.rect(surface, self.config.grid_color, cell)
            pygame.draw.rect(surface, self.config.border_color, cell, 1)

            if idx < len(tiles):
                tile = tiles[idx]
                tile_img = pygame.transform.smoothscale(tile.surface, (tw, tw))
                surface.blit(tile_img, (x, y))
                if self.selected and tile.local_id == self.selected.local_id and tile.tileset_name == self.selected.tileset_name:
                    pygame.draw.rect(surface, (200, 200, 50), cell, 2)
                elif self.hovered == idx:
                    pygame.draw.rect(surface, (150, 150, 150), cell, 1)

    def _draw_paging(self, surface: pygame.Surface) -> None:
        pygame.draw.rect(surface, self.config.grid_color, self._prev_button)
        pygame.draw.rect(surface, self.config.border_color, self._prev_button, 1)
        prev_text = self.font.render("<", True, self.config.text_color)
        surface.blit(
            prev_text,
            (
                self._prev_button.centerx - prev_text.get_width() // 2,
                self._prev_button.centery - prev_text.get_height() // 2,
            ),
        )

        pygame.draw.rect(surface, self.config.grid_color, self._next_button)
        pygame.draw.rect(surface, self.config.border_color, self._next_button, 1)
        next_text = self.font.render(">", True, self.config.text_color)
        surface.blit(
            next_text,
            (
                self._next_button.centerx - next_text.get_width() // 2,
                self._next_button.centery - next_text.get_height() // 2,
            ),
        )

        page_label = f"{self.model.state.page_index + 1}/{max(1, self.model.page_count)}"
        label_surf = self.font.render(page_label, True, self.config.text_color)
        surface.blit(
            label_surf,
            (
                self.rect.centerx - label_surf.get_width() // 2,
                self._prev_button.y + (self._prev_button.height - label_surf.get_height()) // 2,
            ),
        )
