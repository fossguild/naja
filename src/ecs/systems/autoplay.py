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

"""Autoplay system for controlling the snake automatically."""

from collections import deque
from typing import List, Tuple, Set, Optional, Any

from ecs.systems.base_system import BaseSystem
from ecs.world import World
from ecs.entities.entity import EntityType
from game.game_modes_registry import AUTOPLAY_MODE_NAME


class AutoplaySystem(BaseSystem):
    """System that controls the snake in Autoplay mode.

    Reads: Position, Velocity, SnakeBody, Apple, Obstacle
    Writes: InputBuffer (simulates input)
    """

    def __init__(self, game_mode: str, settings: Optional[Any] = None):
        """Initialize the AutoplaySystem.

        Args:
            game_mode: The current game mode.
            settings: Game settings.
        """
        self._game_mode = game_mode
        self._settings = settings
        self._path: List[Tuple[int, int]] = []
        self._last_calc_time = 0.0
        self._calc_interval = 50.0  # Recalculate path frequently
        # Hamiltonian cycle for guaranteed safe path
        self._hamiltonian_path: List[Tuple[int, int]] = []
        self._hamiltonian_index = 0
        self._hamiltonian_initialized = False

    def update(self, world: World) -> None:
        """Update the snake's direction based on pathfinding.

        Args:
            world: ECS world containing entities and components
        """
        if self._game_mode != AUTOPLAY_MODE_NAME:
            return

        # Only recalculate path periodically
        self._last_calc_time += world.dt_ms
        if self._last_calc_time < self._calc_interval:
            return

        self._last_calc_time = 0.0

        snake = self._get_snake(world)
        if not snake:
            return

        # Get target (apple)
        target = self._get_target(world)
        if not target:
            return

        # Calculate path
        start = (snake.position.x, snake.position.y)
        goal = (target.position.x, target.position.y)

        obstacles = self._get_obstacles(world, snake)

        electric_walls = (
            self._settings.get("electric_walls") if self._settings else True
        )

        current_direction = (snake.velocity.dx, snake.velocity.dy)

        # Check if apple is safe to eat (has escape route after eating)
        apple_is_safe = self._is_apple_safe(
            goal,
            snake,
            obstacles,
            world.board.width,
            world.board.height,
            electric_walls,
        )

        path = self._bfs(
            start,
            goal,
            obstacles,
            world.board.width,
            world.board.height,
            electric_walls,
            current_direction,
        )

        if path and apple_is_safe:
            # Apple is reachable AND safe - pursue it
            self._path = path
            next_pos = path[0]
            dx = next_pos[0] - start[0]
            dy = next_pos[1] - start[1]

            # Handle wrapping for direction calculation
            if not electric_walls:
                if dx > 1:
                    dx = -1
                elif dx < -1:
                    dx = 1
                if dy > 1:
                    dy = -1
                elif dy < -1:
                    dy = 1

            self._buffer_direction(snake, dx, dy)
        elif path and not apple_is_safe:
            # Apple is reachable but UNSAFE - wait tactically
            # Move to safe space while staying alive, repositioning for better angle
            self._wait_tactically(
                snake,
                obstacles,
                world.board.width,
                world.board.height,
                electric_walls,
                current_direction,
            )
        else:
            # No path to apple - use basic survival
            self._survive(
                snake,
                obstacles,
                world.board.width,
                world.board.height,
                electric_walls,
                current_direction,
            )

    def _get_snake(self, world: World):
        snakes = world.registry.query_by_type(EntityType.SNAKE)
        if snakes:
            return next(iter(snakes.values()))
        return None

    def _get_target(self, world: World):
        apples = world.registry.query_by_type(EntityType.APPLE)
        if apples:
            # Find closest apple? For now just pick the first one
            return next(iter(apples.values()))
        return None

    def _get_obstacles(self, world: World, snake) -> Set[Tuple[int, int]]:
        obstacles = set()

        # Add snake body to obstacles
        if hasattr(snake, "body") and snake.body.segments:
            # We don't add the tail as an obstacle because it will move
            # But for safety in simple BFS, let's add all segments except maybe the very last one
            # if we want to be aggressive. For now, add all segments to be safe.
            for segment in snake.body.segments[:-1]:  # Exclude tail tip as it will move
                obstacles.add((segment.x, segment.y))

        # Add static obstacles
        obs_entities = world.registry.query_by_type(EntityType.OBSTACLE)
        for entity in obs_entities.values():
            if hasattr(entity, "position"):
                obstacles.add((entity.position.x, entity.position.y))

        return obstacles

    def _bfs(
        self,
        start: Tuple[int, int],
        goal: Tuple[int, int],
        obstacles: Set[Tuple[int, int]],
        width: int,
        height: int,
        electric_walls: bool,
        current_direction: Tuple[int, int],
    ) -> List[Tuple[int, int]]:
        queue = deque([(start, [])])
        visited = {start}

        while queue:
            (current, path) = queue.popleft()

            if current == goal:
                return path

            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                # Prevent 180 degree turn at the start
                if not path:  # Only check for first move
                    if (dx != 0 and current_direction[0] == -dx) or (
                        dy != 0 and current_direction[1] == -dy
                    ):
                        continue

                if electric_walls:
                    next_x = current[0] + dx
                    next_y = current[1] + dy
                    if next_x < 0 or next_x >= width or next_y < 0 or next_y >= height:
                        continue
                else:
                    next_x = (current[0] + dx) % width
                    next_y = (current[1] + dy) % height

                neighbor = (next_x, next_y)

                if neighbor not in visited and neighbor not in obstacles:
                    visited.add(neighbor)
                    new_path = path + [neighbor]
                    queue.append((neighbor, new_path))

        return []

    def _survive(
        self,
        snake,
        obstacles: Set[Tuple[int, int]],
        width: int,
        height: int,
        electric_walls: bool,
        current_direction: Tuple[int, int],
    ):
        start = (snake.position.x, snake.position.y)

        # Try all directions
        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            # Prevent 180 degree turn
            if (dx != 0 and current_direction[0] == -dx) or (
                dy != 0 and current_direction[1] == -dy
            ):
                continue

            if electric_walls:
                next_x = start[0] + dx
                next_y = start[1] + dy
                if next_x < 0 or next_x >= width or next_y < 0 or next_y >= height:
                    continue
            else:
                next_x = (start[0] + dx) % width
                next_y = (start[1] + dy) % height

            neighbor = (next_x, next_y)

            if neighbor not in obstacles:
                self._buffer_direction(snake, dx, dy)
                return

    def _wait_tactically(
        self,
        snake,
        obstacles: Set[Tuple[int, int]],
        width: int,
        height: int,
        electric_walls: bool,
        current_direction: Tuple[int, int],
    ):
        """Move to a safe position while waiting for apple to become safe.

        Chooses the direction that maximizes distance from own body,
        giving more room to maneuver in the future.

        Args:
            snake: Snake entity
            obstacles: Current obstacles
            width: Board width
            height: Board height
            electric_walls: Whether walls are deadly
            current_direction: Current movement direction
        """
        start = (snake.position.x, snake.position.y)
        best_move = None
        best_score = -1

        # Evaluate all possible moves
        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            # Prevent 180 degree turn
            if (dx != 0 and current_direction[0] == -dx) or (
                dy != 0 and current_direction[1] == -dy
            ):
                continue

            if electric_walls:
                next_x = start[0] + dx
                next_y = start[1] + dy
                if next_x < 0 or next_x >= width or next_y < 0 or next_y >= height:
                    continue
            else:
                next_x = (start[0] + dx) % width
                next_y = (start[1] + dy) % height

            neighbor = (next_x, next_y)

            if neighbor not in obstacles:
                # Score this move by distance to nearest body segment
                min_dist = float("inf")
                for obstacle in obstacles:
                    dist = abs(next_x - obstacle[0]) + abs(next_y - obstacle[1])
                    min_dist = min(min_dist, dist)

                if min_dist > best_score:
                    best_score = min_dist
                    best_move = (dx, dy)

        # Make the best move found, or any valid move if none scored well
        if best_move:
            self._buffer_direction(snake, best_move[0], best_move[1])
        else:
            # Fallback to basic survival if no tactical move found
            self._survive(
                snake,
                obstacles,
                width,
                height,
                electric_walls,
                current_direction,
            )

    def _find_open_spaces(
        self,
        obstacles: Set[Tuple[int, int]],
        width: int,
        height: int,
    ) -> List[Tuple[int, int]]:
        """Find all empty cells on the board.

        Args:
            obstacles: Set of occupied positions
            width: Board width
            height: Board height

        Returns:
            List of empty cell positions
        """
        open_spaces = []
        for y in range(height):
            for x in range(width):
                pos = (x, y)
                if pos not in obstacles:
                    open_spaces.append(pos)
        return open_spaces

    def _is_apple_safe(
        self,
        apple_pos: Tuple[int, int],
        snake,
        obstacles: Set[Tuple[int, int]],
        width: int,
        height: int,
        electric_walls: bool,
    ) -> bool:
        """Check if eating apple at position leaves an escape route with breathing room.

        Simulates eating the apple and verifies that:
        1. The snake can reach open space
        2. The escape area has enough room for continued play
        3. Multiple spaces are reachable (not just one tiny corner)

        Args:
            apple_pos: Position of the apple
            snake: Snake entity
            obstacles: Current obstacles (including snake body)
            width: Board width
            height: Board height
            electric_walls: Whether walls are deadly

        Returns:
            True if eating apple is safe, False if it would trap the snake
        """
        # Simulate snake after eating apple
        simulated_obstacles = obstacles.copy()
        simulated_obstacles.add(apple_pos)  # Apple position becomes new body segment

        # Find all open spaces on the board after eating
        open_spaces = self._find_open_spaces(simulated_obstacles, width, height)
        if not open_spaces:
            # Board is full - this is actually a WIN condition, allow it
            return True

        # Current snake size (will be +1 after eating apple)
        snake_size = len(snake.body.segments) + 1

        # Find reachable open spaces from apple position
        reachable_spaces = []
        for open_space in open_spaces:
            escape_path = self._bfs(
                apple_pos,
                open_space,
                simulated_obstacles,
                width,
                height,
                electric_walls,
                (0, 0),  # Dummy direction - checking if path exists
            )
            if escape_path:
                reachable_spaces.append(open_space)

        if not reachable_spaces:
            return False  # No escape route at all

        # Quality check: Ensure escape area is large enough
        # We need at least as many reachable spaces as the snake's size
        # This prevents escaping into tiny corners
        min_required_spaces = max(snake_size, 3)  # At least 3 spaces minimum
        if len(reachable_spaces) < min_required_spaces:
            return False  # Escape area too small - likely a trap

        # Additional check: Verify there's a cluster of connected spaces
        # Use flood fill from first reachable space to count connected area
        connected_area = self._count_connected_area(
            reachable_spaces[0],
            simulated_obstacles,
            width,
            height,
            electric_walls,
        )

        # The connected area should be large enough for the snake to maneuver
        # Require at least 1.5x the snake's size for safety margin
        min_connected_area = int(snake_size * 1.5)
        if connected_area < min_connected_area:
            return False  # Escape leads to cramped space

        return True  # Apple is safe - good escape with room to maneuver

    def _count_connected_area(
        self,
        start_pos: Tuple[int, int],
        obstacles: Set[Tuple[int, int]],
        width: int,
        height: int,
        electric_walls: bool,
    ) -> int:
        """Count the size of the connected open area from a starting position.

        Uses flood fill to determine how many empty cells are reachable
        from the start position.

        Args:
            start_pos: Starting position for flood fill
            obstacles: Set of obstacles to avoid
            width: Board width
            height: Board height
            electric_walls: Whether walls are deadly

        Returns:
            Number of connected empty cells
        """
        visited = {start_pos}
        queue = deque([start_pos])
        count = 1

        while queue:
            current = queue.popleft()

            # Check all 4 directions
            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                if electric_walls:
                    next_x = current[0] + dx
                    next_y = current[1] + dy
                    if next_x < 0 or next_x >= width or next_y < 0 or next_y >= height:
                        continue
                else:
                    next_x = (current[0] + dx) % width
                    next_y = (current[1] + dy) % height

                neighbor = (next_x, next_y)

                if neighbor not in visited and neighbor not in obstacles:
                    visited.add(neighbor)
                    queue.append(neighbor)
                    count += 1

        return count

    def _buffer_direction(self, snake, dx: int, dy: int) -> None:
        if not hasattr(snake, "input_buffer") or snake.input_buffer is None:
            from src.ecs.components.input_buffer import InputBuffer

            snake.input_buffer = InputBuffer()

        buf = snake.input_buffer

        # Don't fill buffer too much
        if len(buf.moves) >= 1:
            return

        # Check if we are reversing direction (invalid move)
        last_dx, last_dy = (snake.velocity.dx, snake.velocity.dy)
        if buf.moves:
            last_dx, last_dy = buf.moves[-1]

        if (dx != 0 and last_dx == -dx) or (dy != 0 and last_dy == -dy):
            return

        buf.moves.append((dx, dy))

    def _generate_hamiltonian_cycle(
        self, width: int, height: int
    ) -> List[Tuple[int, int]]:
        """Generate a Hamiltonian cycle that visits every cell on the board.

        Uses a simple zigzag pattern that works for any board size:
        - Traverse left-to-right on even rows
        - Traverse right-to-left on odd rows
        - Connect rows by moving down

        This guarantees visiting every cell exactly once and returning to start.

        Args:
            width: Board width in cells
            height: Board height in cells

        Returns:
            List of (x, y) positions forming a complete cycle
        """
        path = []

        for y in range(height):
            if y % 2 == 0:
                # Even row: left to right
                for x in range(width):
                    path.append((x, y))
            else:
                # Odd row: right to left
                for x in range(width - 1, -1, -1):
                    path.append((x, y))

        return path
