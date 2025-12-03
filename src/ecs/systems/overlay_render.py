#!/usr/bin/env python3
#
#   Copyright (c) 2023, Monaco F. J. <monaco@usp.br>
#
#   This file is part of Naja.
#
#   Naja is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""OverlayRenderSystem - renders pause and settings overlays.

This system follows ECS Single Responsibility Principle by handling ONLY
overlay rendering (pause screen, settings menu) on top of the game.
"""

import pygame
from ecs.systems.base_system import BaseSystem
from ecs.world import World
from core.rendering.pygame_surface_renderer import RenderEnqueue
from core.types.color import Color
from game import constants


class OverlayRenderSystem(BaseSystem):
    """System responsible for rendering game overlays.

    Responsibilities:
    - Render pause overlay (when paused)
    - Render settings overlay (when settings menu is open)

    NOT responsible for:
    - Basic HUD rendering (use UIRenderSystem)
    - Game world rendering (use BoardRenderSystem)
    """

    def __init__(self, renderer: RenderEnqueue, settings=None, config=None):
        """Initialize the OverlayRenderSystem.

        Args:
            renderer: RenderEnqueue view to queue draw commands
            settings: Optional GameSettings instance for accessing settings
            config: Game config for calculating grid size
        """
        self._renderer = renderer
        self._settings = settings
        self._config = config

    def draw_pause_overlay(self, surface_width: int, surface_height: int) -> None:
        """Draw pause overlay with semi-transparent background and text.

        Args:
            surface_width: Width of the surface
            surface_height: Height of the surface
        """
        try:
            # create semi-transparent overlay
            overlay = pygame.Surface((surface_width, surface_height))
            overlay.set_alpha(128)  # 50% transparent
            overlay.fill(Color.from_hex(constants.ARENA_PRIMARY_COLOR).to_tuple())
            self._renderer.blit(overlay, (0, 0))

            # render "PAUSED" text
            font_size = int(surface_width / 10)
            font_path = "assets/font/GetVoIP-Grotesque.ttf"

            try:
                pause_font = pygame.font.Font(font_path, font_size)
            except Exception:
                pause_font = pygame.font.Font(None, font_size)

            pause_text = pause_font.render(
                "PAUSED", True, Color.from_hex(constants.SCORE_COLOR).to_tuple()
            )
            pause_rect = pause_text.get_rect()
            pause_rect.center = (surface_width // 2, surface_height // 2)

            # blit to screen
            self._renderer.blit(pause_text, pause_rect)

            # render hint text below
            hint_font_size = int(surface_width / 30)
            try:
                hint_font = pygame.font.Font(font_path, hint_font_size)
            except Exception:
                hint_font = pygame.font.Font(None, hint_font_size)

            hint_text = hint_font.render(
                "Press P to resume or ESC/M for settings",
                True,
                Color.from_hex(constants.MESSAGE_COLOR).to_tuple(),
            )
            hint_rect = hint_text.get_rect()
            hint_rect.midtop = (surface_width // 2, pause_rect.bottom + 20)

            # blit hint
            self._renderer.blit(hint_text, hint_rect)

        except Exception:
            # silently fail if rendering fails
            pass

    def draw_settings_overlay(
        self,
        surface_width: int,
        surface_height: int,
        selected_index: int,
    ) -> None:
        """Draw settings overlay with semi-transparent background and settings menu.

        Args:
            surface_width: Width of the surface
            surface_height: Height of the surface
            selected_index: Currently selected setting index
        """
        if not self._settings:
            return

        try:
            # create semi-transparent overlay
            overlay = pygame.Surface((surface_width, surface_height))
            overlay.set_alpha(200)  # more opaque than pause
            overlay.fill(Color.from_hex(constants.ARENA_PRIMARY_COLOR).to_tuple())
            self._renderer.blit(overlay, (0, 0))

            # draw title
            self._draw_settings_title(surface_width, surface_height)

            # draw settings items
            self._draw_settings_items(surface_width, surface_height, selected_index)

            # draw hint footer
            self._draw_settings_hint(surface_width, surface_height)

        except Exception:
            # silently fail if rendering fails
            pass

    def _draw_settings_title(self, surface_width: int, surface_height: int) -> None:
        """Draw settings menu title."""
        font_path = "assets/font/GetVoIP-Grotesque.ttf"
        title_font_size = int(surface_width / 12)
        try:
            title_font = pygame.font.Font(font_path, title_font_size)
        except Exception:
            title_font = pygame.font.Font(None, title_font_size)

        title_text = title_font.render(
            "Settings", True, Color.from_hex(constants.MESSAGE_COLOR).to_tuple()
        )
        title_rect = title_text.get_rect(
            center=(surface_width / 2, surface_height / 10)
        )
        self._renderer.blit(title_text, title_rect)

    def _draw_settings_items(
        self, surface_width: int, surface_height: int, selected_index: int
    ) -> None:
        """Draw individual settings items with categorized layout."""
        font_path = "assets/font/GetVoIP-Grotesque.ttf"

        # Layout parameters
        row_h = int(surface_height * 0.055)
        category_h = int(surface_height * 0.07)
        padding_y = int(surface_height * 0.20)
        left_margin = int(surface_width * 0.15)
        category_indent = int(surface_width * 0.05)

        # Calculate scroll offset
        item_height_avg = row_h
        scroll_offset = max(0, (selected_index - 3) * item_height_avg)

        # Get in-game adjustable settings
        menu_fields = self._settings.get_in_game_menu_fields()
        return_to_menu_index = len(menu_fields)

        # Calculate available height for content
        content_start_y = padding_y
        content_end_y = int(surface_height * 0.88)

        # Fonts
        item_font_size = int(surface_width / 32)
        category_font_size = int(surface_width / 32)
        try:
            item_font = pygame.font.Font(font_path, item_font_size)
            category_font = pygame.font.Font(font_path, category_font_size)
        except Exception:
            item_font = pygame.font.Font(None, item_font_size)
            category_font = pygame.font.Font(None, category_font_size)

        current_y = padding_y - scroll_offset
        current_category = None

        # Draw settings grouped by category
        for field_i, f in enumerate(menu_fields):
            # Draw category header if this is a new category
            if f.get("category") != current_category:
                current_category = f.get("category", "Other")

                # Add spacing before category (except first)
                if field_i > 0:
                    current_y += int(surface_height * 0.03)

                # Draw category header only if visible
                if content_start_y - category_h <= current_y <= content_end_y:
                    category_text = category_font.render(
                        f"─── {current_category} ───",
                        True,
                        (180, 180, 180),
                    )
                    category_rect = category_text.get_rect()
                    category_rect.left = left_margin - category_indent
                    category_rect.top = current_y
                    self._renderer.blit(category_text, category_rect)

                current_y += category_h

            # Draw setting field only if visible
            if content_start_y - row_h <= current_y <= content_end_y:
                val = self._settings.get(f["key"])

                # Calculate current grid size for display
                current_grid_size = 20
                if self._config:
                    desired_cells = max(10, int(self._settings.get("cells_per_side")))
                    current_grid_size = self._config.get_optimal_grid_size(
                        desired_cells
                    )

                formatted_val = self._settings.format_setting_value(
                    f,
                    val,
                    surface_width,
                    current_grid_size,
                )

                # Highlight selected item
                text_color = (
                    Color.from_hex(constants.SCORE_COLOR).to_tuple()
                    if field_i == selected_index
                    else Color.from_hex(constants.MESSAGE_COLOR).to_tuple()
                )
                text = item_font.render(
                    f"{f['label']}: {formatted_val}", True, text_color
                )
                rect = text.get_rect()
                rect.left = left_margin
                rect.top = current_y
                self._renderer.blit(text, rect)

            current_y += row_h

        # Draw "Return to Menu" option
        current_y += int(surface_height * 0.04)

        # Only draw if visible
        if content_start_y - row_h <= current_y <= content_end_y:
            text_color = (
                Color.from_hex(constants.SCORE_COLOR).to_tuple()
                if selected_index == return_to_menu_index
                else (200, 100, 100)
            )
            return_text = item_font.render(
                "──  Return to Main Menu  ──", True, text_color
            )
            rect = return_text.get_rect()
            rect.left = left_margin - category_indent
            rect.top = current_y
            self._renderer.blit(return_text, rect)

    def _draw_settings_hint(self, surface_width: int, surface_height: int) -> None:
        """Draw settings menu hint footer."""
        font_path = "assets/font/GetVoIP-Grotesque.ttf"
        hint_text = "[A/D] change   [W/S] navigate   [Enter] select   [Esc] back   [C] random colors"
        hint_font_size = int(surface_width / 50)
        try:
            hint_font = pygame.font.Font(font_path, hint_font_size)
        except Exception:
            hint_font = pygame.font.Font(None, hint_font_size)

        hint_surf = hint_font.render(
            hint_text, True, Color.from_hex(constants.GRID_COLOR).to_tuple()
        )
        hint_rect = hint_surf.get_rect(
            center=(surface_width / 2, surface_height * 0.95)
        )
        self._renderer.blit(hint_surf, hint_rect)

    def update(self, world: World) -> None:
        """Update method required by BaseSystem.

        Renders overlays based on game state.
        Note: This system is called manually from GameplayScene,
        not in the regular system update loop.

        Args:
            world: Game world
        """
        pass  # overlays are drawn manually by GameplayScene
