#!/usr/bin/env python3
#
#   Copyright (c) 2023, Monaco F. J. <monaco@usp.br>
#   Copyright (c) 2024, Felipe Diniz <lfelipediniz@usp.br>
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

"""Unit tests for command protocol."""

import pytest
from src.ecs.components.commands import (
    MoveCommand,
    PauseCommand,
    QuitCommand,
    OpenSettingsCommand,
    ToggleMusicCommand,
    RandomizePaletteCommand,
    ApplySettingsCommand,
)


class TestMoveCommand:
    """Tests for MoveCommand."""

    def test_valid_horizontal_movement(self):
        """Test creating valid horizontal move commands."""
        # right
        cmd = MoveCommand(dx=1, dy=0)
        assert cmd.dx == 1
        assert cmd.dy == 0

        # left
        cmd = MoveCommand(dx=-1, dy=0)
        assert cmd.dx == -1
        assert cmd.dy == 0

    def test_valid_vertical_movement(self):
        """Test creating valid vertical move commands."""
        # down
        cmd = MoveCommand(dx=0, dy=1)
        assert cmd.dx == 0
        assert cmd.dy == 1

        # up
        cmd = MoveCommand(dx=0, dy=-1)
        assert cmd.dx == 0
        assert cmd.dy == -1

    def test_invalid_zero_direction(self):
        """Test that (0, 0) direction is rejected."""
        with pytest.raises(ValueError, match="Direction cannot be \\(0, 0\\)"):
            MoveCommand(dx=0, dy=0)

    def test_invalid_diagonal_direction(self):
        """Test that diagonal directions are rejected."""
        with pytest.raises(
            ValueError, match="Direction must be horizontal or vertical"
        ):
            MoveCommand(dx=1, dy=1)

        with pytest.raises(
            ValueError, match="Direction must be horizontal or vertical"
        ):
            MoveCommand(dx=-1, dy=-1)

        with pytest.raises(
            ValueError, match="Direction must be horizontal or vertical"
        ):
            MoveCommand(dx=1, dy=-1)

        with pytest.raises(
            ValueError, match="Direction must be horizontal or vertical"
        ):
            MoveCommand(dx=-1, dy=1)

    def test_invalid_out_of_range(self):
        """Test that out-of-range values are rejected."""
        with pytest.raises(ValueError, match="Invalid direction"):
            MoveCommand(dx=2, dy=0)

        with pytest.raises(ValueError, match="Invalid direction"):
            MoveCommand(dx=0, dy=3)

        with pytest.raises(ValueError, match="Invalid direction"):
            MoveCommand(dx=-2, dy=0)

    def test_immutability(self):
        """Test that MoveCommand is immutable."""
        cmd = MoveCommand(dx=1, dy=0)
        with pytest.raises(Exception):  # FrozenInstanceError
            cmd.dx = -1  # type: ignore


class TestPauseCommand:
    """Tests for PauseCommand."""

    def test_creation(self):
        """Test creating a pause command."""
        cmd = PauseCommand()
        assert cmd is not None

    def test_immutability(self):
        """Test that PauseCommand is immutable."""
        cmd = PauseCommand()
        # Pause command has no fields, so just verify it's frozen
        assert cmd.__class__.__dataclass_params__.frozen is True  # type: ignore


class TestQuitCommand:
    """Tests for QuitCommand."""

    def test_creation(self):
        """Test creating a quit command."""
        cmd = QuitCommand()
        assert cmd is not None

    def test_immutability(self):
        """Test that QuitCommand is immutable."""
        cmd = QuitCommand()
        assert cmd.__class__.__dataclass_params__.frozen is True  # type: ignore


class TestOpenSettingsCommand:
    """Tests for OpenSettingsCommand."""

    def test_creation(self):
        """Test creating an open settings command."""
        cmd = OpenSettingsCommand()
        assert cmd is not None

    def test_immutability(self):
        """Test that OpenSettingsCommand is immutable."""
        cmd = OpenSettingsCommand()
        assert cmd.__class__.__dataclass_params__.frozen is True  # type: ignore


class TestToggleMusicCommand:
    """Tests for ToggleMusicCommand."""

    def test_creation(self):
        """Test creating a toggle music command."""
        cmd = ToggleMusicCommand()
        assert cmd is not None

    def test_immutability(self):
        """Test that ToggleMusicCommand is immutable."""
        cmd = ToggleMusicCommand()
        assert cmd.__class__.__dataclass_params__.frozen is True  # type: ignore


class TestRandomizePaletteCommand:
    """Tests for RandomizePaletteCommand."""

    def test_creation(self):
        """Test creating a randomize palette command."""
        cmd = RandomizePaletteCommand()
        assert cmd is not None

    def test_immutability(self):
        """Test that RandomizePaletteCommand is immutable."""
        cmd = RandomizePaletteCommand()
        assert cmd.__class__.__dataclass_params__.frozen is True  # type: ignore


class TestApplySettingsCommand:
    """Tests for ApplySettingsCommand."""

    def test_creation_without_reset(self):
        """Test creating apply settings command without reset."""
        cmd = ApplySettingsCommand(reset_objects=False)
        assert cmd.reset_objects is False

    def test_creation_with_reset(self):
        """Test creating apply settings command with reset."""
        cmd = ApplySettingsCommand(reset_objects=True)
        assert cmd.reset_objects is True

    def test_default_value(self):
        """Test that reset_objects defaults to False."""
        cmd = ApplySettingsCommand()
        assert cmd.reset_objects is False

    def test_immutability(self):
        """Test that ApplySettingsCommand is immutable."""
        cmd = ApplySettingsCommand(reset_objects=True)
        with pytest.raises(Exception):  # FrozenInstanceError
            cmd.reset_objects = False  # type: ignore


class TestCommandEquality:
    """Tests for command equality."""

    def test_move_command_equality(self):
        """Test that identical move commands are equal."""
        cmd1 = MoveCommand(dx=1, dy=0)
        cmd2 = MoveCommand(dx=1, dy=0)
        assert cmd1 == cmd2

    def test_move_command_inequality(self):
        """Test that different move commands are not equal."""
        cmd1 = MoveCommand(dx=1, dy=0)
        cmd2 = MoveCommand(dx=0, dy=1)
        assert cmd1 != cmd2

    def test_pause_command_equality(self):
        """Test that pause commands are equal."""
        cmd1 = PauseCommand()
        cmd2 = PauseCommand()
        assert cmd1 == cmd2

    def test_different_command_types_not_equal(self):
        """Test that different command types are not equal."""
        pause_cmd = PauseCommand()
        quit_cmd = QuitCommand()
        assert pause_cmd != quit_cmd


class TestCommandRepr:
    """Tests for command string representation."""

    def test_move_command_repr(self):
        """Test MoveCommand string representation."""
        cmd = MoveCommand(dx=1, dy=0)
        assert "MoveCommand" in repr(cmd)
        assert "dx=1" in repr(cmd)
        assert "dy=0" in repr(cmd)

    def test_pause_command_repr(self):
        """Test PauseCommand string representation."""
        cmd = PauseCommand()
        assert "PauseCommand" in repr(cmd)

    def test_apply_settings_command_repr(self):
        """Test ApplySettingsCommand string representation."""
        cmd = ApplySettingsCommand(reset_objects=True)
        assert "ApplySettingsCommand" in repr(cmd)
        assert "reset_objects=True" in repr(cmd)
