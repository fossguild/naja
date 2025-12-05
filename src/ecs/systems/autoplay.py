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

"""Autoplay system implementing John Tapsell's Perturbed Hamiltonian Cycle.

This is a faithful implementation of the algorithm described at:
https://johnflux.com/2015/05/02/nokia-6110-part-3-algorithms/

Algorithm Summary:
1. Pre-compute a Hamiltonian cycle covering the entire board
2. Assign each cell a "tour number" (position in the 1D cycle)
3. The key insight: head can take shortcuts as long as it doesn't "overtake" tail
4. cuttingAmountAvailable = distanceToTail - snakeLength - buffer
5. Choose the direction with HIGHEST path_distance within cuttingAmountAvailable
6. Disable shortcuts when snake covers >50% of board
"""

from typing import Optional, Any, Tuple, Set, Dict

from ecs.systems.base_system import BaseSystem
from ecs.world import World
from ecs.entities.entity import EntityType
from game.game_modes_registry import AUTOPLAY_MODE_NAME


class HamiltonianCycle:
    """Generates and manages a Hamiltonian cycle over a 2D grid.

    Uses a simple zigzag pattern that visits every cell exactly once.
    Each cell gets a "tour number" (0 to W*H-1).
    """

    def __init__(self, width: int, height: int):
        """Initialize and generate a Hamiltonian cycle."""
        self.width = width
        self.height = height
        self.board_size = width * height

        # Tour number for each cell: position in the cycle (0 to board_size-1)
        self._tour_numbers: Dict[Tuple[int, int], int] = {}

        # Generate the proper Hamiltonian cycle
        self._generate_cycle()

    def _generate_cycle(self) -> None:
        """Generate a proper Hamiltonian cycle that closes correctly.

        Pattern:
        - Row 0: go right from (0,0) to (W-1, 0)
        - Rows 1 to H-1: zigzag through columns 1 to W-1 (leaving column 0 empty)
        - Return path: go up column 0 from (0, H-1) to (0, 1)
        - This creates a closed cycle where all adjacent tour numbers are grid-adjacent

        Example for 4x4:
         0  1  2  3
        15  6  5  4
        14  7  8  9
        13 12 11 10

        The cycle: 0→1→2→3→4→5→6→7→8→9→10→11→12→13→14→15→0
        Every transition is exactly 1 grid cell (up/down/left/right).
        """
        self._tour_numbers.clear()
        number = 0

        # Row 0: go right from (0,0) to (W-1, 0)
        for x in range(self.width):
            self._tour_numbers[(x, 0)] = number
            number += 1

        # Inner zigzag: rows 1 to H-1, columns 1 to W-1
        for y in range(1, self.height):
            if y % 2 == 1:  # Odd row: go left from W-1 to 1
                for x in range(self.width - 1, 0, -1):
                    self._tour_numbers[(x, y)] = number
                    number += 1
            else:  # Even row: go right from 1 to W-1
                for x in range(1, self.width):
                    self._tour_numbers[(x, y)] = number
                    number += 1

        # Return path: column 0, from bottom (H-1) up to row 1
        for y in range(self.height - 1, 0, -1):
            self._tour_numbers[(0, y)] = number
            number += 1

    def get_tour_number(self, x: int, y: int) -> int:
        """Get the tour number for a cell."""
        return self._tour_numbers.get((x, y), 0)

    def path_distance(self, from_tour: int, to_tour: int) -> int:
        """Calculate distance along the cycle from one point to another.

        This is the key function - returns how many steps along the cycle
        from 'from_tour' to 'to_tour', wrapping around if needed.

        Following John Tapsell's original:
        if(a < b) return b - a - 1;
        return b - a - 1 + ARENA_SIZE;
        """
        if from_tour < to_tour:
            return to_tour - from_tour - 1
        return to_tour - from_tour - 1 + self.board_size

    def get_next_direction(self, x: int, y: int) -> Tuple[int, int]:
        """Get the direction to the next cell in the Hamiltonian cycle.

        This is used to explicitly follow the cycle when no shortcuts are safe.
        """
        current_tour = self.get_tour_number(x, y)
        next_tour = (current_tour + 1) % self.board_size

        # Find the cell with next_tour
        for pos, tour in self._tour_numbers.items():
            if tour == next_tour:
                dx = pos[0] - x
                dy = pos[1] - y
                return (dx, dy)

        # Fallback (shouldn't happen with valid cycle)
        return (1, 0)


