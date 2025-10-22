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

"""Settings application system.

This system detects changes in game settings and applies them to the world
and entities in real-time during gameplay.
"""

from typing import Any, Optional

import pygame

from src.ecs.systems.base_system import BaseSystem
from src.ecs.world import World
from src.ecs.entities.entity import EntityType


class SettingsApplySystem(BaseSystem):
    """System that applies settings changes to the game world.

    Responsibilities:
    - Detect changes in settings (grid size, palette, speeds, obstacle difficulty)
    - Apply grid size changes (resize board and window)
    - Apply palette changes to snake
    - Apply speed changes to snake
    - Regenerate obstacles when difficulty changes

    This system should run after game logic systems but before rendering,
    so changes take effect immediately in the current frame.
    """

    def __init__(
        self,
        settings: Optional[Any] = None,
        config: Optional[Any] = None,
        assets: Optional[Any] = None,
    ):
        """Initialize the settings apply system.

        Args:
            settings: Game settings object
            config: Game configuration object
            assets: Game assets (for font reloading)
        """
        self._settings = settings
        self._config = config
        self._assets = assets

        # track previous settings to detect changes
        self._previous_cells_per_side = None
        self._previous_palette = None
        self._previous_initial_speed = None
        self._previous_max_speed = None
        self._previous_obstacle_difficulty = None

        # initialize tracking on first update
        self._initialized = False

    def update(self, world: World) -> None:
        """Apply any pending settings changes.

        Args:
            world: ECS world instance
        """
        if not self._settings or not self._config:
            return

        # initialize tracking on first run
        if not self._initialized:
            self._initialize_tracking()
            self._initialized = True
            return

        # check and apply each setting type
        self._check_and_apply_grid_size(world)
        self._check_and_apply_palette(world)
        self._check_and_apply_speeds(world)
        self._check_and_apply_obstacle_difficulty(world)

    def _initialize_tracking(self) -> None:
        """Initialize tracking of current settings."""
        if not self._settings:
            return

        self._previous_cells_per_side = self._settings.get("cells_per_side")
        self._previous_palette = self._get_current_palette_key()
        self._previous_initial_speed = self._settings.get("initial_speed")
        self._previous_max_speed = self._settings.get("max_speed")
        self._previous_obstacle_difficulty = self._settings.get("obstacle_difficulty")

    def _get_current_palette_key(self) -> str:
        """Get a unique key representing current palette colors.

        Returns:
            String key combining head and tail colors
        """
        snake_colors = self._settings.get_snake_colors()
        head = snake_colors.get("head", "")
        tail = snake_colors.get("tail", "")
        return f"{head}:{tail}"

    def _check_and_apply_grid_size(self, world: World) -> None:
        """Check if grid size changed and apply it.

        Args:
            world: ECS world instance
        """
        current_cells = self._settings.get("cells_per_side")
        if current_cells == self._previous_cells_per_side:
            return

        # grid size changed, apply it
        self._apply_grid_size_change(world, current_cells)
        self._previous_cells_per_side = current_cells

    def _apply_grid_size_change(self, world: World, desired_cells: int) -> None:
        """Apply grid size change to board and window.

        Args:
            world: ECS world instance
            desired_cells: Desired number of cells per side
        """
        # ensure minimum size
        desired_cells = max(10, int(desired_cells))

        # calculate optimal grid/cell size
        new_cell_size = self._config.get_optimal_grid_size(desired_cells)

        # calculate new window dimensions (must be multiple of cell size)
        new_width_pixels, new_height_pixels = self._config.calculate_window_size(
            new_cell_size
        )

        # calculate board dimensions in cells
        new_width_cells = new_width_pixels // new_cell_size
        new_height_cells = new_height_pixels // new_cell_size

        # create a new board with the new dimensions
        from src.ecs.board import Board

        new_board = Board(
            width=new_width_cells, height=new_height_cells, cell_size=new_cell_size
        )

        # replace the board in the world
        world.board = new_board

        # update pygame display if dimensions changed
        current_surface = pygame.display.get_surface()
        if current_surface:
            current_w, current_h = current_surface.get_size()
            if current_w != new_width_pixels or current_h != new_height_pixels:
                pygame.display.set_mode((new_width_pixels, new_height_pixels))

                # reload fonts with new dimensions if assets available
                if self._assets:
                    self._assets.reload_fonts(new_width_pixels)

        print(
            f"Applied grid size: {desired_cells}x{desired_cells} cells, "
            f"cell_size={new_cell_size}px, "
            f"board={new_width_cells}x{new_height_cells} cells, "
            f"window={new_width_pixels}x{new_height_pixels}px"
        )

    def _check_and_apply_palette(self, world: World) -> None:
        """Check if palette changed and apply it.

        Args:
            world: ECS world instance
        """
        current_palette = self._get_current_palette_key()
        if current_palette == self._previous_palette:
            return

        # palette changed, apply it
        self._apply_palette_change(world)
        self._previous_palette = current_palette

    def _apply_palette_change(self, world: World) -> None:
        """Apply palette change to snake entity.

        Args:
            world: ECS world instance
        """
        # get the colors from the current palette
        snake_colors = self._settings.get_snake_colors()
        head_color_hex = snake_colors.get("head")
        tail_color_hex = snake_colors.get("tail")

        # convert hex colors to RGB tuples
        head_color = self._hex_to_rgb(head_color_hex)
        tail_color = self._hex_to_rgb(tail_color_hex)

        # find the snake entity and update its palette
        snakes = world.registry.query_by_type(EntityType.SNAKE)
        for _, snake in snakes.items():
            if hasattr(snake, "palette"):
                # update the palette colors
                snake.palette.primary_color = head_color
                snake.palette.secondary_color = tail_color
                print(f"Applied palette: head={head_color_hex}, tail={tail_color_hex}")
                break

    def _check_and_apply_speeds(self, world: World) -> None:
        """Check if speeds changed and apply them.

        Args:
            world: ECS world instance
        """
        current_initial = self._settings.get("initial_speed")
        current_max = self._settings.get("max_speed")

        initial_changed = current_initial != self._previous_initial_speed
        max_changed = current_max != self._previous_max_speed

        if not (initial_changed or max_changed):
            return

        # apply speed changes
        if max_changed:
            self._apply_max_speed_change(world, float(current_max))
            self._previous_max_speed = current_max

        if initial_changed:
            self._apply_initial_speed_change(world, float(current_initial))
            self._previous_initial_speed = current_initial

    def _apply_initial_speed_change(self, world: World, new_speed: float) -> None:
        """Apply initial speed change to snake entity.

        Args:
            world: ECS world instance
            new_speed: New initial speed value
        """
        # get max_speed to ensure initial_speed doesn't exceed it
        max_speed = float(self._settings.get("max_speed") or 20.0)

        # cap initial_speed to max_speed if needed
        if new_speed > max_speed:
            new_speed = max_speed
            print(f"Warning: initial_speed capped to max_speed ({max_speed})")

        snakes = world.registry.query_by_type(EntityType.SNAKE)
        for _, snake in snakes.items():
            if hasattr(snake, "velocity"):
                # reset speed to new initial value
                snake.velocity.speed = new_speed
                print(f"Applied initial speed: {new_speed}")
                break

    def _apply_max_speed_change(self, world: World, new_max_speed: float) -> None:
        """Apply max speed change to snake entity.

        If the current speed exceeds the new max speed, it will be capped.

        Args:
            world: ECS world instance
            new_max_speed: New maximum speed value
        """
        snakes = world.registry.query_by_type(EntityType.SNAKE)
        for _, snake in snakes.items():
            if hasattr(snake, "velocity"):
                current_speed = snake.velocity.speed
                # cap current speed to new max if it exceeds it
                if current_speed > new_max_speed:
                    snake.velocity.speed = new_max_speed
                    print(
                        f"Applied max speed: {new_max_speed} "
                        f"(capped from {current_speed:.2f})"
                    )
                else:
                    print(
                        f"Applied max speed: {new_max_speed} "
                        f"(current speed {current_speed:.2f} is within limit)"
                    )
                break

    def _check_and_apply_obstacle_difficulty(self, world: World) -> None:
        """Check if obstacle difficulty changed and apply it.

        Args:
            world: ECS world instance
        """
        current_difficulty = self._settings.get("obstacle_difficulty")
        if current_difficulty == self._previous_obstacle_difficulty:
            return

        # difficulty changed, apply it
        self._apply_obstacle_difficulty_change(world, current_difficulty)
        self._previous_obstacle_difficulty = current_difficulty

    def _apply_obstacle_difficulty_change(
        self, world: World, new_difficulty: str
    ) -> None:
        """Apply obstacle difficulty change by regenerating obstacles.

        Args:
            world: ECS world instance
            new_difficulty: New difficulty level string
        """
        # remove all existing obstacles
        obstacles = world.registry.query_by_type(EntityType.OBSTACLE)
        obstacle_ids = list(obstacles.keys())
        for obstacle_id in obstacle_ids:
            world.registry.remove(obstacle_id)

        # generate new obstacles if difficulty is not "None"
        if new_difficulty and new_difficulty != "None":
            from src.ecs.prefabs.obstacle_field import create_obstacles

            grid_size = world.board.cell_size

            new_obstacle_ids = create_obstacles(
                world=world,
                difficulty=new_difficulty,
                grid_size=grid_size,
                random_seed=None,  # use true randomness
            )

            print(
                f"Applied obstacle difficulty '{new_difficulty}': "
                f"{len(new_obstacle_ids)} obstacles created"
            )
        else:
            print(f"Applied obstacle difficulty '{new_difficulty}': obstacles removed")

    def _hex_to_rgb(self, hex_color: str) -> tuple[int, int, int]:
        """Convert hex color string to RGB tuple.

        Args:
            hex_color: Hex color string (e.g., "#00aa00")

        Returns:
            RGB tuple (r, g, b)
        """
        hex_color = hex_color.lstrip("#")
        return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))
