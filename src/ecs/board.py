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

"""Class for the game board."""

from enum import Enum, auto


class Tile(Enum):
    """Tile types for board rendering.
    
    Each tile type determines how the cell should be rendered.
    Mainly used for color differentiation.
    """

    EMPTY = auto()
    SNAKE_HEAD = auto()
    SNAKE_BODY = auto()
    APPLE = auto()
    OBSTACLE = auto()
    WALL = auto()


class BoardOutOfBoundsError(Exception):
    """Exception raised when accessing board outside valid bounds."""

    def __init__(self, x: int, y: int, width: int, height: int):
        """Initialize the error with position and board dimensions.
        
        Args:
            x: X coordinate that was out of bounds
            y: Y coordinate that was out of bounds
            width: Board width
            height: Board height
        """
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        message = f"Position ({x}, {y}) is out of bounds for board of size ({width}, {height})"
        super().__init__(message)


class Board:
    """2D game board with tile-based grid system.
    
    Provides O(1) lookup and modification of tiles using a 2D matrix.
    Supports batch updates and bounds checking.
    
    Attributes:
        width: Board width in tiles
        height: Board height in tiles
        is_square: True if width equals height
    """

    _grid: list[list[Tile]]
    _width: int
    _height: int

    def __init__(self, width: int, height: int, default_tile: Tile = Tile.EMPTY):
        """Initialize board with given dimensions.
        
        Args:
            width: Board width in tiles (must be > 0)
            height: Board height in tiles (must be > 0)
            default_tile: Initial tile type for all cells
            
        Raises:
            ValueError: If width or height is less than 1
        """
        if width < 1 or height < 1:
            raise ValueError(f"Board dimensions must be at least 1x1, got {width}x{height}")

        self._width = width
        self._height = height
        # initialize 2D grid with default tiles (row-major order)
        self._grid = [[default_tile for _ in range(width)] for _ in range(height)]

    @property
    def width(self) -> int:
        """Get board width.
        
        Returns:
            int: Width in tiles
        """
        return self._width

    @property
    def height(self) -> int:
        """Get board height.
        
        Returns:
            int: Height in tiles
        """
        return self._height

    @property
    def is_square(self) -> bool:
        """Check if board is square.
        
        Returns:
            bool: True if width equals height
        """
        return self._width == self._height

    def _check_bounds(self, x: int, y: int) -> None:
        """Check if coordinates are within board bounds.
        
        Args:
            x: X coordinate (column)
            y: Y coordinate (row)
            
        Raises:
            BoardOutOfBoundsError: If coordinates are out of bounds
        """
        if not (0 <= x < self._width and 0 <= y < self._height):
            raise BoardOutOfBoundsError(x, y, self._width, self._height)

    def get_tile(self, x: int, y: int) -> Tile:
        """Get tile at specified position.
        
        O(1) operation.
        
        Args:
            x: X coordinate (column)
            y: Y coordinate (row)
            
        Returns:
            Tile: Tile type at position
            
        Raises:
            BoardOutOfBoundsError: If position is out of bounds
        """
        self._check_bounds(x, y)
        return self._grid[y][x]

    def set_tile(self, x: int, y: int, tile: Tile) -> None:
        """Set tile at specified position.
        
        O(1) operation.
        
        Args:
            x: X coordinate (column)
            y: Y coordinate (row)
            tile: Tile type to set
            
        Raises:
            BoardOutOfBoundsError: If position is out of bounds
        """
        self._check_bounds(x, y)
        self._grid[y][x] = tile

    def set_tiles(self, tile_updates: list[tuple[int, int, Tile]]) -> None:
        """Update multiple tiles at once.
        
        O(n) operation where n is the number of updates.
        All positions are validated before any modifications.
        
        Args:
            tile_updates: List of (x, y, tile) tuples
            
        Raises:
            BoardOutOfBoundsError: If any position is out of bounds
            
        Example:
            board.set_tiles([
                (0, 0, Tile.SNAKE_HEAD),
                (0, 1, Tile.SNAKE_BODY),
                (5, 5, Tile.APPLE),
            ])
        """
        # validate all positions first
        for x, y, _ in tile_updates:
            self._check_bounds(x, y)

        # if all valid, apply updates
        for x, y, tile in tile_updates:
            self._grid[y][x] = tile

    def clear(self, tile: Tile = Tile.EMPTY) -> None:
        """Clear the entire board to a specific tile type.
        
        Args:
            tile: Tile type to fill board with
        """
        for y in range(self._height):
            for x in range(self._width):
                self._grid[y][x] = tile

    def get_row(self, y: int) -> list[Tile]:
        """Get entire row as a list.
        
        Args:
            y: Row index
            
        Returns:
            list[Tile]: Copy of the row
            
        Raises:
            BoardOutOfBoundsError: If row index is out of bounds
        """
        if not (0 <= y < self._height):
            raise BoardOutOfBoundsError(0, y, self._width, self._height)
        return self._grid[y].copy()

    def get_column(self, x: int) -> list[Tile]:
        """Get entire column as a list.
        
        Args:
            x: Column index
            
        Returns:
            list[Tile]: Copy of the column
            
        Raises:
            BoardOutOfBoundsError: If column index is out of bounds
        """
        if not (0 <= x < self._width):
            raise BoardOutOfBoundsError(x, 0, self._width, self._height)
        return [self._grid[y][x] for y in range(self._height)]

    def __repr__(self) -> str:
        """String representation of board.
        
        Returns:
            str: Board representation
        """
        return f"Board(width={self._width}, height={self._height}, is_square={self.is_square})"
