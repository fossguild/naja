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

"""Resize system tests."""

import pytest
from unittest.mock import Mock

from ecs.world import World
from ecs.board import Board
from ecs.systems.resize import ResizeSystem


@pytest.fixture
def board():
    """Create a standard board for testing."""
    return Board(width=800, height=800, cell_size=20)


@pytest.fixture
def world(board):
    """Create a world with board."""
    return World(board)


@pytest.fixture
def resize_system():
    """Create a ResizeSystem."""
    return ResizeSystem(max_dimension=800, min_cell_size=8)


@pytest.fixture
def resize_system_with_callback():
    """Create a ResizeSystem with mock callback."""
    callback = Mock()
    return (
        ResizeSystem(
            max_dimension=800, min_cell_size=8, asset_reload_callback=callback
        ),
        callback,
    )


class TestResizeSystemInitialization:
    """Test ResizeSystem initialization."""

    def test_system_created_successfully(self):
        """Test that ResizeSystem can be initialized."""
        system = ResizeSystem()
        assert system is not None

    def test_system_with_max_dimension(self):
        """Test system with custom max dimension."""
        system = ResizeSystem(max_dimension=1024)
        assert system.get_max_dimension() == 1024

    def test_system_with_min_cell_size(self):
        """Test system with custom min cell size."""
        system = ResizeSystem(min_cell_size=10)
        assert system.get_min_cell_size() == 10

    def test_system_with_callback(self):
        """Test system with asset reload callback."""
        callback = Mock()
        system = ResizeSystem(asset_reload_callback=callback)
        assert system._asset_reload_callback == callback

    def test_no_pending_resize_initially(self, resize_system):
        """Test no resize is pending initially."""
        assert resize_system.has_pending_resize() is False


class TestCellSizeCalculation:
    """Test cell size calculation."""

    def test_calculate_optimal_cell_size_normal(self, resize_system):
        """Test calculating optimal cell size."""
        # max_dimension = 800, cells_per_side = 40
        # cell_size = 800 / 40 = 20
        cell_size = resize_system.calculate_optimal_cell_size(40)
        assert cell_size == 20

    def test_calculate_optimal_cell_size_small_cells(self, resize_system):
        """Test with many small cells."""
        # max_dimension = 800, cells_per_side = 100
        # cell_size = 800 / 100 = 8 (at minimum)
        cell_size = resize_system.calculate_optimal_cell_size(100)
        assert cell_size == 8

    def test_calculate_optimal_cell_size_large_cells(self, resize_system):
        """Test with few large cells."""
        # max_dimension = 800, cells_per_side = 10
        # cell_size = 800 / 10 = 80
        cell_size = resize_system.calculate_optimal_cell_size(10)
        assert cell_size == 80

    def test_calculate_optimal_cell_size_enforces_minimum(self):
        """Test that minimum cell size is enforced."""
        system = ResizeSystem(max_dimension=800, min_cell_size=20)

        # request 200 cells per side would give 4px cells
        # but minimum is 20px, so should return 20
        cell_size = system.calculate_optimal_cell_size(200)
        assert cell_size == 20

    def test_calculate_optimal_cell_size_invalid_input(self, resize_system):
        """Test with invalid input (negative or zero)."""
        # should default to 10 cells
        cell_size = resize_system.calculate_optimal_cell_size(0)
        assert cell_size == 80  # 800 / 10

        cell_size = resize_system.calculate_optimal_cell_size(-5)
        assert cell_size == 80


