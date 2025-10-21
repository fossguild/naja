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

"""Interpolation system for smooth movement rendering.

This system calculates interpolation values for smooth rendering between
discrete grid positions. It handles edge wrapping detection and updates
the Interpolation component used by the RenderSystem.
"""

from __future__ import annotations

from src.ecs.systems.base_system import BaseSystem
from src.ecs.world import World


class InterpolationSystem(BaseSystem):
    """System for calculating smooth movement interpolation.

    Reads: Position (current, target), Velocity, Speed, ElectricWalls setting
    Writes: Interpolation (alpha, wrapped_axis)
    Queries: entities with Position, Velocity, and Interpolation components

    Responsibilities:
    - Calculate interpolation alpha based on delta time and speed
    - Detect edge wrapping for special rendering handling
    - Update Interpolation component for RenderSystem
    - Clamp alpha to valid range [0.0, 1.0]
    - Handle both snake head and tail interpolation

    Note: This system runs before RenderSystem to prepare smooth positions.
    """

    def __init__(self, electric_walls: bool = True):
        """Initialize the InterpolationSystem.

        Args:
            electric_walls: Whether walls are electric (no wrapping). Can be updated.
        """
        self._electric_walls = electric_walls

    def update(self, world: World) -> None:
        """Update interpolation values for all entities with movement.

        This method calculates smooth positions between grid cells based on
        delta time and entity speed.

        Args:
            world: ECS world containing entities and components
        """
        from src.ecs.entities.entity import EntityType

        # update interpolation for all snakes
        snakes = world.registry.query_by_type_and_components(
            EntityType.SNAKE, "position", "interpolation"
        )

        for _, snake in snakes.items():
            # for now, just keep alpha at 0 (no interpolation)
            # this makes the snake draw at exact grid positions
            snake.interpolation.alpha = 0.0
            snake.interpolation.wrapped_axis = "none"

    def update_interpolation(
        self,
        world: World,
        entity_id: int,
        dt_ms: float,
        speed: float,
        current_x: int,
        current_y: int,
        target_x: int,
        target_y: int,
        current_alpha: float = 0.0,
    ) -> tuple[float, str]:
        """Calculate interpolation alpha and detect edge wrapping.

        Args:
            world: ECS world
            entity_id: Entity to update interpolation for
            dt_ms: Delta time in milliseconds
            speed: Entity movement speed (cells per second)
            current_x: Current X position (grid-aligned)
            current_y: Current Y position (grid-aligned)
            target_x: Target X position (grid-aligned)
            target_y: Target Y position (grid-aligned)
            current_alpha: Current interpolation alpha [0.0, 1.0]

        Returns:
            Tuple of (new_alpha, wrapped_axis)
            - new_alpha: Updated interpolation factor [0.0, 1.0]
            - wrapped_axis: "none", "x", "y", or "both"
        """
        # if already at target, no interpolation needed
        if current_x == target_x and current_y == target_y:
            return 0.0, "none"

        # calculate how much time one grid cell movement takes
        move_interval_ms = 1000.0 / speed

        # advance interpolation based on delta time
        new_alpha = current_alpha + (dt_ms / move_interval_ms)

        # clamp to valid range
        new_alpha = min(1.0, max(0.0, new_alpha))

        # detect edge wrapping if walls are not electric
        wrapped_axis = self._detect_wrapping(
            world, current_x, current_y, target_x, target_y
        )

        return new_alpha, wrapped_axis

    def calculate_interpolated_position(
        self,
        world: World,
        current_x: int,
        current_y: int,
        target_x: int,
        target_y: int,
        alpha: float,
        wrapped_axis: str,
        velocity_x: int = 0,
        velocity_y: int = 0,
    ) -> tuple[float, float]:
        """Calculate the smooth interpolated position for rendering.

        Args:
            world: ECS world
            current_x: Current X position (grid-aligned)
            current_y: Current Y position (grid-aligned)
            target_x: Target X position (grid-aligned)
            target_y: Target Y position (grid-aligned)
            alpha: Interpolation factor [0.0, 1.0]
            wrapped_axis: "none", "x", "y", or "both"
            velocity_x: X velocity direction (-1, 0, or 1)
            velocity_y: Y velocity direction (-1, 0, or 1)

        Returns:
            Tuple of (draw_x, draw_y) - smooth positions for rendering
        """
        board = world.board
        grid_size = board.cell_size

        # calculate X position
        if "x" in wrapped_axis or wrapped_axis == "both":
            # wrapping on X axis - use velocity to continue in same direction
            draw_x = current_x + (velocity_x * grid_size * alpha)
        else:
            # normal linear interpolation
            draw_x = current_x + ((target_x - current_x) * alpha)

        # calculate Y position
        if "y" in wrapped_axis or wrapped_axis == "both":
            # wrapping on Y axis - use velocity to continue in same direction
            draw_y = current_y + (velocity_y * grid_size * alpha)
        else:
            # normal linear interpolation
            draw_y = current_y + ((target_y - current_y) * alpha)

        return draw_x, draw_y

    def reset_interpolation(self, alpha: float = 0.0) -> tuple[float, str]:
        """Reset interpolation to initial state.

        Args:
            alpha: Initial alpha value (default 0.0)

        Returns:
            Tuple of (alpha, wrapped_axis)
        """
        return alpha, "none"

    def set_electric_walls(self, electric_walls: bool) -> None:
        """Update electric walls setting.

        Args:
            electric_walls: Whether walls are electric (no wrapping)
        """
        self._electric_walls = electric_walls

    def get_electric_walls(self) -> bool:
        """Get electric walls setting.

        Returns:
            True if walls are electric, False if wrapping is allowed
        """
        return self._electric_walls

    def _detect_wrapping(
        self,
        world: World,
        current_x: int,
        current_y: int,
        target_x: int,
        target_y: int,
    ) -> str:
        """Detect if movement will wrap around edges.

        Args:
            world: ECS world
            current_x: Current X position
            current_y: Current Y position
            target_x: Target X position
            target_y: Target Y position

        Returns:
            "none", "x", "y", or "both" indicating which axes wrap
        """
        if self._electric_walls:
            return "none"

        board = world.board
        grid_size = board.cell_size

        # check X axis wrapping
        x_wraps = self._will_wrap_around(current_x, target_x, board.width, grid_size)

        # check Y axis wrapping
        y_wraps = self._will_wrap_around(current_y, target_y, board.height, grid_size)

        # return combined result
        if x_wraps and y_wraps:
            return "both"
        elif x_wraps:
            return "x"
        elif y_wraps:
            return "y"
        else:
            return "none"

    @staticmethod
    def _will_wrap_around(origin: int, dest: int, limit: int, grid_size: int) -> bool:
        """Check if movement from origin to dest will wrap around the edge.

        This is the core logic from the old code's _will_wrap_around function.
        It checks if the distance between origin and dest is close to the limit,
        indicating an edge wrap.

        Args:
            origin: Starting position
            dest: Destination position
            limit: Arena dimension (width or height)
            grid_size: Size of one grid cell

        Returns:
            True if movement will wrap around, False otherwise
        """
        return abs(abs(origin - dest) - limit) <= grid_size
