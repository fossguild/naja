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
    DEAD_HEAD_COLOR,
    ARENA_COLOR,
    GRID_COLOR,
    SCORE_COLOR,
    MESSAGE_COLOR,
    WINDOW_TITLE,
    POWERUP_SPAWN_INTERVAL_MS,
    POWERUP_SPAWN_CHANCE,
)
from src.state import GameState
from src.assets import GameAssets
from src.config import GameConfig
from src.settings import GameSettings
from src.power_ups import (
    powerups_init,
    powerups_draw_all,
    powerups_draw_overlay_on_head,
    powerups_handle_collisions,
    powerups_death_guard,
    powerups_draw_timer,
    powerups_try_periodic_spawn,
    powerups_pause_begin,
    powerups_pause_end,
)

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


def _draw_settings_menu(
    state: GameState, assets: GameAssets, settings: GameSettings, selected_index: int
) -> None:
    """Draw the settings menu screen.

    Args:
        state: GameState instance
        assets: GameAssets instance
        settings: GameSettings instance
        selected_index: Currently selected menu item index
    """
    state.arena.fill(ARENA_COLOR)

    title = assets.render_custom("Settings", MESSAGE_COLOR, int(state.width / 10))
    title_rect = title.get_rect(center=(state.width / 2, state.height / 10))
    state.arena.blit(title, title_rect)

    # Spacing and scroll parameters
    visible_rows = int(state.height * 0.75 // (state.height * 0.07))
    top_index = max(0, selected_index - visible_rows + 3)
    padding_y = int(state.height * 0.20)
    row_h = int(state.height * 0.07)

    # Draw visible rows
    for draw_i, field_i in enumerate(range(top_index, len(settings.MENU_FIELDS))):
        if draw_i >= visible_rows:
            break
        f = settings.MENU_FIELDS[field_i]
        val = settings.get(f["key"])
        formatted_val = settings.format_setting_value(
            f, val, state.width, state.grid_size
        )
        text = assets.render_small(
            f"{f['label']}: {formatted_val}",
            SCORE_COLOR if field_i == selected_index else MESSAGE_COLOR,
        )
        rect = text.get_rect()
        rect.left = int(state.width * 0.12)
        rect.top = padding_y + draw_i * row_h
        state.arena.blit(text, rect)

    # Hint footer (smaller)
    hint_text = "[A/D] change   [W/S] select   [Enter/Esc] back [C] random colors"
    hint = assets.render_custom(hint_text, GRID_COLOR, int(state.width / 40))
    state.arena.blit(hint, hint.get_rect(center=(state.width / 2, state.height * 0.95)))

    pygame.display.update()


def run_settings_menu(
    state: GameState, assets: GameAssets, settings: GameSettings
) -> None:
    """Run the settings menu modal loop.

    Args:
        state: GameState instance
        assets: GameAssets instance
        settings: GameSettings instance
    """
    selected = 0

    while True:
        _draw_settings_menu(state, assets, settings, selected)

        for event in pygame.event.get():
            # Guard clauses keep nesting shallow.
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type != pygame.KEYDOWN:
                continue

            key = event.key

            if key in (pygame.K_ESCAPE, pygame.K_RETURN):
                return  # exit menu

            if key in (pygame.K_DOWN, pygame.K_s):
                selected = (selected + 1) % len(settings.MENU_FIELDS)
                continue

            if key in (pygame.K_UP, pygame.K_w):
                selected = (selected - 1) % len(settings.MENU_FIELDS)
                continue

            if key in (pygame.K_LEFT, pygame.K_a):
                settings.step_setting(settings.MENU_FIELDS[selected], -1)
                continue

            if key in (pygame.K_RIGHT, pygame.K_d):
                settings.step_setting(settings.MENU_FIELDS[selected], +1)
                continue


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
## Start menu (Start / Settings)
##


def start_menu(
    state: GameState,
    assets: GameAssets,
    config: GameConfig,
    settings: GameSettings,
) -> None:
    """Main menu shown before the game starts.

    Args:
        state: GameState instance
        assets: GameAssets instance
        config: GameConfig instance
        settings: GameSettings instance
    """
    selected = 0
    items = ["Start Game", "Settings"]

    while True:
        state.arena.fill(ARENA_COLOR)

        # Title
        title = assets.render_big(WINDOW_TITLE, MESSAGE_COLOR)
        state.arena.blit(
            title, title.get_rect(center=(state.width / 2, state.height / 4))
        )

        # Draw buttons
        for i, text_label in enumerate(items):
            color = SCORE_COLOR if i == selected else MESSAGE_COLOR
            text = assets.render_small(text_label, color)
            rect = text.get_rect(
                center=(state.width / 2, state.height / 2 + i * (state.height * 0.12))
            )
            state.arena.blit(text, rect)

        pygame.display.update()

        # Input handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                key = event.key
                if key in (pygame.K_UP, pygame.K_w):
                    selected = (selected - 1) % len(items)
                elif key in (pygame.K_DOWN, pygame.K_s):
                    selected = (selected + 1) % len(items)
                elif key in (pygame.K_RETURN, pygame.K_SPACE):
                    if items[selected] == "Start Game":
                        return  # proceed to game
                    elif items[selected] == "Settings":
                        run_settings_menu(state, assets, settings)
                        apply_settings(
                            state, assets, config, settings, reset_objects=False
                        )
                elif key == pygame.K_m:
                    run_settings_menu(state, assets, settings)
                    apply_settings(state, assets, config, settings, reset_objects=False)
                elif key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # Simple click detection
                mx, my = event.pos
                for i, text_label in enumerate(items):
                    rect = assets.render_small(text_label, MESSAGE_COLOR).get_rect(
                        center=(
                            state.width / 2,
                            state.height / 2 + i * (state.height * 0.12),
                        )
                    )
                    if rect.collidepoint(mx, my):
                        if text_label == "Start Game":
                            return
                        elif text_label == "Settings":
                            run_settings_menu(state, assets, settings)
                            apply_settings(
                                state, assets, config, settings, reset_objects=False
                            )


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


def draw_pause_screen(state: GameState, assets: GameAssets):
    """Desenha uma sobreposição semi-transparente e o texto de pausa."""
    # Cria uma superfície para a sobreposição com transparência alfa
    overlay = pygame.Surface((state.width, state.height), pygame.SRCALPHA)
    overlay.fill((32, 32, 32, 180))  # Cinza escuro, semi-transparente
    state.arena.blit(overlay, (0, 0))

    # Mostra o texto "Paused"
    paused_title = assets.render_big("Paused", MESSAGE_COLOR)
    paused_title_rect = paused_title.get_rect(
        center=(state.width / 2, state.height / 2)
    )
    state.arena.blit(paused_title, paused_title_rect)

    paused_subtitle = assets.render_small("Press P to continue", MESSAGE_COLOR)
    paused_subtitle_rect = paused_subtitle.get_rect(
        center=(state.width / 2, state.height * 2 / 3)
    )
    state.arena.blit(paused_subtitle, paused_subtitle_rect)


def _will_wrap_around(state: GameState, origin: int, dest: int, limit: int) -> bool:
    """
    Checks if an object on the game's grid will wrap around by moving in a
    straight line (horizontally or vertically) from origin to dest.

    The limit parameter should be either the arena's width or height.
    """

    return abs(abs(origin - dest) - limit) <= state.grid_size


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

    # Initialize power ups
    powerups_init(state)

    # Apply default settings with state
    apply_settings(state, assets, config, settings, reset_objects=False)

    # Calculate and create obstacles from settings
    num_obstacles = Obstacle.calculate_obstacles_from_difficulty(
        settings.get("obstacle_difficulty"), state.width, state.grid_size, state.height
    )
    state.create_obstacles_constructively(num_obstacles)
    pygame.display.set_caption(WINDOW_TITLE)

    ##
    ## Start flow
    ##
    start_menu(state, assets, config, settings)  # blocks until user picks "Start Game"

    # Schedule the first periodic attempt a few seconds after starting the game
    state.powerups_next_try_ms = pygame.time.get_ticks() + (
        POWERUP_SPAWN_INTERVAL_MS // 2
    )  # delay

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
                    prev = state.game_on
                    state.toggle_pause()
                    # Bridge power-ups timers with the pause state
                    if prev and not state.game_on:
                        powerups_pause_begin(state)  # just entered pause
                    elif not prev and state.game_on:
                        powerups_pause_end(state)  # just resumed
                elif event.key in (pygame.K_m, pygame.K_ESCAPE):  # M or ESC : open menu
                    was_running = state.game_on
                    state.pause()
                    powerups_pause_begin(state)  # freeze power-up timers during menu

                    # Store old values of critical settings
                    old_cells = settings.get("cells_per_side")
                    old_obstacles = settings.get("obstacle_difficulty")
                    old_initial_speed = settings.get("initial_speed")
                    old_num_apples = settings.get("number_of_apples")
                    old_electric_walls = settings.get("electric_walls")

                    run_settings_menu(state, assets, settings)

                    # Check if critical settings changed (require reset)
                    needs_reset = (
                        old_cells != settings.get("cells_per_side")
                        or old_obstacles != settings.get("obstacle_difficulty")
                        or old_initial_speed != settings.get("initial_speed")
                        or old_num_apples != settings.get("number_of_apples")
                        or old_electric_walls != settings.get("electric_walls")
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
                    if was_running:
                        powerups_pause_end(state)
                    state.game_on = was_running
                elif event.key == pygame.K_n:  # N : toggle music mute
                    settings.set(
                        "background_music", not settings.get("background_music")
                    )
                    apply_settings(state, assets, config, settings, reset_objects=False)

                elif event.key == pygame.K_c:  # C : randomize snake colors
                    settings.randomize_snake_colors()

        ## Update the game
        if state.game_on:
            # Only update snake position when it has reached its current target
            if (
                state.snake.target_x == state.snake.head.x
                and state.snake.target_y == state.snake.head.y
            ):
                if state.snake.xmov or state.snake.ymov:
                    # While invincible, walls behave as wrap-around (ignore electric walls)
                    is_invincible = pygame.time.get_ticks() < getattr(
                        state, "invincible_until_ms", 0
                    )
                    effective_electric_walls = (
                        settings.get("electric_walls") and not is_invincible
                    )

                    state.snake.update(
                        state.apples,
                        state.obstacles,
                        powerups_death_guard(
                            state, lambda: game_over_handler(state, assets, settings)
                        ),
                        effective_electric_walls,
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

                # While invincible, allow wrap-around instead of electric walls
                is_invincible = pygame.time.get_ticks() < getattr(
                    state, "invincible_until_ms", 0
                )
                electric_walls = settings.get("electric_walls") and not is_invincible

                # We multiply by xmov (respectively, ymov) so that the snake
                # keeps moving in the direction it was moving earlier
                if not electric_walls and _will_wrap_around(
                    state, state.snake.head.x, state.snake.target_x, state.snake.width
                ):
                    state.snake.draw_x = (
                        state.snake.head.x
                        + state.snake.xmov * state.grid_size * state.snake.move_progress
                    )
                else:
                    state.snake.draw_x = (
                        state.snake.head.x
                        + (state.snake.target_x - state.snake.head.x)
                        * state.snake.move_progress
                    )

                if not electric_walls and _will_wrap_around(
                    state, state.snake.head.y, state.snake.target_y, state.snake.height
                ):
                    state.snake.draw_y = (
                        state.snake.head.y
                        + state.snake.ymov * state.grid_size * state.snake.move_progress
                    )
                else:
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

        # Draw all power-ups
        powerups_draw_all(state, state.arena)

        electric_walls = settings.get("electric_walls")

        snake_colors = settings.get_snake_colors()
        current_head_color = snake_colors["head"]
        current_tail_color = snake_colors["tail"]

        # Draw the tail with smooth interpolation
        for i, (tx, ty) in enumerate(state.snake.tail):
            draw_tx = tx
            draw_ty = ty

            if i == 0:
                prev_tx = state.snake.head.x
                prev_ty = state.snake.head.y
            else:
                prev_tx, prev_ty = state.snake.tail[i - 1]

            if state.snake.move_progress > 0.0:
                if not electric_walls and _will_wrap_around(
                    state, prev_tx, tx, state.snake.width
                ):
                    draw_tx = (
                        prev_tx
                        + state.snake.xmov * state.grid_size * state.snake.move_progress
                    )
                else:
                    draw_tx = prev_tx + (tx - prev_tx) * (
                        1.0 - state.snake.move_progress
                    )

                if not electric_walls and _will_wrap_around(
                    state, prev_ty, ty, state.snake.height
                ):
                    draw_ty = (
                        prev_ty
                        + state.snake.ymov * state.grid_size * state.snake.move_progress
                    )
                else:
                    draw_ty = prev_ty + (ty - prev_ty) * (
                        1.0 - state.snake.move_progress
                    )

            pygame.draw.rect(
                state.arena,
                current_tail_color,
                pygame.Rect(
                    round(draw_tx), round(draw_ty), state.grid_size, state.grid_size
                ),
            )

        # Draw head (use int coords for Rect)
        pygame.draw.rect(
            state.arena,
            current_head_color,
            pygame.Rect(
                round(state.snake.draw_x),
                round(state.snake.draw_y),
                state.grid_size,
                state.grid_size,
            ),
        )

        powerups_draw_overlay_on_head(state, state.arena)

        # Show score (snake length = head + tail)
        score = assets.render_big(f"{len(state.snake.tail)}", SCORE_COLOR)
        score.set_alpha(75)  # opacity
        score_rect = score.get_rect(center=(state.width / 2, state.height / 12))
        state.arena.blit(score, score_rect)

        # Draw the shield timer HUD (icon + remaining time) when invincibility is active
        powerups_draw_timer(state, state.arena, assets)

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

        # Check collision with power-ups + effects
        if state.game_on:
            # Check collision with power-ups + effects
            powerups_handle_collisions(state)

        if not state.game_on:
            draw_pause_screen(state, assets)

        if state.game_on:
            # Periodically attempt to spawn a shield if none exists (gameplay loop)
            powerups_try_periodic_spawn(
                state,
                interval_ms=POWERUP_SPAWN_INTERVAL_MS,
                chance=POWERUP_SPAWN_CHANCE,
            )

        # Update display
        pygame.display.update()


if __name__ == "__main__":
    main()
