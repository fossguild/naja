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

"""Board class tests."""

import pytest
from src.ecs.board import Board, Tile, BoardOutOfBoundsError


class TestBoardInitialization:
    """Test board initialization and properties."""

    def test_create_board_with_default_size(self):
        """Test creating a board with valid dimensions."""
        board = Board(10, 10)
        assert board.width == 10
        assert board.height == 10
        assert board.is_square is True

    def test_create_rectangular_board(self):
        """Test creating a non-square board."""
        board = Board(15, 10)
        assert board.width == 15
        assert board.height == 10
        assert board.is_square is False

    def test_create_board_with_custom_default_tile(self):
        """Test creating a board with a custom default tile."""
        board = Board(5, 5, Tile.WALL)
        assert board.get_tile(0, 0) == Tile.WALL
        assert board.get_tile(4, 4) == Tile.WALL

    def test_board_initialized_with_empty_tiles(self):
        """Test that board initializes all tiles to EMPTY by default."""
        board = Board(5, 5)
        for y in range(5):
            for x in range(5):
                assert board.get_tile(x, y) == Tile.EMPTY

    def test_invalid_dimensions_raises_error(self):
        """Test that invalid board dimensions raise ValueError."""
        with pytest.raises(ValueError):
            Board(0, 10)
        with pytest.raises(ValueError):
            Board(10, 0)
        with pytest.raises(ValueError):
            Board(-5, 10)

    def test_board_repr(self):
        """Test string representation of board."""
        board = Board(20, 15)
        repr_str = repr(board)
        assert "20" in repr_str
        assert "15" in repr_str
        assert "Board" in repr_str


class TestBoardTileAccess:
    """Test getting and setting tiles."""

    def test_get_tile_returns_correct_value(self):
        """Test getting a tile value."""
        board = Board(10, 10)
        board.set_tile(5, 5, Tile.APPLE)
        assert board.get_tile(5, 5) == Tile.APPLE

    def test_set_tile_modifies_board(self):
        """Test setting a tile modifies the board state."""
        board = Board(10, 10)
        board.set_tile(3, 7, Tile.SNAKE_HEAD)
        assert board.get_tile(3, 7) == Tile.SNAKE_HEAD

    def test_set_multiple_different_tiles(self):
        """Test setting different tile types."""
        board = Board(10, 10)
        board.set_tile(0, 0, Tile.SNAKE_HEAD)
        board.set_tile(1, 1, Tile.SNAKE_BODY)
        board.set_tile(2, 2, Tile.APPLE)
        board.set_tile(3, 3, Tile.OBSTACLE)

        assert board.get_tile(0, 0) == Tile.SNAKE_HEAD
        assert board.get_tile(1, 1) == Tile.SNAKE_BODY
        assert board.get_tile(2, 2) == Tile.APPLE
        assert board.get_tile(3, 3) == Tile.OBSTACLE

    def test_overwrite_existing_tile(self):
        """Test overwriting a tile with a new value."""
        board = Board(10, 10)
        board.set_tile(5, 5, Tile.APPLE)
        assert board.get_tile(5, 5) == Tile.APPLE

        board.set_tile(5, 5, Tile.OBSTACLE)
        assert board.get_tile(5, 5) == Tile.OBSTACLE


class TestBoardBoundsChecking:
    """Test boundary checking and error handling."""

    def test_get_tile_out_of_bounds_raises_error(self):
        """Test that accessing out-of-bounds position raises error."""
        board = Board(10, 10)

        with pytest.raises(BoardOutOfBoundsError):
            board.get_tile(-1, 5)

        with pytest.raises(BoardOutOfBoundsError):
            board.get_tile(5, -1)

        with pytest.raises(BoardOutOfBoundsError):
            board.get_tile(10, 5)

        with pytest.raises(BoardOutOfBoundsError):
            board.get_tile(5, 10)

    def test_set_tile_out_of_bounds_raises_error(self):
        """Test that setting out-of-bounds position raises error."""
        board = Board(10, 10)

        with pytest.raises(BoardOutOfBoundsError):
            board.set_tile(-1, 5, Tile.APPLE)

        with pytest.raises(BoardOutOfBoundsError):
            board.set_tile(5, 15, Tile.APPLE)

    def test_bounds_error_contains_useful_information(self):
        """Test that BoardOutOfBoundsError provides useful error info."""
        board = Board(10, 10)

        try:
            board.get_tile(15, 20)
            pytest.fail("Should have raised BoardOutOfBoundsError")
        except BoardOutOfBoundsError as e:
            assert e.x == 15
            assert e.y == 20
            assert e.width == 10
            assert e.height == 10
            assert "15" in str(e)
            assert "20" in str(e)

    def test_edge_positions_are_valid(self):
        """Test that edge positions (0 and max) are valid."""
        board = Board(10, 10)

        # Test corners
        board.set_tile(0, 0, Tile.APPLE)
        board.set_tile(9, 0, Tile.APPLE)
        board.set_tile(0, 9, Tile.APPLE)
        board.set_tile(9, 9, Tile.APPLE)

        assert board.get_tile(0, 0) == Tile.APPLE
        assert board.get_tile(9, 0) == Tile.APPLE
        assert board.get_tile(0, 9) == Tile.APPLE
        assert board.get_tile(9, 9) == Tile.APPLE


