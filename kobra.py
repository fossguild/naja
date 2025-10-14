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

import pygame
import random
import sys

##
## Game customization.
##

WIDTH, HEIGHT = 800, 800     # Game screen dimensions.

GRID_SIZE = 50               # Square grid size.

HEAD_COLOR      = "#00aa00"  # Color of the snake's head.
DEAD_HEAD_COLOR = "#4b0082"  # Color of the dead snake's head.
TAIL_COLOR      = "#00ff00"  # Color of the snake's tail.
APPLE_COLOR     = "#aa0000"  # Color of the apple.
ARENA_COLOR     = "#202020"  # Color of the ground.
GRID_COLOR      = "#3c3c3b"  # Color of the grid lines.
SCORE_COLOR     = "#ffffff"  # Color of the scoreboard.
MESSAGE_COLOR   = "#808080"  # Color of the game-over message.

WINDOW_TITLE    = "KobraPy"  # Window title.

CLOCK_TICKS     = 7         # How fast the snake moves.
# Apple step cadence (in game ticks). Lower = faster apple movement.
APPLE_MOVE_INTERVAL = 2
# Apple placement modes
APPLE_MODES = ["vertical", "horizontal", "ambos"]

##
## Game implementation.
##

pygame.init()

clock = pygame.time.Clock()

# Load gameover sound
gameover_sound = pygame.mixer.Sound("assets/sound/gameover.wav")

arena = pygame.display.set_mode((WIDTH, HEIGHT))

# BIG_FONT   = pygame.font.Font("assets/font/Ramasuri.ttf", int(WIDTH/8))
# SMALL_FONT = pygame.font.Font("assets/font/Ramasuri.ttf", int(WIDTH/20))

BIG_FONT   = pygame.font.Font("assets/font/GetVoIP-Grotesque.ttf", int(WIDTH/8))
SMALL_FONT = pygame.font.Font("assets/font/GetVoIP-Grotesque.ttf", int(WIDTH/20))

pygame.display.set_caption(WINDOW_TITLE)

game_on = 1
apple_mode = "ambos"  # default; will be overwritten by pre-game menu
last_apple_region = None  # track last spawn quadrant
last_vertical_col = None   # track last column used in vertical mode spawns
last_horizontal_row = None # track last row used in horizontal mode spawns
last_ambos_signature = None # track last (dx,dy) used in ambos spawns

## This function is called when the snake dies.

def center_prompt(title, subtitle):

    # Show title and subtitle.

    center_title = BIG_FONT.render(title, True, MESSAGE_COLOR)
    center_title_rect = center_title.get_rect(center=(WIDTH/2, HEIGHT/2))
    arena.blit(center_title, center_title_rect)

    center_subtitle = SMALL_FONT.render(subtitle, True, MESSAGE_COLOR)
    center_subtitle_rect = center_subtitle.get_rect(center=(WIDTH/2, HEIGHT*2/3))
    arena.blit(center_subtitle, center_subtitle_rect)

    pygame.display.update()

   # Wait for a keypres or a game quit event.

    while ( event := pygame.event.wait() ):
        if event.type == pygame.KEYDOWN:
            break
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
    if event.key == pygame.K_q:          # 'Q' quits game
        pygame.quit()
        sys.exit()


