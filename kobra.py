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

##
## Game customization.
##

# Initialize Pygame to access display info.
# Allows to detect the screen size before creating the main window.
pygame.init()

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
ARENA_COLOR = "#202020"  # Color of the ground.
GRID_COLOR = "#3c3c3b"  # Color of the grid lines.
SCORE_COLOR = "#ffffff"  # Color of the scoreboard.
MESSAGE_COLOR = "#808080"  # Color of the game-over message.

WINDOW_TITLE = "KobraPy"  # Window title.

CLOCK_TICKS = 4  # How fast the snake moves.

##
## Settings (existing features only) and menu helpers
##

# Central settings used by the menu; only existing features here.
SETTINGS = {
    "grid_size": 50,  # current GRID_SIZE
    "initial_speed": 4.0,  # current CLOCK_TICKS
    "max_speed": 20.0,  # current speed clamp at apple pickup
    "death_sound": True,  # toggle death sound playback
}

# Declarative menu fields.
MENU_FIELDS = [
    {
        "key": "grid_size",
        "label": "Grid size",
        "type": "int",
        "min": 10,
        "max": 100,
        "step": 5,
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
]

# Effective runtime values (hydrated by apply_settings).
MAX_SPEED = SETTINGS["max_speed"]
DEATH_SOUND_ON = SETTINGS["death_sound"]


def _clamp(v, lo, hi):
    return max(lo, min(hi, v))


## Format a setting value for display.
def _fmt_setting_value(field, value):
    if isinstance(value, bool):
        return "On" if value else "Off"
    if isinstance(value, float):
        return f"{value:.1f}"
    return str(value)


## Draw the entire settings screen (scrollable if needed).
def _draw_settings_menu(selected_index: int) -> None:
    arena.fill(ARENA_COLOR)

    title = BIG_FONT.render("Settings", True, MESSAGE_COLOR)
    arena.blit(title, title.get_rect(center=(WIDTH / 2, HEIGHT / 8)))

    # spacing and scroll parameters
    visible_rows = int(HEIGHT * 0.75 // (HEIGHT * 0.07))
    top_index = max(0, selected_index - visible_rows + 3)
    padding_y = int(HEIGHT * 0.18)
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
    global CLOCK_TICKS, MAX_SPEED, DEATH_SOUND_ON

    old_grid = GRID_SIZE

    GRID_SIZE = int(SETTINGS["grid_size"])
    CLOCK_TICKS = float(SETTINGS["initial_speed"])
    MAX_SPEED = float(SETTINGS["max_speed"])
    DEATH_SOUND_ON = bool(SETTINGS["death_sound"])

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
            globals()["snake"] = Snake()
            globals()["apple"] = Apple()
            snake.speed = CLOCK_TICKS
        except NameError:
            # If called before classes/instances exist, ignore.
            pass


clock = pygame.time.Clock()

# Load gameover sound
gameover_sound = pygame.mixer.Sound("assets/sound/gameover.wav")

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
    max_width_ratio: fraction of WIDTH allowed (e.g., 0.9 for 90%).
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


## Game-over prompt: only Space/Enter restart; Q quits.
def game_over_prompt() -> None:
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
## Snake class
##


class Snake:
    def __init__(self):
        # Dimension of each snake segment.

        self.x, self.y = GRID_SIZE, GRID_SIZE

        # Initial direction
        # xmov :  -1 left,    0 still,   1 right
        # ymov :  -1 up       0 still,   1 dows
        self.xmov = 1
        self.ymov = 0

        # The snake has a head segement,
        self.head = pygame.Rect(self.x, self.y, GRID_SIZE, GRID_SIZE)

        # and a tail (array of segments).
        self.tail = []

        # The snake is born.
        self.alive = True

        # No collected apples.
        self.got_apple = False

        # Initial speed
        self.speed = CLOCK_TICKS

    # This function is called at each loop interation.

    def update(self):
        global apple

        # Calculate the head's next position based on current movement
        next_x = self.head.x + self.xmov * GRID_SIZE
        next_y = self.head.y + self.ymov * GRID_SIZE

        # Only check collisions if the snake is currently moving
        if self.xmov or self.ymov:
            # Check for border crash.
            if next_x not in range(0, WIDTH) or next_y not in range(0, HEIGHT):
                self.alive = False
                if DEATH_SOUND_ON:
                    gameover_sound.play()

            # Check for self-bite.
            for square in self.tail:
                if next_x == square.x and next_y == square.y:
                    self.alive = False
                    if DEATH_SOUND_ON:
                        gameover_sound.play()

        # In the event of death, reset the game arena.
        if not self.alive:
            # Tell the bad news
            pygame.draw.rect(arena, DEAD_HEAD_COLOR, snake.head)
            pygame.display.update()
            game_over_prompt()

            # Respan the head
            self.x, self.y = GRID_SIZE, GRID_SIZE
            self.head = pygame.Rect(self.x, self.y, GRID_SIZE, GRID_SIZE)

            # Respan the initial tail
            self.tail = []

            # Initial direction
            self.xmov = 1  # Right
            self.ymov = 0  # Still

            # Resurrection
            self.alive = True
            self.got_apple = False

            # Reset speed
            self.speed = CLOCK_TICKS

            # Drop an apple
            apple = Apple()

        # Move the snake.

        # If head hasn't moved, tail shouldn't either (otherwise, self-byte).
        if self.xmov or self.ymov:
            # Prepend a new segment to tail.
            self.tail.insert(
                0, pygame.Rect(self.head.x, self.head.y, GRID_SIZE, GRID_SIZE)
            )

            if self.got_apple:
                self.got_apple = False
            else:
                self.tail.pop()

            # Move the head along current direction.
            self.head.x += self.xmov * GRID_SIZE
            self.head.y += self.ymov * GRID_SIZE


##
## The apple class.
##


class Apple:
    def __init__(self):
        # Pick a random position within the game arena
        self.x = random.randrange(0, WIDTH, GRID_SIZE)
        self.y = random.randrange(0, HEIGHT, GRID_SIZE)

        # Create an apple at that location
        self.rect = pygame.Rect(self.x, self.y, GRID_SIZE, GRID_SIZE)

    # This function is called each interation of the game loop

    def update(self):
        # Drop the apple
        pygame.draw.rect(arena, APPLE_COLOR, self.rect)


##
## Draw the arena
##


def draw_grid():
    for x in range(0, WIDTH, GRID_SIZE):
        for y in range(0, HEIGHT, GRID_SIZE):
            rect = pygame.Rect(x, y, GRID_SIZE, GRID_SIZE)
            pygame.draw.rect(arena, GRID_COLOR, rect, 1)


##
## Start flow
##
start_menu()  # blocks until user picks "Start Game"
snake = Snake()  # create with the final, chosen GRID_SIZE
apple = Apple()

##
## Main loop
##

while True:
    for event in pygame.event.get():  # Wait for events
        # App terminated
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        # Key pressed
        if event.type == pygame.KEYDOWN:
            if event.key in (
                pygame.K_DOWN,
                pygame.K_s,
            ):  # Down arrow (or S):  move down
                snake.ymov = 1
                snake.xmov = 0
            elif event.key in (pygame.K_UP, pygame.K_w):  # Up arrow (or W):    move up
                snake.ymov = -1
                snake.xmov = 0
            elif event.key in (
                pygame.K_RIGHT,
                pygame.K_d,
            ):  # Right arrow (or D): move right
                snake.ymov = 0
                snake.xmov = 1
            elif event.key in (
                pygame.K_LEFT,
                pygame.K_a,
            ):  # Left arrow (or A):  move left
                snake.ymov = 0
                snake.xmov = -1
            elif event.key == pygame.K_q:  # Q         : quit game
                pygame.quit()
                sys.exit()
            elif event.key == pygame.K_p:  # P         : pause game
                game_on = not game_on
            elif event.key == pygame.K_m:
                was_running = game_on
                game_on = 0
                run_settings_menu()
                apply_settings(reset_objects=True)
                game_on = was_running
    ## Update the game

    if game_on:
        snake.update()

        arena.fill(ARENA_COLOR)
        draw_grid()

        apple.update()

    # Draw the tail
    for square in snake.tail:
        pygame.draw.rect(arena, TAIL_COLOR, square)

    # Draw head
    pygame.draw.rect(arena, HEAD_COLOR, snake.head)

    # Show score (snake length = head + tail)
    score = BIG_FONT.render(f"{len(snake.tail)}", True, SCORE_COLOR)
    score_rect = score.get_rect(center=(WIDTH / 2, HEIGHT / 12))
    arena.blit(score, score_rect)

    # If the head pass over an apple, lengthen the snake and drop another apple
    if snake.head.x == apple.x and snake.head.y == apple.y:
        # snake.tail.append(pygame.Rect(snake.head.x, snake.head.y, GRID_SIZE, GRID_SIZE))
        snake.got_apple = True
        snake.speed = min(snake.speed * 1.1, MAX_SPEED)  # Increase speed
        # print(f"[APPLE] Speed increased to: {snake.speed:.2f}")
        apple = Apple()

    # Update display and move clock.
    pygame.display.update()
    clock.tick_busy_loop(int(snake.speed))
