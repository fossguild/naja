#!/usr/bin/env python3
#
#   Copyright (c) 2023, Monaco F. J. <monaco@usp.br>
#
#   This file is part of KobraPy.
#
#   KobraPy is free software: you can redistribute it and/or modify
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

"""
This module contains the GameState class that encapsulates all mutable game state,
including the game arena, entities (snake, apples, obstacles), and game flow control.
"""

import random
import pygame
from .entities import Snake, Apple, Obstacle


class GameState:
    """Holds all mutable game state variables."""

    clock: pygame.time.Clock
    arena: pygame.Surface
    game_on: int
    snake: Snake
    apples: list[Apple]
    obstacles: list[Obstacle]

    # Private fields
    _width: int
    _height: int
    _grid_size: int

    def __init__(self, display_width: int, display_height: int, grid_size: int):
        """Initialize game state with default values.

        Args:
            display_width: Width of the game window
            display_height: Height of the game window
            grid_size: Size of each grid cell
        """
        # Store dimensions as private fields
        self._width = display_width
        self._height = display_height
        self._grid_size = grid_size

        # Pygame resources (initialized during game setup)
        self.clock = pygame.time.Clock()
        self.arena = pygame.display.set_mode(
            (display_width, display_height), pygame.SCALED, vsync=1
        )

        # Game state
        self.game_on = 1  # 1 = running, 0 = paused

        # Game objects (initialized with proper dimensions)
        self.snake = Snake(display_width, display_height, grid_size)
        self.obstacles = []  # Will be populated by create_obstacles if needed

        # Initialize with a single apple (will be updated by apply_settings)
        self.apples = []
        apple = Apple(display_width, display_height, grid_size)
        apple.ensure_valid_position(self.snake, self.obstacles)
        self.apples.append(apple)

    def update_dimensions(self, width: int, height: int, grid_size: int) -> None:
        """Update the game dimensions.

        Args:
            width: New game window width
            height: New game window height
            grid_size: New grid cell size
        """
        self._width = width
        self._height = height
        self._grid_size = grid_size

    def create_obstacles_constructively(self, num_obstacles: int) -> None:
        """Builds a valid map by adding obstacles one by one safely."""
        # Early return if no obstacles needed
        if num_obstacles == 0:
            self.obstacles = []
            return

        max_retries = 100
        for _ in range(max_retries):
            obstacles = []
            obstacles_positions = set()

            # Get all possible spawn points for obstacles, avoiding the snake's start area
            available_positions = []
            for x in range(0, self._width, self._grid_size):
                for y in range(0, self._height, self._grid_size):
                    if not (
                        abs(x - self.snake.x) < self._grid_size * 8
                        and abs(y - self.snake.y) < self._grid_size * 2
                    ):
                        available_positions.append((x, y))
            random.shuffle(available_positions)

            temp_available = list(available_positions)

            # Attempt to place one obstacle at a time
            while len(obstacles) < num_obstacles and temp_available:
                candidate_pos = temp_available.pop()

                # Rule 1: Don't create narrow passages or traps
                if self.__would_create_trap(candidate_pos, obstacles_positions):
                    continue

                # If the local check passes, add the obstacle
                obstacles.append(
                    Obstacle(
                        candidate_pos[0], candidate_pos[1], self.arena, self._grid_size
                    )
                )
                obstacles_positions.add(candidate_pos)

            # Rule 2: Don't disconnect the map
            if len(obstacles) == num_obstacles and self.__is_grid_connected(obstacles):
                self.obstacles = obstacles
                return

        # If we couldn't place all obstacles after max_retries, use what we have
        print(
            f"Warning: Could only place {len(obstacles)} of {num_obstacles} requested obstacles"
        )
        self.obstacles = obstacles

    # private helper functions

    def __is_grid_connected(self, obstacles: list[Obstacle]) -> bool:
        """Checks if all free cells on the grid are connected using BFS."""
        obstacles_positions = {(obs.x, obs.y) for obs in obstacles}
        if (self.snake.x, self.snake.y) in obstacles_positions:
            return False

        # Calculate the expected number of reachable cells
        total_cells = (self._width // self._grid_size) * (
            self._height // self._grid_size
        )
        total_free_cells = total_cells - len(obstacles)

        # Use a standard list as a queue
        queue = [(self.snake.x, self.snake.y)]
        visited = set([(self.snake.x, self.snake.y)])

        while queue:
            # Pop the first element to behave like a queue (FIFO)
            x, y = queue.pop(0)

            # Check all four neighbors
            for dx, dy in [
                (0, self._grid_size),
                (0, -self._grid_size),
                (self._grid_size, 0),
                (-self._grid_size, 0),
            ]:
                neighbor = (x + dx, y + dy)

                # If neighbor is valid and unvisited, add it to the queue
                if (
                    0 <= neighbor[0] < self._width
                    and 0 <= neighbor[1] < self._height
                    and neighbor not in obstacles_positions
                    and neighbor not in visited
                ):
                    visited.add(neighbor)
                    queue.append(neighbor)

        # The grid is connected if all free cells were visited
        return len(visited) == total_free_cells

    def __would_create_trap(
        self,
        new_obstacle_pos: tuple[int, int],
        obstacles_positions: set[tuple[int, int]],
    ) -> bool:
        """
        Checks if placing a new obstacle creates a trap for any adjacent cell.
        A trap is a free cell with 3 or more blocked sides.
        """
        new_x, new_y = new_obstacle_pos

        # We only need to check the four direct neighbors of the new obstacle.
        # Only these cells could possibly become trapped by this new addition.
        for dx, dy in [
            (0, self._grid_size),
            (0, -self._grid_size),
            (self._grid_size, 0),
            (-self._grid_size, 0),
        ]:
            neighbor_x, neighbor_y = new_x + dx, new_y + dy

            # If the neighbor is not a free cell, we don't need to check it.
            if Obstacle.is_blocked(
                neighbor_x,
                neighbor_y,
                (0, 0),
                obstacles_positions,
                self._width,
                self._height,
            ):  # Note: passing dummy new_pos
                continue

            # This neighbor is a free cell. Let's count how many of its sides are blocked.
            blocked_sides_count = 0

            # Check the 4 sides of this neighbor cell
            sides_to_check = [
                (neighbor_x + self._grid_size, neighbor_y),  # Right
                (neighbor_x - self._grid_size, neighbor_y),  # Left
                (neighbor_x, neighbor_y + self._grid_size),  # Down
                (neighbor_x, neighbor_y - self._grid_size),  # Up
            ]

            for side_x, side_y in sides_to_check:
                if Obstacle.is_blocked(
                    side_x,
                    side_y,
                    new_obstacle_pos,
                    obstacles_positions,
                    self._width,
                    self._height,
                ):
                    blocked_sides_count += 1

            # If 3 or more sides are blocked, it's a trap.
            if blocked_sides_count >= 3:
                return True

        # If we check all neighbors and none of them become traps, the placement is safe.
        return False

    # Public properties for safe dimension access

    @property
    def width(self) -> int:
        """Get current game window width.

        Returns:
            Window width in pixels
        """
        return self._width

    @property
    def height(self) -> int:
        """Get current game window height.

        Returns:
            Window height in pixels
        """
        return self._height

    @property
    def grid_size(self) -> int:
        """Get current grid cell size.

        Returns:
            Grid cell size in pixels
        """
        return self._grid_size

    @property
    def cells_per_side(self) -> int:
        """Get number of cells per side of the square grid.

        Returns:
            Number of cells per side
        """
        return self._width // self._grid_size

    @property
    def total_cells(self) -> int:
        """Get total number of cells in the grid.

        Returns:
            Total number of cells
        """
        return (self._width // self._grid_size) * (self._height // self._grid_size)

    @property
    def is_paused(self) -> bool:
        """Check if game is paused.

        Returns:
            True if paused, False if running
        """
        return self.game_on == 0

    @property
    def is_running(self) -> bool:
        """Check if game is running.

        Returns:
            True if running, False if paused
        """
        return self.game_on == 1

    # Public utility methods

    def pause(self) -> None:
        """Pause the game."""
        self.game_on = 0

    def resume(self) -> None:
        """Resume the game."""
        self.game_on = 1

    def toggle_pause(self) -> None:
        """Toggle game pause state."""
        self.game_on = 1 - self.game_on

    def reset_snake(self) -> None:
        """Reset snake to initial position and state."""
        self.snake = Snake(self._width, self._height, self._grid_size)

    def clear_obstacles(self) -> None:
        """Remove all obstacles from the game."""
        self.obstacles = []

    def clear_apples(self) -> None:
        """Remove all apples from the game."""
        self.apples = []

    def add_apple(self) -> Apple | None:
        """Add a new apple to the game at a valid position.

        Returns:
            The newly created apple, or None if no valid position available
        """
        apple = Apple(self._width, self._height, self._grid_size)
        if apple.ensure_valid_position(self.snake, self.obstacles):
            self.apples.append(apple)
            return apple
        return None

    def remove_apple(self, apple: Apple) -> None:
        """Remove a specific apple from the game.

        Args:
            apple: The apple instance to remove
        """
        if apple in self.apples:
            self.apples.remove(apple)

    def get_free_cells_count(self) -> int:
        """Calculate number of free (unoccupied) cells in the grid.

        Returns:
            Number of free cells
        """
        occupied = len(self.obstacles) + len(self.snake.tail) + 1  # +1 for head
        return self.total_cells - occupied

    def recreate_arena(self) -> None:
        """Recreate the pygame display surface with current dimensions."""
        self.arena = pygame.display.set_mode(
            (self._width, self._height), pygame.SCALED, vsync=1
        )

    def get_state_summary(self) -> dict:
        """Get a summary of the current game state.

        Returns:
            Dictionary containing state information
        """
        return {
            "width": self._width,
            "height": self._height,
            "grid_size": self._grid_size,
            "cells_per_side": self.cells_per_side,
            "total_cells": self.total_cells,
            "free_cells": self.get_free_cells_count(),
            "snake_length": len(self.snake.tail),
            "apple_count": len(self.apples),
            "obstacle_count": len(self.obstacles),
            "is_running": self.is_running,
            "is_paused": self.is_paused,
        }
