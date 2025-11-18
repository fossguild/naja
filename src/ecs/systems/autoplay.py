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

"""Autoplay system for AI-controlled snake gameplay.

This system uses BFS pathfinding to navigate the snake to apples while
avoiding obstacles and the snake's own body.
"""

from collections import deque
from typing import Optional, Callable

from ecs.systems.base_system import BaseSystem
from ecs.world import World
from ecs.entities.entity import EntityType


class AutoplaySystem(BaseSystem):
    """AI system that controls snake movement using pathfinding.

    Reads: Position, Velocity, SnakeBody, Edible (apples), Obstacle
    Writes: Velocity (snake direction)

    Uses BFS pathfinding to find the shortest safe path to the nearest apple.
    Avoids walls, obstacles, and the snake's own body.
    """

    def __init__(self, get_electric_walls: Optional[Callable[[], bool]] = None):
        """Initialize autoplay system.

        Args:
            get_electric_walls: Optional callback to check if electric walls are enabled.
                               If None, assumes wrapping mode (default behavior).
        """
        self._get_electric_walls = get_electric_walls
        self._last_direction = (1, 0)  # default: moving right

    def update(self, world: World) -> None:
        """Update snake direction using pathfinding.

        Args:
            world: ECS world containing entities and components
        """
        game_state = self._get_game_state(world)
        if not game_state or not getattr(game_state, "autoplay_enabled", False):
            return

        snake = self._get_snake_entity(world)
        if not snake or not hasattr(snake, "position") or not hasattr(snake, "body"):
            return

        if not snake.body.alive:
            return

        head_x = snake.position.x
        head_y = snake.position.y

        current_dx = snake.velocity.dx if hasattr(snake, "velocity") else 1
        current_dy = snake.velocity.dy if hasattr(snake, "velocity") else 0

        apple = self._find_nearest_apple(world, head_x, head_y)
        if not apple:
            return

        target_x = apple.position.x
        target_y = apple.position.y

        next_direction = self._find_path_bfs(
            world, head_x, head_y, target_x, target_y, current_dx, current_dy
        )

        if next_direction:
            dx, dy = next_direction
            if hasattr(snake, "velocity"):
                snake.velocity.dx = dx
                snake.velocity.dy = dy
                self._last_direction = (dx, dy)

    def _get_game_state(self, world: World):
        """Get the GameState component from world.

        Args:
            world: ECS world

        Returns:
            GameState component or None if not found
        """
        game_state_entities = world.registry.query_by_component("game_state")
        if game_state_entities:
            entity = next(iter(game_state_entities.values()))
            if hasattr(entity, "game_state"):
                return entity.game_state
        return None

    def _get_snake_entity(self, world: World):
        """Get the snake entity from the world.

        Args:
            world: ECS world

        Returns:
            Snake entity or None if not found
        """
        snakes = world.registry.query_by_type(EntityType.SNAKE)
        for _, snake in snakes.items():
            return snake
        return None

    def _find_nearest_apple(self, world: World, head_x: int, head_y: int):
        """Find the nearest apple to the snake's head.

        Args:
            world: ECS world
            head_x: Snake head x position
            head_y: Snake head y position

        Returns:
            Nearest apple entity or None if no apples found
        """
        apples = world.registry.query_by_component("edible", "position")
        if not apples:
            return None

        nearest_apple = None
        min_distance = float("inf")

        for _, apple in apples.items():
            distance = abs(apple.position.x - head_x) + abs(apple.position.y - head_y)
            if distance < min_distance:
                min_distance = distance
                nearest_apple = apple

        return nearest_apple

    def _is_position_safe(
        self,
        world: World,
        x: int,
        y: int,
        snake_segments: list,
        electric_walls: bool,
    ) -> bool:
        """Check if a position is safe to move to.

        Args:
            world: ECS world
            x: X coordinate to check
            y: Y coordinate to check
            snake_segments: List of snake body segment positions
            electric_walls: Whether electric walls mode is enabled

        Returns:
            True if position is safe, False otherwise
        """
        board = world.board

        if electric_walls:
            if x < 0 or x >= board.width or y < 0 or y >= board.height:
                return False
        else:
            x = x % board.width
            y = y % board.height

        for segment in snake_segments:
            if segment.x == x and segment.y == y:
                return False

        obstacles = world.registry.query_by_component("obstacle", "position")
        for _, obstacle in obstacles.items():
            if obstacle.position.x == x and obstacle.position.y == y:
                return False

        return True

    def _find_path_bfs(
        self,
        world: World,
        start_x: int,
        start_y: int,
        target_x: int,
        target_y: int,
        current_dx: int,
        current_dy: int,
    ) -> Optional[tuple[int, int]]:
        """Find path to target using BFS pathfinding.

        Args:
            world: ECS world
            start_x: Starting x position (snake head)
            start_y: Starting y position (snake head)
            target_x: Target x position (apple)
            target_y: Target y position (apple)
            current_dx: Current direction x component
            current_dy: Current direction y component

        Returns:
            Next direction tuple (dx, dy) or None if no path found
        """
        electric_walls = (
            self._get_electric_walls() if self._get_electric_walls else False
        )

        snake = self._get_snake_entity(world)
        snake_segments = snake.body.segments if snake and hasattr(snake, "body") else []

        queue = deque([(start_x, start_y, [])])
        visited = {(start_x, start_y)}
        directions = [(0, -1), (0, 1), (-1, 0), (1, 0)]
        board = world.board

        while queue:
            x, y, path = queue.popleft()

            if x == target_x and y == target_y:
                if path:
                    return path[0]
                return None

            for dx, dy in directions:
                if path:
                    last_dx, last_dy = path[-1]
                else:
                    last_dx, last_dy = current_dx, current_dy

                if (dx != 0 and last_dx == -dx) or (dy != 0 and last_dy == -dy):
                    continue

                next_x = x + dx
                next_y = y + dy

                if not electric_walls:
                    next_x = next_x % board.width
                    next_y = next_y % board.height

                if (next_x, next_y) in visited:
                    continue

                if self._is_position_safe(
                    world, next_x, next_y, snake_segments, electric_walls
                ):
                    visited.add((next_x, next_y))
                    new_path = path + [(dx, dy)]
                    queue.append((next_x, next_y, new_path))

        return self._find_safe_direction(
            world, start_x, start_y, current_dx, current_dy
        )

    def _find_safe_direction(
        self,
        world: World,
        x: int,
        y: int,
        current_dx: int,
        current_dy: int,
    ) -> Optional[tuple[int, int]]:
        """Find any safe direction when no path to apple exists.

        Args:
            world: ECS world
            x: Current x position
            y: Current y position
            current_dx: Current direction x component
            current_dy: Current direction y component

        Returns:
            Safe direction tuple (dx, dy) or current direction if none found
        """
        electric_walls = (
            self._get_electric_walls() if self._get_electric_walls else False
        )

        snake = self._get_snake_entity(world)
        snake_segments = snake.body.segments if snake and hasattr(snake, "body") else []

        directions = [(0, -1), (0, 1), (-1, 0), (1, 0)]

        for dx, dy in directions:
            if (dx != 0 and current_dx == -dx) or (dy != 0 and current_dy == -dy):
                continue

            next_x = x + dx
            next_y = y + dy

            if self._is_position_safe(
                world, next_x, next_y, snake_segments, electric_walls
            ):
                return (dx, dy)

        return (current_dx, current_dy)
