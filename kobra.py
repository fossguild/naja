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

WIDTH, HEIGHT = 800, 800  # Game screen dimensions.

GRID_SIZE = 50  # Square grid size.

HEAD_COLOR = "#00aa00"  # Color of the snake's head.
DEAD_HEAD_COLOR = "#4b0082"  # Color of the dead snake's head.
TAIL_COLOR = "#00ff00"  # Color of the snake's tail.
APPLE_COLOR = "#aa0000"  # Color of the apple.
ORANGE_COLOR = "#ff7700"  # Color of the orange.
GRAPE_COLOR = "#800080"  # Color of the grape.
ARENA_COLOR = "#202020"  # Color of the ground.
GRID_COLOR = "#3c3c3b"  # Color of the grid lines.
SCORE_COLOR = "#ffffff"  # Color of the scoreboard.
MESSAGE_COLOR = "#808080"  # Color of the game-over message.

WINDOW_TITLE = "KobraPy"  # Window title.

CLOCK_TICKS = 4  # How fast the snake moves.

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

        # Track how many segments to grow.
        self.segments_to_grow = 0

        # Initial speed
        self.speed = CLOCK_TICKS

    # This function is called at each loop interation.

    def update(self):
        global current_fruit, player_score

        # Check for border crash.
        if self.head.x not in range(0, WIDTH) or self.head.y not in range(0, HEIGHT):
            self.alive = False
            gameover_sound.play()

        # Check for self-bite.
        for square in self.tail:
            if self.head.x == square.x and self.head.y == square.y:
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
            self.segments_to_grow = 0

            # Reset speed
            self.speed = CLOCK_TICKS

            # Reset fruit and score
            current_fruit = spawn_random_fruit()
            player_score = 0

        # Move the snake.

        # If head hasn't moved, tail shouldn't either (otherwise, self-byte).
        if self.xmov or self.ymov:
            # Prepend a new segment to tail.
            self.tail.insert(
                0, pygame.Rect(self.head.x, self.head.y, GRID_SIZE, GRID_SIZE)
            )

            # If snake should grow, decrement the counter; otherwise remove last segment
            if self.segments_to_grow > 0:
                self.segments_to_grow -= 1
            else:
                self.tail.pop()

            # Move the head along current direction.
            self.head.x += self.xmov * GRID_SIZE
            self.head.y += self.ymov * GRID_SIZE


##
## The fruit classes.
##


class Apple:
    def __init__(self):
        # Pick a random position within the game arena
        self.x = int(random.randint(0, WIDTH) / GRID_SIZE) * GRID_SIZE
        self.y = int(random.randint(0, HEIGHT) / GRID_SIZE) * GRID_SIZE

        # Create an apple at that location
        self.rect = pygame.Rect(self.x, self.y, GRID_SIZE, GRID_SIZE)
        self.points = 1  # Apple gives 1 point
        self.growth = 1  # Apple grows snake by 1 segment
        self.speed_modifier = 1.0  # No speed change

    # This function is called each interation of the game loop

    def update(self):
        # Drop the apple
        pygame.draw.rect(arena, APPLE_COLOR, self.rect)


class Orange:
    def __init__(self):
        # Pick a random position within the game arena
        self.x = int(random.randint(0, WIDTH) / GRID_SIZE) * GRID_SIZE
        self.y = int(random.randint(0, HEIGHT) / GRID_SIZE) * GRID_SIZE

        # Create an orange at that location
        self.rect = pygame.Rect(self.x, self.y, GRID_SIZE, GRID_SIZE)
        self.points = 2  # Orange gives 2 points
        self.growth = 2  # Orange grows snake by 2 segments
        self.speed_modifier = 1.0  # No speed change

    # This function is called each interation of the game loop

    def update(self):
        # Drop the orange
        pygame.draw.rect(arena, ORANGE_COLOR, self.rect)


class Grape:
    def __init__(self):
        # Pick a random position within the game arena
        self.x = int(random.randint(0, WIDTH) / GRID_SIZE) * GRID_SIZE
        self.y = int(random.randint(0, HEIGHT) / GRID_SIZE) * GRID_SIZE

        # Create a grape at that location
        self.rect = pygame.Rect(self.x, self.y, GRID_SIZE, GRID_SIZE)
        self.points = 3  # Grape gives 3 points
        self.growth = 1  # Grape grows snake by 1 segment (normal)
        self.speed_modifier = 0.8  # Grape slows down the snake (20% slower)

    # This function is called each interation of the game loop

    def update(self):
        # Drop the grape
        pygame.draw.rect(arena, GRAPE_COLOR, self.rect)


##
## Fruit spawning logic
##


def spawn_random_fruit():
    # Spawn a random fruit based on weighted probabilities.
    rand = random.random()
    if rand < 0.65:  # 65% chance for apple
        return Apple()
    elif rand < 0.85:  # 20% chance for orange
        return Orange()
    else:  # 15% for grape
        return Grape()


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

# Initialize fruit (only one fruit at a time)
current_fruit = spawn_random_fruit()

# Score tracking
player_score = 0

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
            elif event.key == pygame.K_p:  # S         : pause game
                game_on = not game_on
    ## Update the game

    if game_on:
        snake.update()

        arena.fill(ARENA_COLOR)
        draw_grid()

        # Draw current fruit
        current_fruit.update()

    # Draw the tail
    for square in snake.tail:
        pygame.draw.rect(arena, TAIL_COLOR, square)

    # Draw head
    pygame.draw.rect(arena, HEAD_COLOR, snake.head)

    # Show score (snake length = head + tail)
    score = BIG_FONT.render(f"{len(snake.tail)}", True, SCORE_COLOR)
    score_rect = score.get_rect(center=(WIDTH / 2, HEIGHT / 12))
    arena.blit(score, score_rect)

    # Check collision with current fruit
    if snake.head.x == current_fruit.x and snake.head.y == current_fruit.y:
        # Add segments to grow
        snake.segments_to_grow += current_fruit.growth

        # Apply speed modifier (grape slows down, others increase speed)
        if current_fruit.speed_modifier < 1.0:
            # Grape: decrease speed (divide to slow down)
            snake.speed = max(snake.speed / 1.2, CLOCK_TICKS)
        else:
            # Apple/Orange: increase speed as before
            snake.speed = min(snake.speed * 1.1, 20)

        # Add points
        player_score += current_fruit.points

        # Spawn a new random fruit
        current_fruit = spawn_random_fruit()

    # Update display and move clock.
    pygame.display.update()
    clock.tick(int(snake.speed))