class TestWindowSizeCalculation:
    """Test window size calculation."""

    def test_calculate_window_size_normal(self, resize_system):
        """Test calculating window size."""
        width, height = resize_system.calculate_window_size(20)

        # 800 / 20 = 40 cells, 40 * 20 = 800
        assert width == 800
        assert height == 800

    def test_calculate_window_size_small_cells(self, resize_system):
        """Test with small cells."""
        width, height = resize_system.calculate_window_size(8)

        # 800 / 8 = 100 cells, 100 * 8 = 800
        assert width == 800
        assert height == 800

    def test_calculate_window_size_large_cells(self, resize_system):
        """Test with large cells."""
        width, height = resize_system.calculate_window_size(80)

        # 800 / 80 = 10 cells, 10 * 80 = 800
        assert width == 800
        assert height == 800

    def test_calculate_window_size_not_exact_multiple(self, resize_system):
        """Test with cell size that's not exact divisor."""
        width, height = resize_system.calculate_window_size(30)

        # 800 / 30 = 26 cells (floor), 26 * 30 = 780
        assert width == 780
        assert height == 780

    def test_window_size_always_square(self, resize_system):
        """Test that window size is always square."""
        for cell_size in [8, 10, 16, 20, 25, 32, 40, 50]:
            width, height = resize_system.calculate_window_size(cell_size)
            assert width == height


class TestGridResize:
    """Test grid resize functionality."""

    def test_resize_grid_changes_dimensions(self, world, resize_system):
        """Test that resize updates board dimensions."""
        initial_cell_size = world.board.cell_size

        # resize to different cells_per_side
        result = resize_system.resize_grid(world, cells_per_side=20)

        assert result is True
        assert world.board.cell_size != initial_cell_size

    def test_resize_grid_no_change_if_same(self, world, resize_system):
        """Test no resize if dimensions would be the same."""
        initial_cell_size = world.board.cell_size
        initial_width = world.board.width

        # calculate cells_per_side for current dimensions
        cells_per_side = initial_width // initial_cell_size

        # request same size
        result = resize_system.resize_grid(world, cells_per_side)

        assert result is False
        assert world.board.cell_size == initial_cell_size

    def test_resize_grid_updates_cell_size(self, world, resize_system):
        """Test that cell size is updated."""
        resize_system.resize_grid(world, cells_per_side=20)

        # 800 / 20 = 40px per cell
        assert world.board.cell_size == 40

    def test_resize_grid_updates_width_height(self, world, resize_system):
        """Test that width and height are updated."""
        resize_system.resize_grid(world, cells_per_side=20)

        # should recalculate based on new cell size
        assert world.board.width == 800
        assert world.board.height == 800

    def test_resize_grid_triggers_callback(self):
        """Test that asset reload callback is triggered."""
        callback = Mock()
        system = ResizeSystem(asset_reload_callback=callback)

        board = Board(width=800, height=800, cell_size=20)
        world = World(board)

        system.resize_grid(world, cells_per_side=20)

        # callback should be called with new width
        callback.assert_called_once()
        args = callback.call_args[0]
        assert args[0] == 800

    def test_resize_grid_no_callback_if_not_set(self, world, resize_system):
        """Test resize works without callback."""
        # should not raise error even without callback
        result = resize_system.resize_grid(world, cells_per_side=20)
        assert result is True


class TestRequestResize:
    """Test resize request functionality."""

    def test_request_resize_sets_pending(self, resize_system):
        """Test that request_resize sets pending flag."""
        resize_system.request_resize(30)

        assert resize_system.has_pending_resize() is True

    def test_request_resize_stores_desired_cells(self, resize_system):
        """Test that desired cells are stored."""
        resize_system.request_resize(30)

        assert resize_system._desired_cells_per_side == 30

    def test_request_resize_enforces_minimum(self, resize_system):
        """Test that minimum cells_per_side is enforced."""
        resize_system.request_resize(5)  # below minimum

        # should be clamped to 10
        assert resize_system._desired_cells_per_side == 10

    def test_update_processes_pending_resize(self, world, resize_system):
        """Test that update processes pending resize."""
        initial_cell_size = world.board.cell_size

        resize_system.request_resize(20)
        assert resize_system.has_pending_resize() is True

        resize_system.update(world)

        # resize should be processed
        assert resize_system.has_pending_resize() is False
        assert world.board.cell_size != initial_cell_size

    def test_update_does_nothing_without_pending(self, world, resize_system):
        """Test update does nothing without pending resize."""
        initial_cell_size = world.board.cell_size

        resize_system.update(world)

        # no change
        assert world.board.cell_size == initial_cell_size

    def test_multiple_resize_requests(self, resize_system):
        """Test multiple resize requests (last one wins)."""
        resize_system.request_resize(20)
        resize_system.request_resize(30)
        resize_system.request_resize(40)

        # last request should be stored
        assert resize_system._desired_cells_per_side == 40


