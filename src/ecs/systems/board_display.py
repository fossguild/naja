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

if TYPE_CHECKING:
    from src.ecs.components.position import Position
    from src.ecs.components.snake_body import SnakeBody
    from src.ecs.components.interpolation import Interpolation
    from src.ecs.components.palette import Palette


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

    def __init__(self, renderer: RenderEnqueue):
        """Initialize the BoardRenderSystem.

        Args:
            renderer: RenderEnqueue view to queue draw commands (enqueue-only access)
        """
        self._renderer = renderer

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

        Args:
            world: Game world to render
        """
        self.clear_screen()
        self.draw_grid(world)
        self.draw_board(world)
        self.draw_ecs_entities(world)

    def draw_ecs_entities(self, world: World) -> None:
        """Draw all ECS entities with renderable components.

        This method renders entities based on their components (Position, Renderable,
        Interpolation, SnakeBody, etc.) following the ECS architecture.

        Args:
            world: Game world containing entities and components
        """
        # Import components locally to avoid circular imports
        from src.ecs.entities.entity import EntityType

        # Render snakes with interpolation
        for entity_id in world.registry.get_entities():
            entity = world.registry.get_entity(entity_id)
            if entity is None:
                continue

            # Check if this is a snake entity
            if entity.get_type() == EntityType.SNAKE:
                position = getattr(entity, "position", None)
                body = getattr(entity, "body", None)
                interpolation = getattr(entity, "interpolation", None)
                palette = getattr(entity, "palette", None)

                if position and body and interpolation:
                    self.draw_snake(world, position, body, interpolation, palette)

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
        # Calculate interpolated position
        draw_x, draw_y = self._calculate_interpolated_position(
            position.x,
            position.y,
            position.prev_x,
            position.prev_y,
            interpolation.alpha,
            interpolation.wrapped_axis,
            cell_size,
            grid_width,
            grid_height,
        )

        # Draw head rectangle
        rect = pygame.Rect(round(draw_x), round(draw_y), cell_size, cell_size)
        self._renderer.draw_rect(color, rect)

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

        alpha = interpolation.alpha

        # Draw each tail segment with interpolation
        for i, segment in enumerate(body.segments):
            # Determine the previous position for this segment
            if i == 0:
                # First segment follows the head
                prev_pos = head_position
            else:
                # Subsequent segments follow the previous segment
                prev_pos = body.segments[i - 1]

            # Calculate interpolated position for this segment
            # When alpha > 0, the segment is moving from prev_pos toward segment
            # When alpha = 0, the segment is at its exact grid position
            draw_x = segment.x + (prev_pos.x - segment.x) * alpha
            draw_y = segment.y + (prev_pos.y - segment.y) * alpha

            # Handle wrapping for this segment if needed
            if interpolation.wrapped_axis in ("x", "both"):
                # Check if there's a wrap between prev_pos and segment
                if abs(prev_pos.x - segment.x) > grid_width / 2:
                    # Wrapped! Adjust interpolation
                    if prev_pos.x < segment.x:
                        # Wrapped from right to left
                        draw_x = prev_pos.x + alpha * cell_size
                    else:
                        # Wrapped from left to right
                        draw_x = prev_pos.x - alpha * cell_size

            if interpolation.wrapped_axis in ("y", "both"):
                # Check if there's a wrap between prev_pos and segment
                if abs(prev_pos.y - segment.y) > grid_height / 2:
                    # Wrapped! Adjust interpolation
                    if prev_pos.y < segment.y:
                        # Wrapped from bottom to top
                        draw_y = prev_pos.y + alpha * cell_size
                    else:
                        # Wrapped from top to bottom
                        draw_y = prev_pos.y - alpha * cell_size

            # Wrap coordinates to grid bounds
            draw_x = draw_x % grid_width
            draw_y = draw_y % grid_height

            # Draw segment rectangle
            rect = pygame.Rect(round(draw_x), round(draw_y), cell_size, cell_size)
            self._renderer.draw_rect(color, rect)

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

    def update(self, world: World) -> None:
        """Update method required by BaseSystem.

        Renders the game world (board, tiles, grid) to the surface.
        Does NOT update the display - that's handled by StaticUISystem.

        Args:
            world: Game world to render
        """
        self.render_frame(world)
