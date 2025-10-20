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

"""Main game loop orchestrator."""

import sys
import pygame
from typing import Optional

from .clock import GameClock
from old_code.config import GameConfig
from old_code.settings import GameSettings
from old_code.assets import GameAssets
from old_code.state import GameState
from old_code.entities import Snake, Apple, Obstacle
from old_code.constants import WINDOW_TITLE


class GameApp:
    """Main game application orchestrator.

    This class manages the game loop, initialization, and high-level flow control.
    It delegates specific game logic to the old code during migration.
    """

    def __init__(self):
        """Initialize the game application."""
        self.config: Optional[GameConfig] = None
        self.settings: Optional[GameSettings] = None
        self.assets: Optional[GameAssets] = None
        self.state: Optional[GameState] = None
        self.clock: Optional[GameClock] = None
        self.running: bool = False

    def initialize(self) -> None:
        """Initialize all game systems and resources."""
        # Initialize pygame subsystems
        pygame.init()
        pygame.mixer.init()

        # Initialize game configuration
        self.config = GameConfig()

        # Initialize game settings
        self.settings = GameSettings(
            self.config.initial_width, self.config.initial_grid_size
        )

        # Initialize game assets
        self.assets = GameAssets(self.config.initial_width)

        # Initialize and start background music
        GameAssets.init_music(volume=0.2, start_playing=True)

        # Initialize game state
        self.state = GameState(
            self.config.initial_width,
            self.config.initial_height,
            self.config.initial_grid_size,
        )

        # Initialize game clock
        self.clock = GameClock()

        # Apply default settings
        self._apply_settings(reset_objects=False)

        # Calculate and create obstacles from settings
        num_obstacles = Obstacle.calculate_obstacles_from_difficulty(
            self.settings.get("obstacle_difficulty"),
            self.state.width,
            self.state.grid_size,
            self.state.height,
        )
        self.state.create_obstacles_constructively(num_obstacles)
        pygame.display.set_caption(WINDOW_TITLE)

    def run(self) -> None:
        """Run the main game loop."""
        if not self.state or not self.clock:
            raise RuntimeError("Game not initialized. Call initialize() first.")

        self.running = True

        # Start menu (blocks until user picks "Start Game")
        self._run_start_menu()

        # Main game loop
        self._run_main_loop()

    def _apply_settings(self, reset_objects: bool = False) -> None:
        """Apply settings to game state, potentially resizing window and recreating objects.

        Args:
            reset_objects: Whether to recreate game objects (snake, apples, obstacles)
        """
        if not all([self.state, self.assets, self.config, self.settings]):
            raise RuntimeError("Game not properly initialized")

        old_grid = self.state.grid_size

        # Calculate new grid size from desired cells per side
        desired_cells = max(10, int(self.settings.get("cells_per_side")))
        new_grid_size = self.config.get_optimal_grid_size(desired_cells)

        # Calculate obstacles from difficulty
        new_width, new_height = self.config.calculate_window_size(new_grid_size)
        num_obstacles = Obstacle.calculate_obstacles_from_difficulty(
            self.settings.get("obstacle_difficulty"),
            new_width,
            new_grid_size,
            new_height,
        )

        # Validate and get apples count
        num_apples = self.settings.validate_apples_count(
            new_width, new_grid_size, new_height
        )

        # Control background music playback based on setting
        if self.settings.get("background_music"):
            pygame.mixer.music.unpause()
        else:
            pygame.mixer.music.pause()

        # Recompute window and recreate surface/fonts if grid changed
        if new_grid_size != old_grid:
            new_width, new_height = self.config.calculate_window_size(new_grid_size)
            self.state.arena = pygame.display.set_mode((new_width, new_height))
            pygame.display.set_caption(WINDOW_TITLE)

            # Update state's dimensions to match new grid size
            self.state.update_dimensions(new_width, new_height, new_grid_size)

            # Reload fonts with new width
            self.assets.reload_fonts(new_width)

            # Force reset_objects when grid size changes to prevent misalignment
            reset_objects = True

        # Recreate moving objects to reflect new geometry/speed
        if reset_objects:
            # Get current dimensions from state
            width = self.state.width
            height = self.state.height
            grid_size = self.state.grid_size

            # Recreate snake with initial speed
            self.state.snake = Snake(width, height, grid_size)
            self.state.snake.speed = float(self.settings.get("initial_speed"))

            # Create obstacles
            self.state.create_obstacles_constructively(num_obstacles)

            # Create multiple apples
            self.state.apples = []
            for _ in range(num_apples):
                apple = Apple(width, height, grid_size)
                apple.ensure_valid_position(self.state.snake, self.state.obstacles)
                # Also ensure it doesn't overlap with existing apples
                while any(apple.x == a.x and apple.y == a.y for a in self.state.apples):
                    apple.ensure_valid_position(self.state.snake, self.state.obstacles)
                self.state.apples.append(apple)

    def _run_start_menu(self) -> None:
        """Run the start menu loop."""
        # Import here to avoid circular imports
        from kobra import start_menu

        start_menu(self.state, self.assets, self.config, self.settings)

    def _run_main_loop(self) -> None:
        """Run the main game loop."""
        # Import here to avoid circular imports
        from kobra import (
            draw_grid,
            draw_music_indicator,
            draw_pause_screen,
        )

        show_pause_hint_end_time = pygame.time.get_ticks() + 2000  # 2 seconds
        previous_tail_length = 0

        while self.running:
            # Get delta time from clock
            dt = self.clock.tick()

            # Process events
            self._process_events()

            # Update game state
            if self.state.game_on:
                self._update_game_state(dt, previous_tail_length)
                previous_tail_length = len(self.state.snake.tail)

            # Render frame
            self._render_frame(
                draw_grid,
                draw_music_indicator,
                draw_pause_screen,
                show_pause_hint_end_time,
            )

            # Update display
            pygame.display.update()

    def _process_events(self) -> None:
        """Process pygame events."""
        for event in pygame.event.get():
            # App terminated
            if event.type == pygame.QUIT:
                self.quit()
                return

            # Key pressed
            if event.type == pygame.KEYDOWN:
                self._handle_keydown(event.key)

    def _handle_keydown(self, key: int) -> None:
        """Handle key down events."""
        # Import here to avoid circular imports

        # Movement keys
        if key in (pygame.K_DOWN, pygame.K_s) and self.state.snake.ymov != -1:
            self.state.snake.ymov = 1
            self.state.snake.xmov = 0
        elif key in (pygame.K_UP, pygame.K_w) and self.state.snake.ymov != 1:
            self.state.snake.ymov = -1
            self.state.snake.xmov = 0
        elif key in (pygame.K_RIGHT, pygame.K_d) and self.state.snake.xmov != -1:
            self.state.snake.ymov = 0
            self.state.snake.xmov = 1
        elif key in (pygame.K_LEFT, pygame.K_a) and self.state.snake.xmov != 1:
            self.state.snake.ymov = 0
            self.state.snake.xmov = -1
        # Control keys
        elif key == pygame.K_q:
            self.quit()
        elif key == pygame.K_p:  # Pause game
            self.state.toggle_pause()
        elif key in (pygame.K_m, pygame.K_ESCAPE):  # Open menu
            self._handle_menu_key()
        elif key == pygame.K_n:  # Toggle music mute
            self.settings.set(
                "background_music", not self.settings.get("background_music")
            )
            self._apply_settings(reset_objects=False)
        elif key == pygame.K_c:  # Randomize snake colors
            self.settings.randomize_snake_colors()

    def _handle_menu_key(self) -> None:
        """Handle menu key press."""
        # Import here to avoid circular imports
        from kobra import run_settings_menu, _show_reset_warning_dialog

        was_running = self.state.game_on
        self.state.pause()

        # Store old values of critical settings
        old_cells = self.settings.get("cells_per_side")
        old_obstacles = self.settings.get("obstacle_difficulty")
        old_initial_speed = self.settings.get("initial_speed")
        old_num_apples = self.settings.get("number_of_apples")
        old_electric_walls = self.settings.get("electric_walls")

        run_settings_menu(self.state, self.assets, self.settings)

        # Check if critical settings changed (require reset)
        needs_reset = (
            old_cells != self.settings.get("cells_per_side")
            or old_obstacles != self.settings.get("obstacle_difficulty")
            or old_initial_speed != self.settings.get("initial_speed")
            or old_num_apples != self.settings.get("number_of_apples")
            or old_electric_walls != self.settings.get("electric_walls")
        )

        # Determine if we should reset
        should_reset = False
        if needs_reset:
            # If "Reset Game on Apply" is enabled, reset automatically
            if self.settings.get("reset_game_on_apply"):
                should_reset = True
            else:
                # Show warning dialog and ask user
                user_choice = _show_reset_warning_dialog(self.state, self.assets)
                if user_choice == "reset":
                    should_reset = True
                else:  # user_choice == "cancel"
                    # Revert the critical settings changes
                    self.settings.set("cells_per_side", old_cells)
                    self.settings.set("obstacle_difficulty", old_obstacles)
                    self.settings.set("initial_speed", old_initial_speed)
                    self.settings.set("number_of_apples", old_num_apples)
                    self.settings.set("electric_walls", old_electric_walls)
                    should_reset = False

        # Apply settings with or without reset
        self._apply_settings(reset_objects=should_reset)
        self.state.game_on = was_running

    def _update_game_state(self, dt: float, previous_tail_length: int) -> None:
        """Update game state for one frame."""
        # Import here to avoid circular imports
        from kobra import game_over_handler, _will_wrap_around

        if len(self.state.snake.tail) == 0 and previous_tail_length > 0:
            # Reset pause hint timer when snake loses tail
            pass

        # Only update snake position when it has reached its current target
        if (
            self.state.snake.target_x == self.state.snake.head.x
            and self.state.snake.target_y == self.state.snake.head.y
        ):
            if self.state.snake.xmov or self.state.snake.ymov:
                self.state.snake.update(
                    self.state.apples,
                    self.state.obstacles,
                    lambda: game_over_handler(self.state, self.assets, self.settings),
                    self.settings.get("electric_walls"),
                )

        # Advance interpolation toward the current target grid cell (if any)
        if (
            self.state.snake.target_x != self.state.snake.head.x
            or self.state.snake.target_y != self.state.snake.head.y
        ):
            move_interval_ms = 1000.0 / self.state.snake.speed
            self.state.snake.move_progress += dt / move_interval_ms

            if self.state.snake.move_progress > 1.0:
                self.state.snake.move_progress = 1.0

            electric_walls = self.settings.get("electric_walls")

            # We multiply by xmov (respectively, ymov) so that the snake
            # keeps moving in the direction it was moving earlier
            if not electric_walls and _will_wrap_around(
                self.state,
                self.state.snake.head.x,
                self.state.snake.target_x,
                self.state.snake.width,
            ):
                self.state.snake.draw_x = (
                    self.state.snake.head.x
                    + self.state.snake.xmov
                    * self.state.grid_size
                    * self.state.snake.move_progress
                )
            else:
                self.state.snake.draw_x = (
                    self.state.snake.head.x
                    + (self.state.snake.target_x - self.state.snake.head.x)
                    * self.state.snake.move_progress
                )

            if not electric_walls and _will_wrap_around(
                self.state,
                self.state.snake.head.y,
                self.state.snake.target_y,
                self.state.snake.height,
            ):
                self.state.snake.draw_y = (
                    self.state.snake.head.y
                    + self.state.snake.ymov
                    * self.state.grid_size
                    * self.state.snake.move_progress
                )
            else:
                self.state.snake.draw_y = (
                    self.state.snake.head.y
                    + (self.state.snake.target_y - self.state.snake.head.y)
                    * self.state.snake.move_progress
                )

            if self.state.snake.move_progress >= 1.0:
                # Move completed: remember previous head position
                prev_x = self.state.snake.head.x
                prev_y = self.state.snake.head.y

                # Snap head to target grid cell
                self.state.snake.head.x = self.state.snake.target_x
                self.state.snake.head.y = self.state.snake.target_y
                self.state.snake.x = self.state.snake.head.x
                self.state.snake.y = self.state.snake.head.y

                # Insert previous head position into tail (store as (x,y) tuple)
                self.state.snake.tail.insert(0, (prev_x, prev_y))
                if self.state.snake.got_apple:
                    self.state.snake.got_apple = False
                else:
                    # Only pop when we didn't just eat an apple
                    if self.state.snake.tail:
                        self.state.snake.tail.pop()

                # Reset progress and ensure draw coords are exact integers
                self.state.snake.move_progress = 0.0
                self.state.snake.draw_x = float(self.state.snake.head.x)
                self.state.snake.draw_y = float(self.state.snake.head.y)
                self.state.snake.prev_head_x = self.state.snake.head.x
                self.state.snake.prev_head_y = self.state.snake.head.y
        else:
            # No pending move: keep draw coordinates synced to head
            self.state.snake.move_progress = 0.0
            self.state.snake.draw_x = float(self.state.snake.head.x)
            self.state.snake.draw_y = float(self.state.snake.head.y)

    def _render_frame(
        self,
        draw_grid,
        draw_music_indicator,
        draw_pause_screen,
        show_pause_hint_end_time: int,
    ) -> None:
        """Render one frame."""
        # Import here to avoid circular imports
        from old_code.constants import ARENA_COLOR, SCORE_COLOR, MESSAGE_COLOR
        from kobra import _will_wrap_around

        self.state.arena.fill(ARENA_COLOR)
        draw_grid(self.state)

        # Draw obstacles
        for obstacle in self.state.obstacles:
            obstacle.update()

        # Draw all apples
        for apple in self.state.apples:
            apple.update(self.state.arena)

        electric_walls = self.settings.get("electric_walls")
        snake_colors = self.settings.get_snake_colors()
        current_head_color = snake_colors["head"]
        current_tail_color = snake_colors["tail"]

        # Draw the tail with smooth interpolation
        for i, (tx, ty) in enumerate(self.state.snake.tail):
            draw_tx = tx
            draw_ty = ty

            if i == 0:
                prev_tx = self.state.snake.head.x
                prev_ty = self.state.snake.head.y
            else:
                prev_tx, prev_ty = self.state.snake.tail[i - 1]

            if self.state.snake.move_progress > 0.0:
                if not electric_walls and _will_wrap_around(
                    self.state, prev_tx, tx, self.state.snake.width
                ):
                    draw_tx = (
                        prev_tx
                        + self.state.snake.xmov
                        * self.state.grid_size
                        * self.state.snake.move_progress
                    )
                else:
                    draw_tx = prev_tx + (tx - prev_tx) * (
                        1.0 - self.state.snake.move_progress
                    )

                if not electric_walls and _will_wrap_around(
                    self.state, prev_ty, ty, self.state.snake.height
                ):
                    draw_ty = (
                        prev_ty
                        + self.state.snake.ymov
                        * self.state.grid_size
                        * self.state.snake.move_progress
                    )
                else:
                    draw_ty = prev_ty + (ty - prev_ty) * (
                        1.0 - self.state.snake.move_progress
                    )

            pygame.draw.rect(
                self.state.arena,
                current_tail_color,
                pygame.Rect(
                    round(draw_tx),
                    round(draw_ty),
                    self.state.grid_size,
                    self.state.grid_size,
                ),
            )

        # Draw head (use int coords for Rect)
        pygame.draw.rect(
            self.state.arena,
            current_head_color,
            pygame.Rect(
                round(self.state.snake.draw_x),
                round(self.state.snake.draw_y),
                self.state.grid_size,
                self.state.grid_size,
            ),
        )

        # Show score (snake length = head + tail)
        score = self.assets.render_custom(
            f"{len(self.state.snake.tail)}", SCORE_COLOR, int(self.state.width / 10)
        )
        score.set_alpha(75)  # opacity
        score_rect = score.get_rect(
            center=(self.state.width / 2, self.state.height / 12)
        )
        self.state.arena.blit(score, score_rect)

        # Draw music status indicator
        draw_music_indicator(self.state, self.assets, self.settings)

        # Check collision with all apples and maintain N apples in arena
        for apple in self.state.apples[:]:  # Use slice to iterate over copy
            if (
                self.state.snake.head.x == apple.x
                and self.state.snake.head.y == apple.y
            ):
                self.state.snake.got_apple = True
                max_speed = float(self.settings.get("max_speed"))
                self.state.snake.speed = min(
                    self.state.snake.speed * 1.1, max_speed
                )  # Increase speed

                # Plays the eating sound if enabled in the settings
                if (
                    self.settings.get("eat_sound")
                    and hasattr(self.assets, "eat_sound")
                    and self.assets.eat_sound
                ):
                    self.assets.eat_sound.play()

                # Remove eaten apple and spawn a new one
                self.state.apples.remove(apple)

                # Calculate available free cells using state properties
                free_cells = self.state.get_free_cells_count()

                # Only spawn new apple if there are free cells
                if free_cells > 0:
                    new_apple = Apple(
                        self.state.width, self.state.height, self.state.grid_size
                    )
                    new_apple.ensure_valid_position(
                        self.state.snake, self.state.obstacles
                    )
                    # Ensure it doesn't overlap with existing apples
                    while any(
                        new_apple.x == a.x and new_apple.y == a.y
                        for a in self.state.apples
                    ):
                        new_apple.ensure_valid_position(
                            self.state.snake, self.state.obstacles
                        )
                    self.state.apples.append(new_apple)

                break  # Only eat one apple per frame

        if pygame.time.get_ticks() < show_pause_hint_end_time and self.state.game_on:
            hint_surf = self.assets.render_custom(
                "Press P to pause", MESSAGE_COLOR, int(self.state.width / 30)
            )
            hint_surf.set_alpha(180)  # Deixa o texto semi-transparente
            hint_rect = hint_surf.get_rect(
                center=(self.state.width / 2, self.state.height - 40)
            )
            self.state.arena.blit(hint_surf, hint_rect)

        # Se o jogo estiver pausado, desenha a tela de pausa por cima de tudo
        if not self.state.game_on:
            draw_pause_screen(self.state, self.assets)

    def quit(self) -> None:
        """Quit the game application."""
        self.running = False
        pygame.quit()
        sys.exit()
