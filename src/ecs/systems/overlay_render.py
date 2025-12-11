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
from ecs.entities.entity import EntityType
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
        # track which sections are collapsed
        self._collapsed_sections = set()
        # initialize collapsed sections from field definitions (only once)
        if self._settings:
            for field in self._settings.MENU_FIELDS:
                if field.get("type") == "section" and field.get("collapsed", False):
                    self._collapsed_sections.add(field["key"])

    def _get_visible_fields(self, all_fields: list) -> list:
        """Get only the fields that should be visible based on section collapse state.

        Returns:
            List of visible fields
        """
        visible = []
        for field in all_fields:
            # section headers are always visible
            if field.get("type") == "section":
                visible.append(field)
            # regular fields are visible if they don't have a parent section,
            # or if their parent section is not collapsed
            else:
                parent = field.get("parent_section")
                if not parent or parent not in self._collapsed_sections:
                    visible.append(field)
        return visible

    def toggle_section(self, section_key: str) -> None:
        """Toggle a section's collapsed state.

        Args:
            section_key: Key of the section to toggle
        """
        if section_key in self._collapsed_sections:
            self._collapsed_sections.remove(section_key)
        else:
            self._collapsed_sections.add(section_key)

    def _get_lights_out_state(self, world: World):
        entities = world.registry.query_by_component("lights_out_state")
        if not entities:
            return None
        entity = next(iter(entities.values()))
        return getattr(entity, "lights_out_state", None)

    def _get_game_state(self, world: World):
        entities = world.registry.query_by_component("game_state")
        if not entities:
            return None
        entity = next(iter(entities.values()))
        return getattr(entity, "game_state", None)

    def _get_board_offset(self) -> tuple[int, int]:
        """Match the board offset used by render systems."""
        surface = pygame.display.get_surface()
        if not surface:
            return (0, 0)
        return (0, 45)

    def _calculate_interpolated_position(
        self,
        current_x: float,
        current_y: float,
        prev_x: float,
        prev_y: float,
        alpha: float,
        wrapped_axis: str,
        cell_size: int,
        grid_width: int,
        grid_height: int,
    ) -> tuple[float, float]:
        """Interpolate between previous and current positions handling wraparound."""
        # Adjust for wraparound so interpolation follows the shorter path
        if wrapped_axis in ("x", "both"):
            if current_x < prev_x:
                current_x += grid_width
            else:
                prev_x += grid_width

        if wrapped_axis in ("y", "both"):
            if current_y < prev_y:
                current_y += grid_height
            else:
                prev_y += grid_height

        interp_x = prev_x + (current_x - prev_x) * alpha
        interp_y = prev_y + (current_y - prev_y) * alpha

        # Wrap back into the grid range
        interp_x %= grid_width
        interp_y %= grid_height

        return interp_x, interp_y

    def _get_snake_head_screen_position(self, world: World):
        snakes = world.registry.query_by_type_and_components(
            EntityType.SNAKE, "position", "interpolation"
        )
        if not snakes:
            snakes = world.registry.query_by_component("position", "interpolation")
        if not snakes:
            return None

        snake = next(iter(snakes.values()))
        position = getattr(snake, "position", None)
        interpolation = getattr(snake, "interpolation", None)
        if not position:
            return None

        cell_size = getattr(world.board, "cell_size", 20)
        grid_width = getattr(world.board, "width", 0) * cell_size
        grid_height = getattr(world.board, "height", 0) * cell_size

        draw_x = position.x * cell_size
        draw_y = position.y * cell_size

        if interpolation:
            draw_x, draw_y = self._calculate_interpolated_position(
                position.x * cell_size,
                position.y * cell_size,
                position.prev_x * cell_size,
                position.prev_y * cell_size,
                interpolation.alpha,
                interpolation.wrapped_axis,
                cell_size,
                grid_width,
                grid_height,
            )

        offset_x, offset_y = self._get_board_offset()
        return (
            int(draw_x + offset_x + cell_size / 2),
            int(draw_y + offset_y + cell_size / 2),
        )

    # Timer-based UI removed: Lights Out is always-on in this build.

    def draw_lights_out_overlay(self, world: World) -> None:
        """Render blackout mask for Lights Out mode (always-on).

        The mode is always-on in this build; no countdown/timers are displayed.
        """
        try:
            game_state = self._get_game_state(world)
            lights_out_state = self._get_lights_out_state(world)

            if (
                not game_state
                or not lights_out_state
                or not game_state.lights_out_enabled
            ):
                return

            surface = pygame.display.get_surface()
            if not surface:
                return

            surface_width, surface_height = surface.get_size()

            if not game_state.lights_out_active:
                return

            overlay = pygame.Surface((surface_width, surface_height), pygame.SRCALPHA)
            # Pure black outside illuminated areas (user requested fully black)
            overlay.fill((0, 0, 0, 255))

            center = self._get_snake_head_screen_position(world)
            radius_px = max(
                8,
                int(lights_out_state.radius * getattr(world.board, "cell_size", 16)),
            )

            if center:
                # carve a hole around the snake head
                pygame.draw.circle(overlay, (0, 0, 0, 0), center, radius_px)

            # Reveal apples only when their glow overlaps the snake's vision.
            try:
                from ecs.entities.entity import EntityType

                cell_size = getattr(world.board, "cell_size", 16)
                # Apple glow radius: 2 cells
                apple_radius_px = max(4, int(2 * cell_size))
                apples = world.registry.query_by_type(EntityType.APPLE)
                offset_x, offset_y = self._get_board_offset()
                for _, apple in apples.items():
                    pos = getattr(apple, "position", None)
                    if not pos:
                        continue
                    ax = int(pos.x * cell_size + offset_x + cell_size / 2)
                    ay = int(pos.y * cell_size + offset_y + cell_size / 2)
                    # Only carve apple hole if apple glow intersects snake vision
                    if center:
                        dx = ax - center[0]
                        dy = ay - center[1]
                        if dx * dx + dy * dy <= (radius_px + apple_radius_px) ** 2:
                            pygame.draw.circle(overlay, (0, 0, 0, 0), (ax, ay), apple_radius_px)
            except Exception:
                pass

            self._renderer.blit(overlay, (0, 0))

        except Exception:
            # Avoid breaking rendering if anything goes wrong
            pass

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
                Color.from_hex(constants.MESSAGE_COLOR_LIGHT).to_tuple(),
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
            "Settings", True, Color.from_hex(constants.MESSAGE_COLOR_LIGHT).to_tuple()
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
        # get visible fields (respecting section collapse state)
        visible_fields = self._get_visible_fields(menu_fields)
        return_to_menu_index = len(visible_fields)

        # Calculate available height for content
        content_start_y = padding_y
        content_end_y = int(surface_height * 0.88)

        # Fonts
        item_font_size = int(surface_width / 32)
        category_font_size = int(surface_width / 32)
        section_font_size = int(surface_width / 28)
        try:
            item_font = pygame.font.Font(font_path, item_font_size)
            category_font = pygame.font.Font(font_path, category_font_size)
            section_font = pygame.font.Font(font_path, section_font_size)
        except Exception:
            item_font = pygame.font.Font(None, item_font_size)
            category_font = pygame.font.Font(None, category_font_size)
            section_font = pygame.font.Font(None, section_font_size)

        current_y = padding_y - scroll_offset
        current_category = None

        # Draw settings grouped by category
        for field_i, f in enumerate(visible_fields):
            # skip category headers for section headers and their children
            is_section_child = f.get("parent_section") is not None
            is_section = f.get("type") == "section"

            # Draw category header if this is a new category (but not for sections or section children)
            if (
                not is_section
                and not is_section_child
                and f.get("category") != current_category
            ):
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
                # handle section headers specially
                if f.get("type") == "section":
                    # section headers get a collapse indicator
                    is_expanded = f["key"] not in self._collapsed_sections
                    indicator = "v" if is_expanded else ">"
                    label_text = f"{indicator} {f['label']}"

                    # make section headers slightly larger
                    text_color = (
                        Color.from_hex(constants.SCORE_COLOR).to_tuple()
                        if field_i == selected_index
                        else Color.from_hex(constants.MESSAGE_COLOR_LIGHT).to_tuple()
                    )
                    text = section_font.render(label_text, True, text_color)
                    rect = text.get_rect()
                    rect.left = left_margin - category_indent
                    rect.top = current_y
                    self._renderer.blit(text, rect)
                else:
                    # regular fields
                    val = self._settings.get(f["key"])

                    # Calculate current grid size for display
                    current_grid_size = 20
                    if self._config:
                        desired_cells = max(
                            10, int(self._settings.get("cells_per_side"))
                        )
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
                        else Color.from_hex(constants.MESSAGE_COLOR_LIGHT).to_tuple()
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

        # Seizure warning for rainbow color in AutoPlay mode
        if self._settings:
            from game.game_modes_registry import AUTOPLAY_MODE_NAME

            is_autoplay = self._settings.get_game_mode() == AUTOPLAY_MODE_NAME
            is_rainbow = (
                "rainbow" in str(self._settings.get("snake_color_palette")).lower()
            )
            if is_autoplay and is_rainbow:
                warning_font_size = int(surface_width / 45)
                try:
                    warning_font = pygame.font.Font(font_path, warning_font_size)
                except Exception:
                    warning_font = pygame.font.Font(None, warning_font_size)

                warning_text = "[!] SEIZURE WARNING: Rainbow colors + high speed may cause discomfort"
                warning_surf = warning_font.render(warning_text, True, (255, 100, 100))
                warning_rect = warning_surf.get_rect(
                    center=(surface_width / 2, surface_height * 0.88)
                )
                # Draw background
                bg_rect = warning_rect.inflate(20, 8)
                self._renderer.draw_rect((40, 20, 20), bg_rect)
                self._renderer.blit(warning_surf, warning_rect)

        hint_text = "[A/D] change   [W/S] navigate   [Enter] select   [Esc] back   [C] random colors"
        hint_font_size = int(surface_width / 50)
        try:
            hint_font = pygame.font.Font(font_path, hint_font_size)
        except Exception:
            hint_font = pygame.font.Font(None, hint_font_size)

        hint_surf = hint_font.render(
            hint_text, True, Color.from_hex(constants.MESSAGE_COLOR_LIGHT).to_tuple()
        )
        hint_rect = hint_surf.get_rect(
            center=(surface_width / 2, surface_height * 0.95)
        )
        self._renderer.blit(hint_surf, hint_rect)

    def update(self, world: World) -> None:
        """Update method required by BaseSystem.

        Renders the Lights Out overlay based on game state. Pause/settings
        overlays are still drawn explicitly by GameplayScene.

        Args:
            world: Game world
        """
        self.draw_lights_out_overlay(world)
