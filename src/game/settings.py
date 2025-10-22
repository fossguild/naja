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

"""Dynamic game settings and menu configuration."""

from .constants import SNAKE_COLOR_PALETTES


class GameSettings:
    """Manages game configuration settings and menu fields."""

    # Default settings values
    DEFAULT_SETTINGS = {
        "cells_per_side": 16,  # Will be calculated from screen size
        "initial_speed": 4.0,
        "max_speed": 20.0,
        "obstacle_difficulty": "None",
        "number_of_apples": 1,
        "background_music": True,
        "sound_effects": True,  # Controls all sound effects (eat, death, etc.)
        "electric_walls": True,
        "snake_color_palette": "Classic Green",  # New setting
    }

    # Declarative menu field definitions
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
        {
            "key": "obstacle_difficulty",
            "label": "Obstacles",
            "type": "select",
            "options": ["None", "Easy", "Medium", "Hard", "Impossible"],
        },
        {
            "key": "number_of_apples",
            "label": "Apples",
            "type": "int",
            "min": 1,
            "max": 30,
            "step": 1,
        },
        {"key": "background_music", "label": "Background Music", "type": "bool"},
        {"key": "sound_effects", "label": "Sound Effects", "type": "bool"},
        {
            "key": "electric_walls",
            "label": "Electric walls",
            "type": "bool",
        },
        {
            "key": "snake_color_palette",
            "label": "Snake Color",
            "type": "select",
            "options": [palette["name"] for palette in SNAKE_COLOR_PALETTES],
        },
    ]

    def __init__(self, initial_width: int, grid_size: int):
        """Initialize game settings with default values.

        Args:
            initial_width: Initial window width
            grid_size: Size of each grid cell
        """
        self.settings = self.DEFAULT_SETTINGS.copy()
        self.settings["cells_per_side"] = initial_width // grid_size

    def get(self, key: str):
        """Get a setting value by key.

        Args:
            key: Setting key to retrieve

        Returns:
            Setting value or None if key doesn't exist
        """
        return self.settings.get(key)

    def set(self, key: str, value) -> None:
        """Set a setting value.

        Args:
            key: Setting key to update
            value: New value for the setting
        """
        if key in self.settings:
            self.settings[key] = value

    def get_all(self) -> dict:
        """Get all settings as a dictionary.

        Returns:
            Dictionary containing all settings
        """
        return self.settings.copy()

    def reset_to_defaults(self) -> None:
        """Reset all settings to their default values."""
        self.settings = self.DEFAULT_SETTINGS.copy()

    @staticmethod
    def clamp(value: float, minimum: float, maximum: float) -> float:
        """Clamp a value between minimum and maximum.

        Args:
            value: Value to clamp
            minimum: Minimum allowed value
            maximum: Maximum allowed value

        Returns:
            Clamped value
        """
        return max(minimum, min(maximum, value))

    def format_setting_value(
        self, field: dict, value, current_width: int, current_grid_size: int
    ) -> str:
        """Format a setting value for display in the menu.

        Args:
            field: Menu field definition
            value: Current value of the setting
            current_width: Current window width
            current_grid_size: Current grid cell size

        Returns:
            Formatted string representation of the value
        """
        if field["key"] == "cells_per_side":
            # Always show the actual/current value that will be used
            actual = current_width // current_grid_size
            return f"{actual} × {actual}"
        elif field["key"] == "obstacle_difficulty":
            return f"{value}"
        elif isinstance(value, bool):
            return "On" if value else "Off"
        elif isinstance(value, float):
            return f"{value:.1f}"
        return str(value)

    def step_setting(self, field: dict, direction: int) -> None:
        """Change a setting value by one step in the given direction.

        Args:
            field: Menu field definition
            direction: Direction to step (-1 for decrease, +1 for increase)
        """
        key = field["key"]
        kind = field["type"]

        if kind == "bool":
            self.settings[key] = not self.settings[key]
            return

        elif kind == "select":
            options = field["options"]
            current_index = options.index(self.settings[key])
            new_index = (current_index + direction) % len(options)
            self.settings[key] = options[new_index]
            return

        step = field.get("step", 1 if kind == "int" else 1.0)
        new_val = self.settings[key] + (direction * step)

        lo = field.get("min", new_val)
        hi = field.get("max", new_val)

        if kind == "int":
            self.settings[key] = int(self.clamp(new_val, lo, hi))
        else:  # float
            self.settings[key] = float(self.clamp(new_val, lo, hi))

    def validate_apples_count(self, width: int, grid_size: int, height: int) -> int:
        """Calculate and validate the maximum number of apples allowed.

        Args:
            width: Current window width
            grid_size: Size of each grid cell
            height: Current window height

        Returns:
            Validated number of apples (clamped to reasonable limits)
        """
        total_cells = (width // grid_size) * (height // grid_size)
        max_apples_by_percent = int(total_cells * 0.15)  # 15% of grid
        max_apples_absolute = 30  # Hard cap
        max_apples = max(1, min(max_apples_by_percent, max_apples_absolute))
        return min(int(self.settings["number_of_apples"]), max_apples)

    def get_field_by_key(self, key: str) -> dict | None:
        """Get menu field definition by setting key.

        Args:
            key: Setting key to find

        Returns:
            Field definition dictionary or None if not found
        """
        for field in self.MENU_FIELDS:
            if field["key"] == key:
                return field
        return None

    def get_snake_colors(self):
        """Get current snake colors based on selected palette.

        Returns:
            dict: Dictionary with 'head', 'tail', and 'name' keys
        """
        from .constants import get_snake_colors_by_name

        palette_name = self.settings.get("snake_color_palette", "Classic Green")
        return get_snake_colors_by_name(palette_name)

    def randomize_snake_colors(self):
        """Randomize snake colors to a random palette.

        This method can be called when the user wants to randomize colors.
        """
        from .constants import get_random_snake_colors

        random_palette = get_random_snake_colors()
        self.settings["snake_color_palette"] = random_palette["name"]
