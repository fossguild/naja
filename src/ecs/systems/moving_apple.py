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

"""System that moves apples when the current game mode allows it."""

from __future__ import annotations

import random
from typing import Optional, Set, Tuple

from ecs.systems.base_system import BaseSystem
from ecs.world import World
from ecs.entities.entity import EntityType
from ecs.components.moving_apple import MovingApple


class MovingAppleSystem(BaseSystem):
    """Move apples on the board without exceeding the snake's speed."""

    _DIRECTIONS: Tuple[Tuple[int, int], ...] = (
        (1, 0),
        (-1, 0),
        (0, 1),
        (0, -1),
    )

    def __init__(
        self,
        base_speed_ratio: float = 0.6,
        speed_ramp_rate: float = 0.6,
        direction_change_chance: float = 0.2,
        random_seed: Optional[int] = None,
    ):
        """Initialize the system.

        Args:
            base_speed_ratio: Fraction of the snake speed targeted for apples.
            speed_ramp_rate: Max delta (cells/s per second) apples can adjust toward target.
            direction_change_chance: Chance per move to pick a new direction randomly.
            random_seed: Optional seed for deterministic movement (useful in tests).
        """
        self._base_speed_ratio = max(0.1, min(base_speed_ratio, 1.0))
        self._speed_ramp_rate = max(0.05, speed_ramp_rate)
        self._direction_change_chance = max(0.0, min(direction_change_chance, 1.0))
        self._random = (
            random.Random(random_seed) if random_seed is not None else random.Random()
        )

    def update(self, world: World) -> None:
        """Move apples only when the moving-apple mode is enabled."""
        game_state = self._get_game_state(world)
        if not game_state or not getattr(game_state, "moving_apples_enabled", False):
            return

        snake = self._get_snake(world)
        if not snake or not hasattr(snake, "velocity"):
            return

        snake_speed = max(1.0, float(getattr(snake.velocity, "speed", 4.0)))
        target_speed = max(0.5, snake_speed * self._base_speed_ratio)

        apples = world.registry.query_by_type(EntityType.APPLE)
        if not apples:
            return

        blocked_positions = self._get_blocked_positions(world)

        for _, apple in apples.items():
            moving: Optional[MovingApple] = getattr(apple, "moving_apple", None)
            if moving is None:
                moving = self._initialize_component(apple)

            current_speed = self._update_speed(moving, target_speed, world.dt_ms)
            move_interval_ms = 1000.0 / max(0.1, current_speed)

            moving.time_accumulator_ms += world.dt_ms
            if moving.time_accumulator_ms < move_interval_ms:
                continue

            moving.time_accumulator_ms -= move_interval_ms

            current_pos = (apple.position.x, apple.position.y)
            direction = (moving.dx, moving.dy)

            if self._should_change_direction():
                new_direction = self._choose_new_direction(
                    current_pos,
                    world,
                    blocked_positions,
                    exclude_direction=direction,
                )
                if new_direction:
                    direction = moving.dx, moving.dy = new_direction

            target = (current_pos[0] + direction[0], current_pos[1] + direction[1])

            if not self._is_valid_target(target, world, blocked_positions):
                new_direction = self._choose_new_direction(
                    current_pos, world, blocked_positions, exclude_direction=None
                )
                if new_direction is None:
                    continue
                moving.dx, moving.dy = new_direction
                target = (current_pos[0] + moving.dx, current_pos[1] + moving.dy)
                if not self._is_valid_target(target, world, blocked_positions):
                    continue

            apple.position.prev_x = apple.position.x
            apple.position.prev_y = apple.position.y
            apple.position.x, apple.position.y = target

            blocked_positions.discard(current_pos)
            blocked_positions.add(target)

    def _initialize_component(self, apple) -> MovingApple:
        """Attach a movement component with a random direction."""
        direction = self._random.choice(self._DIRECTIONS)
        moving = MovingApple(dx=direction[0], dy=direction[1])
        apple.moving_apple = moving
        return moving

    def _get_game_state(self, world: World):
        """Retrieve the singleton GameState component."""
        entities = world.registry.query_by_component("game_state")
        if entities:
            entity = next(iter(entities.values()))
            return getattr(entity, "game_state", None)
        return None

    def _get_snake(self, world: World):
        """Get the snake entity, if available."""
        snakes = world.registry.query_by_type(EntityType.SNAKE)
        for _, snake in snakes.items():
            return snake
        return None

    def _get_blocked_positions(self, world: World) -> Set[Tuple[int, int]]:
        """Collect positions that apples should avoid."""
        blocked: Set[Tuple[int, int]] = set()

        snakes = world.registry.query_by_type(EntityType.SNAKE)
        for _, snake in snakes.items():
            if hasattr(snake, "position"):
                blocked.add((snake.position.x, snake.position.y))
            if hasattr(snake, "body"):
                for segment in snake.body.segments:
                    blocked.add((segment.x, segment.y))

        obstacles = world.registry.query_by_type(EntityType.OBSTACLE)
        for _, obstacle in obstacles.items():
            if hasattr(obstacle, "position"):
                blocked.add((obstacle.position.x, obstacle.position.y))

        apples = world.registry.query_by_type(EntityType.APPLE)
        for _, apple in apples.items():
            if hasattr(apple, "position"):
                blocked.add((apple.position.x, apple.position.y))

        return blocked

    def _is_valid_target(
        self,
        target: Tuple[int, int],
        world: World,
        blocked_positions: Set[Tuple[int, int]],
    ) -> bool:
        """Check if a target cell is inside the board and free."""
        x, y = target
        board = world.board
        if not (0 <= x < board.width and 0 <= y < board.height):
            return False

        return target not in blocked_positions

    def _choose_new_direction(
        self,
        current_pos: Tuple[int, int],
        world: World,
        blocked_positions: Set[Tuple[int, int]],
        exclude_direction: Optional[Tuple[int, int]] = None,
    ) -> Optional[Tuple[int, int]]:
        """Pick a valid direction randomly."""
        directions = list(self._DIRECTIONS)
        if exclude_direction:
            directions = [d for d in directions if d != exclude_direction]
        self._random.shuffle(directions)

        for dx, dy in directions:
            target = (current_pos[0] + dx, current_pos[1] + dy)
            if self._is_valid_target(target, world, blocked_positions):
                return (dx, dy)
        return None

    def _update_speed(
        self, moving: MovingApple, target_speed: float, dt_ms: float
    ) -> float:
        """Adjust the apple's current speed toward the target smoothly."""
        if moving.current_speed <= 0:
            moving.current_speed = target_speed
            return moving.current_speed

        delta = target_speed - moving.current_speed
        if delta == 0:
            return moving.current_speed

        max_change = self._speed_ramp_rate * (dt_ms / 1000.0)
        if delta > 0:
            moving.current_speed += min(delta, max_change)
        else:
            moving.current_speed += max(delta, -max_change)

        return moving.current_speed

    def _should_change_direction(self) -> bool:
        """Randomly decide whether to pick a new heading this tick."""
        if self._direction_change_chance <= 0.0:
            return False
        return self._random.random() < self._direction_change_chance
