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

"""Input system for handling user input events.

This system converts raw pygame events into game actions by modifying
ECS components directly, following proper ECS architecture.
"""

from typing import Optional, Any

import pygame

from ecs.systems.base_system import BaseSystem
from ecs.world import World
from game.game_modes_registry import PLAYER_VS_PLAYER_MODE_NAME, MIRRORED_MODE_NAME


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
        game_mode: str = "Classic Snake Game",
        overlay_render_system: Optional[Any] = None,
    ):
        """Initialize the InputSystem.

        Args:
            pygame_adapter: Pygame IO adapter for reading events
            settings: Game settings for palette randomization
            game_mode: Current game mode
            overlay_render_system: OverlayRenderSystem for section toggling
        """
        self._pygame_adapter = pygame_adapter
        self._settings = settings
        self._overlay_render_system = overlay_render_system
        self._game_mode = game_mode
        # key repeat tracking for smooth scrolling in settings menu
        self._key_down_pressed = False
        self._key_up_pressed = False
        self._key_repeat_timer = 0.0
        self._last_update_time = pygame.time.get_ticks()
        self._key_repeat_initial_delay = 300.0  # ms before repeat starts
        self._key_repeat_interval = 80.0  # ms between repeats

    def update(self, world: World) -> None:
        """Process input events and modify ECS components.

        Args:
            world: ECS world containing entities and components
        """
        if not self._pygame_adapter:
            return

        # calculate delta time
        current_time = pygame.time.get_ticks()
        dt_ms = current_time - self._last_update_time
        self._last_update_time = current_time

        # handle key repeat for smooth scrolling in settings menu
        game_state = self._get_game_state(world)
        if game_state and game_state.settings_menu_open:
            if self._key_down_pressed or self._key_up_pressed:
                self._key_repeat_timer += dt_ms
                # check if we should trigger a repeat
                should_repeat = False
                if self._key_repeat_timer >= self._key_repeat_initial_delay:
                    # after initial delay, repeat at interval
                    if (
                        self._key_repeat_timer
                        >= self._key_repeat_initial_delay + self._key_repeat_interval
                    ):
                        should_repeat = True
                        # reset timer but keep the "credit" for smooth repeating
                        self._key_repeat_timer = self._key_repeat_initial_delay

                if should_repeat and self._settings:
                    # use only in-game adjustable fields
                    menu_fields = self._settings.get_in_game_menu_fields()
                    # get visible fields
                    if self._overlay_render_system:
                        visible_fields = (
                            self._overlay_render_system._get_visible_fields(menu_fields)
                        )
                    else:
                        visible_fields = menu_fields
                    total_items = len(visible_fields) + 1

                    if self._key_down_pressed:
                        game_state.settings_selected_index = (
                            game_state.settings_selected_index + 1
                        ) % total_items
                    elif self._key_up_pressed:
                        game_state.settings_selected_index = (
                            game_state.settings_selected_index - 1
                        ) % total_items

        # get all pygame events
        events = self._pygame_adapter.get_events()

        # process each event
        for event in events:
            if event.type == pygame.QUIT:
                self._handle_quit(world)
            elif event.type == pygame.KEYDOWN:
                self._handle_keydown(world, event.key)
            elif event.type == pygame.KEYUP:
                self._handle_keyup(world, event.key)

    def _handle_quit(self, world: World) -> None:
        """Handle quit event (window close button).

        Args:
            world: ECS world
        """
        # set next_scene to menu in GameState component
        game_state = self._get_game_state(world)
        if game_state:
            game_state.next_scene = "menu"

    def _buffer_direction(
        self, world: World, dx: int, dy: int, player_id: Optional[int] = None
    ) -> None:
        """Append a new direction to the snake's input buffer if valid.

        This method ensures that rapid direction changes are stored in order
        and prevents immediate 180° reversals. It also respects the buffer's
        maximum length.

        Args:
            world: ECS world containing the snake entity
            dx: Horizontal component of the direction (-1, 0, 1)
            dy: Vertical component of the direction (-1, 0, 1)
            player_id: Player ID (1 or 2) for PvP mode, None for single player
        """
        # Get the appropriate snake based on mode
        if self._game_mode == PLAYER_VS_PLAYER_MODE_NAME and player_id is not None:
            snake = self._get_snake_by_player_id(world, player_id)
        else:
            snake = self._get_snake_entity(world)

        if not snake:
            return

        # Handle mirrored mode: apply input to both snakes with opposite directions
        if self._game_mode == MIRRORED_MODE_NAME:
            self._buffer_mirrored_direction(world, snake, dx, dy)
            return

        # Mark game as started on first input
        game_state = self._get_game_state(world)
        if game_state and not game_state.game_started:
            game_state.game_started = True

        # get or create input buffer on the snake entity
        if not hasattr(snake, "input_buffer") or snake.input_buffer is None:
            # fallback: create attribute if prefabs didn't add it
            from src.ecs.components.input_buffer import InputBuffer

            snake.input_buffer = InputBuffer()

        buf = snake.input_buffer

        # get last buffered direction or current velocity if buffer is empty
        last_dx, last_dy = (snake.velocity.dx, snake.velocity.dy)
        if buf.moves:
            last_dx, last_dy = buf.moves[-1]

        if (dx != 0 and last_dx == -dx) or (dy != 0 and last_dy == -dy):
            # don't queue a reversal against the last buffered direction
            return

        # Limit buffer length
        if len(buf.moves) >= buf.max_len:
            return

        # Enqueue the new direction
        buf.moves.append((dx, dy))

    def _buffer_mirrored_direction(self, world: World, snake, dx: int, dy: int) -> None:
        """Buffer direction for both mirrored snakes with opposite directions.

        Args:
            world: ECS world
            snake: The primary snake entity
            dx: Horizontal direction for primary snake
            dy: Vertical direction for primary snake
        """
        from ecs.entities.entity import EntityType

        # Mark game as started on first input
        game_state = self._get_game_state(world)
        if game_state and not game_state.game_started:
            game_state.game_started = True

        # Get both snakes
        snakes = world.registry.query_by_type(EntityType.SNAKE)
        snake_list = list(snakes.values())

        if len(snake_list) < 2:
            return

        snake1 = snake_list[0]
        snake2 = snake_list[1]

        # Buffer direction for snake 1
        if hasattr(snake1, "input_buffer"):
            buf1 = snake1.input_buffer
            last_dx1, last_dy1 = (snake1.velocity.dx, snake1.velocity.dy)
            if buf1.moves:
                last_dx1, last_dy1 = buf1.moves[-1]

            if not ((dx != 0 and last_dx1 == -dx) or (dy != 0 and last_dy1 == -dy)):
                if len(buf1.moves) < buf1.max_len:
                    buf1.moves.append((dx, dy))

        # Buffer OPPOSITE direction for snake 2 (mirrored)
        mirrored_dx = -dx
        mirrored_dy = -dy

        if hasattr(snake2, "input_buffer"):
            buf2 = snake2.input_buffer
            last_dx2, last_dy2 = (snake2.velocity.dx, snake2.velocity.dy)
            if buf2.moves:
                last_dx2, last_dy2 = buf2.moves[-1]

            if not (
                (mirrored_dx != 0 and last_dx2 == -mirrored_dx)
                or (mirrored_dy != 0 and last_dy2 == -mirrored_dy)
            ):
                if len(buf2.moves) < buf2.max_len:
                    buf2.moves.append((mirrored_dx, mirrored_dy))

    def _handle_keydown(self, world: World, key: int) -> None:
        """Handle key down events.

        Args:
            world: ECS world
            key: Pygame key constant
        """
        # check if settings menu is open first
        game_state = self._get_game_state(world)
        if game_state and game_state.settings_menu_open:
            self._handle_settings_menu_input(world, key)
            return

        # get current direction for 180° turn prevention
        current_dx, current_dy = self._get_current_direction(world)

        # movement keys - modify velocity directly with 180° turn prevention
        from game.game_modes_registry import AUTOPLAY_MODE_NAME

        if self._game_mode != AUTOPLAY_MODE_NAME:
            if self._game_mode == PLAYER_VS_PLAYER_MODE_NAME:
                # Player 1 controls (WASD)
                if key == pygame.K_s:
                    self._buffer_direction(world, 0, 1, player_id=1)
                elif key == pygame.K_w:
                    self._buffer_direction(world, 0, -1, player_id=1)
                elif key == pygame.K_d:
                    self._buffer_direction(world, 1, 0, player_id=1)
                elif key == pygame.K_a:
                    self._buffer_direction(world, -1, 0, player_id=1)
                # Player 2 controls (Arrow keys)
                elif key == pygame.K_DOWN:
                    self._buffer_direction(world, 0, 1, player_id=2)
                elif key == pygame.K_UP:
                    self._buffer_direction(world, 0, -1, player_id=2)
                elif key == pygame.K_RIGHT:
                    self._buffer_direction(world, 1, 0, player_id=2)
                elif key == pygame.K_LEFT:
                    self._buffer_direction(world, -1, 0, player_id=2)
            else:
                # Single player mode (both WASD and arrows control the same snake)
                if key in (pygame.K_DOWN, pygame.K_s):
                    self._buffer_direction(world, 0, 1)
                elif key in (pygame.K_UP, pygame.K_w):
                    self._buffer_direction(world, 0, -1)
                elif key in (pygame.K_RIGHT, pygame.K_d):
                    self._buffer_direction(world, 1, 0)
                elif key in (pygame.K_LEFT, pygame.K_a):
                    self._buffer_direction(world, -1, 0)

        # control keys
        if key == pygame.K_q:
            self._handle_quit(world)
        elif key == pygame.K_p:
            self._handle_pause(world)
        elif key in (pygame.K_ESCAPE, pygame.K_m):
            self._handle_open_settings(world)
        elif key == pygame.K_n:
            self._handle_music_toggle()
        elif key == pygame.K_c:
            self._handle_palette_randomize()

    def _handle_keyup(self, world: World, key: int) -> None:
        """Handle key up events.

        Args:
            world: ECS world
            key: Pygame key constant
        """
        # check if settings menu is open
        game_state = self._get_game_state(world)
        if game_state and game_state.settings_menu_open:
            # stop key repeat when up/down keys are released
            if key in (pygame.K_DOWN, pygame.K_s):
                self._key_down_pressed = False
                self._key_repeat_timer = 0.0
            elif key in (pygame.K_UP, pygame.K_w):
                self._key_up_pressed = False
                self._key_repeat_timer = 0.0

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

    def _get_snake_by_player_id(self, world: World, player_id: int):
        """Get a specific snake by player ID (for PvP mode).

        Args:
            world: ECS world
            player_id: Player number (1 or 2)

        Returns:
            Snake entity or None if not found
        """
        from ecs.entities.entity import EntityType

        snakes = world.registry.query_by_type(EntityType.SNAKE)
        for _, snake in snakes.items():
            if (
                hasattr(snake, "player_id")
                and snake.player_id.player_number == player_id
            ):
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

    def _handle_open_settings(self, world: World) -> None:
        """Handle settings menu open key press (ESC or M).

        Opens in-game settings overlay and pauses the game.

        Args:
            world: ECS world
        """
        game_state = self._get_game_state(world)
        if game_state:
            # calculate total menu items (settings + "Return to Menu" option)
            in_game_fields = (
                self._settings.get_in_game_menu_fields() if self._settings else []
            )
            game_state.settings_menu_item_count = (
                len(in_game_fields) + 1
            )  # +1 for "Return to Menu"
            game_state.settings_menu_open = True
            game_state.paused = True
            game_state.settings_selected_index = 0

    def _handle_settings_menu_input(self, world: World, key: int) -> None:
        """Handle input when settings menu is open.

        Args:
            world: ECS world
            key: Pygame key constant
        """
        game_state = self._get_game_state(world)
        if not game_state or not self._settings:
            return

        # use only in-game adjustable fields (no reset required)
        menu_fields = self._settings.get_in_game_menu_fields()
        # get visible fields (respecting section collapse state)
        if self._overlay_render_system:
            visible_fields = self._overlay_render_system._get_visible_fields(
                menu_fields
            )
        else:
            visible_fields = menu_fields
        total_items = len(visible_fields) + 1  # +1 for "Return to Menu" option
        return_to_menu_index = len(visible_fields)  # last item

        # handle ESC to close settings
        if key == pygame.K_ESCAPE:
            game_state.settings_menu_open = False
            game_state.paused = False
            # reset key repeat state
            self._key_down_pressed = False
            self._key_up_pressed = False
            self._key_repeat_timer = 0.0
        # handle RETURN to activate selected item
        elif key == pygame.K_RETURN:
            if game_state.settings_selected_index == return_to_menu_index:
                # "Return to Menu" selected
                game_state.settings_menu_open = False
                game_state.paused = False
                game_state.next_scene = "menu"
                # reset key repeat state
                self._key_down_pressed = False
                self._key_up_pressed = False
                self._key_repeat_timer = 0.0
            elif game_state.settings_selected_index < len(visible_fields):
                # check if this is a section header
                current_field = visible_fields[game_state.settings_selected_index]
                if (
                    current_field.get("type") == "section"
                    and self._overlay_render_system
                ):
                    # toggle section
                    self._overlay_render_system.toggle_section(current_field["key"])
                else:
                    # close settings and resume game
                    game_state.settings_menu_open = False
                    game_state.paused = False
                    # reset key repeat state
                    self._key_down_pressed = False
                    self._key_up_pressed = False
                    self._key_repeat_timer = 0.0
            else:
                # close settings and resume game
                game_state.settings_menu_open = False
                game_state.paused = False
                # reset key repeat state
                self._key_down_pressed = False
                self._key_up_pressed = False
                self._key_repeat_timer = 0.0
        # navigate down
        elif key in (pygame.K_DOWN, pygame.K_s):
            game_state.settings_selected_index = (
                game_state.settings_selected_index + 1
            ) % total_items
            # mark key as pressed and reset timer for repeat
            self._key_down_pressed = True
            self._key_up_pressed = False
            self._key_repeat_timer = 0.0
        # navigate up
        elif key in (pygame.K_UP, pygame.K_w):
            game_state.settings_selected_index = (
                game_state.settings_selected_index - 1
            ) % total_items
            # mark key as pressed and reset timer for repeat
            self._key_up_pressed = True
            self._key_down_pressed = False
            self._key_repeat_timer = 0.0
        # adjust setting left/right (only for actual settings, not "Return to Menu")
        elif key in (pygame.K_LEFT, pygame.K_a):
            if game_state.settings_selected_index < len(menu_fields):
                field = menu_fields[game_state.settings_selected_index]
                self._settings.step_setting(field, -1)
                self._apply_audio_setting_if_changed(field["key"])
        elif key in (pygame.K_RIGHT, pygame.K_d):
            if game_state.settings_selected_index < len(menu_fields):
                field = menu_fields[game_state.settings_selected_index]
                self._settings.step_setting(field, +1)
                self._apply_audio_setting_if_changed(field["key"])
        # randomize colors
        elif key == pygame.K_c:
            self._handle_palette_randomize()

    def _apply_audio_setting_if_changed(self, field_key: str) -> None:
        """Apply audio settings immediately when changed.

        Args:
            field_key: The key of the field that was changed
        """
        if field_key == "background_music":
            # control background music
            if self._settings.get("background_music"):
                # try to unpause first
                pygame.mixer.music.unpause()
                # if music isn't playing, reload and start it
                if not pygame.mixer.music.get_busy():
                    try:
                        pygame.mixer.music.load("assets/sound/Slither_Sprint.mp3")
                        pygame.mixer.music.play(-1)
                    except Exception:
                        pass
            else:
                pygame.mixer.music.pause()
        elif field_key == "sound_effects":
            # control all sound effect channels
            if self._settings.get("sound_effects"):
                pygame.mixer.unpause()
            else:
                pygame.mixer.pause()

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
