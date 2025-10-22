#!/usr/bin/env python3
#
#   Copyright (c) 2023, Monaco F. J. <monaco@usp.br>
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

"""Game initialization service.

This service is responsible for initializing and resetting the game world,
creating initial entities, and managing game state transitions.
"""

import random
from typing import Any, Optional

from src.ecs.world import World
from src.core.types.color_utils import hex_to_rgb


class GameInitializer:
    """Service responsible for initializing game state.

    This service encapsulates the logic for:
    - Resetting the game world
    - Creating initial entities (snake, apples, obstacles, score)
    - Managing game over state
    - Applying initial configurations

    By extracting this from GameplayScene, we achieve better separation
    of concerns and make the code more testable.
    """

    def __init__(self, settings: Optional[Any] = None):
        """Initialize the game initializer.

        Args:
            settings: Game settings object (Settings instance)
        """
        self._settings = settings
        self._game_over = False
        self._death_reason = ""

    def reset_world(self, world: World) -> None:
        """Reset the game world for a new game.

        This clears all existing entities and recreates them with fresh state.
        Called when entering gameplay scene to ensure clean state.

        Args:
            world: ECS world instance to reset
        """
        # clear all entities from the world
        world.registry.clear()

        # reset game over state
        self._game_over = False
        self._death_reason = ""

        # create initial entities
        self.create_initial_entities(world)

    def create_initial_entities(self, world: World) -> None:
        """Create all initial game entities.

        Creates:
        - ColorScheme entity for rendering colors
        - Snake entity at center of board
        - AppleConfig entity to track desired apple count
        - Initial apples at random valid positions
        - Obstacles based on difficulty setting
        - Score entity to track progress

        Args:
            world: ECS world instance to populate with entities
        """
        grid_size = world.board.cell_size

        # create color scheme entity for rendering systems
        self._create_color_scheme(world)

        # create snake at center of board
        self._create_snake(world, grid_size)

        # create apple config entity
        self._create_apple_config(world)

        # create initial apples
        self._create_initial_apples(world, grid_size)

        # create obstacles based on difficulty
        self._create_obstacles(world, grid_size)

        # create score entity
        self._create_score_entity(world)

    def _create_color_scheme(self, world: World) -> None:
        """Create ColorScheme entity for rendering systems.

        This entity stores the global color palette used by rendering systems.
        Following ECS principles, this is a singleton entity that systems query.

        Args:
            world: ECS world instance
        """
        from src.ecs.components.color_scheme import ColorScheme

        class ColorSchemeEntity:
            def __init__(self):
                self.color_scheme = ColorScheme()

            def get_type(self):
                return None  # config entity has no specific type

        color_scheme_entity = ColorSchemeEntity()
        world.registry.add(color_scheme_entity)

    def _create_snake(self, world: World, grid_size: int) -> None:
        """Create the snake entity.

        Args:
            world: ECS world instance
            grid_size: Size of grid cells in pixels
        """
        from src.ecs.prefabs.snake import create_snake

        # get snake colors from settings
        snake_colors = self._settings.get_snake_colors()
        head_color_hex = snake_colors.get("head")
        tail_color_hex = snake_colors.get("tail")

        # convert hex colors to RGB tuples
        head_color = hex_to_rgb(head_color_hex)
        tail_color = hex_to_rgb(tail_color_hex)

        _ = create_snake(
            world=world,
            grid_size=grid_size,
            initial_speed=float(self._settings.get("initial_speed")),
            head_color=head_color,
            tail_color=tail_color,
        )

    def _create_apple_config(self, world: World) -> None:
        """Create AppleConfig entity to track desired apple count.

        Args:
            world: ECS world instance
        """
        from src.ecs.components.apple_config import AppleConfig

        class AppleConfigEntity:
            def __init__(self, desired_count: int):
                self.apple_config = AppleConfig(desired_count=desired_count)

            def get_type(self):
                return None  # config entity has no specific type

        desired_apples = self._settings.validate_apples_count(
            world.board.width * world.board.cell_size,
            world.board.cell_size,
            world.board.height * world.board.cell_size,
        )
        apple_config_entity = AppleConfigEntity(desired_apples)
        world.registry.add(apple_config_entity)

    def _create_initial_apples(self, world: World, grid_size: int) -> None:
        """Create initial apples at random valid positions.

        Args:
            world: ECS world instance
            grid_size: Size of grid cells in pixels
        """
        from src.ecs.prefabs.apple import create_apple
        from src.ecs.entities.entity import EntityType

        # get desired apple count from config entity
        apple_configs = world.registry.query_by_component("apple_config")
        if not apple_configs:
            return

        config_entity = list(apple_configs.values())[0]
        desired_apples = config_entity.apple_config.desired_count

        # get occupied positions (snake)
        occupied_positions = set()
        snakes = world.registry.query_by_type(EntityType.SNAKE)
        for _, snake in snakes.items():
            if hasattr(snake, "position"):
                occupied_positions.add((snake.position.x, snake.position.y))
                if hasattr(snake, "body"):
                    for segment in snake.body.segments:
                        occupied_positions.add((segment.x, segment.y))

        # spawn initial apples
        for _ in range(desired_apples):
            # try to find a valid position
            attempts = 0
            max_attempts = 1000
            while attempts < max_attempts:
                x = random.randint(0, world.board.width - 1)
                y = random.randint(0, world.board.height - 1)

                if (x, y) not in occupied_positions:
                    create_apple(world, x=x, y=y, grid_size=grid_size, color=None)
                    occupied_positions.add((x, y))
                    break

                attempts += 1

    def _create_obstacles(self, world: World, grid_size: int) -> None:
        """Create obstacles based on difficulty setting.

        Args:
            world: ECS world instance
            grid_size: Size of grid cells in pixels
        """
        difficulty = self._settings.get("obstacle_difficulty")
        if difficulty and difficulty != "None":
            from src.ecs.prefabs.obstacle_field import create_obstacles

            _ = create_obstacles(
                world=world,
                difficulty=difficulty,
                grid_size=grid_size,
                random_seed=None,  # use true randomness
            )

    def _create_score_entity(self, world: World) -> None:
        """Create score entity to track apples eaten.

        Args:
            world: ECS world instance
        """
        from src.ecs.components.score import Score

        # create a simple object to hold the score component
        # we don't use a specific entity type since this is just for UI tracking
        class ScoreEntity:
            def __init__(self):
                self.score = Score(current=0, high_score=0)

            def get_type(self):
                """Return a dummy type to satisfy registry interface."""
                return None  # no specific type for UI entities

        score_entity = ScoreEntity()
        world.registry.add(score_entity)

    @property
    def game_over(self) -> bool:
        """Check if game is over.

        Returns:
            True if game is over, False otherwise
        """
        return self._game_over

    @property
    def death_reason(self) -> str:
        """Get the reason for game over.

        Returns:
            Death reason string
        """
        return self._death_reason

    def set_game_over(self, reason: str) -> None:
        """Set game over state.

        Args:
            reason: Reason for game over (e.g., "wall collision", "self collision")
        """
        self._game_over = True
        self._death_reason = reason
