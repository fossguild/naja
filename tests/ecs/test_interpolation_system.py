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

"""Interpolation system tests."""

import pytest
from dataclasses import dataclass

from ecs.world import World
from ecs.board import Board
from ecs.systems.interpolation import InterpolationSystem


@dataclass
class InterpolationEntity:
    """Simple entity for testing interpolation."""

    x: int = 0
    y: int = 0
    target_x: int = 0
    target_y: int = 0
    alpha: float = 0.0
    wrapped_axis: str = "none"


@pytest.fixture
def board():
    """Create a standard board for testing."""
    return Board(width=600, height=400, cell_size=20)


@pytest.fixture
def world(board):
    """Create a world with board."""
    return World(board)


@pytest.fixture
def interpolation_system():
    """Create an InterpolationSystem."""
    return InterpolationSystem(electric_walls=True)


@pytest.fixture
def interpolation_system_no_walls():
    """Create an InterpolationSystem without electric walls."""
    return InterpolationSystem(electric_walls=False)


class TestInterpolationSystemInitialization:
    """Test InterpolationSystem initialization."""

    def test_system_created_successfully(self):
        """Test that InterpolationSystem can be initialized."""
        system = InterpolationSystem()
        assert system is not None

    def test_system_with_electric_walls(self):
        """Test system with electric walls enabled."""
        system = InterpolationSystem(electric_walls=True)
        assert system.get_electric_walls() is True

    def test_system_without_electric_walls(self):
        """Test system without electric walls."""
        system = InterpolationSystem(electric_walls=False)
        assert system.get_electric_walls() is False

    def test_set_electric_walls(self, interpolation_system):
        """Test changing electric walls setting."""
        interpolation_system.set_electric_walls(False)
        assert interpolation_system.get_electric_walls() is False

        interpolation_system.set_electric_walls(True)
        assert interpolation_system.get_electric_walls() is True