class AutoplaySystem(BaseSystem):
    """System that controls the snake using Perturbed Hamiltonian Cycle.

    Faithful implementation of John Tapsell's algorithm:
    1. Calculate cuttingAmountAvailable (how far we can shortcut)
    2. For each valid direction, check if path_distance <= cuttingAmountAvailable
    3. Choose direction with HIGHEST path_distance (maximum safe shortcut)
    4. If no shortcut available, follow any valid direction

    Reads: Position, Velocity, SnakeBody
    Writes: InputBuffer (simulates input)
    """

    def __init__(self, game_mode: str, settings: Optional[Any] = None):
        """Initialize the AutoplaySystem."""
        self._game_mode = game_mode
        self._settings = settings
        self._cycle: Optional[HamiltonianCycle] = None
        self._initialized = False

    def update(self, world: World) -> None:
        """Update the snake's direction using Perturbed Hamiltonian Cycle."""
        if self._game_mode != AUTOPLAY_MODE_NAME:
            return

        snake = self._get_snake(world)
        if not snake:
            return

        # Get head position
        head_x = snake.position.x
        head_y = snake.position.y

        # Initialize on first update
        if not self._initialized:
            self._cycle = HamiltonianCycle(world.board.width, world.board.height)
            self._initialized = True
            print(
                f"[Autoplay] Generated Hamiltonian cycle for "
                f"{world.board.width}x{world.board.height} board"
            )

            # Compute first safe direction
            first_dir = self._get_new_direction(
                snake,
                world,
                head_x,
                head_y,
                0,
                0,  # No current velocity
            )

            if first_dir:
                self._buffer_direction(snake, first_dir[0], first_dir[1])
                print(f"[Autoplay] First direction: {first_dir}")

            # Signal game can start
            game_state_entities = world.registry.query_by_component("game_state")
            if game_state_entities:
                entity = next(iter(game_state_entities.values()))
                if hasattr(entity, "game_state"):
                    entity.game_state.game_started = True
                    print("[Autoplay] Game started - first direction issued")
            return

        # Normal update
        best_dir = self._get_new_direction(
            snake, world, head_x, head_y, snake.velocity.dx, snake.velocity.dy
        )

        if best_dir:
            self._buffer_direction(snake, best_dir[0], best_dir[1])

    def _get_new_direction(
        self,
        snake,
        world: World,
        head_x: int,
        head_y: int,
        current_dx: int,
        current_dy: int,
    ) -> Optional[Tuple[int, int]]:
        """Get new direction following John Tapsell's algorithm exactly.

        This is a faithful translation of his aiGetNewSnakeDirection function.
        """
        width = world.board.width
        height = world.board.height

        # Get head tour number
        head_tour = self._cycle.get_tour_number(head_x, head_y)

        # Get food position and tour number
        apple = self._get_target(world)
        if apple:
            food_x = apple.position.x
            food_y = apple.position.y
            food_tour = self._cycle.get_tour_number(food_x, food_y)
        else:
            food_tour = head_tour
            food_x, food_y = head_x, head_y

        # Get tail position and tour number
        # IMPORTANT: For size-1 snake (no segments), use head position as tail
        tail_pos = self._get_tail_position(snake)
        if tail_pos:
            tail_x, tail_y = tail_pos
        else:
            # Snake has no body segments - use head as tail
            # This gives distanceToTail = board_size - 1 (almost full cycle)
            tail_x, tail_y = head_x, head_y

        tail_tour = self._cycle.get_tour_number(tail_x, tail_y)

        # Calculate distances
        distance_to_food = self._cycle.path_distance(head_tour, food_tour)
        distance_to_tail = self._cycle.path_distance(head_tour, tail_tour)

        # Get snake length (including growth pending)
        snake_length = self._get_snake_length(snake)

        # Calculate cutting amount available (following Tapsell's formula)
        # cuttingAmountAvailable = distanceToTail - snake.growth_length - 3
        growth_length = 0  # We don't track pending growth separately
        cutting_available = distance_to_tail - snake_length - growth_length - 3

        # Count empty squares
        num_empty_squares = self._cycle.board_size - snake_length

        # If snake covers >50% of board, don't take shortcuts
        if num_empty_squares < self._cycle.board_size // 2:
            cutting_available = 0
        elif distance_to_food < distance_to_tail:
            # We will eat food on the way to tail, account for growth
            cutting_available -= 1  # food.value = 1 in our game

            # Extra safety buffer if food might spawn in front
            if (distance_to_tail - distance_to_food) * 4 > num_empty_squares:
                cutting_available -= 10

        # Cap cutting to distance to food (no point cutting more)
        cutting_desired = distance_to_food
        if cutting_desired < cutting_available:
            cutting_available = cutting_desired

        if cutting_available < 0:
            cutting_available = 0

        # Get obstacles (snake body)
        obstacles = self._get_obstacles(world, snake)

        # Check which directions we can go
        directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]  # Right, Left, Down, Up

        best_dir = None
        best_dist = -1

        for dx, dy in directions:
            nx, ny = head_x + dx, head_y + dy

            # Check bounds
            if nx < 0 or nx >= width or ny < 0 or ny >= height:
                continue

            # Check collision with snake body
            if (nx, ny) in obstacles:
                continue

            # Don't reverse
            if current_dx != 0 or current_dy != 0:
                if dx == -current_dx and dy == -current_dy:
                    continue

            # Calculate path distance for this move
            next_tour = self._cycle.get_tour_number(nx, ny)
            dist = self._cycle.path_distance(head_tour, next_tour)

            # Following Tapsell: choose direction with HIGHEST dist within limit
            if dist <= cutting_available and dist > best_dist:
                best_dir = (dx, dy)
                best_dist = dist

        # If we found a valid shortcut, use it
        if best_dist >= 0:
            return best_dir

        # No shortcut available - FOLLOW THE HAMILTONIAN CYCLE
        # This is the key fix: always follow the cycle, not just any direction
        cycle_dir = self._cycle.get_next_direction(head_x, head_y)
        cycle_dx, cycle_dy = cycle_dir
        cycle_nx, cycle_ny = head_x + cycle_dx, head_y + cycle_dy

        # Check if cycle direction is valid
        if 0 <= cycle_nx < width and 0 <= cycle_ny < height:
            if (cycle_nx, cycle_ny) not in obstacles:
                is_reverse = (current_dx != 0 or current_dy != 0) and (
                    cycle_dx == -current_dx and cycle_dy == -current_dy
                )
                if not is_reverse:
                    return (cycle_dx, cycle_dy)

        # Cycle direction blocked - pick any valid direction (emergency fallback)
        for dx, dy in directions:
            nx, ny = head_x + dx, head_y + dy

            if nx < 0 or nx >= width or ny < 0 or ny >= height:
                continue

            if (nx, ny) in obstacles:
                continue

            if current_dx != 0 or current_dy != 0:
                if dx == -current_dx and dy == -current_dy:
                    continue

            return (dx, dy)

        # Absolute last resort (shouldn't happen)
        return (1, 0)

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
        """Get the snake's current length (head + body segments)."""
        if hasattr(snake, "body") and snake.body.segments:
            return len(snake.body.segments) + 1
        return 1

    def _get_obstacles(self, world: World, snake) -> Set[Tuple[int, int]]:
        """Get all obstacle positions including snake body (excluding tail tip)."""
        obstacles = set()

        if hasattr(snake, "body") and snake.body.segments:
            # Exclude tail tip since it will move
            for segment in snake.body.segments[:-1]:
                obstacles.add((segment.x, segment.y))

        obs_entities = world.registry.query_by_type(EntityType.OBSTACLE)
        for entity in obs_entities.values():
            if hasattr(entity, "position"):
                obstacles.add((entity.position.x, entity.position.y))

        return obstacles

    def _buffer_direction(self, snake, dx: int, dy: int) -> None:
        """Buffer a direction command for the snake."""
        if not hasattr(snake, "input_buffer") or snake.input_buffer is None:
            return

        buf = snake.input_buffer

        # Don't overflow buffer
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
