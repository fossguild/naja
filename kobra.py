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

import sys
import random
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

# Get the current display's resolution from the system.
display_info = pygame.display.Info()
user_screen_width = display_info.current_w
user_screen_height = display_info.current_h

# Determine the largest possible square size that fits safely on the screen.
safe_max_dimension = int(min(user_screen_width, user_screen_height) * 0.9)

# Define the size of each cell in the game's grid.
GRID_SIZE = 50

# Calculate the final window dimension.
WIDTH = HEIGHT = (safe_max_dimension // GRID_SIZE) * GRID_SIZE

HEAD_COLOR = "#00aa00"  # Color of the snake's head.
DEAD_HEAD_COLOR = "#4b0082"  # Color of the dead snake's head.
TAIL_COLOR = "#00ff00"  # Color of the snake's tail.
APPLE_COLOR = "#aa0000"  # Color of the apple.
OBSTACLE_COLOR = "#666666"  # Color of the obstacles.
ARENA_COLOR = "#202020"  # Color of the ground.
GRID_COLOR = "#3c3c3b"  # Color of the grid lines.
SCORE_COLOR = "#ffffff"  # Color of the scoreboard.
MESSAGE_COLOR = "#808080"  # Color of the game-over message.

WINDOW_TITLE = "KobraPy"  # Window title.

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
def _draw_settings_menu(selected_index: int) -> None:
    arena.fill(ARENA_COLOR)

    title_font = pygame.font.Font("assets/font/GetVoIP-Grotesque.ttf", int(WIDTH / 10))
    title = title_font.render("Settings", True, MESSAGE_COLOR)
    title_rect = title.get_rect(center=(WIDTH / 2, HEIGHT / 10))
    arena.blit(title, title_rect)

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
        arena.blit(text, rect)

    # hint footer (smaller)
    hint_font = pygame.font.Font("assets/font/GetVoIP-Grotesque.ttf", int(WIDTH / 40))
    hint_text = "[A/D] change   [W/S] select   [Enter/Esc] back"
    hint = hint_font.render(hint_text, True, GRID_COLOR)
    arena.blit(hint, hint.get_rect(center=(WIDTH / 2, HEIGHT * 0.95)))

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
def run_settings_menu() -> None:
    selected = 0

    while True:
        _draw_settings_menu(selected)

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
def apply_settings(reset_objects: bool = False) -> None:
    global GRID_SIZE, WIDTH, HEIGHT, arena, BIG_FONT, SMALL_FONT
    global CLOCK_TICKS, MAX_SPEED, DEATH_SOUND_ON, NUM_OBSTACLES, MUSIC_ON

    old_grid = GRID_SIZE

    # GRID_SIZE = int(SETTINGS["grid_size"])

    # Derive cell size from desired cells per side
    desired_cells = max(10, int(SETTINGS["cells_per_side"]))
    # Size each cell so that desired_cells fit within the safe dimension.
    GRID_SIZE = max(8, safe_max_dimension // desired_cells)

    CLOCK_TICKS = float(SETTINGS["initial_speed"])
    MAX_SPEED = float(SETTINGS["max_speed"])
    DEATH_SOUND_ON = bool(SETTINGS["death_sound"])
    NUM_OBSTACLES = Obstacle.calculate_obstacles_from_difficulty(
        SETTINGS["obstacle_difficulty"],WIDTH,GRID_SIZE,HEIGHT
    )
    MUSIC_ON = bool(SETTINGS["background_music"])

    # Control background music playback based on setting
    if MUSIC_ON:
        pygame.mixer.music.unpause()
    else:
        pygame.mixer.music.pause()

    # Recompute window and recreate surface/fonts if grid changed.
    if GRID_SIZE != old_grid:
        new_dim = (safe_max_dimension // GRID_SIZE) * GRID_SIZE
        WIDTH = HEIGHT = new_dim
        arena = pygame.display.set_mode((WIDTH, HEIGHT), pygame.SCALED, vsync=1)
        BIG_FONT = pygame.font.Font("assets/font/GetVoIP-Grotesque.ttf", int(WIDTH / 8))
        SMALL_FONT = pygame.font.Font(
            "assets/font/GetVoIP-Grotesque.ttf", int(WIDTH / 20)
        )
        pygame.display.set_caption(WINDOW_TITLE)

    # Optionally recreate moving objects to reflect new geometry/speed.
    if reset_objects:
        try:
            globals()["snake"] = Snake(WIDTH, HEIGHT, GRID_SIZE)
            globals()["obstacles"] = create_obstacles_constructively(
                NUM_OBSTACLES, snake.x, snake.y
            )
            globals()["apple"] = Apple(WIDTH, HEIGHT, GRID_SIZE)
            snake.speed = CLOCK_TICKS
            apple.move_away_from_snake(snake) #ensure apple is not on snake
        except NameError:
            # If called before classes/instances exist, ignore.
            pass


clock = pygame.time.Clock()

# Load gameover sound
gameover_sound = pygame.mixer.Sound("assets/sound/gameover.wav")

# Load speaker sprites
try:
    speaker_on_sprite = pygame.image.load("assets/sprites/speaker-on.png")
    speaker_muted_sprite = pygame.image.load("assets/sprites/speaker-muted.png")
except pygame.error as e:
    print(f"Warning: Could not load speaker sprites: {e}")
    speaker_on_sprite = None
    speaker_muted_sprite = None

arena = pygame.display.set_mode((WIDTH, HEIGHT), pygame.SCALED, vsync=1)


# BIG_FONT   = pygame.font.Font("assets/font/Ramasuri.ttf", int(WIDTH/8))
# SMALL_FONT = pygame.font.Font("assets/font/Ramasuri.ttf", int(WIDTH/20))

BIG_FONT = pygame.font.Font("assets/font/GetVoIP-Grotesque.ttf", int(WIDTH / 8))
SMALL_FONT = pygame.font.Font("assets/font/GetVoIP-Grotesque.ttf", int(WIDTH / 20))


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


def _draw_center_message(title: str, subtitle: str) -> None:
    arena.fill(ARENA_COLOR)

    # Title ~ up to 80% of window width, start from BIG font size.
    title_surf = _render_text_fit(
        title, MESSAGE_COLOR, max_width_ratio=0.8, base_px=int(WIDTH / 8)
    )
    arena.blit(title_surf, title_surf.get_rect(center=(WIDTH / 2, HEIGHT / 2.6)))

    # Subtitle ~ up to 90% of width, start from SMALL font size.
    sub_surf = _render_text_fit(
        subtitle, MESSAGE_COLOR, max_width_ratio=0.9, base_px=int(WIDTH / 20)
    )
    arena.blit(sub_surf, sub_surf.get_rect(center=(WIDTH / 2, HEIGHT / 1.8)))

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


def game_over_handler() -> None:
    # Tell the bad news
    pygame.draw.rect(arena, DEAD_HEAD_COLOR, snake.head)
    pygame.display.update()
    ## Game-over prompt: only Space/Enter restart; Q quits.
    _draw_center_message("Game Over", "Press Enter/Space to restart  •  Q to exit")
    key = _wait_for_keys({pygame.K_RETURN, pygame.K_SPACE, pygame.K_q})
    if key == pygame.K_q:
        pygame.quit()
        sys.exit()


##
## Apply default settings once
##
apply_settings(reset_objects=False)

pygame.display.set_caption(WINDOW_TITLE)

game_on = 1


##
## Start menu (Start / Settings)
##
def start_menu():
    """Main menu shown before the game starts."""
    selected = 0
    items = ["Start Game", "Settings"]

    while True:
        arena.fill(ARENA_COLOR)

        # title
        title = BIG_FONT.render(WINDOW_TITLE, True, MESSAGE_COLOR)
        arena.blit(title, title.get_rect(center=(WIDTH / 2, HEIGHT / 4)))

        # draw buttons
        for i, text_label in enumerate(items):
            color = SCORE_COLOR if i == selected else MESSAGE_COLOR
            text = SMALL_FONT.render(text_label, True, color)
            rect = text.get_rect(center=(WIDTH / 2, HEIGHT / 2 + i * (HEIGHT * 0.12)))
            arena.blit(text, rect)

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
                        run_settings_menu()
                        apply_settings(reset_objects=False)
                elif key == pygame.K_m:
                    run_settings_menu()
                    apply_settings(reset_objects=False)
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
                            run_settings_menu()
                            apply_settings(reset_objects=False)


##
## Draw the arena
##


def draw_grid():
    for x in range(0, WIDTH, GRID_SIZE):
        for y in range(0, HEIGHT, GRID_SIZE):
            rect = pygame.Rect(x, y, GRID_SIZE, GRID_SIZE)
            pygame.draw.rect(arena, GRID_COLOR, rect, 1)


##
## Draws the icon representing whether the background music is on or off
##


def draw_music_indicator():
    """Draw a subtle music status indicator in the bottom-right corner."""
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
        arena.blit(scaled_sprite, (icon_x, icon_y))

    # Add [N] text hint below the icon
    hint_font = pygame.font.Font("assets/font/GetVoIP-Grotesque.ttf", int(WIDTH / 50))
    hint_color = SCORE_COLOR if MUSIC_ON else GRID_COLOR
    hint_text = "[N]"
    hint_surf = hint_font.render(hint_text, True, hint_color)
    hint_rect = hint_surf.get_rect()
    hint_rect.centerx = icon_x + icon_size // 2
    hint_rect.top = icon_y + icon_size + 2

    arena.blit(hint_surf, hint_rect)


##
## Start flow
##
start_menu()  # blocks until user picks "Start Game"
snake = Snake(WIDTH, HEIGHT, GRID_SIZE)  # create with the final, chosen GRID_SIZE
obstacles = create_obstacles_constructively(
    NUM_OBSTACLES, snake.x, snake.y
)  # create obstacles
apple = Apple(WIDTH, HEIGHT, GRID_SIZE)
apple.move_away_from_snake(snake)

##
## Main loop
##

while True:
    dt = clock.tick_busy_loop(0)
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
                and snake.ymov != -1
            ):
                snake.ymov = 1
                snake.xmov = 0
            # Up arrow (or W): move up
            elif event.key in (pygame.K_UP, pygame.K_w) and snake.ymov != 1:
                snake.ymov = -1
                snake.xmov = 0
            # Right arrow (or D): move right
            elif event.key in (pygame.K_RIGHT, pygame.K_d) and snake.xmov != -1:
                snake.ymov = 0
                snake.xmov = 1
            # Left arrow (or A): move left
            elif event.key in (pygame.K_LEFT, pygame.K_a) and snake.xmov != 1:
                snake.ymov = 0
                snake.xmov = -1
            # Q : quit game
            elif event.key == pygame.K_q:
                pygame.quit()
                sys.exit()
            elif event.key == pygame.K_p:  # P         : pause game
                game_on = not game_on
            elif event.key in (pygame.K_m, pygame.K_ESCAPE):  # M or ESC : open menu
                was_running = game_on
                game_on = 0
                run_settings_menu()
                apply_settings(reset_objects=True)
                game_on = was_running
            elif event.key == pygame.K_n:  # N : toggle music mute
                SETTINGS["background_music"] = not SETTINGS["background_music"]
                apply_settings(reset_objects=False)
    ## Update the game
 
    died = False
    if game_on:
        # If we're not currently interpolating between grid cells and a movement
        # direction is set, schedule the next grid move by calling snake.update().
        if snake.target_x == snake.head.x and snake.target_y == snake.head.y:
            if snake.xmov or snake.ymov:
                died = snake.update(apple,obstacles,game_over_handler)
        
        # Play death sound if snake died
        if died and DEATH_SOUND_ON:
            gameover_sound.play()

        # Advance interpolation toward the current target grid cell (if any)
        if snake.target_x != snake.head.x or snake.target_y != snake.head.y:
            move_interval_ms = 1000.0 / snake.speed
            snake.move_progress += dt / move_interval_ms
            if snake.move_progress > 1.0:
                snake.move_progress = 1.0
            snake.draw_x = (
                snake.head.x + (snake.target_x - snake.head.x) * snake.move_progress
            )
            snake.draw_y = (
                snake.head.y + (snake.target_y - snake.head.y) * snake.move_progress
            )
            if snake.move_progress >= 1.0:
                # Move completed: remember previous head position
                prev_x = snake.head.x
                prev_y = snake.head.y

                # Snap head to target grid cell
                snake.head.x = snake.target_x
                snake.head.y = snake.target_y
                snake.x = snake.head.x
                snake.y = snake.head.y

                # Insert previous head position into tail (store as (x,y) tuple)
                snake.tail.insert(0, (prev_x, prev_y))
                if snake.got_apple:
                    snake.got_apple = False
                else:
                    # Only pop when we didn't just eat an apple
                    if snake.tail:
                        snake.tail.pop()

                # Reset progress and ensure draw coords are exact integers
                snake.move_progress = 0.0
                snake.draw_x = float(snake.head.x)
                snake.draw_y = float(snake.head.y)
                snake.prev_head_x = snake.head.x
                snake.prev_head_y = snake.head.y
        else:
            # No pending move: keep draw coordinates synced to head
            snake.move_progress = 0.0
            snake.draw_x = float(snake.head.x)
            snake.draw_y = float(snake.head.y)

        arena.fill(ARENA_COLOR)
        draw_grid()

        # Draw obstacles
        for obstacle in obstacles:
            obstacle.update()

        apple.update(arena)

    # Draw the tail with smooth interpolation
    for i, (tx, ty) in enumerate(snake.tail):
        draw_tx = tx
        draw_ty = ty

        if i == 0 and snake.move_progress > 0.0:
            draw_tx = snake.head.x + (tx - snake.head.x) * (1.0 - snake.move_progress)
            draw_ty = snake.head.y + (ty - snake.head.y) * (1.0 - snake.move_progress)
        elif i > 0 and snake.move_progress > 0.0:
            prev_tx, prev_ty = snake.tail[i - 1]
            draw_tx = prev_tx + (tx - prev_tx) * (1.0 - snake.move_progress)
            draw_ty = prev_ty + (ty - prev_ty) * (1.0 - snake.move_progress)

        pygame.draw.rect(
            arena,
            TAIL_COLOR,
            pygame.Rect(round(draw_tx), round(draw_ty), GRID_SIZE, GRID_SIZE),
        )

    # Draw head (use int coords for Rect)
    pygame.draw.rect(
        arena,
        HEAD_COLOR,
        pygame.Rect(round(snake.draw_x), round(snake.draw_y), GRID_SIZE, GRID_SIZE),
    )

    # Show score (snake length = head + tail)
    score = BIG_FONT.render(f"{len(snake.tail)}", True, SCORE_COLOR)
    score_rect = score.get_rect(center=(WIDTH / 2, HEIGHT / 12))
    arena.blit(score, score_rect)

    # Draw music status indicator
    draw_music_indicator()

    # If the head pass over an apple, lengthen the snake and drop another apple
    if snake.head.x == apple.x and snake.head.y == apple.y:
        # snake.tail.append(pygame.Rect(snake.head.x, snake.head.y, GRID_SIZE, GRID_SIZE))
        snake.got_apple = True
        snake.speed = min(snake.speed * 1.1, MAX_SPEED)  # Increase speed
        # print(f"[APPLE] Speed increased to: {snake.speed:.2f}")
        apple = Apple(WIDTH, HEIGHT, GRID_SIZE)
        apple.ensure_valid_position(snake, obstacles)

    # Update display and move clock.
    pygame.display.update()