class TestAlphaCalculation:
    """Test interpolation alpha calculation."""

    def test_update_interpolation_advances_alpha(self, world, interpolation_system):
        """Test that alpha advances based on delta time."""
        # speed = 10 cells/sec -> move_interval = 100ms
        new_alpha, wrapped = interpolation_system.update_interpolation(
            world=world,
            entity_id=1,
            dt_ms=50.0,  # half of move interval
            speed=10.0,
            current_x=0,
            current_y=0,
            target_x=20,
            target_y=0,
            current_alpha=0.0,
        )

        # alpha should be 50/100 = 0.5
        assert new_alpha == pytest.approx(0.5)
        assert wrapped == "none"

    def test_alpha_accumulates_over_time(self, world, interpolation_system):
        """Test that alpha accumulates across multiple updates."""
        alpha = 0.0

        # first update: 25ms out of 100ms
        alpha, _ = interpolation_system.update_interpolation(
            world=world,
            entity_id=1,
            dt_ms=25.0,
            speed=10.0,
            current_x=0,
            current_y=0,
            target_x=20,
            target_y=0,
            current_alpha=alpha,
        )
        assert alpha == pytest.approx(0.25)

        # second update: another 25ms
        alpha, _ = interpolation_system.update_interpolation(
            world=world,
            entity_id=1,
            dt_ms=25.0,
            speed=10.0,
            current_x=0,
            current_y=0,
            target_x=20,
            target_y=0,
            current_alpha=alpha,
        )
        assert alpha == pytest.approx(0.5)

        # third update: another 25ms
        alpha, _ = interpolation_system.update_interpolation(
            world=world,
            entity_id=1,
            dt_ms=25.0,
            speed=10.0,
            current_x=0,
            current_y=0,
            target_x=20,
            target_y=0,
            current_alpha=alpha,
        )
        assert alpha == pytest.approx(0.75)

    def test_alpha_clamped_to_one(self, world, interpolation_system):
        """Test that alpha is clamped to 1.0 maximum."""
        # large delta time should clamp alpha to 1.0
        new_alpha, _ = interpolation_system.update_interpolation(
            world=world,
            entity_id=1,
            dt_ms=200.0,  # more than move interval
            speed=10.0,
            current_x=0,
            current_y=0,
            target_x=20,
            target_y=0,
            current_alpha=0.0,
        )

        assert new_alpha == 1.0

    def test_alpha_already_at_max(self, world, interpolation_system):
        """Test alpha when already at maximum."""
        new_alpha, _ = interpolation_system.update_interpolation(
            world=world,
            entity_id=1,
            dt_ms=50.0,
            speed=10.0,
            current_x=0,
            current_y=0,
            target_x=20,
            target_y=0,
            current_alpha=1.0,  # already at max
        )

        assert new_alpha == 1.0

    def test_no_interpolation_at_target(self, world, interpolation_system):
        """Test no interpolation when already at target."""
        new_alpha, wrapped = interpolation_system.update_interpolation(
            world=world,
            entity_id=1,
            dt_ms=50.0,
            speed=10.0,
            current_x=100,
            current_y=100,
            target_x=100,  # same as current
            target_y=100,  # same as current
            current_alpha=0.5,
        )

        assert new_alpha == 0.0
        assert wrapped == "none"

    def test_different_speeds_affect_alpha(self, world, interpolation_system):
        """Test that different speeds produce different alpha values."""
        # slow speed (5 cells/sec = 200ms per cell)
        slow_alpha, _ = interpolation_system.update_interpolation(
            world=world,
            entity_id=1,
            dt_ms=50.0,
            speed=5.0,
            current_x=0,
            current_y=0,
            target_x=20,
            target_y=0,
            current_alpha=0.0,
        )

        # fast speed (20 cells/sec = 50ms per cell)
        fast_alpha, _ = interpolation_system.update_interpolation(
            world=world,
            entity_id=2,
            dt_ms=50.0,
            speed=20.0,
            current_x=0,
            current_y=0,
            target_x=20,
            target_y=0,
            current_alpha=0.0,
        )

        # fast speed should have progressed more
        assert fast_alpha > slow_alpha
        assert slow_alpha == pytest.approx(0.25)
        assert fast_alpha == 1.0  # full movement in 50ms


class TestEdgeWrapping:
    """Test edge wrapping detection."""

    def test_no_wrapping_with_electric_walls(self, world, interpolation_system):
        """Test no wrapping detected when electric walls are on."""
        # even if positions would wrap, electric walls prevents it
        _, wrapped = interpolation_system.update_interpolation(
            world=world,
            entity_id=1,
            dt_ms=50.0,
            speed=10.0,
            current_x=0,
            current_y=0,
            target_x=580,  # near opposite edge
            target_y=0,
            current_alpha=0.0,
        )

        assert wrapped == "none"

    def test_wrapping_on_x_axis(self, world, interpolation_system_no_walls):
        """Test wrapping detection on X axis."""
        # board width = 600, moving from x=0 to x=580 wraps
        _, wrapped = interpolation_system_no_walls.update_interpolation(
            world=world,
            entity_id=1,
            dt_ms=50.0,
            speed=10.0,
            current_x=0,
            current_y=100,
            target_x=580,
            target_y=100,
            current_alpha=0.0,
        )

        assert wrapped == "x"

    def test_wrapping_on_y_axis(self, world, interpolation_system_no_walls):
        """Test wrapping detection on Y axis."""
        # board height = 400, moving from y=0 to y=380 wraps
        _, wrapped = interpolation_system_no_walls.update_interpolation(
            world=world,
            entity_id=1,
            dt_ms=50.0,
            speed=10.0,
            current_x=100,
            current_y=0,
            target_x=100,
            target_y=380,
            current_alpha=0.0,
        )

        assert wrapped == "y"

    def test_wrapping_on_both_axes(self, world, interpolation_system_no_walls):
        """Test wrapping detection on both axes."""
        _, wrapped = interpolation_system_no_walls.update_interpolation(
            world=world,
            entity_id=1,
            dt_ms=50.0,
            speed=10.0,
            current_x=0,
            current_y=0,
            target_x=580,
            target_y=380,
            current_alpha=0.0,
        )

        assert wrapped == "both"

    def test_no_wrapping_for_normal_movement(
        self, world, interpolation_system_no_walls
    ):
        """Test no wrapping for normal adjacent cell movement."""
        _, wrapped = interpolation_system_no_walls.update_interpolation(
            world=world,
            entity_id=1,
            dt_ms=50.0,
            speed=10.0,
            current_x=100,
            current_y=100,
            target_x=120,  # just one cell over
            target_y=100,
            current_alpha=0.0,
        )

        assert wrapped == "none"


