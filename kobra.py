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

clock = pygame.time.Clock()

# Load gameover sound
gameover_sound = pygame.mixer.Sound("assets/sound/gameover.wav")

arena = pygame.display.set_mode((WIDTH, HEIGHT))

# BIG_FONT   = pygame.font.Font("assets/font/Ramasuri.ttf", int(WIDTH/8))
# SMALL_FONT = pygame.font.Font("assets/font/Ramasuri.ttf", int(WIDTH/20))

BIG_FONT = pygame.font.Font("assets/font/GetVoIP-Grotesque.ttf", int(WIDTH / 8))
SMALL_FONT = pygame.font.Font("assets/font/GetVoIP-Grotesque.ttf", int(WIDTH / 20))

pygame.display.set_caption(WINDOW_TITLE)

game_on = 1

## This function is called when the snake dies.


def center_prompt(title, subtitle):
    # Show title and subtitle.

    center_title = BIG_FONT.render(title, True, MESSAGE_COLOR)
    center_title_rect = center_title.get_rect(center=(WIDTH / 2, HEIGHT / 2))
    arena.blit(center_title, center_title_rect)

    center_subtitle = SMALL_FONT.render(subtitle, True, MESSAGE_COLOR)
    center_subtitle_rect = center_subtitle.get_rect(center=(WIDTH / 2, HEIGHT * 2 / 3))
    arena.blit(center_subtitle, center_subtitle_rect)

    pygame.display.update()

    # Wait for a keypres or a game quit event.
    while event := pygame.event.wait():
        if event.type == pygame.KEYDOWN:
            break
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
    if event.key == pygame.K_q:  # 'Q' quits game
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
                gameover_sound.play()

            # Check for self-bite.
            for square in self.tail:
                if next_x == square.x and next_y == square.y:
                    self.alive = False
                    gameover_sound.play()

        # In the event of death, reset the game arena.
        if not self.alive:
            # Tell the bad news
            pygame.draw.rect(arena, DEAD_HEAD_COLOR, snake.head)
            center_prompt("Game Over", "Press to restart (Q to exit)")

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
        self.x = int(random.randint(0, WIDTH) / GRID_SIZE) * GRID_SIZE
        self.y = int(random.randint(0, HEIGHT) / GRID_SIZE) * GRID_SIZE

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


draw_grid()

snake = Snake()  # The snake

apple = Apple()  # An apple

center_prompt(WINDOW_TITLE, "Press to start")

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
            # P : pause game
            elif event.key == pygame.K_p:
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
    score_rect = score.get_rect(center=(WIDTH / 2, HEIGHT / 12))
    arena.blit(score, score_rect)

    # If the head pass over an apple, lengthen the snake and drop another apple
    if snake.head.x == apple.x and snake.head.y == apple.y:
        # snake.tail.append(pygame.Rect(snake.head.x, snake.head.y, GRID_SIZE, GRID_SIZE))
        snake.got_apple = True
        snake.speed = min(snake.speed * 1.1, 20)  # Increase speed, max 20
        # print(f"[APPLE] Speed increased to: {snake.speed:.2f}")
        apple = Apple()

    # Update display and move clock.
    pygame.display.update()
    clock.tick(int(snake.speed))
