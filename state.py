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
Game state configuration.
This module contains the GameState class that holds all mutable game state variables.
"""

from entities import Snake, Apple
import pygame


class GameState:
    """Holds all mutable game state variables."""

    clock: pygame.time.Clock
    arena: pygame.Surface
    game_on: int
    snake: Snake
    apple: Apple

    def __init__(self, display_width: int, display_height: int, grid_size: int):
        """Initialize game state with default values.
        
        Args:
            display_width: Width of the game window
            display_height: Height of the game window
            grid_size: Size of each grid cell
        """
        # Pygame resources (initialized during game setup)
        self.clock = pygame.time.Clock()
        self.arena = pygame.display.set_mode(
            (display_width, display_height), pygame.SCALED, vsync=1
        )

        # Game state
        self.game_on = 1  # 1 = running, 0 = paused

        # Game objects (initialized with proper dimensions)
        self.snake = Snake(display_width, display_height, grid_size)
        self.apple = Apple(display_width, display_height, grid_size)
        self.apple.ensure_not_on_snake(self.snake)
