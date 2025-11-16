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

Follows proper ECS architecture by querying world directly.
"""

from typing import Optional, Any

from ecs.systems.base_system import BaseSystem
from ecs.world import World


class CollisionSystem(BaseSystem):
    """System for detecting all types of collisions.

    Reads: Position, Velocity, SnakeBody, GameState, Board
    Writes: GameState (death), SnakeBody (size), Score, Velocity (speed)
    Queries:
        - Snake entity (EntityType.SNAKE)
        - Apple entities (EntityType.APPLE)
        - Obstacle entities (EntityType.OBSTACLE)
        - Score entities (component "score")
        - GameState entity (component "game_state")

    Responsibilities:
    - Detect wall collisions (electric mode only)
    - Detect self-bite collisions
    - Detect obstacle collisions
    - Detect apple collisions
    - Handle death (modify GameState, play sounds)
    - Handle apple eating (grow snake, increase score/speed, play sound)
    - Maintain collision check order (fatal before non-fatal)

    Note: This system follows proper ECS architecture by querying
    components and modifying them directly, without callbacks.
    """

    def __init__(
        self,
        settings: Optional[Any] = None,
        audio_service: Optional[Any] = None,
    ):
        """Initialize the CollisionSystem.

        Args:
            settings: Game settings for electric_walls, max_speed
            audio_service: Audio service for playing sounds
        """
        self._settings = settings
        self._audio_service = audio_service

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
        if self._check_wall_collision(world):
            print("☠️  DEATH CAUSE: Wall collision")
            self._handle_death(world, "wall")
            return

        # Check self-bite collision
        if self._check_self_bite(world):
            print("☠️  DEATH CAUSE: Self-bite collision")
            self._handle_death(world, "self-bite")
            return

        # Check obstacle collision
        if self._check_obstacle_collision(world):
            print("☠️  DEATH CAUSE: Obstacle collision")
            self._handle_death(world, "obstacle")
            return

        # Check apple collision (doesn't kill)
        self._check_apple_collision(world)

    def _get_snake_entity(self, world: World):
        """Get the snake entity from the world.

        Args:
            world: ECS world

        Returns:
            Snake entity or None if not found
        """
        from ecs.entities.entity import EntityType

        snakes = world.registry.query_by_type(EntityType.SNAKE)
        for _, snake in snakes.items():
            return snake
        return None

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

    def _check_wall_collision(self, world: World) -> bool:
        """Check collision with walls (electric mode only).

        Checks if snake's CURRENT position is out of bounds.
        Movement system handles wrapping when electric walls are disabled.
        Collision system only checks if we're already out of bounds.

        Args:
            world: ECS world

        Returns:
            bool: True if collision detected, False otherwise
        """
        snake = self._get_snake_entity(world)
        if not snake or not hasattr(snake, "position"):
            return False

        # get electric walls setting
        electric_walls = (
            self._settings.get("electric_walls") if self._settings else True
        )

        if not electric_walls:
            return False  # no wall collisions when walls are disabled

        # check current position
        current_x = snake.position.x
        current_y = snake.position.y
        grid_width = world.board.width
        grid_height = world.board.height

        # grid dimensions are in cells, not pixels
        # valid positions are 0 to grid_width-1 and 0 to grid_height-1
        # snake dies when its current position is out of bounds
        if (
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

    def _check_self_bite(self, world: World) -> bool:
        """Check if snake head collides with its own tail.

        Args:
            world: ECS world

        Returns:
            bool: True if self-bite detected, False otherwise
        """
        snake = self._get_snake_entity(world)
        if (
            not snake
            or not hasattr(snake, "position")
            or not hasattr(snake, "velocity")
            or not hasattr(snake, "body")
        ):
            return False

        # calculate head position
        head_x = snake.position.x
        head_y = snake.position.y

        # wrap if electric walls are disabled
        electric_walls = (
            self._settings.get("electric_walls") if self._settings else True
        )
        if not electric_walls:
            head_x = head_x % world.board.width
            head_y = head_y % world.board.height

        # check collision with tail segments
        tail_positions = [(seg.x, seg.y) for seg in snake.body.segments]
        for square in tail_positions:
            if head_x == square[0] and head_y == square[1]:
                return True

        return False

    def _check_obstacle_collision(self, world: World) -> bool:
        """Check collision with obstacles.

        Checks if snake's CURRENT position (after movement) collides with obstacle.

        Args:
            world: ECS world to query obstacles

        Returns:
            bool: True if collision detected, False otherwise
        """
        snake = self._get_snake_entity(world)
        if not snake or not hasattr(snake, "position"):
            return False

        # check current position
        current_x = snake.position.x
        current_y = snake.position.y

        # query all obstacles
        from ecs.entities.entity import EntityType

        obstacles = world.registry.query_by_type(EntityType.OBSTACLE)

        # check if snake's current position collides with any obstacle
        for _, obstacle in obstacles.items():
            if hasattr(obstacle, "position"):
                if (
                    current_x == obstacle.position.x
                    and current_y == obstacle.position.y
                ):
                    return True

        return False

    def _check_apple_collision(self, world: World) -> None:
        """Check collision with apples and handle eating.

        Maintains exact logic from old code.
        Directly modifies snake body, score, and velocity components.

        Args:
            world: ECS world to query apples
        """
        snake = self._get_snake_entity(world)
        if not snake or not hasattr(snake, "position"):
            return

        head_x = snake.position.x
        head_y = snake.position.y

        # query apples from world
        from ecs.entities.entity import EntityType

        apples = world.registry.query_by_type(EntityType.APPLE)
        for entity_id, apple in apples.items():
            # check if apple is at the same position as head
            if hasattr(apple, "position"):
                if head_x == apple.position.x and head_y == apple.position.y:
                    print(f"APPLE EATEN: head=({head_x},{head_y})")

                    # play apple eating sound
                    if self._audio_service:
                        self._audio_service.play_sound("assets/sound/eat.flac")

                    # grow snake
                    if hasattr(snake, "body"):
                        snake.body.size += 1

                    # increment score
                    score_entities = world.registry.query_by_component("score")
                    if score_entities:
                        score_entity = list(score_entities.values())[0]
                        if hasattr(score_entity, "score"):
                            score_entity.score.current += 1

                    # increase speed by 10%, respect max_speed
                    if hasattr(snake, "velocity"):
                        current_speed = snake.velocity.speed
                        max_speed = (
                            float(self._settings.get("max_speed"))
                            if self._settings
                            else 20.0
                        )
                        new_speed = min(current_speed * 1.1, max_speed)
                        snake.velocity.speed = new_speed

                    # remove eaten apple
                    world.registry.remove(entity_id)

                    break  # only eat one apple per frame

    def _handle_death(self, world: World, reason: str) -> None:
        """Handle snake death.

        Modifies GameState component and plays death audio.

        Args:
            world: ECS world
            reason: Death reason message (e.g., "wall", "self-bite", "obstacle")
        """
        # kill the snake
        snake = self._get_snake_entity(world)
        if snake and hasattr(snake, "body"):
            snake.body.alive = False

        # play death sound and music
        if self._audio_service:
            self._audio_service.play_sound("assets/sound/gameover.wav")
            self._audio_service.play_music("assets/sound/death_song.mp3")

        # update game state
        game_state = self._get_game_state(world)
        if game_state:
            game_state.game_over = True
            game_state.death_reason = reason
            game_state.next_scene = "game_over"

        print(f"GAME OVER: {reason}")
