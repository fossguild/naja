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
This file is for defining the main game entities
"""

from __future__ import annotations

import random
from typing import Callable
import pygame

from constants import CLOCK_TICKS, APPLE_COLOR, OBSTACLE_COLOR


##
## Snake class
##


class Snake:

    def __init__(self, width: int, height: int, grid_size: int):
        """Initialize the Snake.

        Args:
            width: Game window width
            height: Game window height
            grid_size: Size of each grid cell
        """
        # Store window dimensions and grid size
        self.width = width
        self.height = height
        self.grid_size = grid_size

        # Dimension of each snake segment.
        self.x, self.y = grid_size, grid_size

        # Initial direction
        # xmov :  -1 left,    0 still,   1 right
        # ymov :  -1 up       0 still,   1 dows
        self.xmov = 1
        self.ymov = 0

        # The snake has a head segement,
        self.head = pygame.Rect(self.x, self.y, grid_size, grid_size)

        # and a tail/history of positions (head first).
        # Store integer grid coordinates (x, y) in `positions`, head at index 0.
        self.positions = [(self.x, self.y)]
        self.tail = self.positions[1:]

        # The snake is born.
        self.alive = True

        # No collected apples.
        self.got_apple = False

        # Initial speed
        self.speed = float(CLOCK_TICKS)

        # For smooth movement
        self.move_progress: float = 0.0
        self.target_x: int = self.x
        self.target_y: int = self.y
        self.draw_x: float = float(self.x)
        self.draw_y: float = float(self.y)

        self.prev_head_x = self.x
        self.prev_head_y = self.y

    # This function is called at each loop interation.

    def update(
        self, apple: Apple, obstacles: list[Obstacle], game_over_func: Callable
    ) -> bool:
        """Update snake position and check for collisions.

        Returns:
            bool: True if the snake died this frame, False otherwise
        """
        died = False

        # Calculate the head's next position based on current movement
        next_x = self.head.x + self.xmov * self.grid_size
        next_y = self.head.y + self.ymov * self.grid_size

        # Only check collisions if the snake is currently moving
        if self.xmov or self.ymov:
            # Check for border crash.
            if next_x not in range(0, self.width) or next_y not in range(
                0, self.height
            ):
                self.alive = False
                died = True

            # Check for self-bite.
            for square in self.tail:
                if next_x == square[0] and next_y == square[1]:
                    self.alive = False
                    died = True

            # Check for obstacle collision.
            for obstacle in obstacles:
                if next_x == obstacle.x and next_y == obstacle.y:
                    self.alive = False
                    died = True

            if self.alive:
                self.target_x = next_x
                self.target_y = next_y
                self.move_progress = 0.0

        # In the event of death, reset the game arena.
        if not self.alive:
            died = True
            # handle game over visuals to the user
            game_over_func()

            # Respan the head
            self.x, self.y = self.grid_size, self.grid_size
            self.head = pygame.Rect(self.x, self.y, self.grid_size, self.grid_size)

            # Respan the initial tail
            self.tail = []

            # Initial direction
            self.xmov = 1  # Right
            self.ymov = 0  # Still

            # Resurrection
            self.alive = True
            self.got_apple = False

            # Reset speed
            self.speed = float(CLOCK_TICKS)

            # For smooth movement
            self.move_progress = 0.0
            self.target_x = self.x
            self.target_y = self.y
            self.draw_x = self.x
            self.draw_y = self.y
            self.prev_head_x = self.x
            self.prev_head_y = self.y

            # Reposition the apple
            apple.ensure_valid_position(self, obstacles)

        return died


##
## The apple class.
##


class Apple:
    def __init__(self, width: int, height: int, grid_size: int):
        """Initialize the Apple in a random position on the grid, but does not guarantee it is not overlaped with the snake

        Args:
            width: Game window width
            height: Game window height
            grid_size: Size of each grid cell
        """
        self.width = width
        self.height = height
        self.grid_size = grid_size

        # Place at random position (will be refined by ensure_valid_position)
        self.x = random.randrange(0, width, grid_size)
        self.y = random.randrange(0, height, grid_size)
        self.rect = pygame.Rect(self.x, self.y, grid_size, grid_size)

    def ensure_valid_position(
        self, snake: Snake, obstacles: list[Obstacle] | None = None
    ):
        """Move apple to a position not occupied by the snak or obstacles

        Args:
            snake: The Snake instance to avoid
            obstacles: Obstacles to avoid
        """
        if obstacles is None:
            obstacles = []

        # Keep trying until we find a free grid cell (not on the snake).
        while True:
            self.x = random.randrange(0, self.width, self.grid_size)
            self.y = random.randrange(0, self.height, self.grid_size)
            self.rect = pygame.Rect(self.x, self.y, self.grid_size, self.grid_size)

            head_free = not (self.x == snake.head.x and self.y == snake.head.y)
            tail_free = all(
                (self.x != seg[0] or self.y != seg[1]) for seg in snake.tail
            )
            obstacle_free = all(
                (self.x != obs.x or self.y != obs.y) for obs in obstacles
            )
            if head_free and tail_free and obstacle_free:
                break

    # This function is called each iteration of the game loop
    def update(self, arena: pygame.Surface):
        """Draw the apple."""
        pygame.draw.rect(arena, APPLE_COLOR, self.rect)


class Obstacle:
    def __init__(self, x, y, arena, grid_size):
        self.x = x
        self.y = y
        self.rect = pygame.Rect(x, y, grid_size, grid_size)
        self.arena = arena

    def update(self):
        # Draw the obstacle
        pygame.draw.rect(self.arena, OBSTACLE_COLOR, self.rect)

    @staticmethod
    def calculate_obstacles_from_difficulty(difficulty, width, grid_size, height):
        total_cells = (width // grid_size) * (height // grid_size)

        difficulty_percentages = {
            "None": 0.0,
            "Easy": 0.04,
            "Medium": 0.06,
            "Hard": 0.10,
            "Impossible": 0.15,
        }

        percentage = difficulty_percentages.get(difficulty, 0.0)
        return int(total_cells * percentage)

    @staticmethod
    def is_blocked(x, y, new_obstacle_pos, obstacles_positions, width, height):
        """Checks if a given coordinate is blocked by an obstacle, the new one, or the board edge."""
        # Check if it's outside the board boundaries
        if not (0 <= x < width and 0 <= y < height):
            return True
        # Check if it's the potential new obstacle
        if (x, y) == new_obstacle_pos:
            return True
        # Check if it's an already existing obstacle
        if (x, y) in obstacles_positions:
            return True
        return False