# New: pre-game centered menu to select apple mode
def select_apple_mode_menu():
    idx = APPLE_MODES.index(apple_mode) if apple_mode in APPLE_MODES else 2
    while True:
        arena.fill(ARENA_COLOR)
        draw_grid()

        # Vertical layout based on font metrics (keeps consistent spacing)
        title_surf = BIG_FONT.render(WINDOW_TITLE, True, MESSAGE_COLOR)
        small_h = SMALL_FONT.get_height()
        y0 = HEIGHT // 2

        # Title
        title_rect = title_surf.get_rect(center=(WIDTH/2, y0 - int(2.2 * small_h)))
        arena.blit(title_surf, title_rect)

        # Subtitle
        subtitle_surf = SMALL_FONT.render("Escolha o modo da maçã", True, MESSAGE_COLOR)
        subtitle_rect = subtitle_surf.get_rect(center=(WIDTH/2, y0 - int(0.8 * small_h)))
        arena.blit(subtitle_surf, subtitle_rect)

        # Mode selector
        mode_label = APPLE_MODES[idx].capitalize()
        mode_text = SMALL_FONT.render(f"[ {mode_label} ]   ←   →   para alterar", True, MESSAGE_COLOR)
        mode_rect = mode_text.get_rect(center=(WIDTH/2, y0 + int(0.3 * small_h)))
        arena.blit(mode_text, mode_rect)

        # Prompts split in two lines to avoid clipping
        prompt1 = SMALL_FONT.render("Enter/Espaço para iniciar", True, MESSAGE_COLOR)
        prompt1_rect = prompt1.get_rect(center=(WIDTH/2, y0 + int(1.5 * small_h)))
        arena.blit(prompt1, prompt1_rect)

        prompt2 = SMALL_FONT.render("Q para sair", True, MESSAGE_COLOR)
        prompt2_rect = prompt2.get_rect(center=(WIDTH/2, y0 + int(2.4 * small_h)))
        arena.blit(prompt2, prompt2_rect)

        pygame.display.update()

        event = pygame.event.wait()
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT:
                idx = (idx - 1) % len(APPLE_MODES)
            elif event.key == pygame.K_RIGHT:
                idx = (idx + 1) % len(APPLE_MODES)
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                return APPLE_MODES[idx]
            elif event.key == pygame.K_q:
                pygame.quit()
                sys.exit()

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

        
    # This function is called at each loop interation.

    def update(self):
        global apple
        global apple_mode

        # Compute the head's next position (where it will be after movement)
        next_x = self.head.x + self.xmov * GRID_SIZE
        next_y = self.head.y + self.ymov * GRID_SIZE

        # Check for border crash at the next position.
        if next_x not in range(0, WIDTH) or next_y not in range(0, HEIGHT):
            self.alive = False
            gameover_sound.play()

        # Check for self-bite against the tail as it will be after movement.
        # Build the "future" tail: current head becomes first segment, and
        # if the snake does not eat an apple the last segment will be removed.
        future_tail = [pygame.Rect(s.x, s.y, s.width, s.height) for s in self.tail]
        future_tail.insert(0, pygame.Rect(self.head.x, self.head.y, GRID_SIZE, GRID_SIZE))
        if not self.got_apple and future_tail:
            future_tail.pop()

        for square in future_tail:
            if next_x == square.x and next_y == square.y:
                self.alive = False
                gameover_sound.play()

        # In the event of death, reset the game arena.
        if not self.alive:

            # Tell the bad news
            pygame.draw.rect(arena, DEAD_HEAD_COLOR, snake.head)
            center_prompt("Game Over", "Press to restart")

            # Respan the head
            self.x, self.y = GRID_SIZE, GRID_SIZE
            self.head = pygame.Rect(self.x, self.y, GRID_SIZE, GRID_SIZE)

            # Respan the initial tail
            self.tail = []

            # Initial direction
            self.xmov = 1 # Right
            self.ymov = 0 # Still

            # Resurrection
            self.alive = True
            self.got_apple = False

            # Drop an apple (avoid spawning on snake cells)
            forbidden_cells = {(self.head.x // GRID_SIZE, self.head.y // GRID_SIZE)}
            apple = Apple(
                mode=apple_mode,
                align=(self.head.x, self.head.y),
                forbidden=forbidden_cells
            )


        # Move the snake.

        # If head hasn't moved, tail shouldn't either (otherwise, self-byte).
        if (self.xmov or self.ymov):

            # Prepend a new segment to tail.
            self.tail.insert(0,pygame.Rect(self.head.x, self.head.y, GRID_SIZE, GRID_SIZE))

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
    def __init__(self, mode="ambos", align=None, forbidden=None):
        global last_apple_region, last_vertical_col, last_horizontal_row, last_ambos_signature

        # Work in grid coordinates to guarantee valid, aligned positions
        cols = WIDTH // GRID_SIZE
        rows = HEIGHT // GRID_SIZE

        # Normalize forbidden input to a set of (col,row)
        if forbidden is None:
            forbidden_set = set()
        elif isinstance(forbidden, set):
            forbidden_set = set(forbidden)
        else:
            forbidden_set = {forbidden}

        def region_quadrant(c, r):
            # 4 quadrants split at the middle column/row
            left = c < (cols // 2)
            top = r < (rows // 2)
            return (0 if left else 1) + (0 if top else 2)

        attempts = 0
        max_attempts = 200
        chosen = None

        while attempts < max_attempts:
            # Random starting cell
            col = random.randrange(cols)
            row = random.randrange(rows)

            # Direction per mode (grid steps)
            if mode == "vertical":
                dx, dy = 0, random.choice([-1, 1])
            elif mode == "horizontal":
                dx, dy = random.choice([-1, 1]), 0
            else:  # "ambos" -> move in both axes
                dx = random.choice([-1, 1])
                dy = random.choice([-1, 1])

            reg = region_quadrant(col, row)
            ok_forbidden = (col, row) not in forbidden_set
            ok_region = (last_apple_region is None) or (reg != last_apple_region)
            ok_lane = True
            if mode == "vertical" and last_vertical_col is not None:
                ok_lane = (col != last_vertical_col) or (attempts > 50)
            if mode == "horizontal" and last_horizontal_row is not None:
                ok_lane = (row != last_horizontal_row) or (attempts > 50)
            ok_signature = True
            if mode == "ambos" and last_ambos_signature is not None:
                ok_signature = ((dx, dy) != last_ambos_signature) or (attempts > 50)

            # Relax region constraint after many attempts to avoid deadlock
            if ok_forbidden and ok_lane and ok_signature and (ok_region or attempts > 100):
                chosen = (col, row, dx, dy, reg)
                break

            attempts += 1

        # Fallback (should rarely happen)
        if chosen is None:
            col, row = 0, 0
            dx, dy = (0, 1) if mode == "vertical" else ((1, 0) if mode == "horizontal" else (1, 1))
            reg = region_quadrant(col, row)
        else:
            col, row, dx, dy, reg = chosen

        # Remember constraints for next time
        last_apple_region = reg
        if mode == "vertical":
            last_vertical_col = col
        elif mode == "horizontal":
            last_horizontal_row = row
        else:
            last_ambos_signature = (dx, dy)

        # Movement setup
        self.mode = mode
        self.cols = cols
        self.rows = rows
        self.col = col
        self.row = row
        self.dx = dx
        self.dy = dy

        self.move_interval = APPLE_MOVE_INTERVAL
        self._ticks = 0

        # Create an apple at that location
        self.x = self.col * GRID_SIZE
        self.y = self.row * GRID_SIZE
        self.rect = pygame.Rect(self.x, self.y, GRID_SIZE, GRID_SIZE)

    # This function is called each interation of the game loop

    def update(self):
        # Move with cadence
        self._ticks += 1
        if self._ticks % self.move_interval == 0:
            # Horizontal movement (only if enabled by mode)
            if self.dx != 0:
                ncol = self.col + self.dx
                if ncol < 0 or ncol >= self.cols:
                    self.dx *= -1
                    ncol = self.col + self.dx
                self.col = ncol

            # Vertical movement (only if enabled by mode)
            if self.dy != 0:
                nrow = self.row + self.dy
                if nrow < 0 or nrow >= self.rows:
                    self.dy *= -1
                    nrow = self.row + self.dy
                self.row = nrow

            # Sync pixel position and rect
            self.x = self.col * GRID_SIZE
            self.y = self.row * GRID_SIZE
            self.rect.topleft = (self.x, self.y)

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

score = BIG_FONT.render("1", True, MESSAGE_COLOR)
score_rect = score.get_rect(center=(WIDTH/2, HEIGHT/20+HEIGHT/30))

draw_grid()

snake = Snake()    # The snake

# New: show centered menu before starting and select apple mode
apple_mode = select_apple_mode_menu()
# Avoid spawning on snake cells (head + tail)
forbidden_cells = {(snake.head.x // GRID_SIZE, snake.head.y // GRID_SIZE)}
forbidden_cells |= {(s.x // GRID_SIZE, s.y // GRID_SIZE) for s in snake.tail}
apple = Apple(
    mode=apple_mode,
    align=(snake.head.x, snake.head.y),
    forbidden=forbidden_cells
)

##
## Main loop
##

while True:

    for event in pygame.event.get():           # Wait for events

       # App terminated
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

          # Key pressed
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_DOWN:    # Down arrow:  move down
                snake.ymov = 1
                snake.xmov = 0
            elif event.key == pygame.K_UP:    # Up arrow:    move up
                snake.ymov = -1
                snake.xmov = 0
            elif event.key == pygame.K_RIGHT: # Right arrow: move right
                snake.ymov = 0
                snake.xmov = 1
            elif event.key == pygame.K_LEFT:  # Left arrow:  move left
                snake.ymov = 0
                snake.xmov = -1
            elif event.key == pygame.K_q:     # Q         : quit game
                pygame.quit()
                sys.exit()
            elif event.key == pygame.K_p:     # S         : pause game
                game_on = not game_on

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
    arena.blit(score, score_rect)

    # If the head pass over an apple, lengthen the snake and drop another apple
    if snake.head.x == apple.x and snake.head.y == apple.y:
        snake.got_apple = True
        # Avoid spawning on snake cells (head + tail)
        forbidden_cells = {(snake.head.x // GRID_SIZE, snake.head.y // GRID_SIZE)}
        forbidden_cells |= {(s.x // GRID_SIZE, s.y // GRID_SIZE) for s in snake.tail}
        apple = Apple(
            mode=apple_mode,
            align=(snake.head.x, snake.head.y),
            forbidden=forbidden_cells
        )


    # Update display and move clock.
    pygame.display.update()
    clock.tick(CLOCK_TICKS)
