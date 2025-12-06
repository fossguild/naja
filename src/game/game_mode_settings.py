#!/usr/bin/env python3
#
#   Copyright (c) 2023, Monaco F. J. <monaco@usp.br>
#
#   This file is part of Naja.
#
#   Naja is free software: you can redistribute it and/or modify
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

"""Game mode-specific settings configuration.

This module defines the available game modes and their specific settings.
Each game mode can have its own unique configuration options that only
appear when that mode is selected.
"""

# Available game modes
GAME_MODES = [
    "Classic",
    # future modes can be added here:
    # "Box Mode",
    # "Cheese Mode",
    # "Tail Mode",
    # "Shrinking Snake Mode",
]


# Mapping from game mode to mode-specific settings
# Each mode can define additional settings fields that will appear
# in the "Game Mode Settings" section when that mode is selected
GAME_MODE_SETTINGS = {
    "Classic": {
        "description": "Traditional snake game with no special mechanics",
        "settings": [
            # no mode-specific settings for classic mode yet
            # future settings can be added here
        ],
    },
    # example of how to add mode-specific settings in the future:
    # "Box Mode": {
    #     "description": "Push boxes around the arena",
    #     "settings": [
    #         {
    #             "key": "box_count",
    #             "label": "  Number of Boxes",
    #             "type": "int",
    #             "min": 1,
    #             "max": 5,
    #             "step": 1,
    #             "default": 1,
    #         },
    #         {
    #             "key": "box_speed_boost",
    #             "label": "  Speed Boost on Push",
    #             "type": "bool",
    #             "default": False,
    #         },
    #     ],
    # },
    # "Shrinking Snake Mode": {
    #     "description": "Snake shrinks instead of growing",
    #     "settings": [
    #         {
    #             "key": "initial_snake_length",
    #             "label": "  Initial Snake Length",
    #             "type": "int",
    #             "min": 5,
    #             "max": 20,
    #             "step": 1,
    #             "default": 10,
    #         },
    #         {
    #             "key": "speed_increase_on_eat",
    #             "label": "  Speed Increase on Eating",
    #             "type": "bool",
    #             "default": False,
    #         },
    #     ],
    # },
}


def get_mode_settings(mode_name: str) -> list[dict]:
    """Get the settings fields for a specific game mode.

    Args:
        mode_name: Name of the game mode

    Returns:
        List of setting field definitions for this mode
    """
    mode_config = GAME_MODE_SETTINGS.get(mode_name, {})
    return mode_config.get("settings", [])


def get_mode_description(mode_name: str) -> str:
    """Get the description for a specific game mode.

    Args:
        mode_name: Name of the game mode

    Returns:
        Description string for this mode
    """
    mode_config = GAME_MODE_SETTINGS.get(mode_name, {})
    return mode_config.get("description", "")


def get_mode_defaults(mode_name: str) -> dict:
    """Get default values for all mode-specific settings.

    Args:
        mode_name: Name of the game mode

    Returns:
        Dictionary mapping setting keys to their default values
    """
    settings = get_mode_settings(mode_name)
    return {
        field["key"]: field.get("default") for field in settings if "default" in field
    }
