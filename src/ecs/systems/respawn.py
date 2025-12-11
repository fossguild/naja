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

"""Respawn system for handling snake respawns in PvP mode."""

import random
from typing import Optional

from ecs.systems.base_system import BaseSystem
from ecs.world import World
from ecs.entities.entity import EntityType
from game.game_modes_registry import PLAYER_VS_PLAYER_MODE_NAME


class RespawnSystem(BaseSystem):
    """System for handling snake respawns after death.

    Reads: RespawnTimer, Lives, Position, SnakeBody, GameState
    Writes: RespawnTimer, Position, SnakeBody, Velocity
    Queries:
        - Snake entities (EntityType.SNAKE)
        - GameState entity (component "game_state")

    Responsibilities:
    - Count down respawn timers
    - Respawn snakes at valid positions after timer expires
    - Reset snake state (position, body, velocity)
    """

    RESPAWN_TIME_MS = 3000.0  # 3 seconds

    def __init__(self):
        """Initialize the RespawnSystem."""
        pass

    def update(self, world: World) -> None:
        """Update respawn timers and respawn snakes when ready.

        Args:
            world: ECS world to query entities
        """
        # assume 16ms per frame (60 FPS)
        dt_ms = 16.0

        # only run in Player vs Player mode
        game_state = self._get_game_state(world)
        if not game_state or game_state.game_mode != PLAYER_VS_PLAYER_MODE_NAME:
            return

        # query all snakes with respawn timers
        snakes = world.registry.query_by_type(EntityType.SNAKE)

        respawning_count = 0
        for snake_id, snake in snakes.items():
            if not hasattr(snake, "respawn_timer") or not hasattr(snake, "lives"):
                continue

            respawn_timer = snake.respawn_timer

            # if snake is respawning, count down the timer
            if respawn_timer.is_respawning:
                respawning_count += 1
                player_name = (
                    f"Player {snake.player_id.player_number}"
                    if hasattr(snake, "player_id")
                    else f"Snake {snake_id}"
                )

                old_time = respawn_timer.time_remaining_ms
                respawn_timer.time_remaining_ms -= dt_ms

                if (
                    respawning_count == 1
                ):  # Only print for first respawning snake to avoid spam
                    print(
                        f"{player_name} respawn timer: {old_time:.0f}ms -> {respawn_timer.time_remaining_ms:.0f}ms"
                    )

                # time to respawn?
                if respawn_timer.time_remaining_ms <= 0:
                    print(f"Timer expired for {player_name}! Respawning now...")
                    self._respawn_snake(world, snake_id, snake)
                    respawn_timer.is_respawning = False
                    respawn_timer.time_remaining_ms = 0.0

    def _get_game_state(self, world: World):
        """Get the game state entity."""
        game_states = world.registry.query_by_component("game_state")
        for _, entity in game_states.items():
            return entity.game_state
        return None

    def _respawn_snake(self, world: World, snake_id: int, snake) -> None:
        """Respawn a snake at a valid position.

        Args:
            world: ECS world
            snake_id: Entity ID of the snake
            snake: Snake entity
        """
        print(f"Respawning snake {snake_id}...")

        # find a valid spawn position
        grid = self._get_grid(world)
        if not grid:
            print("No grid found!")
            return

        spawn_pos = self._find_valid_spawn_position(world, grid)
        if not spawn_pos:
            print("No valid spawn position found!")
            return

        print(f"Spawning at position: {spawn_pos}")

        # reset snake position
        if hasattr(snake, "position"):
            snake.position.x = spawn_pos[0]
            snake.position.y = spawn_pos[1]
            snake.position.prev_x = spawn_pos[0]
            snake.position.prev_y = spawn_pos[1]

        # reset snake body - IMPORTANT: Set alive to True
        if hasattr(snake, "body"):
            snake.body.segments = []
            snake.body.size = 1
            snake.body.alive = True  # Make sure snake is alive
            snake.body.pending_growth = 0

        # reset velocity to a random direction
        if hasattr(snake, "velocity"):
            directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]
            dx, dy = random.choice(directions)
            snake.velocity.dx = dx
            snake.velocity.dy = dy

        print(f"Snake respawned successfully at {spawn_pos}")

    def _get_grid(self, world: World):
        """Get the grid component from world.board."""
        # Use world.board directly instead of querying components
        if hasattr(world, "board"):
            return world.board
        return None

    def _find_valid_spawn_position(
        self, world: World, board
    ) -> Optional[tuple[int, int]]:
        """Find a valid position to spawn a snake.

        Args:
            world: ECS world
            board: Board object with width and height

        Returns:
            Tuple of (x, y) coordinates, or None if no valid position found
        """
        # get all occupied positions
        occupied = set()

        # add snake positions
        snakes = world.registry.query_by_type(EntityType.SNAKE)
        for _, snake in snakes.items():
            if (
                hasattr(snake, "position")
                and hasattr(snake, "body")
                and snake.body.alive
            ):
                occupied.add((snake.position.x, snake.position.y))
                if hasattr(snake, "body"):
                    for segment in snake.body.segments:
                        occupied.add((segment.x, segment.y))

        # add apple positions
        apples = world.registry.query_by_type(EntityType.APPLE)
        for _, apple in apples.items():
            if hasattr(apple, "position"):
                occupied.add((apple.position.x, apple.position.y))

        # add obstacle positions
        obstacles = world.registry.query_by_type(EntityType.OBSTACLE)
        for _, obstacle in obstacles.items():
            if hasattr(obstacle, "position"):
                occupied.add((obstacle.position.x, obstacle.position.y))

        # try to find a valid position (with some margin from edges)
        margin = 2
        attempts = 0
        max_attempts = 100

        while attempts < max_attempts:
            x = random.randint(margin, board.width - margin - 1)
            y = random.randint(margin, board.height - margin - 1)

            if (x, y) not in occupied:
                return (x, y)

            attempts += 1

        # if we couldn't find a position with margin, try anywhere
        attempts = 0
        while attempts < max_attempts:
            x = random.randint(0, board.width - 1)
            y = random.randint(0, board.height - 1)

            if (x, y) not in occupied:
                return (x, y)

            attempts += 1

        return None

    def trigger_respawn(self, snake) -> None:
        """Trigger a respawn for a snake.

        Args:
            snake: Snake entity to respawn
        """
        if hasattr(snake, "respawn_timer") and hasattr(snake, "lives"):
            # check if snake has lives left
            if snake.lives.remaining > 0:
                player_name = (
                    f"Player {snake.player_id.player_number}"
                    if hasattr(snake, "player_id")
                    else "Snake"
                )
                print(
                    f"Triggering respawn for {player_name}. Timer: {self.RESPAWN_TIME_MS}ms"
                )

                snake.respawn_timer.is_respawning = True
                snake.respawn_timer.time_remaining_ms = self.RESPAWN_TIME_MS

                # make snake invisible/inactive during respawn
                if hasattr(snake, "body"):
                    snake.body.alive = False
                    print(f"{player_name} set to not alive during respawn countdown")
