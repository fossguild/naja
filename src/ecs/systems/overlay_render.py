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
    - Render Lights Out mode darkness overlay with vision circles

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
            cell_size = getattr(world.board, "cell_size", 16)
            board_px_w = getattr(world.board, "width", 0) * cell_size
            board_px_h = getattr(world.board, "height", 0) * cell_size
            offset_x, offset_y = self._get_board_offset()

            # If board has zero size, fall back to full-surface overlay
            if board_px_w <= 0 or board_px_h <= 0:
                overlay = pygame.Surface(
                    (surface_width, surface_height), pygame.SRCALPHA
                )
                overlay.fill((0, 0, 0, 255))
                self._renderer.blit(overlay, (0, 0))
                return
            # Create overlay for board area only
            overlay = pygame.Surface((board_px_w, board_px_h), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 255))

            # Get snake head position directly from world
            snakes = world.registry.query_by_type_and_components(
                EntityType.SNAKE, "position", "interpolation"
            )
            if not snakes:
                snakes = world.registry.query_by_type_and_components(
                    EntityType.SNAKE, "position"
                )
            if not snakes:
                self._renderer.blit(overlay, (offset_x, offset_y))
                return

            snake = next(iter(snakes.values()))
            position = getattr(snake, "position", None)
            interpolation = getattr(snake, "interpolation", None)
            if not position:
                self._renderer.blit(overlay, (offset_x, offset_y))
                return

            # Calculate vision center in overlay coordinates
            cx = position.x * cell_size + cell_size / 2
            cy = position.y * cell_size + cell_size / 2

            # Apply smooth interpolation if available
            if interpolation:
                prev_cx = position.prev_x * cell_size + cell_size / 2
                prev_cy = position.prev_y * cell_size + cell_size / 2
                # Handle wrapping interpolation
                if interpolation.wrapped_axis in ("x", "both"):
                    # Wrapping on X - interpolate in the direction of movement
                    if abs(cx - prev_cx) > board_px_w / 2:
                        if cx < prev_cx:
                            cx += board_px_w
                        else:
                            prev_cx += board_px_w
                if interpolation.wrapped_axis in ("y", "both"):
                    # Wrapping on Y - interpolate in the direction of movement
                    if abs(cy - prev_cy) > board_px_h / 2:
                        if cy < prev_cy:
                            cy += board_px_h
                        else:
                            prev_cy += board_px_h
                # Linear interpolation
                cx = prev_cx + (cx - prev_cx) * interpolation.alpha
                cy = prev_cy + (cy - prev_cy) * interpolation.alpha
                # Wrap back to board bounds
                cx = cx % board_px_w
                cy = cy % board_px_h
            radius_px = max(8, int(lights_out_state.radius * cell_size))

            # Check if electric walls are enabled
            electric_walls = (
                self._settings.get("electric_walls") if self._settings else True
            )

            # Draw vision circles
            self._draw_vision_circle(
                overlay, cx, cy, radius_px, board_px_w, board_px_h, electric_walls
            )

            # Reveal apples
            self._draw_apple_glows(
                world,
                overlay,
                cx,
                cy,
                radius_px,
                cell_size,
                board_px_w,
                board_px_h,
                electric_walls,
            )

            # Blit overlay at board offset
            self._renderer.blit(overlay, (offset_x, offset_y))

        except Exception:
            pass

    def _draw_vision_circle(
        self, overlay, cx, cy, radius_px, board_w, board_h, electric_walls
    ):
        """Draw vision circle(s) at the given center, handling wrapping if needed."""
        # Always draw at primary position
        pygame.draw.circle(overlay, (0, 0, 0, 0), (int(cx), int(cy)), radius_px)
        # If walls wrap, draw at wrapped positions when near edges
        if not electric_walls:
            # Draw wrapped circles for seamless edge wrapping
            if cx - radius_px < 0:  # Near left
                pygame.draw.circle(
                    overlay, (0, 0, 0, 0), (int(cx + board_w), int(cy)), radius_px
                )
            if cx + radius_px > board_w:  # Near right
                pygame.draw.circle(
                    overlay, (0, 0, 0, 0), (int(cx - board_w), int(cy)), radius_px
                )
            if cy - radius_px < 0:  # Near top
                pygame.draw.circle(
                    overlay, (0, 0, 0, 0), (int(cx), int(cy + board_h)), radius_px
                )
            if cy + radius_px > board_h:  # Near bottom
                pygame.draw.circle(
                    overlay, (0, 0, 0, 0), (int(cx), int(cy - board_h)), radius_px
                )

            # Corner cases
            if cx - radius_px < 0 and cy - radius_px < 0:
                pygame.draw.circle(
                    overlay,
                    (0, 0, 0, 0),
                    (int(cx + board_w), int(cy + board_h)),
                    radius_px,
                )
            if cx + radius_px > board_w and cy - radius_px < 0:
                pygame.draw.circle(
                    overlay,
                    (0, 0, 0, 0),
                    (int(cx - board_w), int(cy + board_h)),
                    radius_px,
                )
            if cx - radius_px < 0 and cy + radius_px > board_h:
                pygame.draw.circle(
                    overlay,
                    (0, 0, 0, 0),
                    (int(cx + board_w), int(cy - board_h)),
                    radius_px,
                )
            if cx + radius_px > board_w and cy + radius_px > board_h:
                pygame.draw.circle(
                    overlay,
                    (0, 0, 0, 0),
                    (int(cx - board_w), int(cy - board_h)),
                    radius_px,
                )

    def _draw_apple_glows(
        self,
        world,
        overlay,
        cx,
        cy,
        radius_px,
        cell_size,
        board_w,
        board_h,
        electric_walls,
    ):
        """Draw apple glows when they're visible in the vision radius."""
        try:
            apple_radius_px = max(4, int(1.5 * cell_size))
            apples = world.registry.query_by_type(EntityType.APPLE)
            for _, apple in apples.items():
                pos = getattr(apple, "position", None)
                if not pos:
                    continue
                ax = pos.x * cell_size + cell_size / 2
                ay = pos.y * cell_size + cell_size / 2
                # Check if apple is visible from any vision position
                vision_positions = [(cx, cy)]
                if not electric_walls:
                    if cx - radius_px < 0:
                        vision_positions.append((cx + board_w, cy))
                    if cx + radius_px > board_w:
                        vision_positions.append((cx - board_w, cy))
                    if cy - radius_px < 0:
                        vision_positions.append((cx, cy + board_h))
                    if cy + radius_px > board_h:
                        vision_positions.append((cx, cy - board_h))
                    if cx - radius_px < 0 and cy - radius_px < 0:
                        vision_positions.append((cx + board_w, cy + board_h))
                    if cx + radius_px > board_w and cy - radius_px < 0:
                        vision_positions.append((cx - board_w, cy + board_h))
                    if cx - radius_px < 0 and cy + radius_px > board_h:
                        vision_positions.append((cx + board_w, cy - board_h))
                    if cx + radius_px > board_w and cy + radius_px > board_h:
                        vision_positions.append((cx - board_w, cy - board_h))

                for vx, vy in vision_positions:
                    dx = ax - vx
                    dy = ay - vy
                    if dx * dx + dy * dy <= (radius_px + apple_radius_px) ** 2:
                        pygame.draw.circle(
                            overlay, (0, 0, 0, 0), (int(ax), int(ay)), apple_radius_px
                        )
                        break
        except Exception:
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
                            5, int(self._settings.get("cells_per_side"))
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
