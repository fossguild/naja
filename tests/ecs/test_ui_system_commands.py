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

"""Unit tests for UISystem command generation."""

import pytest
from unittest.mock import Mock
import pygame

from src.ecs.systems.ui import UISystem, CommandConverter
from src.ecs.components.commands import (
    MoveCommand,
    PauseCommand,
    QuitCommand,
    OpenSettingsCommand,
    ToggleMusicCommand,
    RandomizePaletteCommand,
)


@pytest.fixture
def mock_renderer():
    """Create a mock renderer."""
    return Mock()


@pytest.fixture
def mock_assets():
    """Create a mock assets system."""
    return Mock()


@pytest.fixture
def ui_system(mock_renderer, mock_assets):
    """Create a UISystem instance for testing."""
    return UISystem(
        renderer=mock_renderer,
        assets=mock_assets,
        get_current_direction=lambda: (1, 0),  # moving right
    )


class TestUISystemCommandGeneration:
    """Tests for UISystem.handle_in_game_event()."""

    def test_quit_event_generates_quit_command(self, ui_system):
        """Test that QUIT event generates QuitCommand."""
        event = pygame.event.Event(pygame.QUIT)
        commands = ui_system.handle_in_game_event(event)

        assert len(commands) == 1
        assert isinstance(commands[0], QuitCommand)

    def test_quit_key_generates_quit_command(self, ui_system):
        """Test that Q key generates QuitCommand."""
        event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_q)
        commands = ui_system.handle_in_game_event(event)

        assert len(commands) == 1
        assert isinstance(commands[0], QuitCommand)

    def test_pause_key_generates_pause_command(self, ui_system):
        """Test that P key generates PauseCommand."""
        event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_p)
        commands = ui_system.handle_in_game_event(event)

        assert len(commands) == 1
        assert isinstance(commands[0], PauseCommand)

    def test_menu_keys_generate_open_settings_command(self, ui_system):
        """Test that M and ESCAPE keys generate OpenSettingsCommand."""
        # Test M key
        event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_m)
        commands = ui_system.handle_in_game_event(event)
        assert len(commands) == 1
        assert isinstance(commands[0], OpenSettingsCommand)

        # Test ESCAPE key
        event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE)
        commands = ui_system.handle_in_game_event(event)
        assert len(commands) == 1
        assert isinstance(commands[0], OpenSettingsCommand)

    def test_music_toggle_key_generates_command(self, ui_system):
        """Test that N key generates ToggleMusicCommand."""
        event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_n)
        commands = ui_system.handle_in_game_event(event)

        assert len(commands) == 1
        assert isinstance(commands[0], ToggleMusicCommand)

    def test_palette_randomize_key_generates_command(self, ui_system):
        """Test that C key generates RandomizePaletteCommand."""
        event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_c)
        commands = ui_system.handle_in_game_event(event)

        assert len(commands) == 1
        assert isinstance(commands[0], RandomizePaletteCommand)

    def test_arrow_down_generates_move_command(self, ui_system):
        """Test that DOWN arrow generates MoveCommand."""
        event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_DOWN)
        commands = ui_system.handle_in_game_event(event)

        assert len(commands) == 1
        assert isinstance(commands[0], MoveCommand)
        assert commands[0].dx == 0
        assert commands[0].dy == 1

    def test_arrow_up_generates_move_command(self, ui_system):
        """Test that UP arrow generates MoveCommand."""
        event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_UP)
        commands = ui_system.handle_in_game_event(event)

        assert len(commands) == 1
        assert isinstance(commands[0], MoveCommand)
        assert commands[0].dx == 0
        assert commands[0].dy == -1

    def test_arrow_right_generates_move_command(self, ui_system):
        """Test that RIGHT arrow generates MoveCommand."""
        event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RIGHT)
        commands = ui_system.handle_in_game_event(event)

        assert len(commands) == 1
        assert isinstance(commands[0], MoveCommand)
        assert commands[0].dx == 1
        assert commands[0].dy == 0

    def test_arrow_left_generates_move_command(self, mock_renderer, mock_assets):
        """Test that LEFT arrow generates MoveCommand."""
        # Create UISystem with snake moving up (so left is valid)
        ui_system = UISystem(
            renderer=mock_renderer,
            assets=mock_assets,
            get_current_direction=lambda: (0, -1),  # moving up
        )

        event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_LEFT)
        commands = ui_system.handle_in_game_event(event)

        assert len(commands) == 1
        assert isinstance(commands[0], MoveCommand)
        assert commands[0].dx == -1
        assert commands[0].dy == 0

    def test_wasd_keys_generate_move_commands(self, mock_renderer, mock_assets):
        """Test that WASD keys generate MoveCommands."""
        # Create UISystem with no current direction (all moves valid)
        ui_system = UISystem(
            renderer=mock_renderer,
            assets=mock_assets,
            get_current_direction=lambda: (0, 0),  # no movement yet
        )

        # W = up
        event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_w)
        commands = ui_system.handle_in_game_event(event)
        assert len(commands) == 1
        assert isinstance(commands[0], MoveCommand)
        assert (commands[0].dx, commands[0].dy) == (0, -1)

        # A = left
        event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_a)
        commands = ui_system.handle_in_game_event(event)
        assert len(commands) == 1
        assert isinstance(commands[0], MoveCommand)
        assert (commands[0].dx, commands[0].dy) == (-1, 0)

        # S = down
        event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_s)
        commands = ui_system.handle_in_game_event(event)
        assert len(commands) == 1
        assert isinstance(commands[0], MoveCommand)
        assert (commands[0].dx, commands[0].dy) == (0, 1)

        # D = right
        event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_d)
        commands = ui_system.handle_in_game_event(event)
        assert len(commands) == 1
        assert isinstance(commands[0], MoveCommand)
        assert (commands[0].dx, commands[0].dy) == (1, 0)

    def test_180_degree_turn_prevention_horizontal(self, mock_renderer, mock_assets):
        """Test that 180° turns are prevented when moving horizontally."""
        # Snake moving right (1, 0)
        ui_system = UISystem(
            renderer=mock_renderer,
            assets=mock_assets,
            get_current_direction=lambda: (1, 0),
        )

        # Try to move left (opposite direction) - should be ignored
        event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_LEFT)
        commands = ui_system.handle_in_game_event(event)
        assert len(commands) == 0  # no command generated

        # Move up should work
        event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_UP)
        commands = ui_system.handle_in_game_event(event)
        assert len(commands) == 1
        assert isinstance(commands[0], MoveCommand)

    def test_180_degree_turn_prevention_vertical(self, mock_renderer, mock_assets):
        """Test that 180° turns are prevented when moving vertically."""
        # Snake moving down (0, 1)
        ui_system = UISystem(
            renderer=mock_renderer,
            assets=mock_assets,
            get_current_direction=lambda: (0, 1),
        )

        # Try to move up (opposite direction) - should be ignored
        event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_UP)
        commands = ui_system.handle_in_game_event(event)
        assert len(commands) == 0  # no command generated

        # Move right should work
        event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RIGHT)
        commands = ui_system.handle_in_game_event(event)
        assert len(commands) == 1
        assert isinstance(commands[0], MoveCommand)

    def test_no_direction_callback_defaults_to_allow_all(
        self, mock_renderer, mock_assets
    ):
        """Test that without direction callback, all moves are allowed."""
        ui_system = UISystem(
            renderer=mock_renderer,
            assets=mock_assets,
            get_current_direction=None,  # no callback
        )

        # All directions should be allowed
        event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_UP)
        commands = ui_system.handle_in_game_event(event)
        assert len(commands) == 1

        event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_DOWN)
        commands = ui_system.handle_in_game_event(event)
        assert len(commands) == 1

    def test_unrecognized_event_returns_empty_list(self, ui_system):
        """Test that unrecognized events return empty command list."""
        # Random key
        event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_x)
        commands = ui_system.handle_in_game_event(event)
        assert len(commands) == 0

        # Mouse event
        event = pygame.event.Event(pygame.MOUSEMOTION, pos=(100, 100))
        commands = ui_system.handle_in_game_event(event)
        assert len(commands) == 0

    def test_keyup_event_returns_empty_list(self, ui_system):
        """Test that KEYUP events are ignored."""
        event = pygame.event.Event(pygame.KEYUP, key=pygame.K_UP)
        commands = ui_system.handle_in_game_event(event)
        assert len(commands) == 0


