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

"""ECS-based game application.

This is the new main game loop that uses pure ECS architecture without
depending on old_code.
"""

import sys

from pygame import RESIZABLE as RESIZABLE_FLAG

from src.core.clock import GameClock
from src.core.io.pygame_adapter import PygameIOAdapter
from src.core.rendering.pygame_surface_renderer import PygameSurfaceRenderer
from src.ecs.board import Board
from src.ecs.prefabs.apple import create_apple
from src.ecs.prefabs.obstacle_field import create_obstacles
from src.ecs.prefabs.snake import create_snake
from src.ecs.world import World
from src.game.config import GameConfig
from src.game.constants import WINDOW_TITLE
from src.game.scenes.game_over import GameOverScene
from src.game.scenes.gameplay import GameplayScene
from src.game.scenes.menu import MenuScene
from src.game.scenes.scene_manager import SceneManager
from src.game.scenes.settings import SettingsScene
from src.game.services.assets import GameAssets
from src.game.settings import GameSettings


class ECSGameApp:
    """ECS-based game application.

    This version uses pure ECS architecture with GameplayScene and systems.
    """

    def __init__(self):
        """Initialize the ECS game application."""
        self.pygame_adapter = None
        self.config = None
        self.settings = None
        self.assets = None
        self.world = None
        self.scene_manager = None
        self.clock = None
        self.renderer = None
        self.running = False
        self.surface = None
        self.min_width = None
        self.min_height = None

    def initialize(self) -> None:
        """Initialize all game systems and resources."""
        # initialize pygame
        self.pygame_adapter = PygameIOAdapter()
        self.pygame_adapter.init()
        self.pygame_adapter.init_mixer()

        # initialize configuration
        self.config = GameConfig()

        # set minimum window dimensions
        self.min_width = self.config.initial_width
        self.min_height = self.config.initial_height

        # initialize settings
        self.settings = GameSettings(
            self.config.initial_width, self.config.initial_grid_size
        )

        # create game window with resizable flag
        self.surface = self.pygame_adapter.set_mode(
            (self.config.initial_width, self.config.initial_height),
            RESIZABLE_FLAG,
        )
        self.pygame_adapter.set_caption(WINDOW_TITLE)

        # initialize assets
        self.assets = GameAssets(self.config.initial_width)

        # initialize music
        GameAssets.init_music(volume=0.2, start_playing=True)

        # create ECS world
        # calculate grid dimensions in tiles
        grid_width_tiles = self.config.initial_width // self.config.initial_grid_size
        grid_height_tiles = self.config.initial_height // self.config.initial_grid_size

        board = Board(
            width=grid_width_tiles,
            height=grid_height_tiles,
            cell_size=self.config.initial_grid_size,
        )
        self.world = World(board)

        # calculate initial grid offset (centered in window)
        grid_pixel_width = grid_width_tiles * self.config.initial_grid_size
        grid_pixel_height = grid_height_tiles * self.config.initial_grid_size
        offset_x = (self.config.initial_width - grid_pixel_width) // 2
        offset_y = (self.config.initial_height - grid_pixel_height) // 2
        self.world.set_grid_offset(offset_x, offset_y)

        # create renderer
        self.renderer = PygameSurfaceRenderer(self.surface)

        # create scene manager
        self.scene_manager = SceneManager()

        # create and register scenes
        self._create_scenes()

        # initialize game clock
        self.clock = GameClock()

        # create initial entities
        self._create_initial_entities()

        # start with menu scene
        self.scene_manager.set_scene("menu")

    def _create_scenes(self) -> None:
        """Create and register all game scenes."""
        # Menu scene
        menu_scene = MenuScene(
            pygame_adapter=self.pygame_adapter,
            renderer=self.renderer.view(),
            width=self.config.initial_width,
            height=self.config.initial_height,
            assets=self.assets,
            settings=self.settings,
        )
        self.scene_manager.register_scene("menu", menu_scene)

        # Settings scene
        settings_scene = SettingsScene(
            pygame_adapter=self.pygame_adapter,
            renderer=self.renderer.view(),
            width=self.config.initial_width,
            height=self.config.initial_height,
            assets=self.assets,
            settings=self.settings,
            config=self.config,
        )
        self.scene_manager.register_scene("settings", settings_scene)

        # Gameplay scene
        gameplay_scene = GameplayScene(
            pygame_adapter=self.pygame_adapter,
            renderer=self.renderer.view(),
            width=self.config.initial_width,
            height=self.config.initial_height,
            world=self.world,
            config=self.config,
            settings=self.settings,
            assets=self.assets,
        )
        self.scene_manager.register_scene("gameplay", gameplay_scene)

        # Game over scene
        game_over_scene = GameOverScene(
            pygame_adapter=self.pygame_adapter,
            renderer=self.renderer.view(),
            width=self.config.initial_width,
            height=self.config.initial_height,
            assets=self.assets,
            settings=self.settings,
        )
        self.scene_manager.register_scene("game_over", game_over_scene)

    def _create_initial_entities(self) -> None:
        """Create initial game entities using prefabs."""
        grid_size = self.world.board.cell_size

        # create snake at center of board
        _ = create_snake(
            world=self.world,
            grid_size=grid_size,
            initial_speed=float(self.settings.get("initial_speed")),
            head_color=None,  # will use default from palette
            tail_color=None,  # will use default from palette
        )

        # create apple at random valid position
        # for now, just create at a fixed position
        # the SpawnSystem will handle proper spawning
        _ = create_apple(
            world=self.world,
            x=self.world.board.width // 2 + 5,
            y=self.world.board.height // 2,
            grid_size=grid_size,
            color=None,  # will use default
        )

        # create obstacles based on difficulty
        difficulty = self.settings.get("obstacle_difficulty")

        if difficulty and difficulty != "None":
            _ = create_obstacles(
                world=self.world,
                difficulty=difficulty,
                grid_size=grid_size,
                random_seed=None,  # use true randomness
            )

    def _calculate_obstacle_count(self) -> int:
        """Calculate number of obstacles based on difficulty setting."""
        difficulty = self.settings.get("obstacle_difficulty")

        # difficulty percentages
        percentages = {
            "None": 0.0,
            "Easy": 0.04,
            "Medium": 0.06,
            "Hard": 0.10,
            "Impossible": 0.15,
        }

        percentage = percentages.get(difficulty, 0.0)
        total_cells = self.world.board.width * self.world.board.height
        return int(total_cells * percentage)

    def _handle_window_resize(self, new_width: int, new_height: int) -> None:
        """Handle window resize event.

        Scales the game to fit new window dimensions while maintaining aspect ratio.
        Calculates new cell_size to fit grid within window, preserving grid dimensions.
        Enforces minimum window size and centers grid in window.

        Args:
            new_width: New window width in pixels
            new_height: New window height in pixels
        """
        # enforce minimum window size
        new_width = max(new_width, self.min_width)
        new_height = max(new_height, self.min_height)

        # reset display mode to enforce minimum size constraint
        # (pygame auto-resizes surface, so we need to explicitly set it back if too small)
        current_size = self.surface.get_size()
        if current_size != (new_width, new_height):
            self.pygame_adapter.set_mode((new_width, new_height), RESIZABLE_FLAG)

        # calculate new cell size that fits grid in window while maintaining aspect ratio
        grid_width = self.world.board.width
        grid_height = self.world.board.height
        new_cell_size = min(new_width // grid_width, new_height // grid_height)

        # ensure minimum cell size of 1 pixel
        new_cell_size = max(1, new_cell_size)

        # update board cell size
        self.world.board.set_cell_size(new_cell_size)

        # calculate grid offset to center it in the window
        grid_pixel_width = grid_width * new_cell_size
        grid_pixel_height = grid_height * new_cell_size
        offset_x = (new_width - grid_pixel_width) // 2
        offset_y = (new_height - grid_pixel_height) // 2
        self.world.set_grid_offset(offset_x, offset_y)

    def run(self) -> None:
        """Run the main game loop."""
        if not self.scene_manager:
            raise RuntimeError("Game not initialized. Call initialize() first.")

        self.running = True

        # main game loop
        while self.running:
            # check for window resize event
            resize_event = self.pygame_adapter.get_resize_event()
            if resize_event:
                self._handle_window_resize(resize_event[0], resize_event[1])

            # get delta time
            dt_ms = self.clock.tick()

            # begin rendering frame (clears command queue)
            self.renderer.begin_frame(clear_color=(32, 32, 32, 255))  # dark gray

            # update scene manager (handles scene transitions and updates)
            self.scene_manager.update(dt_ms)

            # render current scene
            self.scene_manager.render()

            # execute all queued draw commands
            self.renderer.update()

            # update display
            self.pygame_adapter.update_display()

            # cap frame rate
            self.world.clock.tick(60)

    def quit(self) -> None:
        """Quit the game application."""
        self.running = False

        if self.pygame_adapter:
            self.pygame_adapter.quit()

        sys.exit()
