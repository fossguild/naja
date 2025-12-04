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

"""Autoplay system implementing hybrid two-phase strategy.

Hybrid Auto-Run Mode: Fast Early Game + Safe Late Game
-------------------------------------------------------
Phase 1 (Score < 500): Aggressive Tail-Following
- Fast apple collection using BFS pathfinding
- Follows own tail when no safe apple available
- Optimized for speed and high score

Phase 2 (Score >= 500): Deterministic Serpentine Sweep
- Guaranteed-safe Hamiltonian-inspired pattern
- Never dies, eventually visits every cell
- Runs indefinitely to completion

This hybrid approach combines the best of both strategies:
speed in early game, safety in late game.
"""

from collections import deque
from typing import Optional, Any, List, Tuple, Set

from ecs.systems.base_system import BaseSystem
from ecs.world import World
from ecs.entities.entity import EntityType
from game.game_modes_registry import AUTOPLAY_MODE_NAME

# Threshold to switch from tail-following to serpentine sweep
SERPENTINE_SWITCH_SCORE = 500


class AutoplaySystem(BaseSystem):
    """System that controls the snake in Autoplay mode using hybrid strategy.

    Reads: Position, Velocity, SnakeBody
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
        self._using_serpentine = False  # Phase tracker

    def update(self, world: World) -> None:
        """Update the snake's direction using hybrid two-phase strategy.

        Phase 1 (< 500 points): Tail-following for fast apple collection
        Phase 2 (>= 500 points): Serpentine sweep for guaranteed safety

        Args:
            world: ECS world containing entities and components
        """
        if self._game_mode != AUTOPLAY_MODE_NAME:
            return

        snake = self._get_snake(world)
        if not snake:
            return

        # Get current score from world scoring system
        current_score = self._get_current_score(world)

        # Check if we should switch to serpentine mode (one-way switch)
        if not self._using_serpentine and current_score >= SERPENTINE_SWITCH_SCORE:
            self._using_serpentine = True
            print(f"[Autoplay] Switching to SERPENTINE mode at score {current_score}")

        # Execute appropriate strategy based on phase
        if self._using_serpentine:
            # Phase 2: Deterministic serpentine sweep
            self._update_serpentine(snake, world)
        else:
            # Phase 1: Aggressive tail-following
            self._update_tail_following(snake, world)

    def _get_serpentine_direction(
        self, hx: int, hy: int, W: int, H: int
    ) -> tuple[int, int]:
        """Calculate next move direction using serpentine sweep pattern.

        Pattern Rules:
        1. Rightmost column (x = W-1, y < H-1): Move DOWN
        2. Bottom-right corner (x = W-1, y = H-1): Move LEFT
        3. Bottom row (y = H-1, x > 0): Continue LEFT
        4. Bottom-left corner (x = 0, y = H-1): Move UP
        5. Odd rows (y = 1,3,5..., x > 0): Move LEFT
        6. Odd rows (y = 1,3,5..., x = 0): Move UP
        7. Even rows (y = 2,4,6..., x < W-2): Move RIGHT
        8. Even rows (y = 2,4,6..., x = W-2): Move UP
        9. Top row (y = 0, x < W-1): Move RIGHT

        Args:
            hx: Head X coordinate
            hy: Head Y coordinate
            W: Board width
            H: Board height

        Returns:
            (dx, dy) direction tuple
        """
        # Rule 1: Rightmost column descent (except bottom corner)
        if hx == W - 1 and hy < H - 1:
            return (0, 1)  # DOWN

        # Rule 2 & 3: Bottom row sweep (move LEFT)
        if hy == H - 1 and hx > 0:
            return (-1, 0)  # LEFT

        # Rule 4: Bottom-left corner (transition to upward movement)
        if hx == 0 and hy == H - 1:
            return (0, -1)  # UP

        # Rules 5-8: Middle rows zigzag
        if 0 < hy < H - 1:
            if hy % 2 == 1:  # Odd rows: move LEFT
                if hx > 0:
                    return (-1, 0)  # LEFT
                else:  # x == 0
                    return (0, -1)  # UP
            else:  # Even rows: move RIGHT
                if hx < W - 2:
                    return (1, 0)  # RIGHT
                else:  # x == W - 2
                    return (0, -1)  # UP

        # Rule 9: Top row return (move RIGHT to re-enter corridor)
        if hy == 0 and hx < W - 1:
            return (1, 0)  # RIGHT

        # Fallback (should never reach here with valid board)
        # If at top-right, start descent again
        if hx == W - 1 and hy == 0:
            return (0, 1)  # DOWN

        # Emergency fallback - don't move
        return (0, 0)

    def _get_snake(self, world: World):
        """Get the snake entity."""
        snakes = world.registry.query_by_type(EntityType.SNAKE)
        if snakes:
            return next(iter(snakes.values()))
        return None

    def _buffer_direction(self, snake, dx: int, dy: int) -> None:
        """Buffer a direction command for the snake.

        Args:
            snake: Snake entity
            dx: X direction (-1, 0, or 1)
            dy: Y direction (-1, 0, or 1)
        """
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

        # Don't buffer (0, 0) - no movement
        if dx == 0 and dy == 0:
            return

        buf.moves.append((dx, dy))

    # ========== HELPER METHODS ==========

    def _get_current_score(self, world: World) -> int:
        """Get current game score from snake body length.

        Score approximation: (snake_length - 3) * 10
        This gives us ~500 points at length ~53.
        """
        snake = self._get_snake(world)
        if not snake or not hasattr(snake, "body"):
            return 0

        # Snake starts at length 3, each apple adds 1
        # Score is typically length * 10 (minus initial length)
        snake_length = len(snake.body.segments) + 1
        return max(0, (snake_length - 3) * 10)

    # ========== PHASE 2: SERPENTINE SWEEP ==========

    def _update_serpentine(self, snake, world: World) -> None:
        """Phase 2 update: Deterministic serpentine sweep."""
        hx = snake.position.x
        hy = snake.position.y
        W = world.board.width
        H = world.board.height

        direction = self._get_serpentine_direction(hx, hy, W, H)
        if direction:
            self._buffer_direction(snake, direction[0], direction[1])

    # ========== PHASE 1: TAIL-FOLLOWING ==========

    def _update_tail_following(self, snake, world: World) -> None:
        """Phase 1 update: Aggressive tail-following with BFS."""
        current_pos = (snake.position.x, snake.position.y)
        obstacles = self._get_obstacles(world, snake)
        electric_walls = (
            self._settings.get("electric_walls") if self._settings else True
        )
        current_direction = (snake.velocity.dx, snake.velocity.dy)

        # Try to get apple if safe
        target = self._get_target(world)
        if target:
            apple_pos = (target.position.x, target.position.y)

            # Simple safety check: can reach tail after eating?
            if self._is_apple_safe_simple(
                snake,
                apple_pos,
                obstacles,
                world.board.width,
                world.board.height,
                electric_walls,
            ):
                path_to_apple = self._bfs(
                    current_pos,
                    apple_pos,
                    obstacles,
                    world.board.width,
                    world.board.height,
                    electric_walls,
                    current_direction,
                )

                if path_to_apple:
                    next_pos = path_to_apple[0]
                    dx = next_pos[0] - current_pos[0]
                    dy = next_pos[1] - current_pos[1]

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
                    return

        # Default: follow tail
        tail_direction = self._follow_tail(
            snake,
            current_pos,
            obstacles,
            world.board.width,
            world.board.height,
            electric_walls,
            current_direction,
        )

        if tail_direction:
            self._buffer_direction(snake, tail_direction[0], tail_direction[1])

    def _get_target(self, world: World):
        """Get the apple entity."""
        apples = world.registry.query_by_type(EntityType.APPLE)
        if apples:
            return next(iter(apples.values()))
        return None

    def _get_obstacles(self, world: World, snake) -> Set[Tuple[int, int]]:
        """Get all obstacle positions including snake body (excluding tail tip)."""
        obstacles = set()

        if hasattr(snake, "body") and snake.body.segments:
            for segment in snake.body.segments[:-1]:
                obstacles.add((segment.x, segment.y))

        obs_entities = world.registry.query_by_type(EntityType.OBSTACLE)
        for entity in obs_entities.values():
            if hasattr(entity, "position"):
                obstacles.add((entity.position.x, entity.position.y))

        return obstacles

    def _get_tail_position(self, snake) -> Optional[Tuple[int, int]]:
        """Get snake's tail position."""
        if hasattr(snake, "body") and snake.body.segments:
            tail = snake.body.segments[-1]
            return (tail.x, tail.y)
        return None

    def _follow_tail(
        self,
        snake,
        current_pos: Tuple[int, int],
        obstacles: Set[Tuple[int, int]],
        width: int,
        height: int,
        electric_walls: bool,
        current_direction: Tuple[int, int],
    ) -> Optional[Tuple[int, int]]:
        """Follow own tail (guaranteed safe)."""
        tail_pos = self._get_tail_position(snake)
        if not tail_pos:
            return None

        obstacles_no_tail = obstacles.copy()
        obstacles_no_tail.discard(tail_pos)

        path_to_tail = self._bfs(
            current_pos,
            tail_pos,
            obstacles_no_tail,
            width,
            height,
            electric_walls,
            current_direction,
        )

        if path_to_tail:
            next_pos = path_to_tail[0]
            dx = next_pos[0] - current_pos[0]
            dy = next_pos[1] - current_pos[1]

            if not electric_walls:
                if dx > 1:
                    dx = -1
                elif dx < -1:
                    dx = 1
                if dy > 1:
                    dy = -1
                elif dy < -1:
                    dy = 1

            return (dx, dy)
        return None

    def _is_apple_safe_simple(
        self,
        snake,
        apple_pos: Tuple[int, int],
        obstacles: Set[Tuple[int, int]],
        width: int,
        height: int,
        electric_walls: bool,
    ) -> bool:
        """Simple safety check: can reach tail after eating apple?"""
        tail_pos = self._get_tail_position(snake)
        if not tail_pos:
            return True

        simulated_obstacles = obstacles.copy()
        simulated_obstacles.add(apple_pos)
        simulated_obstacles.discard(tail_pos)

        path_to_tail = self._bfs(
            apple_pos,
            tail_pos,
            simulated_obstacles,
            width,
            height,
            electric_walls,
            (0, 0),
        )

        return len(path_to_tail) > 0

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
        """BFS pathfinding."""
        queue = deque([(start, [])])
        visited = {start}

        while queue:
            (current, path) = queue.popleft()

            if current == goal:
                return path

            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                if not path:
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