class TestWillWrapAround:
    """Test the _will_wrap_around helper function."""

    def test_wrap_near_edge(self, interpolation_system):
        """Test wrapping detection near edge."""
        # distance = 580, limit = 600, diff = 20, grid_size = 20
        # abs(abs(0-580) - 600) = abs(580-600) = 20 <= 20 -> True
        result = interpolation_system._will_wrap_around(
            origin=0, dest=580, limit=600, grid_size=20
        )
        assert result is True

    def test_no_wrap_far_from_edge(self, interpolation_system):
        """Test no wrapping for movement far from edge."""
        # distance = 20, limit = 600, diff = 580
        # abs(abs(0-20) - 600) = abs(20-600) = 580 > 20 -> False
        result = interpolation_system._will_wrap_around(
            origin=0, dest=20, limit=600, grid_size=20
        )
        assert result is False

    def test_wrap_reverse_direction(self, interpolation_system):
        """Test wrapping in reverse direction."""
        # moving from 580 to 0 should also wrap
        result = interpolation_system._will_wrap_around(
            origin=580, dest=0, limit=600, grid_size=20
        )
        assert result is True


class TestInterpolatedPositionCalculation:
    """Test smooth position calculation."""

    def test_linear_interpolation_no_wrap(self, world, interpolation_system):
        """Test normal linear interpolation without wrapping."""
        draw_x, draw_y = interpolation_system.calculate_interpolated_position(
            world=world,
            current_x=0,
            current_y=0,
            target_x=100,
            target_y=100,
            alpha=0.5,
            wrapped_axis="none",
        )

        # should be halfway between current and target
        assert draw_x == pytest.approx(50.0)
        assert draw_y == pytest.approx(50.0)

    def test_interpolation_with_x_wrap(self, world, interpolation_system):
        """Test interpolation with X axis wrapping."""
        draw_x, draw_y = interpolation_system.calculate_interpolated_position(
            world=world,
            current_x=0,
            current_y=100,
            target_x=580,
            target_y=100,
            alpha=0.5,
            wrapped_axis="x",
            velocity_x=1,  # moving right
            velocity_y=0,
        )

        # X should use velocity-based calculation
        # draw_x = 0 + (1 * 20 * 0.5) = 10
        assert draw_x == pytest.approx(10.0)
        # Y should be normal interpolation (no change)
        assert draw_y == pytest.approx(100.0)

    def test_interpolation_with_y_wrap(self, world, interpolation_system):
        """Test interpolation with Y axis wrapping."""
        draw_x, draw_y = interpolation_system.calculate_interpolated_position(
            world=world,
            current_x=100,
            current_y=0,
            target_x=100,
            target_y=380,
            alpha=0.5,
            wrapped_axis="y",
            velocity_x=0,
            velocity_y=1,  # moving down
        )

        # X should be normal (no change)
        assert draw_x == pytest.approx(100.0)
        # Y should use velocity-based calculation
        # draw_y = 0 + (1 * 20 * 0.5) = 10
        assert draw_y == pytest.approx(10.0)

    def test_interpolation_with_both_wrap(self, world, interpolation_system):
        """Test interpolation with both axes wrapping."""
        draw_x, draw_y = interpolation_system.calculate_interpolated_position(
            world=world,
            current_x=0,
            current_y=0,
            target_x=580,
            target_y=380,
            alpha=0.5,
            wrapped_axis="both",
            velocity_x=1,
            velocity_y=1,
        )

        # both should use velocity-based calculation
        assert draw_x == pytest.approx(10.0)
        assert draw_y == pytest.approx(10.0)

    def test_interpolation_at_alpha_zero(self, world, interpolation_system):
        """Test interpolation at alpha = 0 (start)."""
        draw_x, draw_y = interpolation_system.calculate_interpolated_position(
            world=world,
            current_x=100,
            current_y=200,
            target_x=120,
            target_y=220,
            alpha=0.0,
            wrapped_axis="none",
        )

        # should be at current position
        assert draw_x == pytest.approx(100.0)
        assert draw_y == pytest.approx(200.0)

    def test_interpolation_at_alpha_one(self, world, interpolation_system):
        """Test interpolation at alpha = 1 (end)."""
        draw_x, draw_y = interpolation_system.calculate_interpolated_position(
            world=world,
            current_x=100,
            current_y=200,
            target_x=120,
            target_y=220,
            alpha=1.0,
            wrapped_axis="none",
        )

        # should be at target position
        assert draw_x == pytest.approx(120.0)
        assert draw_y == pytest.approx(220.0)

    def test_interpolation_negative_velocity(self, world, interpolation_system):
        """Test interpolation with negative velocity (moving left/up)."""
        draw_x, draw_y = interpolation_system.calculate_interpolated_position(
            world=world,
            current_x=580,
            current_y=380,
            target_x=0,
            target_y=0,
            alpha=0.5,
            wrapped_axis="both",
            velocity_x=-1,  # moving left
            velocity_y=-1,  # moving up
        )

        # velocity-based: 580 + (-1 * 20 * 0.5) = 570
        assert draw_x == pytest.approx(570.0)
        assert draw_y == pytest.approx(370.0)


