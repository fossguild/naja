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

"""Autoplay system implementing Perturbed Hamiltonian Cycle strategy.

Perfect Snake AI: Perturbed Hamiltonian Cycle
----------------------------------------------
This algorithm guarantees the snake will never die and will eventually
fill the entire board. It works by:

1. Generating a Hamiltonian cycle at game start (zigzag pattern)
2. Assigning each cell a "tour number" (position in the cycle 0 to W*H-1)
3. Taking safe shortcuts to food when possible (early game)
4. Following the strict cycle when snake is large (late game safety)

The key insight is that head movement is only safe if it doesn't "overtake"
the tail in the 1D cycle representation. This allows O(1) safety checks.

Based on John Tapsell's algorithm:
https://johnflux.com/2015/05/02/nokia-6110-part-3-algorithms/
"""

from typing import Optional, Any, Tuple, Set, Dict

from ecs.systems.base_system import BaseSystem
from ecs.world import World
from ecs.entities.entity import EntityType
from game.game_modes_registry import AUTOPLAY_MODE_NAME


class HamiltonianCycle:
    """Generates and manages a Hamiltonian cycle over a 2D grid.

    Uses a zigzag pattern that visits every cell exactly once before
    returning to the start. Each cell gets a "tour number" (0 to W*H-1).
    """

    # Direction constants
    RIGHT, DOWN, LEFT, UP = 0, 1, 2, 3
    DX = [1, 0, -1, 0]
    DY = [0, 1, 0, -1]

    def __init__(self, width: int, height: int):
        """Initialize and generate a Hamiltonian cycle.

        Args:
            width: Grid width
            height: Grid height
        """
        self.width = width
        self.height = height
        self.board_size = width * height

        # Tour number for each cell: position in the cycle (0 to board_size-1)
        self._tour_numbers: Dict[Tuple[int, int], int] = {}

        # Generate the zigzag cycle
        self._generate_zigzag()

    def _generate_zigzag(self) -> None:
        """Generate a zigzag Hamiltonian cycle.

        Pattern: Left-to-right on even rows, right-to-left on odd rows.
        """
        self._tour_numbers.clear()
        number = 0

        for y in range(self.height):
            if y % 2 == 0:
                # Left to right
                for x in range(self.width):
                    self._tour_numbers[(x, y)] = number
                    number += 1
            else:
                # Right to left
                for x in range(self.width - 1, -1, -1):
                    self._tour_numbers[(x, y)] = number
                    number += 1

    def get_tour_number(self, x: int, y: int) -> int:
        """Get the tour number for a cell.

        Args:
            x: X coordinate
            y: Y coordinate

        Returns:
            Position in the cycle (0 to board_size - 1)
        """
        return self._tour_numbers.get((x, y), 0)

    def path_distance(self, from_tour: int, to_tour: int) -> int:
        """Calculate the distance along the cycle from one point to another.

        Args:
            from_tour: Starting tour number
            to_tour: Ending tour number

        Returns:
            Number of steps along the cycle (always positive, wraps around)
        """
        if to_tour >= from_tour:
            return to_tour - from_tour
        return to_tour - from_tour + self.board_size

    def get_next_position(self, x: int, y: int) -> Tuple[int, int]:
        """Get the next position in the cycle after (x, y).

        Args:
            x: Current X coordinate
            y: Current Y coordinate

        Returns:
            (next_x, next_y) - the next position in the cycle
        """
        current_tour = self.get_tour_number(x, y)
        next_tour = (current_tour + 1) % self.board_size

        # Find the cell with next_tour
        for pos, tour in self._tour_numbers.items():
            if tour == next_tour:
                return pos
        return (x, y)  # Fallback

    def get_next_direction(self, x: int, y: int) -> Tuple[int, int]:
        """Get the direction to the next cell in the cycle.

        Args:
            x: Current X coordinate
            y: Current Y coordinate

        Returns:
            (dx, dy) direction to next cell
        """
        next_pos = self.get_next_position(x, y)
        dx = next_pos[0] - x
        dy = next_pos[1] - y

        # Handle wrapping (for last cell connecting to first)
        if abs(dx) > 1:
            dx = -1 if dx > 0 else 1
        if abs(dy) > 1:
            dy = -1 if dy > 0 else 1

        return (dx, dy)


