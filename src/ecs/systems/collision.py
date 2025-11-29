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

from typing import Optional

from ecs.systems.base_system import BaseSystem
from ecs.world import World

from ecs.systems.scoring import ScoringSystem
from game.settings import GameSettings
from game.services.audio_service import AudioService
from game.game_modes_registry import GAME_MODE_TELEPORT
from game.services.game_over_service import GameOverService


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
        settings: Optional[GameSettings] = None,
        audio_service: Optional[AudioService] = None,
        scoring_system: Optional[ScoringSystem] = None,
        game_over_service: Optional[GameOverService] = None,
    ):
        """Initialize the CollisionSystem.

        Args:
            settings: Game settings for electric_walls, max_speed (GameSettings)
            audio_service: Audio service for playing sounds (AudioService)
            scoring_system: Scoring system for tracking score (ScoringSystem)
        """
        self._settings = settings
        self._audio_service = audio_service
        self._scoring_system = scoring_system
        self._game_over_service = game_over_service

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
            self._handle_death(world, "Wall collision")
            return

        # Check self-bite collision
        if self._check_self_bite(world):
            self._handle_death(world, "Self-bite collision")
            return

        # Check obstacle collision
        if self._check_obstacle_collision(world):
            self._handle_death(world, "Obstacle collision")
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

    def _swap_head_and_tail(self, snake) -> None:
        """Swap snake head with tail by reversing the body chain.

        This helper is called when the snake eats an apple.
        It moves the head to the old tail position and reverses
        the order of the body segments, so the snake continues
        a coherent path from the other end.
        """

        if not hasattr(snake, "position") or not hasattr(snake, "body"):
            return

        position = snake.position
        body = snake.body

        if not body.segments:
            return
        chain = [position] + body.segments

        coords = []
        for seg in chain:
            x = getattr(seg, "x", None)
            y = getattr(seg, "y", None)
            prev_x = getattr(seg, "prev_x", x)
            prev_y = getattr(seg, "prev_y", y)
            coords.append((x, y, prev_x, prev_y))

        # Reverse
        coords.reverse()

        # apply to the head
        head_x, head_y, head_prev_x, head_prev_y = coords[0]
        position.x = head_x
        position.y = head_y
        position.prev_x = head_prev_x
        position.prev_y = head_prev_y

        # apply to the body (segments)
        for seg, (x, y, prev_x, prev_y) in zip(body.segments, coords[1:]):
            seg.x = x
            seg.y = y
            seg.prev_x = prev_x
            seg.prev_y = prev_y

        if hasattr(snake, "velocity") and body.segments:
            first = body.segments[0]
            dx = position.x - first.x
            dy = position.y - first.y

            # normalize
            if dx > 0:
                snake.velocity.dx = 1
                snake.velocity.dy = 0
            elif dx < 0:
                snake.velocity.dx = -1
                snake.velocity.dy = 0
            elif dy > 0:
                snake.velocity.dx = 0
                snake.velocity.dy = 1
            elif dy < 0:
                snake.velocity.dx = 0
                snake.velocity.dy = -1

        # clean buffer
        if (
            hasattr(snake, "input_buffer")
            and snake.input_buffer
            and snake.input_buffer.moves
        ):
            snake.input_buffer.moves.clear()

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

        # check if Cheese mode is enabled
        game_state = self._get_game_state(world)
        cheese_mode = game_state.cheese_mode_enabled if game_state else False

        # check collision with tail segments
        tail_positions = snake.body.segments
        for i, segment in enumerate(tail_positions):
            # In Cheese mode, segments array now contains ONLY solid segments
            # Holes are not stored at all - they're just empty space
            # So we check ALL segments for collision

            # Standard overlap check
            if head_x == segment.x and head_y == segment.y:
                return True

            # Cheese Mode Special Case: Tunneling/Swap Check
            # If moving against the body, head and segment can swap positions in one frame,
            # skipping the overlap check. We must detect this "swap".
            if cheese_mode:
                # Check if Head and Segment swapped places
                # Head is now where Segment was, AND Segment is now where Head was
                if (
                    head_x == segment.prev_x
                    and head_y == segment.prev_y
                    and snake.position.prev_x == segment.x
                    and snake.position.prev_y == segment.y
                ):
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

                    # grow snake - use pending_growth for Cheese mode (+2), immediate for others
                    game_state = self._get_game_state(world)
                    cheese_mode = (
                        game_state.cheese_mode_enabled if game_state else False
                    )

                    if hasattr(snake, "body"):
                        if cheese_mode:
                            # Cheese mode: +2 growth via pending_growth
                            snake.body.pending_growth += 2
                        else:
                            # Classic/other modes: +1 immediate growth
                            snake.body.size += 1

                        if self._should_swap_head_and_tail(world):
                            self._swap_head_and_tail(snake)

                    # increment score using scoring system
                    if self._scoring_system:
                        # Get points from apple's edible component (default to 1)
                        points = 1
                        if hasattr(apple, "edible"):
                            points = apple.edible.points
                        self._scoring_system.on_apple_eaten(world, points)

                    game_state = self._get_game_state(world)
                    if game_state:
                        game_state.apples_eaten_count += 1

                    # increase speed by 10%, respect max_speed
                    if hasattr(snake, "velocity"):
                        current_speed = snake.velocity.speed
                        max_speed = (
                            float(self._settings.get("max_speed"))
                            if self._settings
                            else 20.0
                        )
                        speed_increase_rate = (
                            self._settings.get("speed_increase_rate")
                            if self._settings
                            else "10%"
                        )
                        # Convert percentage string to multiplier (5% -> 1.05, 10% -> 1.10)
                        if speed_increase_rate == "5%":
                            multiplier = 1.05
                        else:  # default to 10%
                            multiplier = 1.10
                        new_speed = min(current_speed * multiplier, max_speed)

                        snake.velocity.speed = new_speed

                    # reset hunger timer when apple is eaten (if enabled)
                    if self._settings and bool(self._settings.get("enable_hunger")):
                        hunger_entities = world.registry.query_by_component("hunger")
                        if hunger_entities:
                            he = list(hunger_entities.values())[0]
                            if hasattr(he, "hunger"):
                                # Recompute hunger max_time from current snake velocity
                                snake_for_hunger = self._get_snake_entity(world)
                                try:
                                    if (
                                        snake_for_hunger
                                        and hasattr(snake_for_hunger, "velocity")
                                        and snake_for_hunger.velocity.speed > 0
                                    ):
                                        he.hunger.max_time = 50.0 / float(
                                            snake_for_hunger.velocity.speed
                                        )
                                except Exception:
                                    pass
                                # reset current time to (possibly updated) max
                                he.hunger.current_time = he.hunger.max_time

                    # Special handling for TELEPORT mode
                    if game_state and game_state.game_mode == GAME_MODE_TELEPORT:
                        # Find another active apple on the board
                        other_apple_id = None
                        other_apple = None
                        for other_id, other in apples.items():
                            if other_id == entity_id:
                                continue
                            if hasattr(other, "position"):
                                other_apple_id = other_id
                                other_apple = other
                                break

                        if other_apple is not None:
                            # Teleport snake head to the other apple's position
                            snake.position.prev_x = snake.position.x
                            snake.position.prev_y = snake.position.y
                            snake.position.x = other_apple.position.x
                            snake.position.y = other_apple.position.y

                            # Keep velocity unchanged (do nothing to snake.velocity)

                            # Remove both apples so AppleSpawnSystem will respawn them
                            try:
                                world.registry.remove(entity_id)
                            except Exception:
                                # ignore removal errors
                                pass
                            try:
                                if other_apple_id is not None:
                                    world.registry.remove(other_apple_id)
                            except Exception:
                                pass

                            break  # handled teleport, only one apple per frame

                    else:
                        # remove eaten apple
                        world.registry.remove(entity_id)

                    break  # only eat one apple per frame

    def _handle_death(self, world: World, reason: str) -> None:
        """Handle snake death.

        Delegates to GameOverService.
        """
        if self._game_over_service:
            self._game_over_service.handle_death(world, reason)
        else:
            print(f"☠️ DEATH CAUSE: {reason} (Service missing)")

    def _should_swap_head_and_tail(self, world: World) -> bool:
        """Determine if apple effects should swap the snake head and tail."""
        game_state = self._get_game_state(world)
        if game_state and getattr(game_state, "swap_head_tail_on_apple", False):
            return True

        return (
            self._settings
            and hasattr(self._settings, "get")
            and self._settings.get("swap_head_tail_on_apple")
        )
