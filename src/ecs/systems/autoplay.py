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
import random

from ecs.systems.base_system import BaseSystem
from ecs.world import World
from ecs.entities.entity import EntityType
from game.game_modes_registry import AUTOPLAY_MODE_NAME


class HamiltonianCycle:
    """Generates and manages a Hamiltonian cycle over a 2D grid.

    Uses Prim's algorithm to generate a random spanning tree maze at half resolution,
    then walks the maze edges to create an interesting Hamiltonian cycle pattern.
    This creates visually engaging, randomized patterns like John Tapsell's original.
    """

    def __init__(self, width: int, height: int):
        """Initialize and generate a Hamiltonian cycle."""
        self.width = width
        self.height = height
        self.board_size = width * height

        # Half-size maze dimensions
        self.maze_width = width // 2
        self.maze_height = height // 2

        # Maze walls (which walls are removed to form passages)
        self._can_go_right: Set[Tuple[int, int]] = set()
        self._can_go_down: Set[Tuple[int, int]] = set()

        # Tour number for each cell: position in the cycle (0 to board_size-1)
        self._tour_numbers: Dict[Tuple[int, int], int] = {}

        # Generate the maze-based Hamiltonian cycle
        self._generate_maze()
        self._generate_tour_from_maze()

    def _generate_maze(self) -> None:
        """Generate a random spanning tree maze using randomized DFS.

        Creates a maze at half the grid resolution. Walking the edges
        of this maze produces a Hamiltonian cycle on the full grid.
        """
        self._can_go_right.clear()
        self._can_go_down.clear()

        if self.maze_width <= 0 or self.maze_height <= 0:
            return

        visited: Set[Tuple[int, int]] = set()

        # Start from (0, 0)
        self._generate_maze_recursive(-1, -1, 0, 0, visited)

    def _generate_maze_recursive(
        self, from_x: int, from_y: int, x: int, y: int, visited: Set[Tuple[int, int]]
    ) -> None:
        """Recursively generate maze using randomized DFS."""
        # Check bounds
        if x < 0 or y < 0 or x >= self.maze_width or y >= self.maze_height:
            return

        # Already visited
        if (x, y) in visited:
            return

        visited.add((x, y))

        # Mark passage from previous cell
        if from_x >= 0:
            if from_x < x:
                self._can_go_right.add((from_x, from_y))
            elif from_x > x:
                self._can_go_right.add((x, y))
            elif from_y < y:
                self._can_go_down.add((from_x, from_y))
            elif from_y > y:
                self._can_go_down.add((x, y))

        # Visit neighbors in random order (randomized DFS creates random spanning tree)
        neighbors = [(x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)]
        random.shuffle(neighbors)

        for nx, ny in neighbors:
            self._generate_maze_recursive(x, y, nx, ny, visited)

    def _can_go_left(self, x: int, y: int) -> bool:
        """Check if can go left in maze."""
        if x <= 0:
            return False
        return (x - 1, y) in self._can_go_right

    def _can_go_up(self, x: int, y: int) -> bool:
        """Check if can go up in maze."""
        if y <= 0:
            return False
        return (x, y - 1) in self._can_go_down

    def _find_next_dir(self, x: int, y: int, dir: str) -> str:
        """Find next direction following 'turn left when possible' rule.

        This walks the maze edges, creating a Hamiltonian cycle.
        """
        # Turn left preference order for each direction
        if dir == "right":
            if self._can_go_up(x, y):
                return "up"
            if (x, y) in self._can_go_right:
                return "right"
            if (x, y) in self._can_go_down:
                return "down"
            return "left"
        elif dir == "down":
            if (x, y) in self._can_go_right:
                return "right"
            if (x, y) in self._can_go_down:
                return "down"
            if self._can_go_left(x, y):
                return "left"
            return "up"
        elif dir == "left":
            if (x, y) in self._can_go_down:
                return "down"
            if self._can_go_left(x, y):
                return "left"
            if self._can_go_up(x, y):
                return "up"
            return "right"
        else:  # up
            if self._can_go_left(x, y):
                return "left"
            if self._can_go_up(x, y):
                return "up"
            if (x, y) in self._can_go_right:
                return "right"
            return "down"

    def _set_tour_number(self, x: int, y: int, number: int) -> None:
        """Set tour number for a cell (only if not already set)."""
        if (x, y) not in self._tour_numbers:
            self._tour_numbers[(x, y)] = number

    def _generate_tour_from_maze(self) -> None:
        """Walk the maze edges to generate Hamiltonian cycle tour numbers."""
        self._tour_numbers.clear()

        if self.maze_width <= 0 or self.maze_height <= 0:
            # Fallback for very small grids
            for y in range(self.height):
                for x in range(self.width):
                    self._tour_numbers[(x, y)] = y * self.width + x
            return

        # Start at maze cell (0, 0), direction based on maze structure
        x, y = 0, 0
        start_dir = "up" if (0, 0) in self._can_go_down else "left"
        dir = start_dir
        number = 0

        # Walk the entire cycle
        while number < self.board_size:
            next_dir = self._find_next_dir(x, y, dir)

            # Fill in the 2x2 block for this maze cell based on direction
            # Each maze cell corresponds to a 2x2 block in the full grid
            bx, by = x * 2, y * 2

            if dir == "right":
                self._set_tour_number(bx, by, number)
                number += 1
                if next_dir in ("right", "down", "left"):
                    self._set_tour_number(bx + 1, by, number)
                    number += 1
                if next_dir in ("down", "left"):
                    self._set_tour_number(bx + 1, by + 1, number)
                    number += 1
                if next_dir == "left":
                    self._set_tour_number(bx, by + 1, number)
                    number += 1
            elif dir == "down":
                self._set_tour_number(bx + 1, by, number)
                number += 1
                if next_dir in ("down", "left", "up"):
                    self._set_tour_number(bx + 1, by + 1, number)
                    number += 1
                if next_dir in ("left", "up"):
                    self._set_tour_number(bx, by + 1, number)
                    number += 1
                if next_dir == "up":
                    self._set_tour_number(bx, by, number)
                    number += 1
            elif dir == "left":
                self._set_tour_number(bx + 1, by + 1, number)
                number += 1
                if next_dir in ("left", "up", "right"):
                    self._set_tour_number(bx, by + 1, number)
                    number += 1
                if next_dir in ("up", "right"):
                    self._set_tour_number(bx, by, number)
                    number += 1
                if next_dir == "right":
                    self._set_tour_number(bx + 1, by, number)
                    number += 1
            else:  # up
                self._set_tour_number(bx, by + 1, number)
                number += 1
                if next_dir in ("up", "right", "down"):
                    self._set_tour_number(bx, by, number)
                    number += 1
                if next_dir in ("right", "down"):
                    self._set_tour_number(bx + 1, by, number)
                    number += 1
                if next_dir == "down":
                    self._set_tour_number(bx + 1, by + 1, number)
                    number += 1

            # Move to next maze cell
            dir = next_dir
            if dir == "right":
                x += 1
            elif dir == "left":
                x -= 1
            elif dir == "down":
                y += 1
            else:
                y -= 1

            # Check if we've returned to start
            if x == 0 and y == 0 and dir == start_dir:
                break

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
        self._game_over_service = None  # Set by gameplay scene

    def set_game_over_service(self, service) -> None:
        """Set the game over service for victory handling."""
        self._game_over_service = service

    def update(self, world: World) -> None:
        """Update the snake's direction using Perturbed Hamiltonian Cycle."""
        if self._game_mode != AUTOPLAY_MODE_NAME:
            return

        snake = self._get_snake(world)
        if not snake:
            return

        # Check for victory (snake fills entire board)
        if self._check_victory(snake, world):
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

    def _check_victory(self, snake, world: World) -> bool:
        """Check if snake has filled the entire board (victory condition).

        Returns True if victory was triggered, False otherwise.
        """
        board_size = world.board.width * world.board.height
        snake_length = self._get_snake_length(snake)

        # Victory when snake fills entire board
        if snake_length >= board_size:
            if self._game_over_service:
                self._game_over_service.handle_victory(world)
            else:
                print("🏆 VICTORY! Snake filled the board")
            return True

        return False

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
