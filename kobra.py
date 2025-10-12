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
from entities import Snake, Apple, Obstacle
from constants import (
    HEAD_COLOR,
    DEAD_HEAD_COLOR,
    TAIL_COLOR,
    ARENA_COLOR,
    GRID_COLOR,
    SCORE_COLOR,
    MESSAGE_COLOR,
    WINDOW_TITLE,
)
from state import GameState

##
## Game customization.
##

# Initialize Pygame to access display info.
# Allows to detect the screen size before creating the main window.
pygame.init()

# Inicializa o mixer de áudio
pygame.mixer.init()

# Carrega e toca a música de fundo (loop infinito)
pygame.mixer.music.load("assets/sound/BoxCat_Games_CPU_Talk.ogg")
pygame.mixer.music.set_volume(0.2)  # volume de 0.0 a 1.0
pygame.mixer.music.play(-1)  # -1 significa repetir para sempre


# Load speaker sprites
try:
    speaker_on_sprite = pygame.image.load("assets/sprites/speaker-on.png")
    speaker_muted_sprite = pygame.image.load("assets/sprites/speaker-muted.png")
except pygame.error as e:
    print(f"Warning: Could not load speaker sprites: {e}")
    speaker_on_sprite = None
    speaker_muted_sprite = None

# Load gameover sound
gameover_sound = pygame.mixer.Sound("assets/sound/gameover.wav")

# Get the current display's resolution from the system.
DISPLAY_INFO = pygame.display.Info()
USER_SCREEN_WIDTH = DISPLAY_INFO.current_w
USER_SCREEN_HEIGHT = DISPLAY_INFO.current_h

# Determine the largest possible square size that fits safely on the screen.
SAFE_MAX_DIMENSION = int(min(USER_SCREEN_WIDTH, USER_SCREEN_HEIGHT) * 0.9)

# Define the size of each cell in the game's grid.
GRID_SIZE = 50

