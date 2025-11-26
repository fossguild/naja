"""
This file is for defining constants for the kobra.py game.
This file is only for objects/constants whose values are known
before runtime and never changed
"""

import random
import platformdirs


HEAD_COLOR = "#00aa00"  # Color of the snake's head.
DEAD_HEAD_COLOR = "#4b0082"  # Color of the dead snake's head.
TAIL_COLOR = "#00ff00"  # Color of the snake's tail.
OBSTACLE_COLOR = "#666666"  # Color of the obstacles.
APPLE_COLOR = "#aa0000"  # Color of the apple.
ARENA_COLOR = "#202020"  # Color of the ground.
GRID_COLOR = "#3c3c3b"  # Color of the grid lines.
SCORE_COLOR = "#ffffff"  # Color of the scoreboard.
MESSAGE_COLOR = "#808080"  # Color of the game-over message.

# Game over screen colors
GAME_OVER_MESSAGE_COLOR = (128, 128, 128)  # Gray for game over message
GAME_OVER_HIGHLIGHT_COLOR = (200, 200, 200)  # Lighter gray for score display
GAME_OVER_NEW_SCORE_COLOR = (
    255,
    215,
    0,
)  # Gold color for highlighting new score in list
GAME_OVER_HIGH_SCORE_COLOR = (255, 69, 0)  # Red-orange for "NEW HIGH SCORE!" message
GAME_OVER_TIMESTAMP_COLOR = (80, 80, 80)  # Dark gray for timestamps
GAME_OVER_TIMESTAMP_HIGHLIGHT_COLOR = (180, 160, 0)  # Gold-ish for new score timestamp

WINDOW_TITLE = "KobraPy"  # Window title.
CLOCK_TICKS = 4  # How fast the snake moves.

# Application data directory constants
APP_NAME = "naja"  # Application name for data directory
APP_AUTHOR = "fossguild"  # Organization/author name for data directory
USER_DATA_DIR = platformdirs.user_data_dir(
    APP_NAME, APP_AUTHOR
)  # Platform-specific user data directory

# Difficulty percentages for obstacle count
DIFFICULTY_PERCENTAGES = {
    "None": 0.0,
    "Easy": 0.04,
    "Medium": 0.06,
    "Hard": 0.10,
    "Impossible": 0.15,
}
"""
Coefficient applied to the difficulty obstacle percentages to calculate
the maximum number of obstacles in dynamic spawn modes, defining a saturation point.
The value is chosen so that, at maximum difficulty, the board can reach up to 33.0%.
"""
DYNAMIC_SPAWN_OBSTACLES_SATURATION_COEFFICIENT = 3.3

"""
Coefficient applied to the difficulty obstacle percentages to calculate
the initial number of obstacles in dynamic spawn modes. The value is chosen
so that the initial number is 3/4 of the initial value in static modes.
"""
DYNAMIC_SPAWN_OBSTACLES_INITIAL_COEFFICIENT = 0.75

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
    # Obsidian
    {"head": "#3d2b4f", "tail": "#17171a", "name": "Obsidian"},
    # Rainbow - special palette that cycles through rainbow colors
    {"head": "#ff0000", "tail": "#rainbow", "name": "Rainbow"},
]

# Rainbow colors for the Rainbow skin (ROYGBIV spectrum)
RAINBOW_COLORS = [
    "#ff0000",  # Red
    "#ff7f00",  # Orange
    "#ffff00",  # Yellow
    "#00ff00",  # Green
    "#0000ff",  # Blue
    "#4b0082",  # Indigo
    "#9400d3",  # Violet
]


def get_rainbow_color(index: int) -> str:
    """Get a rainbow color by index, cycling through the spectrum.

    Args:
        index: Segment index (0 = head, 1+ = body segments)

    Returns:
        Hex color string for the segment
    """
    return RAINBOW_COLORS[index % len(RAINBOW_COLORS)]


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
