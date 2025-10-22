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

import pygame

from src.ecs.world import World
from src.ecs.board import Board
from src.ecs.prefabs.snake import create_snake
from src.ecs.prefabs.apple import create_apple
from src.ecs.prefabs.obstacle_field import create_obstacles
from src.game.scenes.scene_manager import SceneManager
from src.game.scenes.menu import MenuScene
from src.game.scenes.gameplay import GameplayScene
from src.game.scenes.game_over import GameOverScene
from src.game.scenes.settings import SettingsScene
from src.core.io.pygame_adapter import PygameIOAdapter
from src.core.clock import GameClock
from src.game.config import GameConfig
from src.game.settings import GameSettings
from src.game.services.assets import GameAssets
from src.game.constants import WINDOW_TITLE
from src.core.rendering.pygame_surface_renderer import PygameSurfaceRenderer


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

    def initialize(self) -> None:
        """Initialize all game systems and resources."""
        # initialize pygame
        self.pygame_adapter = PygameIOAdapter()
        self.pygame_adapter.init()
        self.pygame_adapter.init_mixer()

        # initialize configuration
        self.config = GameConfig()

        # initialize settings
        self.settings = GameSettings(
            self.config.initial_width, self.config.initial_grid_size
        )

        # create game window
        self.surface = self.pygame_adapter.set_mode(
            (self.config.initial_width, self.config.initial_height)
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

    def _apply_settings_changes(self) -> None:
        """Apply settings changes made in menu."""
        # control music based on setting
        if self.settings.get("background_music"):
            pygame.mixer.music.unpause()
        else:
            pygame.mixer.music.pause()

    def _run_start_menu(self) -> None:
        """Run the start menu before gameplay."""
        # Import here to avoid circular imports
        from kobra import start_menu

        # create a minimal state object for menu compatibility
        class MenuState:
            def __init__(self, width, height, grid_size):
                self.width = width
                self.height = height
                self.grid_size = grid_size
                self.arena = None

        menu_state = MenuState(
            self.config.initial_width,
            self.config.initial_height,
            self.config.initial_grid_size,
        )
        menu_state.arena = self.surface

        start_menu(menu_state, self.assets, self.config, self.settings)

        # apply settings that were changed in menu
        self._apply_settings_changes()

    def run(self) -> None:
        """Run the main game loop."""
        if not self.scene_manager:
            raise RuntimeError("Game not initialized. Call initialize() first.")

        self.running = True

        # main game loop
        while self.running:
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
