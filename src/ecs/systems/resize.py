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

"""Resize system for handling window and grid size changes.

This system detects resize requests (from settings or window events),
recalculates grid dimensions, updates the Grid component, and triggers
asset reload when needed.
"""

from __future__ import annotations

from typing import Optional, Callable

from src.ecs.systems.base_system import BaseSystem
from src.ecs.world import World


class ResizeSystem(BaseSystem):
    """System for handling window and grid resize operations.

    Reads: Grid (current dimensions), Settings (cells_per_side)
    Writes: Grid (updated dimensions), Board (updated dimensions)
    Queries: entities with Grid component

    Responsibilities:
    - Detect window resize events or settings changes
    - Recalculate optimal cell size based on desired cells per side
    - Calculate new window dimensions (must be multiples of cell size)
    - Update Grid component with new dimensions
    - Update Board with new dimensions
    - Trigger asset reload callback if needed (fonts)

    Note: This system coordinates with display adapter and asset system
    to ensure consistent resizing across the game.
    """

    def __init__(
        self,
        max_dimension: int = 800,
        min_cell_size: int = 8,
        asset_reload_callback: Optional[Callable[[int], None]] = None,
    ):
        """Initialize the ResizeSystem.

        Args:
            max_dimension: Maximum safe screen dimension (width or height)
            min_cell_size: Minimum allowed cell size in pixels
            asset_reload_callback: Optional callback for asset reload (receives new width)
        """
        self._max_dimension = max_dimension
        self._min_cell_size = min_cell_size
        self._asset_reload_callback = asset_reload_callback
        self._pending_resize = False
        self._desired_cells_per_side: Optional[int] = None

    def update(self, world: World) -> None:
        """Process pending resize operations.

        This method is called every tick but only acts when resize is pending.

        Args:
            world: ECS world containing entities and components
        """
        if self._pending_resize and self._desired_cells_per_side is not None:
            self.resize_grid(world, self._desired_cells_per_side)
            self._pending_resize = False
            self._desired_cells_per_side = None

    def request_resize(self, cells_per_side: int) -> None:
        """Request a grid resize operation.

        Args:
            cells_per_side: Desired number of cells per side of the grid
        """
        self._pending_resize = True
        self._desired_cells_per_side = max(10, cells_per_side)  # minimum 10 cells

    def resize_grid(self, world: World, cells_per_side: int) -> bool:
        """Resize the grid based on desired cells per side.

        Args:
            world: ECS world
            cells_per_side: Desired number of cells per side

        Returns:
            True if resize was performed, False if no change needed
        """
        board = world.board
        current_cell_size = board.cell_size

        # calculate new optimal cell size
        new_cell_size = self.calculate_optimal_cell_size(cells_per_side)

        # check if resize is needed
        if new_cell_size == current_cell_size:
            return False

        # calculate new window dimensions
        new_width, new_height = self.calculate_window_size(new_cell_size)

        # update board dimensions
        board.width = new_width
        board.height = new_height
        board.cell_size = new_cell_size

        # trigger asset reload if callback is set
        if self._asset_reload_callback:
            self._asset_reload_callback(new_width)

        return True

    def calculate_optimal_cell_size(self, cells_per_side: int) -> int:
        """Calculate optimal cell size for desired number of cells.

        Args:
            cells_per_side: Desired number of cells per side

        Returns:
            Optimal cell size in pixels (at least min_cell_size)
        """
        if cells_per_side <= 0:
            cells_per_side = 10  # default

        # calculate cell size to fit desired number of cells
        cell_size = self._max_dimension // cells_per_side

        # ensure minimum cell size
        cell_size = max(self._min_cell_size, cell_size)

        return cell_size

    def calculate_window_size(self, cell_size: int) -> tuple[int, int]:
        """Calculate window dimensions for a given cell size.

        Dimensions must be multiples of cell_size.

        Args:
            cell_size: Size of each grid cell in pixels

        Returns:
            Tuple of (width, height)
        """
        # calculate dimension as multiple of cell_size
        dimension = (self._max_dimension // cell_size) * cell_size

        # return square window
        return dimension, dimension

    def get_max_dimension(self) -> int:
        """Get maximum safe screen dimension.

        Returns:
            Maximum dimension in pixels
        """
        return self._max_dimension

    def set_max_dimension(self, max_dimension: int) -> None:
        """Set maximum safe screen dimension.

        Args:
            max_dimension: New maximum dimension in pixels
        """
        self._max_dimension = max(100, max_dimension)  # minimum 100

    def get_min_cell_size(self) -> int:
        """Get minimum allowed cell size.

        Returns:
            Minimum cell size in pixels
        """
        return self._min_cell_size

    def set_min_cell_size(self, min_cell_size: int) -> None:
        """Set minimum allowed cell size.

        Args:
            min_cell_size: New minimum cell size in pixels
        """
        self._min_cell_size = max(4, min_cell_size)  # minimum 4

    def set_asset_reload_callback(
        self, callback: Optional[Callable[[int], None]]
    ) -> None:
        """Set callback for asset reload.

        Args:
            callback: Callback function that receives new window width
        """
        self._asset_reload_callback = callback

    def has_pending_resize(self) -> bool:
        """Check if there is a pending resize operation.

        Returns:
            True if resize is pending, False otherwise
        """
        return self._pending_resize

    def get_current_cells_per_side(self, world: World) -> int:
        """Calculate current number of cells per side.

        Args:
            world: ECS world

        Returns:
            Number of cells per side based on current board dimensions
        """
        board = world.board
        return board.width // board.cell_size

    def calculate_grid_dimensions(
        self, cell_size: int
    ) -> tuple[int, int, int, int]:
        """Calculate grid dimensions for a given cell size.

        Args:
            cell_size: Size of each grid cell in pixels

        Returns:
            Tuple of (width_pixels, height_pixels, width_cells, height_cells)
        """
        width_pixels, height_pixels = self.calculate_window_size(cell_size)
        width_cells = width_pixels // cell_size
        height_cells = height_pixels // cell_size

        return width_pixels, height_pixels, width_cells, height_cells

    def validate_resize_request(
        self, cells_per_side: int
    ) -> tuple[bool, Optional[str]]:
        """Validate a resize request.

        Args:
            cells_per_side: Desired cells per side

        Returns:
            Tuple of (is_valid, error_message)
        """
        if cells_per_side < 10:
            return False, "Cells per side must be at least 10"

        cell_size = self.calculate_optimal_cell_size(cells_per_side)

        if cell_size < self._min_cell_size:
            return (
                False,
                f"Resulting cell size ({cell_size}px) would be below minimum "
                f"({self._min_cell_size}px)",
            )

        # check if window dimensions would be too small
        width, height = self.calculate_window_size(cell_size)
        if width < 200 or height < 200:
            return False, "Resulting window would be too small (minimum 200x200)"

        return True, None
