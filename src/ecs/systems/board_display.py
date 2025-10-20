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

import pygame
from src.ecs.systems.base_system import BaseSystem
from src.ecs.world import World
from src.ecs.board import Tile
from src.core.types.color import Color
from src.core.rendering.pygame_surface_renderer import RenderEnqueue


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

    def update(self, world: World) -> None:
        """Update method required by BaseSystem.

        Renders the game world (board, tiles, grid) to the surface.
        Does NOT update the display - that's handled by StaticUISystem.

        Args:
            world: Game world to render
        """
        self.render_frame(world)
