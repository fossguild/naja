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

"""Game configuration and display initialization."""

import pygame


class GameConfig:
    """Manages immutable game configuration (screen dimensions, initial grid size)."""

    # Default configuration constants
    DEFAULT_GRID_SIZE = 50
    DEFAULT_INITIAL_SPEED = 4.0
    SCREEN_USAGE_RATIO = 0.9  # Use 90% of screen for game window

    def __init__(self):
        """Initialize game configuration based on display information.

        Automatically detects screen size and calculates optimal window dimensions.
        """
        # Ensure Pygame is initialized before accessing display info
        if not pygame.get_init():
            pygame.init()

        # Get display information
        self.display_info = pygame.display.Info()
        self.user_screen_width = self.display_info.current_w
        self.user_screen_height = self.display_info.current_h

        # Calculate safe maximum dimension (90% of smallest screen dimension)
        self.safe_max_dimension = int(
            min(self.user_screen_width, self.user_screen_height)
            * self.SCREEN_USAGE_RATIO
        )

        # Initial grid configuration
        self.initial_grid_size = self.DEFAULT_GRID_SIZE

        # Calculate initial window dimensions (must be multiple of grid size)
        self.initial_width = (
            self.safe_max_dimension // self.initial_grid_size
        ) * self.initial_grid_size
        self.initial_height = self.initial_width  # Square window

        # Initial game speed
        self.initial_clock_ticks = self.DEFAULT_INITIAL_SPEED

    def calculate_window_size(self, grid_size: int) -> tuple[int, int]:
        """Calculate window dimensions for a given grid size.

        Args:
            grid_size: Size of each grid cell in pixels

        Returns:
            Tuple of (width, height) ensuring dimensions are multiples of grid_size
        """
        dimension = (self.safe_max_dimension // grid_size) * grid_size
        return dimension, dimension

    def get_optimal_grid_size(self, cells_per_side: int) -> int:
        """Calculate optimal grid size for desired number of cells per side.

        Args:
            cells_per_side: Desired number of cells per side

        Returns:
            Optimal grid size in pixels (minimum 8 pixels)
        """
        return max(8, self.safe_max_dimension // cells_per_side)

    def get_display_info(self) -> dict:
        """Get comprehensive display information.

        Returns:
            Dictionary containing screen dimensions and configuration
        """
        return {
            "screen_width": self.user_screen_width,
            "screen_height": self.user_screen_height,
            "safe_dimension": self.safe_max_dimension,
            "initial_width": self.initial_width,
            "initial_height": self.initial_height,
            "initial_grid_size": self.initial_grid_size,
            "initial_speed": self.initial_clock_ticks,
        }

    def validate_grid_size(self, grid_size: int) -> bool:
        """Check if a grid size is valid for the current display.

        Args:
            grid_size: Grid size to validate

        Returns:
            True if valid, False otherwise
        """
        if grid_size < 8:
            return False
        if grid_size > self.safe_max_dimension:
            return False
        return True

    def get_max_cells_per_side(self) -> int:
        """Calculate maximum number of cells that can fit per side.

        Returns:
            Maximum cells per side (with minimum grid size of 8)
        """
        return self.safe_max_dimension // 8

    def get_min_cells_per_side(self) -> int:
        """Calculate minimum practical number of cells per side.

        Returns:
            Minimum cells per side (for reasonable gameplay)
        """
        return max(10, self.safe_max_dimension // 100)

    @property
    def aspect_ratio(self) -> float:
        """Get display aspect ratio.

        Returns:
            Screen width divided by height
        """
        return self.user_screen_width / self.user_screen_height

    @property
    def is_portrait(self) -> bool:
        """Check if display is in portrait orientation.

        Returns:
            True if height > width, False otherwise
        """
        return self.user_screen_height > self.user_screen_width

    @property
    def is_landscape(self) -> bool:
        """Check if display is in landscape orientation.

        Returns:
            True if width >= height, False otherwise
        """
        return not self.is_portrait
