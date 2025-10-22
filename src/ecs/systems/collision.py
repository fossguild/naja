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

"""Collision detection system for all game entities.

This system detects collisions between the snake and:
- Walls (in electric mode)
- Its own tail (self-bite)
- Obstacles
- Apples (edible items)

Maintains identical logic to the old code.
"""

from typing import Optional, Callable, Any

from src.ecs.systems.base_system import BaseSystem
from src.ecs.world import World


class CollisionSystem(BaseSystem):
    """System for detecting all types of collisions.

    Reads: Position, Edible, ObstacleTag (via World queries)
    Writes: None (emits events via callbacks)
    Queries:
        - Entities with Position + Edible (apples)
        - Entities with Position + ObstacleTag (obstacles)

    Responsibilities:
    - Detect wall collisions (electric mode only)
    - Detect self-bite collisions
    - Detect obstacle collisions
    - Detect apple collisions
    - Emit appropriate callbacks for each collision type
    - Maintain collision check order (fatal before non-fatal)

    Note: This system only DETECTS collisions and calls callbacks.
    It does not modify game state directly (ECS principle).
    """

    def __init__(
        self,
        get_snake_head_position: Optional[Callable[[], tuple[int, int]]] = None,
        get_snake_tail_positions: Optional[Callable[[], list[tuple[int, int]]]] = None,
        get_snake_next_position: Optional[Callable[[], tuple[int, int]]] = None,
        get_electric_walls: Optional[Callable[[], bool]] = None,
        get_grid_dimensions: Optional[Callable[[], tuple[int, int, int]]] = None,
        get_current_speed: Optional[Callable[[], float]] = None,
        get_max_speed: Optional[Callable[[], float]] = None,
        death_callback: Optional[Callable[[str], None]] = None,
        apple_eaten_callback: Optional[Callable[[Any, tuple[int, int]], None]] = None,
        speed_increase_callback: Optional[Callable[[float], None]] = None,
    ):
        """Initialize the CollisionSystem.

        Args:
            get_snake_head_position: Function to get current head position (x, y)
            get_snake_tail_positions: Function to get tail segments [(x, y), ...]
            get_snake_next_position: Function to get next head position (x, y)
            get_electric_walls: Function to check if electric walls are enabled
            get_grid_dimensions: Function to get (width, height, grid_size)
            get_current_speed: Function to get current snake speed
            get_max_speed: Function to get maximum allowed speed
            death_callback: Function to call on death with reason string
            apple_eaten_callback: Function to call when apple is eaten
            speed_increase_callback: Function to call to increase speed
        """
        self._get_snake_head_position = get_snake_head_position
        self._get_snake_tail_positions = get_snake_tail_positions
        self._get_snake_next_position = get_snake_next_position
        self._get_electric_walls = get_electric_walls
        self._get_grid_dimensions = get_grid_dimensions
        self._get_current_speed = get_current_speed
        self._get_max_speed = get_max_speed
        self._death_callback = death_callback
        self._apple_eaten_callback = apple_eaten_callback
        self._speed_increase_callback = speed_increase_callback

    def update(self, world: World) -> None:
        """Check for all collision types in priority order.

        Priority (same as old code):
        1. Wall collision (electric mode only)
        2. Self-bite collision
        3. Obstacle collision
        4. Apple collision

        Args:
            world: ECS world to query entities
        """
        # Check wall collision first (highest priority)
        if self._check_wall_collision():
            print("☠️  DEATH CAUSE: Wall collision")
            if self._death_callback:
                self._death_callback("wall")
            return

        # Check self-bite collision
        if self._check_self_bite():
            print("☠️  DEATH CAUSE: Self-bite collision")
            if self._death_callback:
                self._death_callback("self-bite")
            return

        # Check obstacle collision
        if self._check_obstacle_collision(world):
            print("☠️  DEATH CAUSE: Obstacle collision")
            if self._death_callback:
                self._death_callback("obstacle")
            return

        # Check apple collision (doesn't kill)
        self._check_apple_collision(world)

    def _check_wall_collision(self) -> bool:
        """Check collision with walls (electric mode only).

        Checks if snake's CURRENT position is out of bounds.
        Movement system handles wrapping when electric walls are disabled.
        Collision system only checks if we're already out of bounds.

        Returns:
            bool: True if collision detected, False otherwise
        """
        if not self._get_snake_head_position or not self._get_grid_dimensions:
            return False

        # Check CURRENT position, not next position
        # Snake dies when it IS out of bounds, not when it WOULD BE out of bounds
        current_x, current_y = self._get_snake_head_position()
        grid_width, grid_height, cell_size = self._get_grid_dimensions()

        # get electric walls setting
        electric_walls = False
        if self._get_electric_walls:
            electric_walls = self._get_electric_walls()

        # Grid dimensions are now in cells, not pixels
        # Valid positions are 0 to grid_width-1 and 0 to grid_height-1
        # Snake dies when its current position is out of bounds
        if electric_walls and (
            current_x < 0
            or current_x >= grid_width
            or current_y < 0
            or current_y >= grid_height
        ):
            print(
                f"WALL COLLISION: current_pos=({current_x},{current_y}), grid=({grid_width}x{grid_height}), valid_range=(0-{grid_width - 1}, 0-{grid_height - 1})"
            )
            return True

        return False

    def _check_self_bite(self) -> bool:
        """Check if snake head collides with its own tail.

        Maintains exact logic from old code (entities.py lines 122-125).

        Returns:
            bool: True if self-bite detected, False otherwise
        """
        if not self._get_snake_next_position or not self._get_snake_tail_positions:
            return False

        next_x, next_y = self._get_snake_next_position()
        tail_positions = self._get_snake_tail_positions()

        # EXACT LOGIC from old code: iterate over each tail segment
        for square in tail_positions:
            if next_x == square[0] and next_y == square[1]:
                return True

        return False

    def _check_obstacle_collision(self, world: World) -> bool:
        """Check collision with obstacles.

        Checks if snake's CURRENT position (after movement) collides with obstacle.
        This matches the wall collision behavior - we check if snake IS on obstacle,
        not if it WOULD BE on obstacle.

        Args:
            world: ECS world to query obstacles

        Returns:
            bool: True if collision detected, False otherwise
        """
        if not self._get_snake_head_position:
            return False

        # Check CURRENT position (after movement), not next position
        # Snake dies when it IS on an obstacle, not when it WOULD BE on an obstacle
        current_x, current_y = self._get_snake_head_position()

        # Query all obstacles using EntityType
        from src.ecs.entities.entity import EntityType

        obstacles = world.registry.query_by_type(EntityType.OBSTACLE)

        # Check if snake's current position collides with any obstacle
        for _, obstacle in obstacles.items():
            if hasattr(obstacle, "position"):
                # Obstacles store position in grid coordinates (tiles)
                if (
                    current_x == obstacle.position.x
                    and current_y == obstacle.position.y
                ):
                    return True

        return False

    def _check_apple_collision(self, world: World) -> None:
        """Check collision with apples and handle eating.

        Maintains exact logic from old code (app.py lines 537-579).

        Calls callbacks for:
        - apple_eaten_callback
        - speed_increase_callback

        Args:
            world: ECS world to query apples
        """
        if not self._get_snake_head_position:
            return

        head_x, head_y = self._get_snake_head_position()

        # query apples from world (ECS way)
        # EXACT LOGIC: iterate over each apple
        from src.ecs.entities.entity import EntityType

        apples = world.registry.query_by_type(EntityType.APPLE)
        for entity_id, apple in apples.items():
            # check if apple is at the same position as head
            if hasattr(apple, "position"):
                if head_x == apple.position.x and head_y == apple.position.y:
                    print(f"APPLE EATEN: head=({head_x},{head_y})")
                    # apple eaten! call callbacks
                    if self._apple_eaten_callback:
                        self._apple_eaten_callback(entity_id, (head_x, head_y))

                    # EXACT LOGIC: increase speed by 10%, respect max_speed
                    if self._speed_increase_callback:
                        if self._get_current_speed and self._get_max_speed:
                            current_speed = self._get_current_speed()
                            max_speed = self._get_max_speed()
                            new_speed = min(current_speed * 1.1, max_speed)
                            self._speed_increase_callback(new_speed)

                    break  # EXACT LOGIC: only eat one apple per frame
