"""
This file is for defining constants for the kobra.py game.
This file is only for objects/constants whose values are known
before runtime and never changed
"""

import random


HEAD_COLOR = "#00aa00"  # Color of the snake's head.
DEAD_HEAD_COLOR = "#4b0082"  # Color of the dead snake's head.
TAIL_COLOR = "#00ff00"  # Color of the snake's tail.
OBSTACLE_COLOR = "#666666"  # Color of the obstacles.
APPLE_COLOR = "#aa0000"  # Color of the apple.
ARENA_COLOR = "#202020"  # Color of the ground.
GRID_COLOR = "#3c3c3b"  # Color of the grid lines.
SCORE_COLOR = "#ffffff"  # Color of the scoreboard.
MESSAGE_COLOR = "#808080"  # Color of the game-over message.

WINDOW_TITLE = "KobraPy"  # Window title.
CLOCK_TICKS = 4  # How fast the snake moves.

# Difficulty percentages for obstacle count
DIFFICULTY_PERCENTAGES = {
    "None": 0.0,
    "Easy": 0.04,
    "Medium": 0.06,
    "Hard": 0.10,
    "Impossible": 0.15,
}

# Color palettes for snake customization
SNAKE_COLOR_PALETTES = [
    # Classic Green
    {"head": "#00aa00", "tail": "#00ff00", "name": "Classic Green"},
    # Fire
    {"head": "#ff4500", "tail": "#ff6347", "name": "Fire"},
    # Ocean
    {"head": "#0066cc", "tail": "#00bfff", "name": "Ocean"},
    # Purple
    {"head": "#8a2be2", "tail": "#da70d6", "name": "Purple"},
    # Gold
    {"head": "#ffd700", "tail": "#ffff00", "name": "Gold"},
    # Pink
    {"head": "#ff1493", "tail": "#ff69b4", "name": "Pink"},
    # Cyan
    {"head": "#00ced1", "tail": "#00ffff", "name": "Cyan"},
    # Orange
    {"head": "#ff8c00", "tail": "#ffa500", "name": "Orange"},
    # Red
    {"head": "#dc143c", "tail": "#ff6b6b", "name": "Red"},
    # Forest
    {"head": "#228b22", "tail": "#32cd32", "name": "Forest"},
]


def get_random_snake_colors():
    """Get a random color palette for the snake.

    Returns:
        dict: Dictionary with 'head', 'tail', and 'name' keys
    """
    return random.choice(SNAKE_COLOR_PALETTES)


def get_snake_colors_by_name(name: str):
    """Get snake colors by palette name.

    Args:
        name: Name of the color palette

    Returns:
        dict: Dictionary with 'head', 'tail', and 'name' keys, or default if not found
    """
    for palette in SNAKE_COLOR_PALETTES:
        if palette["name"] == name:
            return palette
    return SNAKE_COLOR_PALETTES[0]  # Return default if not found
