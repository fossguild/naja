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

"""Tests for settings application system."""

import pytest
from unittest.mock import Mock
from ecs.systems.ui import SettingsApplicator


class TestSettingsApplicator:
    """Tests for SettingsApplicator class."""

    @pytest.fixture
    def mock_pygame_adapter(self):
        """Create mock pygame adapter."""
        adapter = Mock()
        adapter.set_mode = Mock(return_value=Mock())
        adapter.set_caption = Mock()
        return adapter

    @pytest.fixture
    def mock_state(self):
        """Create mock game state."""
        state = Mock()
        state.grid_size = 20
        state.width = 800
        state.height = 600
        state.arena = Mock()
        state.update_dimensions = Mock()
        state.snake = Mock()
        state.obstacles = []
        state.apples = []
        state.create_obstacles_constructively = Mock()
        return state

    @pytest.fixture
    def mock_assets(self):
        """Create mock assets."""
        assets = Mock()
        assets.reload_fonts = Mock()
        return assets

    @pytest.fixture
    def mock_config(self):
        """Create mock config."""
        config = Mock()
        config.get_optimal_grid_size = Mock(return_value=20)
        config.calculate_window_size = Mock(return_value=(800, 600))
        return config

    @pytest.fixture
    def mock_settings(self):
        """Create mock settings."""
        settings = Mock()
        settings.get = Mock(
            side_effect=lambda key: {
                "cells_per_side": 30,
                "obstacle_difficulty": "medium",
                "initial_speed": 5.0,
                "number_of_apples": 1,
                "electric_walls": False,
                "background_music": True,
            }.get(key)
        )
        settings.validate_apples_count = Mock(return_value=1)
        return settings

    @pytest.fixture
    def applicator(self, mock_pygame_adapter, mock_state, mock_assets, mock_config):
        """Create SettingsApplicator instance."""
        return SettingsApplicator(
            mock_pygame_adapter,
            mock_state,
            mock_assets,
            mock_config,
        )

    def test_initialization(self, applicator, mock_pygame_adapter, mock_state):
        """Test that applicator initializes correctly."""
        assert applicator._pygame_adapter == mock_pygame_adapter
        assert applicator._state == mock_state
        assert applicator._settings_snapshot == {}

    def test_needs_reset_without_snapshot(self, applicator, mock_settings):
        """Test needs_reset returns False without snapshot."""
        assert applicator.needs_reset(mock_settings) is False

    def test_needs_reset_no_changes(self, applicator, mock_settings):
        """Test needs_reset returns False when no critical settings changed."""
        applicator.snapshot_critical_settings(mock_settings)
        assert applicator.needs_reset(mock_settings) is False

    def test_needs_reset_with_changes(self, applicator, mock_settings):
        """Test needs_reset returns True when critical settings changed."""
        # Take snapshot
        applicator.snapshot_critical_settings(mock_settings)

        # Change a critical setting
        mock_settings.get = Mock(
            side_effect=lambda key: {
                "cells_per_side": 40,  # Changed!
                "obstacle_difficulty": "medium",
                "initial_speed": 5.0,
                "number_of_apples": 1,
                "electric_walls": False,
                "background_music": True,
            }.get(key)
        )

        assert applicator.needs_reset(mock_settings) is True


class TestSettingsApplicatorIntegration:
    """Integration tests for SettingsApplicator."""

    def test_critical_settings_snapshot_and_detection(self):
        """Test snapshot and needs_reset detection work together."""
        # Setup minimal mocks
        pygame_adapter = Mock()
        state = Mock()
        state.grid_size = 20
        assets = Mock()
        config = Mock()

        applicator = SettingsApplicator(pygame_adapter, state, assets, config)

        # Create settings mock
        settings = Mock()
        settings.get = Mock(
            side_effect=lambda key: {
                "cells_per_side": 30,
                "obstacle_difficulty": "medium",
                "initial_speed": 5.0,
                "number_of_apples": 1,
                "electric_walls": False,
            }.get(key)
        )

        # Take snapshot
        applicator.snapshot_critical_settings(settings)

        # No changes - should not need reset
        assert applicator.needs_reset(settings) is False

        # Change a critical setting
        settings.get = Mock(
            side_effect=lambda key: {
                "cells_per_side": 40,  # Changed!
                "obstacle_difficulty": "medium",
                "initial_speed": 5.0,
                "number_of_apples": 1,
                "electric_walls": False,
            }.get(key)
        )

        # Should need reset now
        assert applicator.needs_reset(settings) is True
