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

"""Simplified BoardRenderSystem - renders only board, grid and basic tiles.

This system follows ECS Single Responsibility Principle by handling ONLY:
- Board background
- Grid lines
- Basic tile rendering from Board state

UI elements (score, speed bar, etc.) are handled by separate UI systems.
Entity rendering is handled by EntityRenderSystem.
Snake rendering is handled by SnakeRenderSystem.
"""

import pygame
from src.ecs.systems.base_system import BaseSystem
from src.ecs.world import World
from src.ecs.board import Tile
from src.core.rendering.pygame_surface_renderer import RenderEnqueue
from src.ecs.components.color_scheme import ColorScheme


class BoardRenderSystem(BaseSystem):
    """System responsible for rendering the game board foundation.

    Responsibilities (following SRP):
    - Clear screen with arena background color
    - Draw grid lines
    - Draw basic tiles from board state (EMPTY, WALL, etc.)

    NOT responsible for:
    - Entity rendering (use EntityRenderSystem)
    - Snake rendering (use SnakeRenderSystem)
    - UI elements (use UI systems)
    - Game over/pause overlays (use UI systems)

    This system queries for ColorScheme component to get colors,
    following ECS data-driven approach instead of hard-coding values.
    """

    def __init__(self, renderer: RenderEnqueue):
        """Initialize the BoardRenderSystem.

        Args:
            renderer: RenderEnqueue view to queue draw commands (enqueue-only access)
        """
        self._renderer = renderer

    def _get_color_scheme(self, world: World) -> ColorScheme:
        """Get ColorScheme component from world entities.

        Args:
            world: Game world

        Returns:
            ColorScheme component, or default if not found
        """
        # Query for entities with ColorScheme component
        color_entities = world.registry.query_by_component("color_scheme")

        if color_entities:
            # Get first entity with color scheme
            entity = next(iter(color_entities.values()))
            return entity.color_scheme

        # Return default color scheme if none found
        return ColorScheme()

    def clear_screen(self, world: World) -> None:
        """Clear the screen with the arena background color.

        Args:
            world: Game world
        """
        color_scheme = self._get_color_scheme(world)
        arena_color = color_scheme.arena.to_tuple()
        self._renderer.fill(arena_color)

    def draw_grid(self, world: World) -> None:
        """Draw the game grid based on the board dimensions.

        Args:
            world: Game world containing the board
        """
        board = world.board
        cell_size = board.cell_size
        width = board.width * cell_size
        height = board.height * cell_size
        offset_x = world.grid_offset_x
        offset_y = world.grid_offset_y

        color_scheme = self._get_color_scheme(world)
        grid_color = color_scheme.grid.to_tuple()

        # Draw vertical lines
        for x in range(0, width, cell_size):
            self._renderer.draw_line(
                grid_color,
                (x + offset_x, offset_y),
                (x + offset_x, height + offset_y),
                1,
            )

        # Draw horizontal lines
        for y in range(0, height, cell_size):
            self._renderer.draw_line(
                grid_color,
                (offset_x, y + offset_y),
                (width + offset_x, y + offset_y),
                1,
            )

    def draw_tile(
        self,
        x: int,
        y: int,
        tile: Tile,
        cell_size: int,
        color_scheme: ColorScheme,
        offset_x: int = 0,
        offset_y: int = 0,
    ) -> None:
        """Draw a single tile at the specified grid position.

        Args:
            x: X coordinate in grid units
            y: Y coordinate in grid units
            tile: Type of tile to draw
            cell_size: Size of grid cell in pixels
            color_scheme: Color scheme to use
            offset_x: X offset for centering grid
            offset_y: Y offset for centering grid
        """
        # Calculate pixel position with offset
        pixel_x = x * cell_size + offset_x
        pixel_y = y * cell_size + offset_y

        # Map tile type to color
        # Note: SNAKE, APPLE tiles are NOT rendered here - handled by entity systems
        tile_colors = {
            Tile.EMPTY: None,  # Don't draw empty tiles
            Tile.WALL: color_scheme.obstacle.to_tuple(),
            # Other tile types are rendered by their respective entity systems
        }

        color = tile_colors.get(tile)
        if color is None:
            return  # Skip tiles without color mapping

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
        color_scheme = self._get_color_scheme(world)
        offset_x = world.grid_offset_x
        offset_y = world.grid_offset_y

        for y in range(board.height):
            for x in range(board.width):
                tile = board.get_tile(x, y)
                self.draw_tile(x, y, tile, cell_size, color_scheme, offset_x, offset_y)

    def update(self, world: World) -> None:
        """Update method required by BaseSystem.

        Renders the game board foundation (background, grid, tiles).
        Entity rendering is handled by separate systems.

        Args:
            world: Game world to render
        """
        # Check if game is over - render only background if dead
        from src.ecs.entities.entity import EntityType

        snakes = world.registry.query_by_type(EntityType.SNAKE)
        game_over = False
        for _, snake in snakes.items():
            if hasattr(snake, "body") and not snake.body.alive:
                game_over = True
                break

        # If game is over, render only arena background
        if game_over:
            self.clear_screen(world)
            return

        # Render normal game board foundation
        self.clear_screen(world)
        self.draw_grid(world)
        self.draw_board(world)
