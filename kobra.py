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

HEAD_COLOR      = "#2E8B57"  # Color of the snake's head (Sea Green).
HEAD_LIGHT      = "#32CD32"  # Light color for head gradient.
HEAD_DARK       = "#006400"  # Dark color for head gradient.
DEAD_HEAD_COLOR = "#4b0082"  # Color of the dead snake's head.
TAIL_COLOR      = "#228B22"  # Color of the snake's tail (Forest Green).
TAIL_LIGHT      = "#32CD32"  # Light color for tail segments.
TAIL_DARK       = "#1C5A1C"  # Dark color for tail segments.
SHADOW_COLOR    = "#1a1a1a"  # Color for shadow effect.
EYE_COLOR       = "#000000"  # Color of the snake's eyes.
EYE_SHINE       = "#ffffff"  # Color for eye shine effect.
APPLE_COLOR     = "#aa0000"  # Color of the apple.
ARENA_COLOR     = "#202020"  # Color of the ground.
GRID_COLOR      = "#3c3c3b"  # Color of the grid lines.
SCORE_COLOR     = "#ffffff"  # Color of the scoreboard.
MESSAGE_COLOR   = "#808080"  # Color of the game-over message.

WINDOW_TITLE    = "KobraPy"  # Window title.

CLOCK_TICKS     = 7         # How fast the snake moves.

##
## Drawing functions for enhanced snake appearance.
##