class TestAssetReloadCallback:
    """Test asset reload callback functionality."""

    def test_callback_called_on_resize(self, world):
        """Test callback is called when resize happens."""
        callback = Mock()
        system = ResizeSystem(asset_reload_callback=callback)

        system.resize_grid(world, cells_per_side=20)

        callback.assert_called_once()

    def test_callback_receives_new_width(self, world):
        """Test callback receives correct new width."""
        callback = Mock()
        system = ResizeSystem(max_dimension=800, asset_reload_callback=callback)

        system.resize_grid(world, cells_per_side=20)

        # 800 / 20 = 40px cells, width = 800
        callback.assert_called_once_with(800)

    def test_callback_not_called_if_no_change(self, world):
        """Test callback not called if dimensions don't change."""
        callback = Mock()
        system = ResizeSystem(asset_reload_callback=callback)

        # calculate current cells_per_side
        cells_per_side = world.board.width // world.board.cell_size

        # request same size (no change)
        system.resize_grid(world, cells_per_side)

        callback.assert_not_called()

    def test_set_asset_reload_callback(self, resize_system):
        """Test setting callback after initialization."""
        callback = Mock()
        resize_system.set_asset_reload_callback(callback)

        assert resize_system._asset_reload_callback == callback

    def test_clear_callback(self, world):
        """Test clearing callback."""
        callback = Mock()
        system = ResizeSystem(asset_reload_callback=callback)

        # clear callback
        system.set_asset_reload_callback(None)

        # resize should work without callback
        system.resize_grid(world, cells_per_side=20)
        callback.assert_not_called()


class TestValidation:
    """Test resize request validation."""

    def test_validate_resize_request_valid(self, resize_system):
        """Test validation of valid resize request."""
        is_valid, error = resize_system.validate_resize_request(20)

        assert is_valid is True
        assert error is None

    def test_validate_resize_request_too_small(self, resize_system):
        """Test validation fails for too small cells_per_side."""
        is_valid, error = resize_system.validate_resize_request(5)

        assert is_valid is False
        assert "at least 10" in error

    def test_validate_resize_request_below_min_cell_size(self):
        """Test validation fails if cell size would be too small."""
        system = ResizeSystem(max_dimension=800, min_cell_size=20)

        # requesting 100 cells would give 8px cells (below min 20px)
        is_valid, error = system.validate_resize_request(100)

        assert is_valid is False
        assert "below minimum" in error

    def test_validate_resize_request_window_too_small(self):
        """Test validation fails if window would be too small."""
        system = ResizeSystem(max_dimension=100, min_cell_size=8)

        # would result in very small window
        is_valid, error = system.validate_resize_request(10)

        assert is_valid is False
        assert "too small" in error.lower()


class TestGettersSetters:
    """Test getter and setter methods."""

    def test_get_set_max_dimension(self, resize_system):
        """Test getting and setting max dimension."""
        resize_system.set_max_dimension(1024)
        assert resize_system.get_max_dimension() == 1024

    def test_set_max_dimension_enforces_minimum(self, resize_system):
        """Test that minimum max_dimension is enforced."""
        resize_system.set_max_dimension(50)  # very small

        # should be clamped to minimum (100)
        assert resize_system.get_max_dimension() == 100

    def test_get_set_min_cell_size(self, resize_system):
        """Test getting and setting min cell size."""
        resize_system.set_min_cell_size(16)
        assert resize_system.get_min_cell_size() == 16

    def test_set_min_cell_size_enforces_minimum(self, resize_system):
        """Test that minimum min_cell_size is enforced."""
        resize_system.set_min_cell_size(2)  # very small

        # should be clamped to minimum (4)
        assert resize_system.get_min_cell_size() == 4

    def test_get_current_cells_per_side(self, world, resize_system):
        """Test getting current cells per side."""
        # board is 800x800 with 20px cells
        cells = resize_system.get_current_cells_per_side(world)

        assert cells == 40  # 800 / 20


