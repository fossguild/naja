#!/usr/bin/env python3
#
#   Copyright (c) 2023, Monaco F. J. <monaco@usp.br>
#
#   This file is part of KobraPy.
#
#   KobraPy is free software: you can redistribute it and/or modify
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

# pylint: disable=no-member
# Pygame uses dynamic imports that pylint doesn't understand

import sys
import pygame
from src.entities import Snake, Apple, Obstacle
from src.constants import (
    HEAD_COLOR,
    DEAD_HEAD_COLOR,
    TAIL_COLOR,
    ARENA_COLOR,
    GRID_COLOR,
    SCORE_COLOR,
    MESSAGE_COLOR,
    WINDOW_TITLE,
)
from src.state import GameState
from src.assets import GameAssets
from src.config import GameConfig
from src.settings import GameSettings
from src.menu import start_menu, run_settings_menu

##
## Game initialization
##

# Initialize Pygame to access display info.
pygame.init()

# Initialize the audio mixer
pygame.mixer.init()


##
## Settings Menu Functions
##


def apply_settings(
    state: GameState,
    assets: GameAssets,
    config: GameConfig,
    settings: GameSettings,
    reset_objects: bool = False,
) -> None:
    """Apply settings to game state, potentially resizing window and recreating objects.

    Args:
        state: GameState instance
        assets: GameAssets instance
        config: GameConfig instance
        settings: GameSettings instance
        reset_objects: Whether to recreate game objects (snake, apples, obstacles)
    """
    old_grid = state.grid_size

    # Calculate new grid size from desired cells per side
    desired_cells = max(10, int(settings.get("cells_per_side")))
    new_grid_size = config.get_optimal_grid_size(desired_cells)

    # Calculate obstacles from difficulty
    new_width, new_height = config.calculate_window_size(new_grid_size)
    num_obstacles = Obstacle.calculate_obstacles_from_difficulty(
        settings.get("obstacle_difficulty"), new_width, new_grid_size, new_height
    )

    # Validate and get apples count
    num_apples = settings.validate_apples_count(new_width, new_grid_size, new_height)

    # Control background music playback based on setting
    if settings.get("background_music"):
        pygame.mixer.music.unpause()
    else:
        pygame.mixer.music.pause()

    # Recompute window and recreate surface/fonts if grid changed
    if new_grid_size != old_grid:
        new_width, new_height = config.calculate_window_size(new_grid_size)
        state.arena = pygame.display.set_mode((new_width, new_height))
        pygame.display.set_caption(WINDOW_TITLE)

        # Update state's dimensions to match new grid size
        state.update_dimensions(new_width, new_height, new_grid_size)

        # Reload fonts with new width
        assets.reload_fonts(new_width)

        # Force reset_objects when grid size changes to prevent misalignment
        reset_objects = True

    # Recreate moving objects to reflect new geometry/speed
    if reset_objects:
        # Get current dimensions from state
        width = state.width
        height = state.height
        grid_size = state.grid_size

        # Recreate snake with initial speed
        state.snake = Snake(width, height, grid_size)
        state.snake.speed = float(settings.get("initial_speed"))

        # Create obstacles
        state.create_obstacles_constructively(num_obstacles)

        # Create multiple apples
        state.apples = []
        for _ in range(num_apples):
            apple = Apple(width, height, grid_size)
            apple.ensure_valid_position(state.snake, state.obstacles)
            # Also ensure it doesn't overlap with existing apples
            while any(apple.x == a.x and apple.y == a.y for a in state.apples):
                apple.ensure_valid_position(state.snake, state.obstacles)
            state.apples.append(apple)


# Load speaker sprites
try:
    speaker_on_sprite = pygame.image.load("assets/sprites/speaker-on.png")
    speaker_muted_sprite = pygame.image.load("assets/sprites/speaker-muted.png")
except pygame.error as e:
    print(f"Warning: Could not load speaker sprites: {e}")
    speaker_on_sprite = None
    speaker_muted_sprite = None


##
## Center message + simple key wait helpers
##


def _render_text_fit(
    assets: GameAssets,
    text: str,
    color,
    max_width_ratio: float,
    base_px: int,
    window_width: int,
):
    """Render text using the game's font, shrinking until it fits the given width ratio.

    Args:
        assets: GameAssets instance
        text: Text to render
        color: Text color
        max_width_ratio: Fraction of window width allowed
        base_px: Starting font size in pixels
        window_width: Current window width

    Returns:
        Rendered text surface
    """
    px = base_px
    while px > 8:  # don't go too tiny
        surf = assets.render_custom(text, color, px)
        if surf.get_width() <= window_width * max_width_ratio:
            return surf
        px -= 2
    return surf  # last attempt even if it doesn't fit perfectly