def hex_to_rgb(hex_color):
    """Convert hex color to RGB tuple."""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def draw_snake_head(surface, rect, direction=(1, 0), is_dead=False):
    """Draw an enhanced snake head with gradient, eyes, and direction awareness."""
    # Draw shadow first
    shadow_rect = pygame.Rect(rect.x + 2, rect.y + 2, rect.width, rect.height)
    pygame.draw.ellipse(surface, hex_to_rgb(SHADOW_COLOR), shadow_rect)
    
    # Choose colors based on state
    if is_dead:
        main_color = hex_to_rgb(DEAD_HEAD_COLOR)
        light_color = main_color
        dark_color = (int(main_color[0] * 0.6), int(main_color[1] * 0.6), int(main_color[2] * 0.6))
    else:
        main_color = hex_to_rgb(HEAD_COLOR)
        light_color = hex_to_rgb(HEAD_LIGHT)
        dark_color = hex_to_rgb(HEAD_DARK)
    
    # Draw the main head shape
    pygame.draw.ellipse(surface, main_color, rect)
    
    # Add simple gradient effect by drawing smaller ellipses
    for i in range(3):
        fade_factor = 0.7 + (i * 0.1)
        gradient_color = (
            int(light_color[0] * fade_factor + dark_color[0] * (1 - fade_factor)),
            int(light_color[1] * fade_factor + dark_color[1] * (1 - fade_factor)),
            int(light_color[2] * fade_factor + dark_color[2] * (1 - fade_factor))
        )
        gradient_rect = pygame.Rect(
            rect.x + i * 2, 
            rect.y + i * 2, 
            rect.width - i * 4, 
            rect.height - i * 4
        )
        if gradient_rect.width > 0 and gradient_rect.height > 0:
            pygame.draw.ellipse(surface, gradient_color, gradient_rect)
    
    # Draw eyes if not dead
    if not is_dead:
        eye_size = rect.width // 5
        if direction[0] == 1:  # Moving right
            eye1_pos = (int(rect.x + rect.width * 0.65), int(rect.y + rect.height * 0.35))
            eye2_pos = (int(rect.x + rect.width * 0.65), int(rect.y + rect.height * 0.65))
        elif direction[0] == -1:  # Moving left
            eye1_pos = (int(rect.x + rect.width * 0.25), int(rect.y + rect.height * 0.35))
            eye2_pos = (int(rect.x + rect.width * 0.25), int(rect.y + rect.height * 0.65))
        elif direction[1] == -1:  # Moving up
            eye1_pos = (int(rect.x + rect.width * 0.35), int(rect.y + rect.height * 0.25))
            eye2_pos = (int(rect.x + rect.width * 0.65), int(rect.y + rect.height * 0.25))
        else:  # Moving down
            eye1_pos = (int(rect.x + rect.width * 0.35), int(rect.y + rect.height * 0.65))
            eye2_pos = (int(rect.x + rect.width * 0.65), int(rect.y + rect.height * 0.65))
        
        # Draw eyes
        pygame.draw.circle(surface, hex_to_rgb(EYE_COLOR), eye1_pos, eye_size)
        pygame.draw.circle(surface, hex_to_rgb(EYE_COLOR), eye2_pos, eye_size)
        
        # Draw eye shine
        shine_size = max(1, eye_size // 2)
        shine1_pos = (eye1_pos[0] - eye_size//3, eye1_pos[1] - eye_size//3)
        shine2_pos = (eye2_pos[0] - eye_size//3, eye2_pos[1] - eye_size//3)
        pygame.draw.circle(surface, hex_to_rgb(EYE_SHINE), shine1_pos, shine_size)
        pygame.draw.circle(surface, hex_to_rgb(EYE_SHINE), shine2_pos, shine_size)

def draw_snake_segment(surface, rect, is_head=False):
    """Draw an enhanced snake body segment with rounded corners and gradient."""
    # Draw shadow
    shadow_rect = pygame.Rect(rect.x + 1, rect.y + 1, rect.width, rect.height)
    pygame.draw.rect(surface, hex_to_rgb(SHADOW_COLOR), shadow_rect, border_radius=rect.width//6)
    
    # Draw main segment with rounded corners
    main_color = hex_to_rgb(TAIL_COLOR)
    pygame.draw.rect(surface, main_color, rect, border_radius=rect.width//6)
    
    # Add simple gradient effect by drawing smaller rectangles
    light_color = hex_to_rgb(TAIL_LIGHT)
    dark_color = hex_to_rgb(TAIL_DARK)
    
    for i in range(2):
        fade_factor = 0.8 + (i * 0.2)
        gradient_color = (
            int(light_color[0] * fade_factor + dark_color[0] * (1 - fade_factor)),
            int(light_color[1] * fade_factor + dark_color[1] * (1 - fade_factor)),
            int(light_color[2] * fade_factor + dark_color[2] * (1 - fade_factor))
        )
        gradient_rect = pygame.Rect(
            rect.x + i * 2, 
            rect.y + i * 2, 
            rect.width - i * 4, 
            rect.height - i * 4
        )
        if gradient_rect.width > 0 and gradient_rect.height > 0:
            pygame.draw.rect(surface, gradient_color, gradient_rect, border_radius=gradient_rect.width//6)

##
## Game implementation.
##

pygame.init()

clock = pygame.time.Clock()

arena = pygame.display.set_mode((WIDTH, HEIGHT))

# BIG_FONT   = pygame.font.Font("assets/font/Ramasuri.ttf", int(WIDTH/8))
# SMALL_FONT = pygame.font.Font("assets/font/Ramasuri.ttf", int(WIDTH/20))

BIG_FONT   = pygame.font.Font("assets/font/GetVoIP-Grotesque.ttf", int(WIDTH/8))
SMALL_FONT = pygame.font.Font("assets/font/GetVoIP-Grotesque.ttf", int(WIDTH/20))

pygame.display.set_caption(WINDOW_TITLE)

game_on = 1

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
        
        # Store current direction for head drawing
        self.direction = (1, 0)

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

        # Check for border crash.
        if self.head.x not in range(0, WIDTH) or self.head.y not in range(0, HEIGHT):
            self.alive = False

        # Check for self-bite.
        for square in self.tail:
            if self.head.x == square.x and self.head.y == square.y:
                self.alive = False

        # In the event of death, reset the game arena.
        if not self.alive:

            # Tell the bad news
            draw_snake_head(arena, snake.head, snake.direction, is_dead=True)
            center_prompt("Game Over", "Press to restart")

            # Respan the head
            self.x, self.y = GRID_SIZE, GRID_SIZE
            self.head = pygame.Rect(self.x, self.y, GRID_SIZE, GRID_SIZE)

            # Respan the initial tail
            self.tail = []

            # Initial direction
            self.xmov = 1 # Right
            self.ymov = 0 # Still
            self.direction = (1, 0)  # Reset direction

            # Resurrection
            self.alive = True
            self.got_apple = False

            # Drop an apple
            apple = Apple()


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
            
            # Update direction for head drawing
            self.direction = (self.xmov, self.ymov)

##
## The apple class.
##

class Apple:
    def __init__(self):

        # Pick a random position within the game arena
        self.x = int(random.randint(0, WIDTH)/GRID_SIZE) * GRID_SIZE
        self.y = int(random.randint(0, HEIGHT)/GRID_SIZE) * GRID_SIZE

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

score = BIG_FONT.render("1", True, MESSAGE_COLOR)
score_rect = score.get_rect(center=(WIDTH/2, HEIGHT/20+HEIGHT/30))

draw_grid()

snake = Snake()    # The snake

apple = Apple()    # An apple

center_prompt(WINDOW_TITLE, "Press to start")

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
        draw_snake_segment(arena, square)

    # Draw head
    draw_snake_head(arena, snake.head, snake.direction, not snake.alive)

    # Show score (snake length = head + tail)
    score = BIG_FONT.render(f"{len(snake.tail)}", True, SCORE_COLOR)
    arena.blit(score, score_rect)

    # If the head pass over an apple, lengthen the snake and drop another apple
    if snake.head.x == apple.x and snake.head.y == apple.y:
        #snake.tail.append(pygame.Rect(snake.head.x, snake.head.y, GRID_SIZE, GRID_SIZE))
        snake.got_apple = True;
        apple = Apple()


    # Update display and move clock.
    pygame.display.update()
    clock.tick(CLOCK_TICKS)