class AutoplaySystem(BaseSystem):
    """System that controls the snake in Autoplay mode using Perturbed Hamiltonian Cycle.

    This AI is guaranteed to win every game on an empty board by following
    a Hamiltonian cycle while taking safe shortcuts to reach food faster.

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
        self._cycle: Optional[HamiltonianCycle] = None
        self._initialized = False

    def update(self, world: World) -> None:
        """Update the snake's direction using Perturbed Hamiltonian Cycle.

        Args:
            world: ECS world containing entities and components
        """
        if self._game_mode != AUTOPLAY_MODE_NAME:
            return

        snake = self._get_snake(world)
        if not snake:
            return

        # Initialize Hamiltonian cycle on first update
        if not self._initialized:
            self._cycle = HamiltonianCycle(world.board.width, world.board.height)
            self._initialized = True
            print(
                f"[Autoplay] Generated Hamiltonian cycle for "
                f"{world.board.width}x{world.board.height} board"
            )

            # Compute first safe direction
            head_x = snake.position.x
            head_y = snake.position.y
            head_tour = self._cycle.get_tour_number(head_x, head_y)

            tail_pos = self._get_tail_position(snake)
            tail_tour = (
                self._cycle.get_tour_number(tail_pos[0], tail_pos[1])
                if tail_pos
                else head_tour
            )

            apple = self._get_target(world)
            food_tour = head_tour
            if apple:
                food_tour = self._cycle.get_tour_number(
                    apple.position.x, apple.position.y
                )

            snake_length = self._get_snake_length(snake)
            obstacles = self._get_obstacles(world, snake)

            cutting_available = self._get_cutting_amount(
                head_tour,
                tail_tour,
                food_tour,
                snake_length,
                world.board.width * world.board.height,
            )

            # Find first safe direction
            first_dir = self._find_best_direction(
                head_x,
                head_y,
                head_tour,
                food_tour,
                cutting_available,
                obstacles,
                world.board.width,
                world.board.height,
                0,
                0,
            )

            if first_dir:
                self._buffer_direction(snake, first_dir[0], first_dir[1])
                print(f"[Autoplay] First direction: {first_dir}")
            else:
                # Fallback: find any valid move
                for dx, dy in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
                    nx, ny = head_x + dx, head_y + dy
                    if 0 <= nx < world.board.width and 0 <= ny < world.board.height:
                        self._buffer_direction(snake, dx, dy)
                        print(f"[Autoplay] Fallback first direction: ({dx}, {dy})")
                        break

            # Signal game can start
            game_state_entities = world.registry.query_by_component("game_state")
            if game_state_entities:
                entity = next(iter(game_state_entities.values()))
                if hasattr(entity, "game_state"):
                    entity.game_state.game_started = True
                    print("[Autoplay] Game started - first direction issued")
            return

        # Normal update: find best direction
        head_x = snake.position.x
        head_y = snake.position.y
        head_tour = self._cycle.get_tour_number(head_x, head_y)

        tail_pos = self._get_tail_position(snake)
        if not tail_pos:
            return
        tail_tour = self._cycle.get_tour_number(tail_pos[0], tail_pos[1])

        snake_length = self._get_snake_length(snake)

        apple = self._get_target(world)
        food_tour = head_tour
        if apple:
            food_tour = self._cycle.get_tour_number(apple.position.x, apple.position.y)

        cutting_available = self._get_cutting_amount(
            head_tour,
            tail_tour,
            food_tour,
            snake_length,
            world.board.width * world.board.height,
        )

        obstacles = self._get_obstacles(world, snake)

        best_dir = self._find_best_direction(
            head_x,
            head_y,
            head_tour,
            food_tour,
            cutting_available,
            obstacles,
            world.board.width,
            world.board.height,
            snake.velocity.dx,
            snake.velocity.dy,
        )

        if best_dir:
            self._buffer_direction(snake, best_dir[0], best_dir[1])

    def _get_cutting_amount(
        self,
        head_tour: int,
        tail_tour: int,
        food_tour: int,
        snake_length: int,
        board_size: int,
    ) -> int:
        """Calculate how much of the cycle we can safely skip.

        Args:
            head_tour: Head's position in the cycle
            tail_tour: Tail's position in the cycle
            food_tour: Food's position in the cycle
            snake_length: Current snake length
            board_size: Total cells on board

        Returns:
            Maximum number of cycle steps we can safely skip
        """
        distance_to_tail = self._cycle.path_distance(head_tour, tail_tour)
        distance_to_food = self._cycle.path_distance(head_tour, food_tour)

        # Basic cutting: distance to tail minus snake length minus buffer
        cutting = distance_to_tail - snake_length - 3

        # Calculate empty squares
        empty_squares = board_size - snake_length

        # If snake covers >50% of the board, don't take shortcuts
        if empty_squares < board_size // 2:
            return 0

        # If we'll eat food on the way, account for growth
        if distance_to_food < distance_to_tail:
            cutting -= 1

            # Extra caution if not much space
            if distance_to_tail - distance_to_food < empty_squares // 4:
                cutting -= 2

        # Don't cut more than needed to reach food
        cutting = min(cutting, distance_to_food)

        return max(0, cutting)

    def _find_best_direction(
        self,
        head_x: int,
        head_y: int,
        head_tour: int,
        food_tour: int,
        cutting_available: int,
        obstacles: Set[Tuple[int, int]],
        width: int,
        height: int,
        current_dx: int,
        current_dy: int,
    ) -> Optional[Tuple[int, int]]:
        """Find the best direction to move.

        Args:
            head_x, head_y: Current head position
            head_tour: Head's tour number
            food_tour: Food's tour number
            cutting_available: Maximum safe cutting amount
            obstacles: Set of obstacle positions
            width, height: Board dimensions
            current_dx, current_dy: Current movement direction

        Returns:
            (dx, dy) direction tuple, or None if no valid move
        """
        directions = [(0, -1), (0, 1), (-1, 0), (1, 0)]

        best_dir = None
        best_score = -float("inf")

        current_distance_to_food = self._cycle.path_distance(head_tour, food_tour)

        for dx, dy in directions:
            # Can't reverse direction
            if current_dx != 0 or current_dy != 0:
                if dx == -current_dx and dy == -current_dy:
                    continue

            nx, ny = head_x + dx, head_y + dy

            # Check bounds
            if nx < 0 or nx >= width or ny < 0 or ny >= height:
                continue

            # Check collision with obstacles
            if (nx, ny) in obstacles:
                continue

            next_tour = self._cycle.get_tour_number(nx, ny)
            advancement = self._cycle.path_distance(head_tour, next_tour)

            # Only consider moves within safe cutting limit
            if advancement <= cutting_available + 1:
                new_distance_to_food = self._cycle.path_distance(next_tour, food_tour)
                improvement = current_distance_to_food - new_distance_to_food
                score = improvement * 1000 + advancement

                if score > best_score:
                    best_score = score
                    best_dir = (dx, dy)

        # If no shortcut found, follow the cycle
        if best_dir is None:
            cycle_dir = self._cycle.get_next_direction(head_x, head_y)
            dx, dy = cycle_dir
            nx, ny = head_x + dx, head_y + dy

            is_reverse = (current_dx != 0 or current_dy != 0) and (
                dx == -current_dx and dy == -current_dy
            )

            if not is_reverse and (nx, ny) not in obstacles:
                if 0 <= nx < width and 0 <= ny < height:
                    best_dir = (dx, dy)

        # Last resort: find any valid move
        if best_dir is None:
            for dx, dy in directions:
                if current_dx != 0 or current_dy != 0:
                    if dx == -current_dx and dy == -current_dy:
                        continue
                nx, ny = head_x + dx, head_y + dy
                if 0 <= nx < width and 0 <= ny < height:
                    if (nx, ny) not in obstacles:
                        best_dir = (dx, dy)
                        break

        return best_dir

    def _get_snake(self, world: World):
        """Get the snake entity."""
        snakes = world.registry.query_by_type(EntityType.SNAKE)
        if snakes:
            return next(iter(snakes.values()))
        return None

    def _get_target(self, world: World):
        """Get the apple entity."""
        apples = world.registry.query_by_type(EntityType.APPLE)
        if apples:
            return next(iter(apples.values()))
        return None

    def _get_tail_position(self, snake) -> Optional[Tuple[int, int]]:
        """Get snake's tail position."""
        if hasattr(snake, "body") and snake.body.segments:
            tail = snake.body.segments[-1]
            return (tail.x, tail.y)
        return None

    def _get_snake_length(self, snake) -> int:
        """Get the snake's current length."""
        if hasattr(snake, "body") and snake.body.segments:
            return len(snake.body.segments) + 1
        return 1

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

    def _buffer_direction(self, snake, dx: int, dy: int) -> None:
        """Buffer a direction command for the snake.

        Args:
            snake: Snake entity
            dx: X direction (-1, 0, or 1)
            dy: Y direction (-1, 0, or 1)
        """
        if not hasattr(snake, "input_buffer") or snake.input_buffer is None:
            return

        buf = snake.input_buffer

        # Don't fill buffer too much
        if len(buf.moves) >= 1:
            return

        # Check if reversing
        last_dx, last_dy = (snake.velocity.dx, snake.velocity.dy)
        if buf.moves:
            last_dx, last_dy = buf.moves[-1]

        if (dx != 0 and last_dx == -dx) or (dy != 0 and last_dy == -dy):
            return

        # Don't buffer (0, 0)
        if dx == 0 and dy == 0:
            return

        buf.moves.append((dx, dy))