def _draw_center_message(
    state: GameState, assets: GameAssets, title: str, subtitle: str
) -> None:
    """Draw a centered message with title and subtitle.

    Args:
        state: GameState instance
        assets: GameAssets instance
        title: Main title text
        subtitle: Subtitle text
    """
    state.arena.fill(ARENA_COLOR)

    # Title ~ up to 80% of window width, start from BIG font size.
    title_surf = _render_text_fit(
        assets,
        title,
        MESSAGE_COLOR,
        max_width_ratio=0.8,
        base_px=int(state.width / 8),
        window_width=state.width,
    )
    state.arena.blit(
        title_surf, title_surf.get_rect(center=(state.width / 2, state.height / 2.6))
    )

    # Subtitle ~ up to 90% of width, start from SMALL font size.
    sub_surf = _render_text_fit(
        assets,
        subtitle,
        MESSAGE_COLOR,
        max_width_ratio=0.9,
        base_px=int(state.width / 20),
        window_width=state.width,
    )
    state.arena.blit(
        sub_surf, sub_surf.get_rect(center=(state.width / 2, state.height / 1.8))
    )

    pygame.display.update()


def _wait_for_keys(allowed_keys: set[int]) -> int:
    """Block until a KEYDOWN for one of allowed_keys (or quit). Return the key."""
    while True:
        event = pygame.event.wait()
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        if event.type == pygame.KEYDOWN and (
            not allowed_keys or event.key in allowed_keys
        ):
            return event.key


def game_over_handler(
    state: GameState, assets: GameAssets, settings: GameSettings
) -> None:
    """Handle game over scenario with visual feedback and prompt.

    Args:
        state: GameState instance
        assets: GameAssets instance
        settings: GameSettings instance
    """
    # Play death sound effect (if enabled)
    if settings.get("death_sound") and assets.gameover_sound:
        assets.gameover_sound.play()

    # Switch to death music (if music is enabled)
    if settings.get("background_music"):
        GameAssets.play_death_music()

    # Tell the bad news
    pygame.draw.rect(state.arena, DEAD_HEAD_COLOR, state.snake.head)
    pygame.display.update()
    # Game-over prompt: only Space/Enter restart; Q quits.
    _draw_center_message(
        state, assets, "Game Over", "Press Enter/Space to restart  •  Q to exit"
    )
    key = _wait_for_keys({pygame.K_RETURN, pygame.K_SPACE, pygame.K_q})

    # Switch back to background music (if music is enabled)
    if settings.get("background_music"):
        GameAssets.play_background_music()

    if key == pygame.K_q:
        pygame.quit()
        sys.exit()


##
## Draw the arena
##


def draw_grid(state: GameState) -> None:
    """Draw the game grid.

    Args:
        state: GameState instance
    """
    for x in range(0, state.width, state.grid_size):
        for y in range(0, state.height, state.grid_size):
            rect = pygame.Rect(x, y, state.grid_size, state.grid_size)
            pygame.draw.rect(state.arena, GRID_COLOR, rect, 1)


##
## Draws the icon representing whether the background music is on or off
##


def draw_music_indicator(
    state: GameState, assets: GameAssets, settings: GameSettings
) -> None:
    """Draw a subtle music status indicator in the bottom-right corner.

    Args:
        state: GameState instance
        assets: GameAssets instance
        settings: GameSettings instance
    """
    music_on = settings.get("background_music")

    # Define dimensions and spacing using proportional padding
    padding_x = int(state.width * 0.02)
    padding_y = int(state.height * 0.02)
    icon_size = int(state.width / 25)
    gap = 4  # Small pixel gap between icon and text

    # Render hint text to get its height
    hint_color = SCORE_COLOR if music_on else GRID_COLOR
    hint_text = "[N]"
    hint_surf = assets.render_custom(hint_text, hint_color, int(state.width / 50))
    hint_rect = hint_surf.get_rect()

    # Calculate total widget height
    total_widget_height = icon_size + gap + hint_rect.height

    # Choose sprite based on music state
    sprite = assets.speaker_on_sprite if music_on else assets.speaker_muted_sprite

    # Calculate positions
    icon_x = state.width - padding_x - icon_size
    icon_y = state.height - padding_y - total_widget_height

    # Scale and draw sprite
    if sprite is not None:
        scaled_sprite = pygame.transform.scale(sprite, (icon_size, icon_size))
        state.arena.blit(scaled_sprite, (icon_x, icon_y))

    # Position and draw text hint below the icon
    hint_rect.centerx = icon_x + icon_size // 2
    hint_rect.top = icon_y + icon_size + gap
    state.arena.blit(hint_surf, hint_rect)


##
## Main game function
##