class TestCommandConverterDirectionValidation:
    """Tests for CommandConverter._is_direction_valid()."""

    @pytest.fixture
    def command_converter(self):
        """Create a CommandConverter instance for testing."""
        return CommandConverter(get_current_direction=lambda: (1, 0))

    def test_horizontal_movement_valid(self, command_converter):
        """Test that horizontal movement is valid when not opposite."""
        # Moving right, try to move right again (valid)
        assert command_converter._is_direction_valid(1, 0, 1, 0) is True

        # Moving right, try to move left (invalid - 180° turn)
        assert command_converter._is_direction_valid(-1, 0, 1, 0) is False

    def test_vertical_movement_valid(self, command_converter):
        """Test that vertical movement is valid when not opposite."""
        # Moving down, try to move down again (valid)
        assert command_converter._is_direction_valid(0, 1, 0, 1) is True

        # Moving down, try to move up (invalid - 180° turn)
        assert command_converter._is_direction_valid(0, -1, 0, 1) is False

    def test_perpendicular_movement_always_valid(self, command_converter):
        """Test that perpendicular movement is always valid."""
        # Moving right, can turn up or down
        assert command_converter._is_direction_valid(0, 1, 1, 0) is True
        assert command_converter._is_direction_valid(0, -1, 1, 0) is True

        # Moving up, can turn left or right
        assert command_converter._is_direction_valid(1, 0, 0, -1) is True
        assert command_converter._is_direction_valid(-1, 0, 0, -1) is True

    def test_no_current_direction_allows_any(self, command_converter):
        """Test that with no current direction, any direction is valid."""
        # No movement (0, 0) should allow any direction
        assert command_converter._is_direction_valid(1, 0, 0, 0) is True
        assert command_converter._is_direction_valid(-1, 0, 0, 0) is True
        assert command_converter._is_direction_valid(0, 1, 0, 0) is True
        assert command_converter._is_direction_valid(0, -1, 0, 0) is True
