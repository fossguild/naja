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
from unittest.mock import Mock, patch
from src.ecs.systems.ui import SettingsApplicator


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

    def test_snapshot_critical_settings(self, applicator, mock_settings):
        """Test taking snapshot of critical settings."""
        applicator.snapshot_critical_settings(mock_settings)

        snapshot = applicator._settings_snapshot
        assert snapshot["cells_per_side"] == 30
        assert snapshot["obstacle_difficulty"] == "medium"
        assert snapshot["initial_speed"] == 5.0
        assert snapshot["number_of_apples"] == 1
        assert snapshot["electric_walls"] is False

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

    def test_get_critical_settings_list(self, applicator):
        """Test getting list of critical settings."""
        critical = applicator.get_critical_settings_list()

        assert "cells_per_side" in critical
        assert "obstacle_difficulty" in critical
        assert "initial_speed" in critical
        assert "number_of_apples" in critical
        assert "electric_walls" in critical
        assert len(critical) == 5

    @patch("pygame.mixer.music")
    def test_apply_settings_music_control(self, mock_music, applicator, mock_settings):
        """Test that music state is controlled by settings."""
        with (
            patch("old_code.entities.Obstacle"),
            patch("old_code.entities.Snake"),
            patch("old_code.entities.Apple"),
        ):
            # Test music on
            mock_settings.get = Mock(
                side_effect=lambda key: {
                    "cells_per_side": 30,
                    "background_music": True,
                    "obstacle_difficulty": "medium",
                    "initial_speed": 5.0,
                }.get(key)
            )
            mock_settings.validate_apples_count = Mock(return_value=1)

            applicator.apply_settings(mock_settings, reset_objects=False)
            mock_music.unpause.assert_called()

            # Reset mocks
            mock_music.reset_mock()

            # Test music off
            mock_settings.get = Mock(
                side_effect=lambda key: {
                    "cells_per_side": 30,
                    "background_music": False,
                    "obstacle_difficulty": "medium",
                    "initial_speed": 5.0,
                }.get(key)
            )

            applicator.apply_settings(mock_settings, reset_objects=False)
            mock_music.pause.assert_called()

    @patch("old_code.entities.Obstacle")
    @patch("old_code.entities.Snake")
    @patch("old_code.entities.Apple")
    @patch("old_code.constants.WINDOW_TITLE", "Naja")
    @patch("pygame.mixer.music")
    def test_apply_settings_grid_change_forces_reset(
        self,
        mock_music,
        mock_apple,
        mock_snake,
        mock_obstacle,
        applicator,
        mock_settings,
        mock_state,
        mock_config,
        mock_assets,
        mock_pygame_adapter,
    ):
        """Test that grid size change forces object reset."""
        # Setup: grid size changes from 20 to 30
        mock_state.grid_size = 20
        mock_config.get_optimal_grid_size = Mock(return_value=30)
        mock_obstacle.calculate_obstacles_from_difficulty = Mock(return_value=5)

        # Mock entity classes
        mock_snake_instance = Mock()
        mock_snake_instance.speed = 5.0
        mock_snake.return_value = mock_snake_instance

        mock_apple_instance = Mock()
        mock_apple_instance.ensure_valid_position = Mock()
        mock_apple.return_value = mock_apple_instance

        # Apply settings with reset_objects=False
        # Should be forced to True because grid changed
        applicator.apply_settings(mock_settings, reset_objects=False)

        # Verify window was resized
        mock_pygame_adapter.set_mode.assert_called()
        mock_assets.reload_fonts.assert_called()
        mock_state.update_dimensions.assert_called()

        # Verify objects were recreated (forced by grid change)
        mock_snake.assert_called()
        assert mock_state.snake == mock_snake_instance

    @patch("old_code.entities.Obstacle")
    @patch("old_code.entities.Snake")
    @patch("old_code.entities.Apple")
    @patch("pygame.mixer.music")
    def test_apply_settings_without_reset(
        self,
        mock_music,
        mock_apple,
        mock_snake,
        mock_obstacle,
        applicator,
        mock_settings,
        mock_state,
        mock_config,
    ):
        """Test applying settings without resetting objects."""
        # Grid size doesn't change
        mock_state.grid_size = 20
        mock_config.get_optimal_grid_size = Mock(return_value=20)
        mock_obstacle.calculate_obstacles_from_difficulty = Mock(return_value=5)

        applicator.apply_settings(mock_settings, reset_objects=False)

        # Verify objects were NOT recreated
        mock_snake.assert_not_called()
        mock_apple.assert_not_called()


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
