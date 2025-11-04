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

"""World composition class containing game state components."""

import pygame
from src.ecs.entity_registry import EntityRegistry
from src.ecs.board import Board

__all__ = ["World"]


class World:
    """Container for core game state components.

    Composed of:
    - EntityRegistry: Manages entities and their IDs
    - Board: 2D grid for spatial indexing and collision detection
    - Clock: Pygame clock for frame timing

    Access components via properties:
    - world.registry: Entity management
    - world.board: Spatial grid
    - world.clock: Frame timing

    Example:
        board = Board(20, 20)
        world = World(board)

        # Add entity via registry
        entity_id = world.registry.add(snake)

        # Query entities
        snakes = world.registry.query_by_type(EntityType.SNAKE)

        # Access board for collision
        tile = world.board.get_tile(5, 5)

        # Control frame rate
        world.clock.tick(60)
    """

    _registry: EntityRegistry
    _board: Board
    _clock: pygame.time.Clock
    _dt_ms: float  # delta time in milliseconds since last frame
    _grid_offset_x: int  # x offset to center grid in window
    _grid_offset_y: int  # y offset to center grid in window

    def __init__(self, board: Board) -> None:
        """Initialize world with required components.

        Args:
            board: Board instance for spatial indexing and collision detection
        """
        self._registry = EntityRegistry()
        self._board = board
        self._clock = pygame.time.Clock()
        self._dt_ms = 16.67  # default to ~60fps
        self._grid_offset_x = 0
        self._grid_offset_y = 0

    @property
    def registry(self) -> EntityRegistry:
        # Get the entity registry for entity management.

        return self._registry

    @property
    def board(self) -> Board:
        """Get the board for spatial indexing and collision detection.

        Returns:
            Board: The board instance
        """
        return self._board

    @board.setter
    def board(self, new_board: Board) -> None:
        self._board = new_board

    @property
    def clock(self) -> pygame.time.Clock:
        """Get the pygame clock for frame timing.

        Returns:
            pygame.time.Clock: The clock instance
        """
        return self._clock

    @property
    def dt_ms(self) -> float:
        """Get delta time in milliseconds since last frame.

        Returns:
            float: Delta time in milliseconds
        """
        return self._dt_ms

    def set_dt_ms(self, dt_ms: float) -> None:
        # set delta time for this frame.
        self._dt_ms = dt_ms

    @property
    def grid_offset_x(self) -> int:
        """Get grid X offset for centering in window.

        Returns:
            int: X offset in pixels
        """
        return self._grid_offset_x

    @property
    def grid_offset_y(self) -> int:
        """Get grid Y offset for centering in window.

        Returns:
            int: Y offset in pixels
        """
        return self._grid_offset_y

    def set_grid_offset(self, offset_x: int, offset_y: int) -> None:
        """Set grid offset for centering in window.

        Args:
            offset_x: X offset in pixels
            offset_y: Y offset in pixels
        """
        self._grid_offset_x = offset_x
        self._grid_offset_y = offset_y