class TestGridDimensions:
    """Test grid dimension calculations."""

    def test_calculate_grid_dimensions(self, resize_system):
        """Test calculating complete grid dimensions."""
        width_px, height_px, width_cells, height_cells = (
            resize_system.calculate_grid_dimensions(20)
        )

        assert width_px == 800
        assert height_px == 800
        assert width_cells == 40  # 800 / 20
        assert height_cells == 40

    def test_calculate_grid_dimensions_various_sizes(self, resize_system):
        """Test grid dimensions with various cell sizes."""
        test_cases = [
            (8, 800, 800, 100, 100),
            (10, 800, 800, 80, 80),
            (16, 800, 800, 50, 50),
            (20, 800, 800, 40, 40),
            (25, 800, 800, 32, 32),
            (40, 800, 800, 20, 20),
            (80, 800, 800, 10, 10),
        ]

        for cell_size, exp_w_px, exp_h_px, exp_w_cells, exp_h_cells in test_cases:
            w_px, h_px, w_cells, h_cells = resize_system.calculate_grid_dimensions(
                cell_size
            )

            assert w_px == exp_w_px
            assert h_px == exp_h_px
            assert w_cells == exp_w_cells
            assert h_cells == exp_h_cells


class TestIntegration:
    """Integration tests for ResizeSystem."""

    def test_full_resize_workflow(self, world):
        """Test complete resize workflow."""
        callback = Mock()
        system = ResizeSystem(max_dimension=800, asset_reload_callback=callback)

        initial_cell_size = world.board.cell_size

        # step 1: request resize
        system.request_resize(20)
        assert system.has_pending_resize() is True

        # step 2: process resize
        system.update(world)
        assert system.has_pending_resize() is False

        # step 3: verify changes
        assert world.board.cell_size != initial_cell_size
        assert world.board.cell_size == 40  # 800 / 20

        # step 4: verify callback
        callback.assert_called_once_with(800)

    def test_resize_with_validation(self, world, resize_system):
        """Test resize with validation check."""
        # validate before requesting
        is_valid, error = resize_system.validate_resize_request(30)
        assert is_valid is True

        # request and process
        resize_system.request_resize(30)
        resize_system.update(world)

        # verify result
        expected_cell_size = 800 // 30  # ~26px
        assert world.board.cell_size == expected_cell_size

    def test_multiple_resize_operations(self, world):
        """Test multiple resize operations in sequence."""
        callback = Mock()
        system = ResizeSystem(asset_reload_callback=callback)

        # first resize
        system.request_resize(20)
        system.update(world)
        first_cell_size = world.board.cell_size

        # second resize
        system.request_resize(40)
        system.update(world)
        second_cell_size = world.board.cell_size

        # third resize
        system.request_resize(10)
        system.update(world)
        third_cell_size = world.board.cell_size

        # all should be different
        assert first_cell_size != second_cell_size != third_cell_size

        # callback should be called 3 times
        assert callback.call_count == 3

    def test_resize_preserves_aspect_ratio(self, world, resize_system):
        """Test that resize maintains square window."""
        for cells_per_side in [10, 20, 30, 40, 50]:
            resize_system.resize_grid(world, cells_per_side)

            assert world.board.width == world.board.height

    def test_resize_maintains_grid_alignment(self, world, resize_system):
        """Test that dimensions remain multiples of cell size."""
        for cells_per_side in [10, 15, 20, 25, 30, 40, 50]:
            resize_system.resize_grid(world, cells_per_side)

            # width and height must be exact multiples of cell_size
            assert world.board.width % world.board.cell_size == 0
            assert world.board.height % world.board.cell_size == 0