class TestBoardBatchOperations:
    """Test batch update operations."""

    def test_set_tiles_updates_multiple_positions(self):
        """Test batch updating multiple tiles."""
        board = Board(10, 10)

        updates = [
            (0, 0, Tile.SNAKE_HEAD),
            (0, 1, Tile.SNAKE_BODY),
            (0, 2, Tile.SNAKE_BODY),
            (5, 5, Tile.APPLE),
        ]

        board.set_tiles(updates)

        assert board.get_tile(0, 0) == Tile.SNAKE_HEAD
        assert board.get_tile(0, 1) == Tile.SNAKE_BODY
        assert board.get_tile(0, 2) == Tile.SNAKE_BODY
        assert board.get_tile(5, 5) == Tile.APPLE

    def test_set_tiles_with_empty_list(self):
        """Test batch update with empty list doesn't error."""
        board = Board(10, 10)
        board.set_tiles([])  # Should not raise error

    def test_set_tiles_validates_all_before_updating(self):
        """Test that set_tiles validates all positions before making changes."""
        board = Board(10, 10)
        board.set_tile(0, 0, Tile.APPLE)

        # Try to update with one invalid position
        updates = [
            (0, 0, Tile.SNAKE_HEAD),
            (5, 5, Tile.SNAKE_BODY),
            (20, 20, Tile.OBSTACLE),  # Invalid!
        ]

        with pytest.raises(BoardOutOfBoundsError):
            board.set_tiles(updates)

        # Board should remain unchanged
        assert board.get_tile(0, 0) == Tile.APPLE
        assert board.get_tile(5, 5) == Tile.EMPTY

    def test_clear_board_resets_all_tiles(self):
        """Test that clear() resets all tiles to EMPTY."""
        board = Board(5, 5)

        # Set some tiles
        board.set_tile(0, 0, Tile.SNAKE_HEAD)
        board.set_tile(2, 2, Tile.APPLE)
        board.set_tile(4, 4, Tile.OBSTACLE)

        # Clear board
        board.clear()

        # Check all tiles are EMPTY
        for y in range(5):
            for x in range(5):
                assert board.get_tile(x, y) == Tile.EMPTY

    def test_clear_board_with_custom_tile(self):
        """Test clearing board to a specific tile type."""
        board = Board(5, 5)
        board.set_tile(2, 2, Tile.APPLE)

        board.clear(Tile.WALL)

        # Check all tiles are WALL
        for y in range(5):
            for x in range(5):
                assert board.get_tile(x, y) == Tile.WALL


class TestBoardRowColumnAccess:
    """Test row and column access methods."""

    def test_get_row_returns_correct_tiles(self):
        """Test getting an entire row."""
        board = Board(5, 5)
        board.set_tile(0, 2, Tile.SNAKE_HEAD)
        board.set_tile(1, 2, Tile.SNAKE_BODY)
        board.set_tile(2, 2, Tile.APPLE)

        row = board.get_row(2)

        assert len(row) == 5
        assert row[0] == Tile.SNAKE_HEAD
        assert row[1] == Tile.SNAKE_BODY
        assert row[2] == Tile.APPLE
        assert row[3] == Tile.EMPTY
        assert row[4] == Tile.EMPTY

    def test_get_column_returns_correct_tiles(self):
        """Test getting an entire column."""
        board = Board(5, 5)
        board.set_tile(2, 0, Tile.SNAKE_HEAD)
        board.set_tile(2, 1, Tile.SNAKE_BODY)
        board.set_tile(2, 2, Tile.APPLE)

        column = board.get_column(2)

        assert len(column) == 5
        assert column[0] == Tile.SNAKE_HEAD
        assert column[1] == Tile.SNAKE_BODY
        assert column[2] == Tile.APPLE
        assert column[3] == Tile.EMPTY
        assert column[4] == Tile.EMPTY

    def test_get_row_returns_copy(self):
        """Test that get_row returns a copy, not reference."""
        board = Board(5, 5)
        board.set_tile(2, 0, Tile.APPLE)

        row = board.get_row(0)
        row[2] = Tile.OBSTACLE

        # Original board should be unchanged
        assert board.get_tile(2, 0) == Tile.APPLE

    def test_get_column_returns_copy(self):
        """Test that get_column returns a copy, not reference."""
        board = Board(5, 5)
        board.set_tile(0, 2, Tile.APPLE)

        column = board.get_column(0)
        column[2] = Tile.OBSTACLE

        # Original board should be unchanged
        assert board.get_tile(0, 2) == Tile.APPLE

    def test_get_row_out_of_bounds(self):
        """Test that getting row with invalid index raises error."""
        board = Board(5, 5)

        with pytest.raises(BoardOutOfBoundsError):
            board.get_row(-1)

        with pytest.raises(BoardOutOfBoundsError):
            board.get_row(5)

    def test_get_column_out_of_bounds(self):
        """Test that getting column with invalid index raises error."""
        board = Board(5, 5)

        with pytest.raises(BoardOutOfBoundsError):
            board.get_column(-1)

        with pytest.raises(BoardOutOfBoundsError):
            board.get_column(5)


class TestBoardPerformance:
    """Test board performance characteristics."""

    def test_large_board_creation(self):
        """Test creating a large board doesn't fail."""
        board = Board(100, 100)
        assert board.width == 100
        assert board.height == 100

    def test_set_and_get_are_fast(self):
        """Test that set/get operations are O(1) - quick even on large boards."""
        board = Board(1000, 1000)

        # These should be instant (O(1))
        board.set_tile(999, 999, Tile.APPLE)
        assert board.get_tile(999, 999) == Tile.APPLE

        board.set_tile(0, 0, Tile.SNAKE_HEAD)
        assert board.get_tile(0, 0) == Tile.SNAKE_HEAD