class TestResetInterpolation:
    """Test interpolation reset."""

    def test_reset_to_default(self, interpolation_system):
        """Test resetting interpolation to default."""
        alpha, wrapped = interpolation_system.reset_interpolation()

        assert alpha == 0.0
        assert wrapped == "none"

    def test_reset_with_custom_alpha(self, interpolation_system):
        """Test resetting with custom alpha value."""
        alpha, wrapped = interpolation_system.reset_interpolation(alpha=0.5)

        assert alpha == 0.5
        assert wrapped == "none"


class TestIntegration:
    """Integration tests for InterpolationSystem."""

    def test_full_movement_cycle(self, world, interpolation_system_no_walls):
        """Test complete movement from one cell to another."""
        alpha = 0.0
        current_x, current_y = 100, 100
        target_x, target_y = 120, 100

        # first update: 25% progress
        alpha, wrapped = interpolation_system_no_walls.update_interpolation(
            world=world,
            entity_id=1,
            dt_ms=25.0,
            speed=10.0,
            current_x=current_x,
            current_y=current_y,
            target_x=target_x,
            target_y=target_y,
            current_alpha=alpha,
        )
        draw_x, draw_y = interpolation_system_no_walls.calculate_interpolated_position(
            world=world,
            current_x=current_x,
            current_y=current_y,
            target_x=target_x,
            target_y=target_y,
            alpha=alpha,
            wrapped_axis=wrapped,
        )
        assert alpha == pytest.approx(0.25)
        assert draw_x == pytest.approx(105.0)

        # second update: 50% progress
        alpha, wrapped = interpolation_system_no_walls.update_interpolation(
            world=world,
            entity_id=1,
            dt_ms=25.0,
            speed=10.0,
            current_x=current_x,
            current_y=current_y,
            target_x=target_x,
            target_y=target_y,
            current_alpha=alpha,
        )
        draw_x, draw_y = interpolation_system_no_walls.calculate_interpolated_position(
            world=world,
            current_x=current_x,
            current_y=current_y,
            target_x=target_x,
            target_y=target_y,
            alpha=alpha,
            wrapped_axis=wrapped,
        )
        assert alpha == pytest.approx(0.5)
        assert draw_x == pytest.approx(110.0)

        # third update: 75% progress
        alpha, wrapped = interpolation_system_no_walls.update_interpolation(
            world=world,
            entity_id=1,
            dt_ms=25.0,
            speed=10.0,
            current_x=current_x,
            current_y=current_y,
            target_x=target_x,
            target_y=target_y,
            current_alpha=alpha,
        )
        draw_x, draw_y = interpolation_system_no_walls.calculate_interpolated_position(
            world=world,
            current_x=current_x,
            current_y=current_y,
            target_x=target_x,
            target_y=target_y,
            alpha=alpha,
            wrapped_axis=wrapped,
        )
        assert alpha == pytest.approx(0.75)
        assert draw_x == pytest.approx(115.0)

        # fourth update: 100% progress (reached target)
        alpha, wrapped = interpolation_system_no_walls.update_interpolation(
            world=world,
            entity_id=1,
            dt_ms=25.0,
            speed=10.0,
            current_x=current_x,
            current_y=current_y,
            target_x=target_x,
            target_y=target_y,
            current_alpha=alpha,
        )
        draw_x, draw_y = interpolation_system_no_walls.calculate_interpolated_position(
            world=world,
            current_x=current_x,
            current_y=current_y,
            target_x=target_x,
            target_y=target_y,
            alpha=alpha,
            wrapped_axis=wrapped,
        )
        assert alpha == 1.0
        assert draw_x == pytest.approx(120.0)  # at target

    def test_wrapping_movement_cycle(self, world, interpolation_system_no_walls):
        """Test movement with edge wrapping."""
        alpha = 0.0
        current_x, current_y = 0, 100
        target_x, target_y = 580, 100

        # update with wrapping
        alpha, wrapped = interpolation_system_no_walls.update_interpolation(
            world=world,
            entity_id=1,
            dt_ms=50.0,
            speed=10.0,
            current_x=current_x,
            current_y=current_y,
            target_x=target_x,
            target_y=target_y,
            current_alpha=alpha,
        )

        # should detect X wrapping
        assert wrapped == "x"
        assert alpha == pytest.approx(0.5)

        # calculate interpolated position
        draw_x, draw_y = interpolation_system_no_walls.calculate_interpolated_position(
            world=world,
            current_x=current_x,
            current_y=current_y,
            target_x=target_x,
            target_y=target_y,
            alpha=alpha,
            wrapped_axis=wrapped,
            velocity_x=-1,  # wrapping left
            velocity_y=0,
        )

        # should use velocity-based calculation
        # draw_x = 0 + (-1 * 20 * 0.5) = -10 (off left edge)
        assert draw_x == pytest.approx(-10.0)
        assert draw_y == pytest.approx(100.0)

    def test_electric_walls_prevents_wrapping(self, world, interpolation_system):
        """Test that electric walls prevent wrapping detection."""
        # even with edge positions, should not wrap
        alpha, wrapped = interpolation_system.update_interpolation(
            world=world,
            entity_id=1,
            dt_ms=50.0,
            speed=10.0,
            current_x=0,
            current_y=0,
            target_x=580,
            target_y=380,
            current_alpha=0.0,
        )

        assert wrapped == "none"  # electric walls prevent wrapping

        # positions should use normal linear interpolation
        draw_x, draw_y = interpolation_system.calculate_interpolated_position(
            world=world,
            current_x=0,
            current_y=0,
            target_x=580,
            target_y=380,
            alpha=alpha,
            wrapped_axis=wrapped,
        )

        # normal linear interpolation
        assert draw_x == pytest.approx(290.0)  # midpoint
        assert draw_y == pytest.approx(190.0)  # midpoint
