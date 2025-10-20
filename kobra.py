#!/usr/bin/env python3
#
#   Copyright (c) 2023, Monaco F. J. <monaco@usp.br>
#
#   This file is part of KobraPy.
#
#   Kobrapy is free software: you can redistribute it and/or modify
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

"""Bootstrap entry point for Naja game.

This file serves as a thin bootstrap layer that initializes the core game loop
and delegates to the new ECS architecture while maintaining compatibility with
the old code during migration.
"""

import sys
import pygame
from old_code.entities import Snake, Apple, Obstacle
from old_code.constants import (
    DEAD_HEAD_COLOR,
    ARENA_COLOR,
    GRID_COLOR,
    SCORE_COLOR,
    MESSAGE_COLOR,
    WINDOW_TITLE,
)
from old_code.state import GameState
from old_code.assets import GameAssets
from old_code.config import GameConfig
from old_code.settings import GameSettings

# Import the new core game loop
from src.core.app import GameApp
from src.core.io.pygame_adapter import PygameIOAdapter

# Global pygame adapter instance
pygame_adapter = PygameIOAdapter()


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

    title = assets.render_custom("Settings", MESSAGE_COLOR, int(state.width / 12))
    title_rect = title.get_rect(center=(state.width / 2, state.height / 10))
    state.arena.blit(title, title_rect)

    # Spacing and scroll parameters - adjusted for smaller text
    row_h = int(state.height * 0.06)
    visible_rows = int(state.height * 0.70 // row_h)
    top_index = max(0, selected_index - visible_rows + 3)
    padding_y = int(state.height * 0.22)

    # Draw visible rows with smaller font
    for draw_i, field_i in enumerate(range(top_index, len(settings.MENU_FIELDS))):
        if draw_i >= visible_rows:
            break
        f = settings.MENU_FIELDS[field_i]
        val = settings.get(f["key"])
        formatted_val = settings.format_setting_value(
            f, val, state.width, state.grid_size
        )
        text = assets.render_custom(
            f"{f['label']}: {formatted_val}",
            SCORE_COLOR if field_i == selected_index else MESSAGE_COLOR,
            int(state.width / 30),
        )
        rect = text.get_rect()
        rect.left = int(state.width * 0.10)
        rect.top = padding_y + draw_i * row_h
        state.arena.blit(text, rect)

    # Hint footer (smaller)
    hint_text = "[A/D] change   [W/S] select   [Enter/Esc] back   [C] random colors"
    hint = assets.render_custom(hint_text, GRID_COLOR, int(state.width / 50))
    state.arena.blit(hint, hint.get_rect(center=(state.width / 2, state.height * 0.95)))

    pygame_adapter.update_display()


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

        for event in pygame_adapter.get_events():
            # Guard clauses keep nesting shallow.
            if event.type == pygame.QUIT:
                pygame_adapter.quit()
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
        state.arena = pygame_adapter.set_mode((new_width, new_height))
        pygame_adapter.set_caption(WINDOW_TITLE)

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

    pygame_adapter.update_display()


def _wait_for_keys(allowed_keys: set[int]) -> int:
    """Block until a KEYDOWN for one of allowed_keys (or quit). Return the key."""
    while True:
        event = pygame_adapter.wait_for_event()
        if event.type == pygame.QUIT:
            pygame_adapter.quit()
            sys.exit()
        if event.type == pygame.KEYDOWN and (
            not allowed_keys or event.key in allowed_keys
        ):
            return event.key


def _show_reset_warning_dialog(state: GameState, assets: GameAssets) -> str:
    """Show a warning dialog when critical settings changed.

    Returns:
        'reset' - User wants to reset now
        'cancel' - User wants to cancel changes
    """
    selected = 0
    options = ["Reset Now", "Cancel Changes"]

    while True:
        state.arena.fill(ARENA_COLOR)

        # Title - smaller size
        title = assets.render_custom("Warning", MESSAGE_COLOR, int(state.width / 15))
        title_rect = title.get_rect(center=(state.width / 2, state.height / 8))
        state.arena.blit(title, title_rect)

        # Message text (multi-line) - smaller font and better fit
        message_lines = [
            "The changes you made require",
            "a game reset to take effect.",
            "",
            "Reset the game now?",
            "If not, changes will be reverted.",
        ]

        y_offset = state.height / 3.2
        line_height = int(state.height * 0.05)
        for line in message_lines:
            if line:  # Skip empty lines for spacing
                msg_surf = assets.render_custom(
                    line, MESSAGE_COLOR, int(state.width / 30)
                )
            else:
                msg_surf = assets.render_custom(
                    " ", MESSAGE_COLOR, int(state.width / 30)
                )
            msg_rect = msg_surf.get_rect(center=(state.width / 2, y_offset))
            state.arena.blit(msg_surf, msg_rect)
            y_offset += line_height

        # Draw option buttons - smaller font
        button_y_start = state.height / 1.65
        for i, option in enumerate(options):
            color = SCORE_COLOR if i == selected else MESSAGE_COLOR
            option_surf = assets.render_custom(option, color, int(state.width / 25))
            option_rect = option_surf.get_rect(
                center=(state.width / 2, button_y_start + i * (state.height * 0.09))
            )
            state.arena.blit(option_surf, option_rect)

        # Hint - smaller
        hint = assets.render_custom(
            "[W/S] select   [Enter] confirm", GRID_COLOR, int(state.width / 50)
        )
        state.arena.blit(
            hint, hint.get_rect(center=(state.width / 2, state.height * 0.92))
        )

        pygame_adapter.update_display()

        # Input handling
        for event in pygame_adapter.get_events():
            if event.type == pygame.QUIT:
                pygame_adapter.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                key = event.key

                if key in (pygame.K_UP, pygame.K_w):
                    selected = (selected - 1) % len(options)
                elif key in (pygame.K_DOWN, pygame.K_s):
                    selected = (selected + 1) % len(options)
                elif key in (pygame.K_RETURN, pygame.K_SPACE):
                    if options[selected] == "Reset Now":
                        return "reset"
                    else:  # Cancel Changes
                        return "cancel"
                elif key == pygame.K_ESCAPE:
                    return "cancel"


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
    pygame_adapter.draw_rect(state.arena, DEAD_HEAD_COLOR, state.snake.head)
    pygame_adapter.update_display()
    # Game-over prompt: only Space/Enter restart; Q quits.
    _draw_center_message(
        state, assets, "Game Over", "Press Enter/Space to restart  •  Q to exit"
    )
    key = _wait_for_keys({pygame.K_RETURN, pygame.K_SPACE, pygame.K_q})

    # Switch back to background music (if music is enabled)
    if settings.get("background_music"):
        GameAssets.play_background_music()

    if key == pygame.K_q:
        pygame_adapter.quit()
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

        pygame_adapter.update_display()

        # Input handling
        for event in pygame_adapter.get_events():
            if event.type == pygame.QUIT:
                pygame_adapter.quit()
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
                    pygame_adapter.quit()
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
            rect = pygame_adapter.create_rect(x, y, state.grid_size, state.grid_size)
            pygame_adapter.draw_rect(state.arena, GRID_COLOR, rect, 1)


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
    overlay = pygame_adapter.create_surface(
        (state.width, state.height), pygame.SRCALPHA
    )
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
    """Main game entry point with proper initialization.

    This function now serves as a thin bootstrap layer that delegates
    to the new ECS-based core game loop while maintaining compatibility
    with the old code during migration.
    """
    # Create and initialize the game application
    app = GameApp()
    app.initialize()

    # Run the game
    app.run()


if __name__ == "__main__":
    main()
