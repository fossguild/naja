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
from game.game_modes_registry import GAME_MODE_TELEPORT, PLAYER_VS_PLAYER_MODE_NAME
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
        respawn_system: Optional["RespawnSystem"] = None,
    ):
        """Initialize the CollisionSystem.

        Args:
            settings: Game settings for electric_walls, max_speed (GameSettings)
            audio_service: Audio service for playing sounds (AudioService)
            scoring_system: Scoring system for tracking score (ScoringSystem)
            game_over_service: Game over service for handling game over
            respawn_system: Respawn system for handling snake respawns in PvP
        """
        self._settings = settings
        self._audio_service = audio_service
        self._scoring_system = scoring_system
        self._game_over_service = game_over_service
        self._respawn_system = respawn_system

    def update(self, world: World) -> None:
        """Check for all collision types in priority order.

        Priority:
        1. Wall collision (electric mode only)
        2. Self-bite collision
        3. Player-vs-player collision (PvP mode)
        4. Obstacle collision
        5. Apple collision

        Args:
            world: ECS world to query entities
        """
        # Check if we're in PvP mode
        game_state = self._get_game_state(world)
        is_pvp_mode = game_state and game_state.game_mode == PLAYER_VS_PLAYER_MODE_NAME

        if is_pvp_mode:
            # In PvP mode, check collisions for each snake individually
            self._check_all_snakes_collisions(world)
        else:
            # Single player mode - check collisions for the single snake
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

            # Check box collision and push logic (Box Mode)
            self._check_box_collision(world)

            # Check if any box is on a hole (Box Mode)
            self._check_all_box_hole_collisions(world)

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

    def _check_all_snakes_collisions(self, world: World) -> None:
        """Check collisions for all snakes in PvP mode.

        Args:
            world: ECS world
        """
        from ecs.entities.entity import EntityType

        snakes = world.registry.query_by_type(EntityType.SNAKE)

        for snake_id, snake in snakes.items():
            # skip if snake is not alive or respawning
            if hasattr(snake, "body") and not snake.body.alive:
                continue
            if hasattr(snake, "respawn_timer") and snake.respawn_timer.is_respawning:
                continue

            # check wall collision for this snake
            if self._check_wall_collision_for_snake(world, snake):
                self._handle_snake_death(world, snake, "Wall collision")
                continue

            # check self-bite for this snake
            if self._check_self_bite_for_snake(world, snake):
                self._handle_snake_death(world, snake, "Self-bite collision")
                continue

            # check obstacle collision for this snake
            if self._check_obstacle_collision_for_snake(world, snake):
                self._handle_snake_death(world, snake, "Obstacle collision")
                continue

        # check player-vs-player collisions
        self._check_player_vs_player_collision(world)

        # check apple collisions for all snakes
        self._check_apple_collision_all_snakes(world)

    def _check_wall_collision_for_snake(self, world: World, snake) -> bool:
        """Check wall collision for a specific snake.

        Args:
            world: ECS world
            snake: Snake entity to check

        Returns:
            bool: True if collision detected
        """
        if not hasattr(snake, "position"):
            return False

        # get electric walls setting
        electric_walls = (
            self._settings.get("electric_walls") if self._settings else True
        )

        if not electric_walls:
            return False

        current_x = snake.position.x
        current_y = snake.position.y
        grid_width = world.board.width
        grid_height = world.board.height

        if (
            current_x < 0
            or current_x >= grid_width
            or current_y < 0
            or current_y >= grid_height
        ):
            return True

        return False

    def _check_self_bite_for_snake(self, world: World, snake) -> bool:
        """Check self-bite collision for a specific snake.

        Args:
            world: ECS world
            snake: Snake entity to check

        Returns:
            bool: True if collision detected
        """
        if not hasattr(snake, "position") or not hasattr(snake, "body"):
            return False

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
        for segment in snake.body.segments:
            if head_x == segment.x and head_y == segment.y:
                return True

        return False

    def _check_obstacle_collision_for_snake(self, world: World, snake) -> bool:
        """Check obstacle collision for a specific snake.

        Args:
            world: ECS world
            snake: Snake entity to check

        Returns:
            bool: True if collision detected
        """
        if not hasattr(snake, "position"):
            return False

        current_x = snake.position.x
        current_y = snake.position.y

        from ecs.entities.entity import EntityType

        obstacles = world.registry.query_by_type(EntityType.OBSTACLE)

        for _, obstacle in obstacles.items():
            if hasattr(obstacle, "position"):
                if (
                    current_x == obstacle.position.x
                    and current_y == obstacle.position.y
                ):
                    return True

        return False

    def _check_apple_collision_all_snakes(self, world: World) -> None:
        """Check apple collisions for all snakes in PvP mode.

        Args:
            world: ECS world
        """
        from ecs.entities.entity import EntityType

        snakes = world.registry.query_by_type(EntityType.SNAKE)
        apples = world.registry.query_by_type(EntityType.APPLE)

        for snake_id, snake in snakes.items():
            # skip if snake is not alive or respawning
            if hasattr(snake, "body") and not snake.body.alive:
                continue
            if hasattr(snake, "respawn_timer") and snake.respawn_timer.is_respawning:
                continue
            if not hasattr(snake, "position"):
                continue

            head_x = snake.position.x
            head_y = snake.position.y

            # check collision with apples
            for apple_id, apple in list(apples.items()):
                if hasattr(apple, "position"):
                    if head_x == apple.position.x and head_y == apple.position.y:
                        # play eating sound
                        if self._audio_service:
                            self._audio_service.play_sound("assets/sound/eat.flac")

                        # grow snake
                        if hasattr(snake, "body"):
                            snake.body.size += 1

                        # update player score
                        if hasattr(snake, "player_id"):
                            snake.player_id.score += 1

                        # remove apple
                        world.registry.remove(apple_id)
                        break

    def _check_player_vs_player_collision(self, world: World) -> None:
        """Check collision between players in PvP mode.

        In PvP mode, if a snake's head collides with another snake's
        body or head, the colliding snake loses a life and respawns.

        Args:
            world: ECS world
        """
        # only run in Player vs Player mode
        game_state = self._get_game_state(world)
        if not game_state or game_state.game_mode != PLAYER_VS_PLAYER_MODE_NAME:
            return

        from ecs.entities.entity import EntityType

        snakes = world.registry.query_by_type(EntityType.SNAKE)
        snake_list = list(snakes.items())

        # check each snake against all other snakes
        for snake_id, snake in snake_list:
            # skip if snake is not alive or respawning
            if hasattr(snake, "body") and not snake.body.alive:
                continue
            if hasattr(snake, "respawn_timer") and snake.respawn_timer.is_respawning:
                continue
            if not hasattr(snake, "position"):
                continue

            head_x = snake.position.x
            head_y = snake.position.y

            # check collision with other snakes
            for other_id, other_snake in snake_list:
                if snake_id == other_id:
                    continue  # don't check against self

                # skip if other snake is not alive or respawning
                if hasattr(other_snake, "body") and not other_snake.body.alive:
                    continue
                if (
                    hasattr(other_snake, "respawn_timer")
                    and other_snake.respawn_timer.is_respawning
                ):
                    continue

                # check collision with other snake's head
                if hasattr(other_snake, "position"):
                    if head_x == other_snake.position.x and head_y == other_snake.position.y:
                        # head-to-head collision - both snakes die
                        self._handle_snake_death(world, snake, "Player collision")
                        self._handle_snake_death(world, other_snake, "Player collision")
                        return

                # check collision with other snake's body
                if hasattr(other_snake, "body"):
                    for segment in other_snake.body.segments:
                        if head_x == segment.x and head_y == segment.y:
                            # this snake hit the other snake's body
                            self._handle_snake_death(world, snake, "Player collision")
                            return

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

    def _check_box_collision(self, world: World) -> None:
        """Check collision with boxes and push them.

        In Box Mode, when the snake moves into a box, the box is pushed
        in the direction the snake is moving.
        """
        snake = self._get_snake_entity(world)
        if (
            not snake
            or not hasattr(snake, "position")
            or not hasattr(snake, "velocity")
        ):
            return

        head_x = snake.position.x
        head_y = snake.position.y

        # query boxes from world
        from ecs.entities.entity import EntityType

        boxes = world.registry.query_by_type(EntityType.BOX)
        for entity_id, box in boxes.items():
            # check if box is at the same position as head
            if hasattr(box, "position"):
                if head_x == box.position.x and head_y == box.position.y:
                    # calculate new box position based on snake's velocity
                    new_box_x = box.position.x + snake.velocity.dx
                    new_box_y = box.position.y + snake.velocity.dy

                    # check if box would go out of bounds
                    if (
                        new_box_x < 0
                        or new_box_x >= world.board.width
                        or new_box_y < 0
                        or new_box_y >= world.board.height
                    ):
                        # respawn box at a new random position
                        self._respawn_box(world, entity_id, box)
                        break

                    # check if new position is valid (not occupied by obstacle or another box)
                    if self._is_position_valid_for_box(world, new_box_x, new_box_y):
                        # update box position
                        box.position.prev_x = box.position.x
                        box.position.prev_y = box.position.y
                        box.position.x = new_box_x
                        box.position.y = new_box_y
                    else:
                        # position is blocked by obstacle or another box, respawn
                        self._respawn_box(world, entity_id, box)

                    break  # only push one box per frame

    def _is_position_valid_for_box(self, world: World, x: int, y: int) -> bool:
        """Check if a position is valid for a box to move to.

        A position is invalid if it's occupied by an obstacle or another box.
        """
        from ecs.entities.entity import EntityType

        # check obstacles
        obstacles = world.registry.query_by_type(EntityType.OBSTACLE)
        for _, obstacle in obstacles.items():
            if hasattr(obstacle, "position"):
                if x == obstacle.position.x and y == obstacle.position.y:
                    return False

        # check other boxes
        boxes = world.registry.query_by_type(EntityType.BOX)
        for _, box in boxes.items():
            if hasattr(box, "position"):
                if x == box.position.x and y == box.position.y:
                    return False

        return True

    def _respawn_box(self, world: World, box_id: int, box) -> None:
        """Respawn a box at a new random valid position.

        Called when a box is pushed to an invalid location (border or blocked).
        """
        from ecs.entities.entity import EntityType
        import random

        # get all occupied positions
        occupied_positions = set()

        # snake positions
        snake = self._get_snake_entity(world)
        if snake and hasattr(snake, "position"):
            occupied_positions.add((snake.position.x, snake.position.y))
            if hasattr(snake, "body"):
                for segment in snake.body.segments:
                    occupied_positions.add((segment.x, segment.y))

        # apple positions
        apples = world.registry.query_by_type(EntityType.APPLE)
        for _, apple in apples.items():
            if hasattr(apple, "position"):
                occupied_positions.add((apple.position.x, apple.position.y))

        # obstacle positions
        obstacles = world.registry.query_by_type(EntityType.OBSTACLE)
        for _, obstacle in obstacles.items():
            if hasattr(obstacle, "position"):
                occupied_positions.add((obstacle.position.x, obstacle.position.y))

        # hole positions
        holes = world.registry.query_by_type(EntityType.HOLE)
        for _, hole in holes.items():
            if hasattr(hole, "position"):
                occupied_positions.add((hole.position.x, hole.position.y))

        # other box positions
        boxes = world.registry.query_by_type(EntityType.BOX)
        for other_id, other_box in boxes.items():
            if other_id != box_id and hasattr(other_box, "position"):
                occupied_positions.add((other_box.position.x, other_box.position.y))

        # find a new valid position (avoid borders)
        attempts = 0
        max_attempts = 1000
        while attempts < max_attempts:
            # avoid borders - box must be at least 1 cell away from edges
            new_x = random.randint(1, world.board.width - 2)
            new_y = random.randint(1, world.board.height - 2)

            if (new_x, new_y) not in occupied_positions:
                # update box position
                box.position.prev_x = box.position.x
                box.position.prev_y = box.position.y
                box.position.x = new_x
                box.position.y = new_y
                print(f"BOX RESPAWNED: new position=({new_x},{new_y})")
                return

            attempts += 1

        # if we can't find a valid position after max attempts, just remove the box
        print("BOX RESPAWN FAILED: removing box")
        world.registry.remove(box_id)

    def _spawn_new_box_and_hole(self, world: World) -> None:
        """Spawn new box and hole at random valid positions.

        Called after a box reaches a hole to continue the Box Mode gameplay.
        """
        from ecs.entities.entity import EntityType
        from ecs.prefabs.box import create_box
        from ecs.prefabs.hole import create_hole
        import random

        grid_size = world.board.cell_size

        # get all occupied positions
        occupied_positions = set()

        # snake positions
        snake = self._get_snake_entity(world)
        if snake and hasattr(snake, "position"):
            occupied_positions.add((snake.position.x, snake.position.y))
            if hasattr(snake, "body"):
                for segment in snake.body.segments:
                    occupied_positions.add((segment.x, segment.y))

        # apple positions
        apples = world.registry.query_by_type(EntityType.APPLE)
        for _, apple in apples.items():
            if hasattr(apple, "position"):
                occupied_positions.add((apple.position.x, apple.position.y))

        # obstacle positions
        obstacles = world.registry.query_by_type(EntityType.OBSTACLE)
        for _, obstacle in obstacles.items():
            if hasattr(obstacle, "position"):
                occupied_positions.add((obstacle.position.x, obstacle.position.y))

        # existing box positions
        boxes = world.registry.query_by_type(EntityType.BOX)
        for _, box in boxes.items():
            if hasattr(box, "position"):
                occupied_positions.add((box.position.x, box.position.y))

        # existing hole positions
        holes = world.registry.query_by_type(EntityType.HOLE)
        for _, hole in holes.items():
            if hasattr(hole, "position"):
                occupied_positions.add((hole.position.x, hole.position.y))

        # find valid position for box (avoid borders)
        box_x, box_y = None, None
        attempts = 0
        max_attempts = 1000
        while attempts < max_attempts:
            # avoid borders - box must be at least 1 cell away from edges
            x = random.randint(1, world.board.width - 2)
            y = random.randint(1, world.board.height - 2)

            if (x, y) not in occupied_positions:
                box_x, box_y = x, y
                occupied_positions.add((x, y))
                break

            attempts += 1

        # find valid position for hole (not on borders)
        hole_x, hole_y = None, None
        attempts = 0
        while attempts < max_attempts:
            # avoid borders - hole must be at least 1 cell away from edges
            x = random.randint(1, world.board.width - 2)
            y = random.randint(1, world.board.height - 2)

            if (x, y) not in occupied_positions:
                hole_x, hole_y = x, y
                break

            attempts += 1

        # create box and hole if valid positions found
        if box_x is not None and hole_x is not None:
            create_box(world, x=box_x, y=box_y, grid_size=grid_size)
            create_hole(world, x=hole_x, y=hole_y, grid_size=grid_size)
            print(
                f"NEW BOX AND HOLE SPAWNED: box=({box_x},{box_y}), hole=({hole_x},{hole_y})"
            )
        else:
            print(
                "WARNING: Failed to spawn new box and hole - no valid positions found"
            )

    def _check_all_box_hole_collisions(self, world: World) -> None:
        """Check all boxes against all holes every frame.

        This ensures box-hole collisions are detected immediately,
        not just when the snake pushes a box.
        """
        from ecs.entities.entity import EntityType

        boxes = world.registry.query_by_type(EntityType.BOX)
        holes = world.registry.query_by_type(EntityType.HOLE)

        for box_id, box in list(boxes.items()):
            if not hasattr(box, "position"):
                continue

            for hole_id, hole in list(holes.items()):
                if not hasattr(hole, "position"):
                    continue

                # check if box is on hole
                if (
                    box.position.x == hole.position.x
                    and box.position.y == hole.position.y
                ):
                    print(f"BOX IN HOLE: box=({box.position.x},{box.position.y})")

                    # play apple eating sound (reuse for box reward)
                    if self._audio_service:
                        self._audio_service.play_sound("assets/sound/eat.flac")

                    # get rewards from box
                    snake = self._get_snake_entity(world)
                    if snake and hasattr(snake, "body") and hasattr(box, "box"):
                        # grow snake
                        snake.body.size += box.box.growth

                        # increment score
                        if self._scoring_system:
                            self._scoring_system.on_apple_eaten(world, box.box.points)

                    # remove old box and hole
                    world.registry.remove(box_id)
                    world.registry.remove(hole_id)

                    # spawn new box and hole at random positions
                    self._spawn_new_box_and_hole(world)

                    return  # only process one match per frame

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

                    # Handle snake size change on apple eaten.
                    # In shrinking mode the snake loses length instead of growing.
                    game_state = self._get_game_state(world)
                    cheese_mode = (
                        game_state.cheese_mode_enabled if game_state else False
                    )
                    shrinking_mode = (
                        game_state.shrinking_mode_enabled if game_state else False
                    )

                    if hasattr(snake, "body"):
                        if shrinking_mode:
                            # Shrinking mode: decrease size immediately (never below 1)
                            try:
                                snake.body.size = max(
                                    1, int(getattr(snake.body, "size", 1)) - 1
                                )
                            except Exception:
                                snake.body.size = max(
                                    1, getattr(snake.body, "size", 1) - 1
                                )

                            # If the snake has reached size 1 (only head), treat as victory.
                            if getattr(snake.body, "size", 1) <= 1:
                                if game_state is not None:
                                    game_state.game_over = True
                                    game_state.death_reason = "Win: shrunk to head"
                                    try:
                                        game_state.final_score = (
                                            game_state.apples_eaten_count
                                        )
                                    except Exception:
                                        pass
                                self._handle_death(world, "Win: shrunk to head")
                        else:
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
                    # NOTE: keep speed constant when shrinking mode is enabled to avoid complications
                    if not shrinking_mode and hasattr(snake, "velocity"):
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

                    # Check for board-fill victory (Classic and other modes)
                    # Skip for shrinking mode (handled separately) and AutoPlay (has its own check)
                    game_state = self._get_game_state(world)
                    if game_state and not getattr(
                        game_state, "shrinking_mode_enabled", False
                    ):
                        if self._check_board_fill_victory(world):
                            return  # Victory triggered, stop processing

                    break  # only eat one apple per frame

    def _handle_death(self, world: World, reason: str) -> None:
        """Handle snake death.

        Delegates to GameOverService.
        """
        if self._game_over_service:
            self._game_over_service.handle_death(world, reason)
        else:
            print(f"☠️ DEATH CAUSE: {reason} (Service missing)")

    def _handle_snake_death(self, world: World, snake, reason: str) -> None:
        """Handle death of a specific snake in PvP mode.

        Args:
            world: ECS world
            snake: Snake entity that died
            reason: Death reason
        """
        # check if snake has lives component (PvP mode)
        if not hasattr(snake, "lives") or not hasattr(snake, "respawn_timer"):
            # not in PvP mode, use normal death handling
            self._handle_death(world, reason)
            return

        # play death sound
        if self._audio_service:
            self._audio_service.play_sound("assets/sound/gameover.wav")

        # decrease lives
        snake.lives.remaining -= 1

        player_name = f"Player {snake.player_id.player_number}" if hasattr(snake, "player_id") else "Snake"
        print(f"☠️ {player_name} died: {reason}. Lives remaining: {snake.lives.remaining}")

        # check if snake has lives left
        if snake.lives.remaining <= 0:
            # no lives left for this snake
            snake.body.alive = False
            print(f"☠️ {player_name} has no lives left!")
            
            # check if all snakes are dead
            from ecs.entities.entity import EntityType
            snakes = world.registry.query_by_type(EntityType.SNAKE)
            winner = None
            for _, s in snakes.items():
                if hasattr(s, "lives") and s.lives.remaining > 0:
                    if hasattr(s, "player_id"):
                        winner = s.player_id.player_number
                    break
            
            if winner:
                # game over - we have a winner
                self._handle_death(world, f"Player {winner} wins!")
            else:
                # all snakes dead
                self._handle_death(world, "Draw! All players eliminated")
        else:
            # trigger respawn
            if self._respawn_system:
                self._respawn_system.trigger_respawn(snake)

    def _check_board_fill_victory(self, world: World) -> bool:
        """Check if snake has filled the entire board (victory for Classic mode).

        Returns True if victory was triggered, False otherwise.
        """
        snake = self._get_snake_entity(world)
        if not snake or not hasattr(snake, "body"):
            return False

        # Calculate snake length (head + body segments)
        snake_length = 1 + len(snake.body.segments)

        # Get board size
        board_size = world.board.width * world.board.height

        # Victory when snake fills entire board
        if snake_length >= board_size:
            if self._game_over_service:
                self._game_over_service.handle_victory(world, "Perfect Game!")
            else:
                print("🏆 VICTORY! Snake filled the board!")
            return True

        return False

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