def main():
    """Main game entry point with proper initialization."""
    # Initialize game configuration
    config = GameConfig()

    # Initialize game settings
    settings = GameSettings(config.initial_width, config.initial_grid_size)

    # Initialize game assets
    assets = GameAssets(config.initial_width)

    # Initialize and start background music
    GameAssets.init_music(volume=0.2, start_playing=True)

    # Initialize game state
    state = GameState(
        config.initial_width, config.initial_height, config.initial_grid_size
    )

    # Define a callback function to pass to the menu
    def apply_settings_callback(reset_objects=False):
        apply_settings(state, assets, config, settings, reset_objects)

    # Apply default settings with state
    apply_settings_callback(reset_objects=True)

    # Calculate and create obstacles from settings
    num_obstacles = Obstacle.calculate_obstacles_from_difficulty(
        settings.get("obstacle_difficulty"), state.width, state.grid_size, state.height
    )
    state.create_obstacles_constructively(num_obstacles)
    pygame.display.set_caption(WINDOW_TITLE)

    ##
    ## Start flow
    ##
    start_menu(
        state, assets, config, settings, apply_settings_callback
    )  # blocks until user picks "Start Game"

    ##
    ## Main loop
    ##
    while True:
        dt = state.clock.tick_busy_loop(0)
        for event in pygame.event.get():  # Wait for events
            # App terminated
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            # Key pressed
            if event.type == pygame.KEYDOWN:
                # Down arrow (or S): move down
                if (
                    event.key
                    in (
                        pygame.K_DOWN,
                        pygame.K_s,
                    )
                    and state.snake.ymov != -1
                ):
                    state.snake.ymov = 1
                    state.snake.xmov = 0
                # Up arrow (or W): move up
                elif event.key in (pygame.K_UP, pygame.K_w) and state.snake.ymov != 1:
                    state.snake.ymov = -1
                    state.snake.xmov = 0
                # Right arrow (or D): move right
                elif (
                    event.key in (pygame.K_RIGHT, pygame.K_d) and state.snake.xmov != -1
                ):
                    state.snake.ymov = 0
                    state.snake.xmov = 1
                # Left arrow (or A): move left
                elif event.key in (pygame.K_LEFT, pygame.K_a) and state.snake.xmov != 1:
                    state.snake.ymov = 0
                    state.snake.xmov = -1
                # Q : quit game
                elif event.key == pygame.K_q:
                    pygame.quit()
                    sys.exit()
                elif event.key == pygame.K_p:  # P : pause game
                    state.toggle_pause()
                elif event.key in (pygame.K_m, pygame.K_ESCAPE):  # M or ESC : open menu
                    was_running = state.game_on
                    state.pause()

                    # Store old values of critical settings
                    old_cells = settings.get("cells_per_side")
                    old_obstacles = settings.get("obstacle_difficulty")
                    old_initial_speed = settings.get("initial_speed")
                    old_num_apples = settings.get("number_of_apples")

                    run_settings_menu(state, assets, settings)

                    # Check if critical settings changed (require reset)
                    needs_reset = (
                        old_cells != settings.get("cells_per_side")
                        or old_obstacles != settings.get("obstacle_difficulty")
                        or old_initial_speed != settings.get("initial_speed")
                        or old_num_apples != settings.get("number_of_apples")
                    )

                    # Force reset if critical settings changed, or use player preference
                    apply_settings(
                        state,
                        assets,
                        config,
                        settings,
                        reset_objects=needs_reset
                        or settings.get("reset_game_on_apply"),
                    )
                    state.game_on = was_running
                elif event.key == pygame.K_n:  # N : toggle music mute
                    settings.set(
                        "background_music", not settings.get("background_music")
                    )
                    apply_settings(state, assets, config, settings, reset_objects=False)

        ## Update the game
        if state.game_on:
            # Only update snake position when it has reached its current target
            if (
                state.snake.target_x == state.snake.head.x
                and state.snake.target_y == state.snake.head.y
            ):
                if state.snake.xmov or state.snake.ymov:
                    state.snake.update(
                        state.apples,
                        state.obstacles,
                        lambda: game_over_handler(state, assets, settings),
                    )

            # Advance interpolation toward the current target grid cell (if any)
            if (
                state.snake.target_x != state.snake.head.x
                or state.snake.target_y != state.snake.head.y
            ):
                move_interval_ms = 1000.0 / state.snake.speed
                state.snake.move_progress += dt / move_interval_ms
                if state.snake.move_progress > 1.0:
                    state.snake.move_progress = 1.0
                state.snake.draw_x = (
                    state.snake.head.x
                    + (state.snake.target_x - state.snake.head.x)
                    * state.snake.move_progress
                )
                state.snake.draw_y = (
                    state.snake.head.y
                    + (state.snake.target_y - state.snake.head.y)
                    * state.snake.move_progress
                )
                if state.snake.move_progress >= 1.0:
                    # Move completed: remember previous head position
                    prev_x = state.snake.head.x
                    prev_y = state.snake.head.y

                    # Snap head to target grid cell
                    state.snake.head.x = state.snake.target_x
                    state.snake.head.y = state.snake.target_y
                    state.snake.x = state.snake.head.x
                    state.snake.y = state.snake.head.y

                    # Insert previous head position into tail (store as (x,y) tuple)
                    state.snake.tail.insert(0, (prev_x, prev_y))
                    if state.snake.got_apple:
                        state.snake.got_apple = False
                    else:
                        # Only pop when we didn't just eat an apple
                        if state.snake.tail:
                            state.snake.tail.pop()

                    # Reset progress and ensure draw coords are exact integers
                    state.snake.move_progress = 0.0
                    state.snake.draw_x = float(state.snake.head.x)
                    state.snake.draw_y = float(state.snake.head.y)
                    state.snake.prev_head_x = state.snake.head.x
                    state.snake.prev_head_y = state.snake.head.y
            else:
                # No pending move: keep draw coordinates synced to head
                state.snake.move_progress = 0.0
                state.snake.draw_x = float(state.snake.head.x)
                state.snake.draw_y = float(state.snake.head.y)

        state.arena.fill(ARENA_COLOR)
        draw_grid(state)

        # Draw obstacles
        for obstacle in state.obstacles:
            obstacle.update()

        # Draw all apples
        for apple in state.apples:
            apple.update(state.arena)

        # Draw the tail with smooth interpolation
        for i, (tx, ty) in enumerate(state.snake.tail):
            draw_tx = tx
            draw_ty = ty

            if i == 0 and state.snake.move_progress > 0.0:
                draw_tx = state.snake.head.x + (tx - state.snake.head.x) * (
                    1.0 - state.snake.move_progress
                )
                draw_ty = state.snake.head.y + (ty - state.snake.head.y) * (
                    1.0 - state.snake.move_progress
                )
            elif i > 0 and state.snake.move_progress > 0.0:
                prev_tx, prev_ty = state.snake.tail[i - 1]
                draw_tx = prev_tx + (tx - prev_tx) * (1.0 - state.snake.move_progress)
                draw_ty = prev_ty + (ty - prev_ty) * (1.0 - state.snake.move_progress)

            pygame.draw.rect(
                state.arena,
                TAIL_COLOR,
                pygame.Rect(
                    round(draw_tx), round(draw_ty), state.grid_size, state.grid_size
                ),
            )

        # Draw head (use int coords for Rect)
        pygame.draw.rect(
            state.arena,
            HEAD_COLOR,
            pygame.Rect(
                round(state.snake.draw_x),
                round(state.snake.draw_y),
                state.grid_size,
                state.grid_size,
            ),
        )

        # Show score (snake length = head + tail)
        score = assets.render_big(f"{len(state.snake.tail)}", SCORE_COLOR)
        score.set_alpha(75)  # opacity
        score_rect = score.get_rect(center=(state.width / 2, state.height / 12))
        state.arena.blit(score, score_rect)

        # Draw music status indicator
        draw_music_indicator(state, assets, settings)

        # Check collision with all apples and maintain N apples in arena
        for apple in state.apples[:]:  # Use slice to iterate over copy
            if state.snake.head.x == apple.x and state.snake.head.y == apple.y:
                state.snake.got_apple = True
                max_speed = float(settings.get("max_speed"))
                state.snake.speed = min(
                    state.snake.speed * 1.1, max_speed
                )  # Increase speed

                # Plays the eating sound if enabled in the settings
                if (
                    settings.get("eat_sound")
                    and hasattr(assets, "eat_sound")
                    and assets.eat_sound
                ):
                    assets.eat_sound.play()

                # Remove eaten apple and spawn a new one
                state.apples.remove(apple)

                # Calculate available free cells using state properties
                free_cells = state.get_free_cells_count()

                # Only spawn new apple if there are free cells
                if free_cells > 0:
                    new_apple = Apple(state.width, state.height, state.grid_size)
                    new_apple.ensure_valid_position(state.snake, state.obstacles)
                    # Ensure it doesn't overlap with existing apples
                    while any(
                        new_apple.x == a.x and new_apple.y == a.y for a in state.apples
                    ):
                        new_apple.ensure_valid_position(state.snake, state.obstacles)
                    state.apples.append(new_apple)

                break  # Only eat one apple per frame

        # Update display
        pygame.display.update()


if __name__ == "__main__":
    main()
