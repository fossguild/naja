#!/usr/bin/env python3
#
#   Copyright (c) 2023, Monaco F. J. <monaco@usp.br>
#   Copyright (c) 2024, Leticia Neves
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

"""Input system for handling user input events.

This system converts raw pygame events into game actions by modifying
ECS components directly, following proper ECS architecture.
"""

from typing import Optional, Any

import pygame

from src.ecs.systems.base_system import BaseSystem
from src.ecs.world import World


class InputSystem(BaseSystem):
    """System for handling user input from keyboard and mouse.

    Reads: Velocity (for 180° turn prevention), GameState, MusicState
    Writes: Velocity (snake direction), GameState (pause, next_scene)
    Queries: Entities with EntityType.SNAKE, singleton game state entity

    Responsibilities:
    - Convert keyboard input to direction changes
    - Handle game control keys (pause, quit, menu)
    - Handle settings shortcuts (music toggle, palette randomize)
    - Directly modify ECS components (no callbacks)

    Note: This system follows proper ECS architecture by querying
    and modifying components directly instead of using callbacks.
    """

    def __init__(
        self,
        pygame_adapter: Optional[Any] = None,
        settings: Optional[Any] = None,
    ):
        """Initialize the InputSystem.

        Args:
            pygame_adapter: Pygame IO adapter for reading events
            settings: Game settings for palette randomization
        """
        self._pygame_adapter = pygame_adapter
        self._settings = settings

    def update(self, world: World) -> None:
        """Process input events and modify ECS components.

        Args:
            world: ECS world containing entities and components
        """
        if not self._pygame_adapter:
            return

        # get all pygame events
        events = self._pygame_adapter.get_events()

        # process each event
        for event in events:
            if event.type == pygame.QUIT:
                self._handle_quit(world)
            elif event.type == pygame.KEYDOWN:
                self._handle_keydown(world, event.key)

    def _handle_quit(self, world: World) -> None:
        """Handle quit event (window close button).

        Args:
            world: ECS world
        """
        # set next_scene to menu in GameState component
        game_state = self._get_game_state(world)
        if game_state:
            game_state.next_scene = "menu"

    def _handle_keydown(self, world: World, key: int) -> None:
        """Handle key down events.

        Args:
            world: ECS world
            key: Pygame key constant
        """
        # get current direction for 180° turn prevention
        current_dx, current_dy = self._get_current_direction(world)

        # movement keys - modify velocity directly with 180° turn prevention
        if key in (pygame.K_DOWN, pygame.K_s):
            self._set_direction(world, 0, 1, current_dx, current_dy)
        elif key in (pygame.K_UP, pygame.K_w):
            self._set_direction(world, 0, -1, current_dx, current_dy)
        elif key in (pygame.K_RIGHT, pygame.K_d):
            self._set_direction(world, 1, 0, current_dx, current_dy)
        elif key in (pygame.K_LEFT, pygame.K_a):
            self._set_direction(world, -1, 0, current_dx, current_dy)
        # control keys
        elif key == pygame.K_q:
            self._handle_quit(world)
        elif key == pygame.K_p:
            self._handle_pause(world)
        # elif key == pygame.K_m:
        #     self._handle_menu(world)  # disabled: removed ability to open settings from gameplay
        elif key == pygame.K_n:
            self._handle_music_toggle()
        elif key == pygame.K_c:
            self._handle_palette_randomize()

    def _get_snake_entity(self, world: World):
        """Get the snake entity from the world.

        Args:
            world: ECS world

        Returns:
            Snake entity or None if not found
        """
        from src.ecs.entities.entity import EntityType

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
        # query for entities with GameState component
        game_state_entities = world.registry.query_by_component("game_state")
        if game_state_entities:
            entity = next(iter(game_state_entities.values()))
            if hasattr(entity, "game_state"):
                return entity.game_state
        return None

    def _get_current_direction(self, world: World) -> tuple[int, int]:
        """Get current snake direction from Velocity component.

        Args:
            world: ECS world

        Returns:
            Tuple of (dx, dy) for current direction, or (0, 0) if not found
        """
        snake = self._get_snake_entity(world)
        if snake and hasattr(snake, "velocity"):
            return (snake.velocity.dx, snake.velocity.dy)
        return (0, 0)

    def _set_direction(
        self, world: World, dx: int, dy: int, current_dx: int = 0, current_dy: int = 0
    ) -> None:
        """Modify snake Velocity component with new direction if valid.

        Args:
            world: ECS world
            dx: X direction (-1, 0, 1)
            dy: Y direction (-1, 0, 1)
            current_dx: Current X direction (to prevent 180° turns)
            current_dy: Current Y direction (to prevent 180° turns)
        """
        # prevent 180-degree turns
        if dx != 0 and current_dx != -dx:  # horizontal movement
            snake = self._get_snake_entity(world)
            if snake and hasattr(snake, "velocity"):
                snake.velocity.dx = dx
                snake.velocity.dy = dy
        elif dy != 0 and current_dy != -dy:  # vertical movement
            snake = self._get_snake_entity(world)
            if snake and hasattr(snake, "velocity"):
                snake.velocity.dx = dx
                snake.velocity.dy = dy

    def _handle_pause(self, world: World) -> None:
        """Handle pause key press by toggling GameState.paused.

        Args:
            world: ECS world
        """
        game_state = self._get_game_state(world)
        if game_state:
            game_state.paused = not game_state.paused

    # disabled: removed ability to open settings from gameplay
    # def _handle_menu(self, world: World) -> None:
    #     """Handle menu key press by pausing and setting next_scene.
    #
    #     Args:
    #         world: ECS world
    #     """
    #     game_state = self._get_game_state(world)
    #     if game_state:
    #         game_state.paused = True
    #         game_state.next_scene = "settings"

    def _handle_music_toggle(self) -> None:
        """Handle audio toggle key press.

        Toggles all audio (both music and sound effects).
        """
        if self._settings:
            # toggle both background music and sound effects
            current_music = self._settings.get("background_music")
            current_sfx = self._settings.get("sound_effects")

            # If either is on, turn both off. If both are off, turn both on.
            new_state = not (current_music or current_sfx)

            self._settings.set("background_music", new_state)
            self._settings.set("sound_effects", new_state)

            # apply music change immediately
            if new_state:
                pygame.mixer.music.unpause()
            else:
                pygame.mixer.music.pause()

    def _handle_palette_randomize(self) -> None:
        """Handle palette randomize key press.

        Note: This temporarily uses settings until palette components are added.
        """
        if self._settings:
            self._settings.randomize_snake_colors()
