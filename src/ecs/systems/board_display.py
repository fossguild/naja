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

"""BoardRenderSystem - handles rendering of the game board and entities."""

from typing import TYPE_CHECKING

import pygame

from src.ecs.systems.base_system import BaseSystem
from src.ecs.world import World
from src.ecs.board import Tile
from src.core.types.color import Color
from src.core.rendering.pygame_surface_renderer import RenderEnqueue
from src.ecs.components.position import Position
from src.ecs.components.snake_body import SnakeBody
from src.ecs.components.interpolation import Interpolation
from src.ecs.components.palette import Palette

if TYPE_CHECKING:
    pass


class BoardRenderSystem(BaseSystem):
    """System responsible for rendering the game board and entities.

    This system reads the game board state and renders it to the screen.
    It handles ONLY game world rendering (board, tiles, grid) and does NOT
    render UI overlays. UI rendering is handled by StaticUISystem.

    The rendering is designed to be generic - it renders based on tile types
    and colors, so the visual style can be easily changed without modifying
    the rendering logic (e.g., switching from pixel art to sprites).

    This system receives a RenderEnqueue view that only allows queueing draw
    commands, preventing interference with the rendering pipeline.

    Attributes:
        renderer: The RenderEnqueue view to queue draw commands
    """

    def __init__(self, renderer: RenderEnqueue, settings=None):
        """Initialize the BoardRenderSystem.

        Args:
            renderer: RenderEnqueue view to queue draw commands (enqueue-only access)
            settings: Optional GameSettings instance for accessing music state
        """
        self._renderer = renderer
        self._settings = settings

        # TODO: In the future, this color scheme should come from a config
        # or settings system, allowing runtime customization
        self._colors: dict[str, Color] = {
            "arena": Color.from_hex("#202020"),  # Background color
            "grid": Color.from_hex("#3c3c3b"),  # Grid line color
            "snake_head": Color.from_hex("#00aa00"),  # Snake head color
            "snake_body": Color.from_hex("#00ff00"),  # Snake body color
            "apple": Color.from_hex("#aa0000"),  # Apple color
            "obstacle": Color.from_hex("#666666"),  # Obstacle color
        }

    def set_color(self, name: str, color: Color) -> None:
        """Update a color in the color scheme.

        Args:
            name: Color name (e.g., "arena", "snake_head")
            color: New Color instance
        """
        self._colors[name] = color

    def get_color(self, name: str) -> Color:
        """Get a color from the color scheme.

        Args:
            name: Color name

        Returns:
            Color: Color instance
        """
        return self._colors.get(name, Color(255, 255, 255))

    def clear_screen(self) -> None:
        """Clear the screen with the arena background color."""
        self._renderer.fill(self.get_color("arena").to_tuple())

    def draw_grid(self, world: World) -> None:
        """Draw the game grid based on the board dimensions.

        Args:
            world: Game world containing the board
        """
        board = world.board
        cell_size = board.cell_size
        width = board.width * cell_size
        height = board.height * cell_size
        grid_color = self.get_color("grid").to_tuple()

        # Draw vertical lines
        for x in range(0, width, cell_size):
            self._renderer.draw_line(grid_color, (x, 0), (x, height), 1)

        # Draw horizontal lines
        for y in range(0, height, cell_size):
            self._renderer.draw_line(grid_color, (0, y), (width, y), 1)

    def draw_tile(self, x: int, y: int, tile: Tile, cell_size: int) -> None:
        """Draw a single tile at the specified grid position.

        Args:
            x: X coordinate in grid units
            y: Y coordinate in grid units
            tile: Type of tile to draw
            cell_size: Size of grid cell in pixels
        """
        # Calculate pixel position
        pixel_x = x * cell_size
        pixel_y = y * cell_size

        # Map tile type to color
        tile_colors = {
            Tile.EMPTY: None,  # Don't draw empty tiles
            Tile.SNAKE_HEAD: self.get_color("snake_head").to_tuple(),
            Tile.SNAKE_BODY: self.get_color("snake_body").to_tuple(),
            Tile.APPLE: self.get_color("apple").to_tuple(),
            Tile.OBSTACLE: self.get_color("obstacle").to_tuple(),
            Tile.WALL: self.get_color("obstacle").to_tuple(),
        }

        color = tile_colors.get(tile)
        if color is None:
            return  # Skip empty tiles

        # Draw the tile as a filled rectangle
        rect = pygame.Rect(pixel_x, pixel_y, cell_size, cell_size)
        self._renderer.draw_rect(color, rect)

    def draw_board(self, world: World) -> None:
        """Draw all tiles on the board.

        Args:
            world: Game world containing the board
        """
        board = world.board
        cell_size = board.cell_size

        for y in range(board.height):
            for x in range(board.width):
                tile = board.get_tile(x, y)
                self.draw_tile(x, y, tile, cell_size)

    def render_frame(self, world: World) -> None:
        """Render a complete frame.

        This is the main rendering method that orchestrates the full rendering pipeline:
        1. Clear the screen
        2. Draw the grid
        3. Draw all board tiles
        4. Draw ECS entities with components (if available)
        5. Draw UI elements (score, etc.)

        Args:
            world: Game world to render
        """
        self.clear_screen()
        self.draw_grid(world)
        self.draw_board(world)
        self.draw_ecs_entities(world)
        self.draw_ui(world)

    def draw_ecs_entities(self, world: World) -> None:
        """Draw all ECS entities with renderable components.

        This method renders entities based on their components (Position, Renderable,
        Interpolation, SnakeBody, etc.) following the ECS architecture.

        Args:
            world: Game world containing entities and components
        """
        # Import components locally to avoid circular imports
        from src.ecs.entities.entity import EntityType

        # Render all entities based on type
        cell_size = world.board.cell_size

        for entity_id, entity in world.registry.get_all().items():
            if entity is None:
                continue

            # Check entity type and render accordingly
            entity_type = entity.get_type()

            if entity_type == EntityType.SNAKE:
                position = getattr(entity, "position", None)
                body = getattr(entity, "body", None)
                interpolation = getattr(entity, "interpolation", None)
                palette = getattr(entity, "palette", None)

                if position and body and interpolation:
                    self.draw_snake(world, position, body, interpolation, palette)

            elif entity_type == EntityType.APPLE:
                position = getattr(entity, "position", None)
                if position:
                    # draw apple as red square
                    pixel_x = position.x * cell_size
                    pixel_y = position.y * cell_size
                    apple_rect = pygame.Rect(pixel_x, pixel_y, cell_size, cell_size)
                    apple_color = self.get_color("apple").to_tuple()
                    self._renderer.draw_rect(apple_color, apple_rect, 0)

            elif entity_type == EntityType.OBSTACLE:
                position = getattr(entity, "position", None)
                if position:
                    # draw obstacle as gray square
                    pixel_x = position.x * cell_size
                    pixel_y = position.y * cell_size
                    obstacle_rect = pygame.Rect(pixel_x, pixel_y, cell_size, cell_size)
                    obstacle_color = self.get_color("obstacle").to_tuple()
                    self._renderer.draw_rect(obstacle_color, obstacle_rect, 0)

    def draw_snake(
        self,
        world: World,
        position: Position,
        body: "SnakeBody",
        interpolation: "Interpolation",
        palette: "Palette" = None,
    ) -> None:
        """Draw the snake with smooth interpolation.

        Args:
            world: Game world
            position: Head position component
            body: Snake body component
            interpolation: Interpolation component for smooth movement
            palette: Optional palette component for custom colors
        """
        if not body.alive:
            return

        cell_size = world.board.cell_size
        grid_width = world.board.width * cell_size
        grid_height = world.board.height * cell_size

        # Get colors from palette component or use defaults
        if palette:
            head_color = palette.primary_color
            tail_color = palette.secondary_color
        else:
            head_color = self.get_color("snake_head").to_tuple()
            tail_color = self.get_color("snake_body").to_tuple()

        # Draw tail segments with interpolation
        self._draw_snake_tail(
            body,
            interpolation,
            position,
            cell_size,
            grid_width,
            grid_height,
            tail_color,
        )

        # Draw head with interpolation
        self._draw_snake_head(
            position, interpolation, cell_size, grid_width, grid_height, head_color
        )

    def _draw_snake_head(
        self,
        position: Position,
        interpolation: "Interpolation",
        cell_size: int,
        grid_width: int,
        grid_height: int,
        color: tuple,
    ) -> None:
        """Draw the snake head with smooth interpolation.

        Args:
            position: Head position component
            interpolation: Interpolation component
            cell_size: Size of grid cells
            grid_width: Total grid width in pixels
            grid_height: Total grid height in pixels
            color: Head color as (r, g, b) tuple
        """
        # calculate smooth interpolated position between prev and current
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

        # Draw head rectangle at interpolated position
        rect = pygame.Rect(int(draw_x), int(draw_y), cell_size, cell_size)
        self._renderer.draw_rect(color, rect, 0)

    def _draw_snake_tail(
        self,
        body: "SnakeBody",
        interpolation: "Interpolation",
        head_position: Position,
        cell_size: int,
        grid_width: int,
        grid_height: int,
        color: tuple,
    ) -> None:
        """Draw the snake tail with smooth interpolation.

        Args:
            body: Snake body component
            interpolation: Interpolation component
            head_position: Current head position
            cell_size: Size of grid cells
            grid_width: Total grid width in pixels
            grid_height: Total grid height in pixels
            color: Tail color as (r, g, b) tuple
        """

        if not body.segments:
            return

        # draw each tail segment with interpolation
        # this creates smooth movement and natural overlap when turning
        for segment in body.segments:
            # calculate interpolated position for each segment
            draw_x, draw_y = self._calculate_interpolated_position(
                segment.x * cell_size,
                segment.y * cell_size,
                segment.prev_x * cell_size,
                segment.prev_y * cell_size,
                interpolation.alpha,
                interpolation.wrapped_axis,
                cell_size,
                grid_width,
                grid_height,
            )

            segment_rect = pygame.Rect(
                int(draw_x),
                int(draw_y),
                cell_size,
                cell_size,
            )
            self._renderer.draw_rect(color, segment_rect, 0)

    def _calculate_interpolated_position(
        self,
        current_x: int,
        current_y: int,
        prev_x: int,
        prev_y: int,
        alpha: float,
        wrapped_axis: str,
        cell_size: int,
        grid_width: int,
        grid_height: int,
    ) -> tuple[float, float]:
        """Calculate interpolated position with edge wrapping support.

        Args:
            current_x: Current x position
            current_y: Current y position
            prev_x: Previous x position
            prev_y: Previous y position
            alpha: Interpolation factor [0.0, 1.0]
            wrapped_axis: Which axis wrapped ("none", "x", "y", "both")
            cell_size: Size of grid cells
            grid_width: Total grid width in pixels
            grid_height: Total grid height in pixels

        Returns:
            Tuple of (interpolated_x, interpolated_y)
        """
        draw_x = prev_x + (current_x - prev_x) * alpha
        draw_y = prev_y + (current_y - prev_y) * alpha

        # Handle wrapping on x-axis
        if wrapped_axis in ("x", "both"):
            # Check if there's a significant jump indicating wrap
            if abs(current_x - prev_x) > grid_width / 2:
                # Determine wrap direction
                if current_x < prev_x:
                    # Wrapped from right edge to left edge
                    draw_x = prev_x + alpha * cell_size
                else:
                    # Wrapped from left edge to right edge
                    draw_x = prev_x - alpha * cell_size

        # Handle wrapping on y-axis
        if wrapped_axis in ("y", "both"):
            # Check if there's a significant jump indicating wrap
            if abs(current_y - prev_y) > grid_height / 2:
                # Determine wrap direction
                if current_y < prev_y:
                    # Wrapped from bottom edge to top edge
                    draw_y = prev_y + alpha * cell_size
                else:
                    # Wrapped from top edge to bottom edge
                    draw_y = prev_y - alpha * cell_size

        # Wrap coordinates to stay within grid bounds
        draw_x = draw_x % grid_width
        draw_y = draw_y % grid_height

        return (draw_x, draw_y)

    def draw_ui(self, world: World) -> None:
        """Draw UI elements like score.

        Args:
            world: Game world
        """
        # TODO: implement score rendering using assets
        # For now, skip UI rendering
        pass

    def draw_pause_overlay(self, surface_width: int, surface_height: int) -> None:
        """Draw pause screen overlay.

        Args:
            surface_width: Width of the surface
            surface_height: Height of the surface
        """
        # create semi-transparent overlay
        overlay_surface = pygame.Surface(
            (surface_width, surface_height), pygame.SRCALPHA
        )
        overlay_surface.fill((32, 32, 32, 180))  # dark gray, semi-transparent

        # blit overlay to main surface
        self._renderer.blit(overlay_surface, (0, 0))

        # add pause text (exactly like old code)
        try:
            # get surface dimensions for font sizing (like old code)
            surface_width, surface_height = surface_width, surface_height

            # calculate font sizes (same as old code)
            big_font_size = int(surface_width / 8)
            small_font_size = int(surface_width / 20)

            # create fonts with same font file and sizing as old code
            # old code: FONT_PATH = "assets/font/GetVoIP-Grotesque.ttf"
            font_path = "assets/font/GetVoIP-Grotesque.ttf"

            try:
                # try to load the same font as old code
                big_font = pygame.font.Font(font_path, big_font_size)
                small_font = pygame.font.Font(font_path, small_font_size)
            except Exception:
                # fallback to default font if GetVoIP font not found
                big_font = pygame.font.Font(None, big_font_size)
                small_font = pygame.font.Font(None, small_font_size)

            # MESSAGE_COLOR from old code: "#808080" (gray)
            message_color = (128, 128, 128)  # #808080

            # "Paused" text centered (exactly like old code)
            paused_text = big_font.render("Paused", True, message_color)
            paused_rect = paused_text.get_rect(
                center=(surface_width // 2, surface_height // 2)
            )

            # "Press P to continue" text below (exactly like old code)
            continue_text = small_font.render(
                "Press P to continue", True, message_color
            )
            continue_rect = continue_text.get_rect(
                center=(surface_width // 2, surface_height * 2 // 3)
            )

            # blit text to main surface
            self._renderer.blit(paused_text, paused_rect)
            self._renderer.blit(continue_text, continue_rect)

        except Exception:
            # if font loading fails, just show overlay
            pass

    def draw_score(self, world: World, surface_width: int, surface_height: int) -> None:
        """Draw score counter horizontally centered near the top, semi-transparent.

        Matches the old style: big number, centered on X, high on Y with a margin,
        using the same font as Game Over and low opacity so the grid is visible through it.

        Args:
            world: Game world to query snake size
            surface_width: Width of the surface
            surface_height: Height of the surface
        """
        # Query score component from world
        score_entities = world.registry.query_by_component("score")
        if not score_entities:
            return

        # Get first score entity (should only be one)
        score_entity = list(score_entities.values())[0]
        if not hasattr(score_entity, "score"):
            return

        current_score = score_entity.score.current

        try:
            # Large font size, like Game Over
            font_size = int(surface_width / 8)
            font_path = "assets/font/GetVoIP-Grotesque.ttf"

            try:
                score_font = pygame.font.Font(font_path, font_size)
            except Exception:
                score_font = pygame.font.Font(None, font_size)

            # Use the same tone as Game Over (MESSAGE_COLOR #808080)
            score_color = (128, 128, 128)

            # Render score text
            score_text = score_font.render(str(current_score), True, score_color)

            # Make it more translucent than before (~25% opaque)
            score_text.set_alpha(64)

            # Horizontal center; vertically near the top with a grid-sized margin
            top_margin = getattr(world.board, "cell_size", max(10, surface_height // 20))
            score_rect = score_text.get_rect()
            score_rect.midtop = (surface_width // 2, top_margin)

            # Blit to main surface
            self._renderer.blit(score_text, score_rect)

        except Exception:
            # Silently fail if font loading or rendering fails
            pass

    def draw_music_indicator(
        self, surface_width: int, surface_height: int, music_on: bool
    ) -> None:
        """Draw music status indicator in the bottom-right corner.

        Shows speaker icon (on/muted) with [N] hint text below it.
        Styled exactly like the old code.

        Args:
            surface_width: Width of the surface
            surface_height: Height of the surface
            music_on: Whether background music is currently enabled
        """
        try:
            # Define dimensions using proportional padding (same as old code)
            padding_x = int(surface_width * 0.02)
            padding_y = int(surface_height * 0.02)
            icon_size = int(surface_width / 25)
            gap = 4  # Small pixel gap between icon and text

            # Load speaker sprites
            try:
                if music_on:
                    sprite = pygame.image.load("assets/sprites/speaker-on.png")
                else:
                    sprite = pygame.image.load("assets/sprites/speaker-muted.png")
            except Exception:
                sprite = None

            # Render hint text
            # SCORE_COLOR from constants: "#ffffff" (white)
            # GRID_COLOR from constants: "#3c3c3b" (dark gray)
            hint_color = (255, 255, 255) if music_on else (60, 60, 59)  # SCORE_COLOR or GRID_COLOR
            hint_text = "[N]"
            hint_font_size = int(surface_width / 50)
            font_path = "assets/font/GetVoIP-Grotesque.ttf"

            try:
                hint_font = pygame.font.Font(font_path, hint_font_size)
            except Exception:
                hint_font = pygame.font.Font(None, hint_font_size)

            hint_surf = hint_font.render(hint_text, True, hint_color)
            hint_rect = hint_surf.get_rect()

            # Calculate total widget height
            total_widget_height = icon_size + gap + hint_rect.height

            # Calculate positions (bottom-right corner)
            icon_x = surface_width - padding_x - icon_size
            icon_y = surface_height - padding_y - total_widget_height

            # Scale and draw sprite
            if sprite is not None:
                scaled_sprite = pygame.transform.scale(sprite, (icon_size, icon_size))
                self._renderer.blit(scaled_sprite, (icon_x, icon_y))

            # Position and draw text hint below the icon
            hint_rect.centerx = icon_x + icon_size // 2
            hint_rect.top = icon_y + icon_size + gap
            self._renderer.blit(hint_surf, hint_rect)

        except Exception:
            # Silently fail if sprite loading or rendering fails
            pass

    def update(self, world: World) -> None:
        """Update method required by BaseSystem.

        Renders the game world (board, tiles, grid) to the surface.
        Does NOT update the display - that's handled by StaticUISystem.

        Args:
            world: Game world to render
        """
        # check if game is over - don't render game world if dead
        from src.ecs.entities.entity import EntityType

        snakes = world.registry.query_by_type(EntityType.SNAKE)
        game_over = False
        for _, snake in snakes.items():
            if hasattr(snake, "body") and not snake.body.alive:
                game_over = True
                break

        # if game is over, render arena background (like old code)
        if game_over:
            # ARENA_COLOR from old code: "#202020" (dark gray)
            arena_color = (32, 32, 32)  # #202020
            self._renderer.fill(arena_color)
            return

        # render normal game world
        self.render_frame(world)

        # Draw score counter on top of game world
        surface = pygame.display.get_surface()
        if surface:
            self.draw_score(world, surface.get_width(), surface.get_height())
            
            # Draw music indicator in bottom-right corner
            if self._settings:
                music_on = self._settings.get("background_music")
                self.draw_music_indicator(
                    surface.get_width(), surface.get_height(), music_on
                )
        
        # (draw_score already called once; avoid duplicate rendering)