# Calculate the final window dimension.
WIDTH = HEIGHT = (SAFE_MAX_DIMENSION // GRID_SIZE) * GRID_SIZE

CLOCK_TICKS = 4  # How fast the snake moves.

##
## Settings and menu helpers
##

# Central settings used by the menu;
SETTINGS = {
    "cells_per_side": WIDTH // GRID_SIZE,
    "initial_speed": 4.0,  # current CLOCK_TICKS
    "max_speed": 20.0,  # current speed clamp at apple pickup
    "death_sound": True,  # toggle death sound playback
    "obstacle_difficulty": "None",  # obstacle difficulty level
    "background_music": True,  # toggle background music playback
}

# Declarative menu fields.
MENU_FIELDS = [
    {
        "key": "cells_per_side",
        "label": "Cells per side",
        "type": "int",
        "min": 10,
        "max": 60,
        "step": 1,
    },
    {
        "key": "initial_speed",
        "label": "Initial speed",
        "type": "float",
        "min": 1.0,
        "max": 40.0,
        "step": 0.5,
    },
    {
        "key": "max_speed",
        "label": "Max speed",
        "type": "float",
        "min": 4.0,
        "max": 60.0,
        "step": 1.0,
    },
    {"key": "death_sound", "label": "Death Sound", "type": "bool"},
    {
        "key": "obstacle_difficulty",
        "label": "Obstacles",
        "type": "select",
        "options": ["None", "Easy", "Medium", "Hard", "Impossible"],
    },
    {"key": "background_music", "label": "Background Music", "type": "bool"},
]

# Effective runtime values (hydrated by apply_settings).
MAX_SPEED = SETTINGS["max_speed"]
DEATH_SOUND_ON = SETTINGS["death_sound"]
NUM_OBSTACLES = 0  # Will be calculated in apply_settings
MUSIC_ON = SETTINGS["background_music"]

# BIG_FONT   = pygame.font.Font("assets/font/Ramasuri.ttf", int(WIDTH/8))
# SMALL_FONT = pygame.font.Font("assets/font/Ramasuri.ttf", int(WIDTH/20))

BIG_FONT = pygame.font.Font("assets/font/GetVoIP-Grotesque.ttf", int(WIDTH / 8))
SMALL_FONT = pygame.font.Font("assets/font/GetVoIP-Grotesque.ttf", int(WIDTH / 20))


def _clamp(v, lo, hi):
    return max(lo, min(hi, v))


## Format a setting value for display.
def _fmt_setting_value(field, value):
    if field["key"] == "cells_per_side":
        requested = int(value)
        actual = WIDTH // GRID_SIZE
        return (
            f"{requested} × {requested}"
            if requested == actual
            else f"{requested} × {requested} (cur: {actual})"
        )
    elif field["key"] == "obstacle_difficulty":
        # Show difficulty with obstacle count
        return f"{value}"
    elif isinstance(value, bool):
        return "On" if value else "Off"
    elif isinstance(value, float):
        return f"{value:.1f}"
    return str(value)


## Draw the entire settings screen (scrollable if needed).
def _draw_settings_menu(state, selected_index: int) -> None:
    state.arena.fill(ARENA_COLOR)

    title_font = pygame.font.Font("assets/font/GetVoIP-Grotesque.ttf", int(WIDTH / 10))
    title = title_font.render("Settings", True, MESSAGE_COLOR)
    title_rect = title.get_rect(center=(WIDTH / 2, HEIGHT / 10))
    state.arena.blit(title, title_rect)

    # spacing and scroll parameters
    visible_rows = int(HEIGHT * 0.75 // (HEIGHT * 0.07))
    top_index = max(0, selected_index - visible_rows + 3)
    padding_y = int(HEIGHT * 0.20)
    row_h = int(HEIGHT * 0.07)

    # draw visible rows
    for draw_i, field_i in enumerate(range(top_index, len(MENU_FIELDS))):
        if draw_i >= visible_rows:
            break
        f = MENU_FIELDS[field_i]
        val = SETTINGS[f["key"]]
        text = SMALL_FONT.render(
            f"{f['label']}: {_fmt_setting_value(f, val)}",
            True,
            SCORE_COLOR if field_i == selected_index else MESSAGE_COLOR,
        )
        rect = text.get_rect()
        rect.left = int(WIDTH * 0.12)
        rect.top = padding_y + draw_i * row_h
        state.arena.blit(text, rect)

    # hint footer (smaller)
    hint_font = pygame.font.Font("assets/font/GetVoIP-Grotesque.ttf", int(WIDTH / 40))
    hint_text = "[A/D] change   [W/S] select   [Enter/Esc] back"
    hint = hint_font.render(hint_text, True, GRID_COLOR)
    state.arena.blit(hint, hint.get_rect(center=(WIDTH / 2, HEIGHT * 0.95)))

    pygame.display.update()


## Change a single setting by one step (direction −1 or +1).
def _step_setting(field: dict, direction: int) -> None:
    key = field["key"]
    kind = field["type"]

    if kind == "bool":
        SETTINGS[key] = not SETTINGS[key]
        return

    elif kind == "select":
        options = field["options"]
        current_index = options.index(SETTINGS[key])
        new_index = (current_index + direction) % len(options)
        SETTINGS[key] = options[new_index]
        return

    step = field.get("step", 1 if kind == "int" else 1.0)
    new_val = SETTINGS[key] + (direction * step)

    lo = field.get("min", new_val)
    hi = field.get("max", new_val)

    if kind == "int":
        SETTINGS[key] = int(_clamp(new_val, lo, hi))
    else:  # float
        SETTINGS[key] = float(_clamp(new_val, lo, hi))


## Modal loop for the Settings screen.
def run_settings_menu(state) -> None:
    selected = 0

    while True:
        _draw_settings_menu(state, selected)

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
                selected = (selected + 1) % len(MENU_FIELDS)
                continue

            if key in (pygame.K_UP, pygame.K_w):
                selected = (selected - 1) % len(MENU_FIELDS)
                continue

            if key in (pygame.K_LEFT, pygame.K_a):
                _step_setting(MENU_FIELDS[selected], -1)
                continue

            if key in (pygame.K_RIGHT, pygame.K_d):
                _step_setting(MENU_FIELDS[selected], +1)
                continue


## Apply SETTINGS to globals; resize surface/fonts if grid size changed.
def apply_settings(state: GameState, reset_objects: bool = False) -> None:
    global GRID_SIZE, WIDTH, HEIGHT, BIG_FONT, SMALL_FONT
    global CLOCK_TICKS, MAX_SPEED, DEATH_SOUND_ON, NUM_OBSTACLES, MUSIC_ON

    old_grid = GRID_SIZE

    # Derive cell size from desired cells per side
    desired_cells = max(10, int(SETTINGS["cells_per_side"]))
    # Size each cell so that desired_cells fit within the safe dimension.
    GRID_SIZE = max(8, SAFE_MAX_DIMENSION // desired_cells)

    CLOCK_TICKS = float(SETTINGS["initial_speed"])
    MAX_SPEED = float(SETTINGS["max_speed"])
    DEATH_SOUND_ON = bool(SETTINGS["death_sound"])
    NUM_OBSTACLES = Obstacle.calculate_obstacles_from_difficulty(
        SETTINGS["obstacle_difficulty"], WIDTH, GRID_SIZE, HEIGHT
    )
    MUSIC_ON = bool(SETTINGS["background_music"])

    # Control background music playback based on setting
    if MUSIC_ON:
        pygame.mixer.music.unpause()
    else:
        pygame.mixer.music.pause()

    # Recompute window and recreate surface/fonts if grid changed.
    if GRID_SIZE != old_grid:
        new_dim = (SAFE_MAX_DIMENSION // GRID_SIZE) * GRID_SIZE
        WIDTH = HEIGHT = new_dim
        state.arena = pygame.display.set_mode((WIDTH, HEIGHT), pygame.SCALED, vsync=1)
        pygame.display.set_caption(WINDOW_TITLE)

        # Update state's dimensions to match new grid size
        state.update_dimensions(WIDTH, HEIGHT, GRID_SIZE)

        # Reload fonts globally with new width
        global BIG_FONT, SMALL_FONT
        BIG_FONT = pygame.font.Font("assets/font/GetVoIP-Grotesque.ttf", int(WIDTH / 8))
        SMALL_FONT = pygame.font.Font(
            "assets/font/GetVoIP-Grotesque.ttf", int(WIDTH / 20)
        )

        # Force reset_objects when grid size changes to prevent misalignment
        reset_objects = True

    # Recreate moving objects to reflect new geometry/speed.
    if reset_objects:
        # Objects will be recreated in the game state
        state.snake = Snake(WIDTH, HEIGHT, GRID_SIZE)
        state.create_obstacles_constructively(NUM_OBSTACLES)
        state.apple = Apple(WIDTH, HEIGHT, GRID_SIZE)
        state.snake.speed = CLOCK_TICKS
        state.apple.ensure_valid_position(state.snake)  # ensure apple is not on snake


##
## Center message + simple key wait helpers
##


## Text fitting helper (keeps long lines inside the window)
def _render_text_fit(text: str, color, max_width_ratio: float, base_px: int):
    """
    Render text using the game's font, shrinking until it fits the given width ratio.
    max_width_ratio: fraction of WIDTH allowed.
    base_px: starting font size in pixels.
    """
    px = base_px
    while px > 8:  # don't go too tiny
        font = pygame.font.Font("assets/font/GetVoIP-Grotesque.ttf", px)
        surf = font.render(text, True, color)
        if surf.get_width() <= WIDTH * max_width_ratio:
            return surf
        px -= 2
    return surf  # last attempt even if it doesn't fit perfectly


def _draw_center_message(state: GameState, title: str, subtitle: str) -> None:
    state.arena.fill(ARENA_COLOR)

    # Title ~ up to 80% of window width, start from BIG font size.
    title_surf = _render_text_fit(
        title, MESSAGE_COLOR, max_width_ratio=0.8, base_px=int(WIDTH / 8)
    )
    state.arena.blit(title_surf, title_surf.get_rect(center=(WIDTH / 2, HEIGHT / 2.6)))

    # Subtitle ~ up to 90% of width, start from SMALL font size.
    sub_surf = _render_text_fit(
        subtitle, MESSAGE_COLOR, max_width_ratio=0.9, base_px=int(WIDTH / 20)
    )
    state.arena.blit(sub_surf, sub_surf.get_rect(center=(WIDTH / 2, HEIGHT / 1.8)))

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


def game_over_handler(state: GameState) -> None:
    """Handle game over scenario with visual feedback and prompt.

    Args:
        state: GameState instance
    """
    # Tell the bad news
    pygame.draw.rect(state.arena, DEAD_HEAD_COLOR, state.snake.head)
    pygame.display.update()
    # Game-over prompt: only Space/Enter restart; Q quits.
    _draw_center_message(
        state, "Game Over", "Press Enter/Space to restart  •  Q to exit"
    )
    key = _wait_for_keys({pygame.K_RETURN, pygame.K_SPACE, pygame.K_q})
    if key == pygame.K_q:
        pygame.quit()
        sys.exit()


##
## Start menu (Start / Settings)
##
def start_menu(state: GameState):
    """Main menu shown before the game starts.

    Args:
        state: GameState instance (required)
    """
    selected = 0
    items = ["Start Game", "Settings"]

    while True:
        state.arena.fill(ARENA_COLOR)

        # title
        title = BIG_FONT.render(WINDOW_TITLE, True, MESSAGE_COLOR)
        state.arena.blit(title, title.get_rect(center=(WIDTH / 2, HEIGHT / 4)))

        # draw buttons
        for i, text_label in enumerate(items):
            color = SCORE_COLOR if i == selected else MESSAGE_COLOR
            text = SMALL_FONT.render(text_label, True, color)
            rect = text.get_rect(center=(WIDTH / 2, HEIGHT / 2 + i * (HEIGHT * 0.12)))
            state.arena.blit(text, rect)

        pygame.display.update()

        # input handling
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
                        run_settings_menu(state)
                        apply_settings(state, reset_objects=False)
                elif key == pygame.K_m:
                    run_settings_menu(state)
                    apply_settings(state, reset_objects=False)
                elif key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # simple click detection
                mx, my = event.pos
                for i, text_label in enumerate(items):
                    rect = SMALL_FONT.render(text_label, True, MESSAGE_COLOR).get_rect(
                        center=(WIDTH / 2, HEIGHT / 2 + i * (HEIGHT * 0.12))
                    )
                    if rect.collidepoint(mx, my):
                        if text_label == "Start Game":
                            return
                        elif text_label == "Settings":
                            run_settings_menu(state)
                            apply_settings(state, reset_objects=False)


##
## Draw the arena
##


def draw_grid(state: GameState):
    for x in range(0, WIDTH, GRID_SIZE):
        for y in range(0, HEIGHT, GRID_SIZE):
            rect = pygame.Rect(x, y, GRID_SIZE, GRID_SIZE)
            pygame.draw.rect(state.arena, GRID_COLOR, rect, 1)


##
## Draws the icon representing whether the background music is on or off
##


def draw_music_indicator(state: GameState):
    """Draw a subtle music status indicator in the bottom-right corner.

    Args:
        state: GameState instance (required)
    """
    # Calculate position in bottom-right corner
    padding = int(WIDTH * 0.02)
    icon_size = int(WIDTH / 25)  # Icon size for scaling
    icon_x = WIDTH - padding - icon_size
    icon_y = HEIGHT - padding - icon_size

    # Choose the appropriate sprite based on music state
    sprite = speaker_on_sprite if MUSIC_ON else speaker_muted_sprite

    # Scale and draw the sprite
    if sprite is not None:
        scaled_sprite = pygame.transform.scale(sprite, (icon_size, icon_size))
        state.arena.blit(scaled_sprite, (icon_x, icon_y))

    # Add [N] text hint below the icon
    hint_font = pygame.font.Font("assets/font/GetVoIP-Grotesque.ttf", int(WIDTH / 50))
    hint_color = SCORE_COLOR if MUSIC_ON else GRID_COLOR
    hint_text = "[N]"
    hint_surf = hint_font.render(hint_text, True, hint_color)
    hint_rect = hint_surf.get_rect()
    hint_rect.centerx = icon_x + icon_size // 2
    hint_rect.top = icon_y + icon_size + 2

    state.arena.blit(hint_surf, hint_rect)


##
## Main game function
##
def main():
    """Main game entry point with GameState initialization."""
    # Initialize game state
    state = GameState(WIDTH, HEIGHT, GRID_SIZE)

    # Apply default settings with state
    apply_settings(state, reset_objects=False)

    # we only have NUM_OBSTACLES set after applyng settings
    state.create_obstacles_constructively(NUM_OBSTACLES)
    pygame.display.set_caption(WINDOW_TITLE)

    ##
    ## Start flow
    ##
    start_menu(state)  # blocks until user picks "Start Game"

    ##
    ## Main loop
    ##
    while True:
        died = False
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
                elif event.key == pygame.K_p:  # P         : pause game
                    state.game_on = not state.game_on
                elif event.key in (pygame.K_m, pygame.K_ESCAPE):  # M or ESC : open menu
                    was_running = state.game_on
                    state.game_on = 0
                    run_settings_menu(state)
                    apply_settings(state, reset_objects=True)
                    state.game_on = was_running
                elif event.key == pygame.K_n:  # N : toggle music mute
                    SETTINGS["background_music"] = not SETTINGS["background_music"]
                    apply_settings(state, reset_objects=False)

        ## Update the game
        if state.game_on:
            # Only update snake position when it has reached its current target
            if (
                state.snake.target_x == state.snake.head.x
                and state.snake.target_y == state.snake.head.y
            ):
                if state.snake.xmov or state.snake.ymov:
                    died = state.snake.update(
                        state.apple, state.obstacles, lambda: game_over_handler(state)
                    )

                    # Play death sound if snake died
            if died and DEATH_SOUND_ON:
                gameover_sound.play()

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

        state.apple.update(state.arena)

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
                pygame.Rect(round(draw_tx), round(draw_ty), GRID_SIZE, GRID_SIZE),
            )

        # Draw head (use int coords for Rect)
        pygame.draw.rect(
            state.arena,
            HEAD_COLOR,
            pygame.Rect(
                round(state.snake.draw_x),
                round(state.snake.draw_y),
                GRID_SIZE,
                GRID_SIZE,
            ),
        )

        # Show score (snake length = head + tail)
        score = BIG_FONT.render(f"{len(state.snake.tail)}", True, SCORE_COLOR)
        score_rect = score.get_rect(center=(WIDTH / 2, HEIGHT / 12))
        state.arena.blit(score, score_rect)

        # Draw music status indicator
        draw_music_indicator(state)

        # If the head pass over an apple, lengthen the snake and drop another apple
        if state.snake.head.x == state.apple.x and state.snake.head.y == state.apple.y:
            state.snake.got_apple = True
            state.snake.speed = min(
                state.snake.speed * 1.1, MAX_SPEED
            )  # Increase speed
            state.apple.ensure_valid_position(state.snake, state.obstacles)

        # Update display
        pygame.display.update()


if __name__ == "__main__":
    main()
