#!/usr/bin/env python3
#
#   Copyright (c) 2023, Monaco F. J. <monaco@usp.br>
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

"""Game initialization service.

This service is responsible for initializing and resetting the game world,
creating initial entities, and managing game state transitions.
"""

import random
from typing import Any, Optional

from ecs.world import World
from core.types.color_utils import hex_to_rgb
from game.game_modes_registry import (
    CLASSIC_MODE_NAME,
    MOVING_APPLE_MODE_NAME,
    HEAD_TAIL_SWITCH_NAME,
    CHEESE_MODE_NAME,
    SHRINKING_MODE_NAME,
    AUTOPLAY_MODE_NAME,
    BOX_MODE_NAME,
    TRAIL_MODE_NAME,
    LIGHTS_OUT_MODE_NAME,
    PLAYER_VS_PLAYER_MODE_NAME,
    MIRRORED_MODE_NAME,
)


class GameInitializer:
    """Service responsible for initializing game state.

    This service encapsulates the logic for:
    - Resetting the game world
    - Creating initial entities (snake, apples, obstacles, score)
    - Managing game over state
    - Applying initial configurations

    By extracting this from GameplayScene, we achieve better separation
    of concerns and make the code more testable.
    """

    def __init__(
        self,
        settings: Optional[Any] = None,
        config: Optional[Any] = None,
        assets: Optional[Any] = None,
        scoreboard: Optional[Any] = None,
    ):
        """Initialize the game initializer.

        Args:
            settings: Game settings object (Settings instance)
            config: Game configuration object
            assets: Game assets (for font reloading when window resizes)
            scoreboard: Scoreboard for loading high scores
        """
        self._settings = settings
        self._config = config
        self._assets = assets
        self._scoreboard = scoreboard
        self._game_over = False
        self._death_reason = ""
        self._game_mode = CLASSIC_MODE_NAME

    def set_game_mode(self, mode: str) -> None:
        """Set the game mode that should be applied during initialization."""
        self._game_mode = mode or CLASSIC_MODE_NAME

        # Track game mode in settings for restriction UI
        if self._settings:
            self._settings.set_game_mode(self._game_mode)

        # Force specific settings for autoplay mode to ensure Hamiltonian cycle works
        if self._game_mode == AUTOPLAY_MODE_NAME and self._settings:
            # Single apple - Hamiltonian cycle tracks one at a time
            self._settings.set("number_of_apples", 1)
            # No obstacles - would break the cycle path
            self._settings.set("obstacle_difficulty", "None")
            self._settings.set("dynamic_spawn_obstacles", False)
            # No hunger - could cause unexpected death
            self._settings.set("enable_hunger", False)
            # Wraparound walls
            self._settings.set("electric_walls", True)

    def reset_world(self, world: World) -> None:
        """Reset the game world for a new game.

        This clears all existing entities and recreates them with fresh state.
        Called when entering gameplay scene to ensure clean state.

        Args:
            world: ECS world instance to reset
        """
        # clear all entities from the world
        world.registry.clear()

        # reset game over state
        self._game_over = False
        self._death_reason = ""

        # ensure board dimensions match current settings BEFORE creating entities
        # this fixes the bug where apple count is wrong on first game after changing cells_per_side
        self._sync_board_with_settings(world)

        # create initial entities
        self.create_initial_entities(world)

    def create_initial_entities(self, world: World) -> None:
        """Create all initial game entities.

        Creates:
        - GameState entity for game flow control
        - ColorScheme entity for rendering colors
        - Snake entity at center of board
        - AppleConfig entity to track desired apple count
        - Initial apples at random valid positions
        - Obstacles based on difficulty setting
        - Score entity to track progress

        Args:
            world: ECS world instance to populate with entities
        """
        grid_size = world.board.cell_size

        # create game state entity for game flow control
        self._create_game_state(world)

        # create color scheme entity for rendering systems
        self._create_color_scheme(world)

        # create snake(s) at center of board
        if self._game_mode == PLAYER_VS_PLAYER_MODE_NAME:
            # create 2 snakes for PvP mode
            self._create_pvp_snakes(world, grid_size)
        elif self._game_mode == MIRRORED_MODE_NAME:
            # create 2 mirrored snakes
            self._create_mirrored_snakes(world, grid_size)
        else:
            # create single snake for other modes
            self._create_snake(world, grid_size)

        # create apple config entity (skip for Box Mode)
        if self._game_mode != BOX_MODE_NAME:
            self._create_apple_config(world)

            # create initial apples (2 for PvP, normal count for others)
            if self._game_mode == PLAYER_VS_PLAYER_MODE_NAME:
                self._create_pvp_apples(world, grid_size)
            else:
                self._create_initial_apples(world, grid_size)

        # create obstacles based on difficulty
        self._create_obstacles(world, grid_size)

        # create box and hole for Box Mode
        if self._game_mode == BOX_MODE_NAME:
            self._create_box_and_hole(world, grid_size)

        # create score entity
        self._create_score_entity(world)

    def _create_game_state(self, world: World) -> None:
        """Create GameState entity for game flow control.

        This entity stores the global game state like pause, game over,
        and scene transitions. Following ECS principles, this is a
        singleton entity that systems query and modify.

        Args:
            world: ECS world instance
        """
        from ecs.components.game_state import GameState
        from ecs.components.lights_out_state import LightsOutState

        current_mode = self._game_mode
        moving_apples_enabled = current_mode == MOVING_APPLE_MODE_NAME
        swap_head_tail_enabled = current_mode == HEAD_TAIL_SWITCH_NAME or (
            self._settings
            and hasattr(self._settings, "get")
            and self._settings.get("swap_head_tail_on_apple")
        )
        cheese_mode_enabled = current_mode == CHEESE_MODE_NAME
        trail_mode_enabled = current_mode == TRAIL_MODE_NAME
        shrinking_mode_enabled = current_mode == SHRINKING_MODE_NAME
        lights_out_enabled = current_mode == LIGHTS_OUT_MODE_NAME

        class GameStateEntity:
            def __init__(self):
                self.game_state = GameState(
                    paused=False,
                    game_over=False,
                    death_reason="",
                    next_scene=None,
                    game_mode=current_mode,
                    moving_apples_enabled=moving_apples_enabled,
                    swap_head_tail_on_apple=swap_head_tail_enabled,
                    cheese_mode_enabled=cheese_mode_enabled,
                    trail_mode_enabled=trail_mode_enabled,
                    shrinking_mode_enabled=shrinking_mode_enabled,
                    lights_out_enabled=lights_out_enabled,
                )

            def get_type(self):
                return None  # config entity has no specific type

        game_state_entity = GameStateEntity()
        world.registry.add(game_state_entity)

        # Create Lights Out state entity if mode is active
        if current_mode == LIGHTS_OUT_MODE_NAME:

            class LightsOutEntity:
                def __init__(self):
                    self.lights_out_state = LightsOutState(radius=4)

                def get_type(self):
                    return None

            lights_out_entity = LightsOutEntity()
            world.registry.add(lights_out_entity)

        # NOTE: For autoplay mode, game_started is NOT set here.
        # AutoplaySystem sets it after computing the first safe direction.
        # This prevents the snake from moving before autoplay is ready.

    def _create_color_scheme(self, world: World) -> None:
        """Create ColorScheme entity for rendering systems.

        This entity stores the global color palette used by rendering systems.
        Following ECS principles, this is a singleton entity that systems query.

        Args:
            world: ECS world instance
        """
        from ecs.components.color_scheme import ColorScheme
        from core.types.color import Color

        # Get board colors from settings
        board_colors = self._settings.get_board_colors()
        primary_hex = board_colors.get("primary")
        secondary_hex = board_colors.get("secondary")
        grid_hex = board_colors.get("grid")

        class ColorSchemeEntity:
            def __init__(self):
                self.color_scheme = ColorScheme()
                # Apply board colors from settings
                self.color_scheme.arena = Color.from_hex(primary_hex)
                self.color_scheme.arena_secondary = Color.from_hex(secondary_hex)
                self.color_scheme.grid = Color.from_hex(grid_hex)

            def get_type(self):
                return None  # config entity has no specific type

        color_scheme_entity = ColorSchemeEntity()
        world.registry.add(color_scheme_entity)

    def _create_snake(self, world: World, grid_size: int) -> None:
        """Create the snake entity.

        Args:
            world: ECS world instance
            grid_size: Size of grid cells in pixels
        """
        from ecs.prefabs.snake import create_snake

        # get snake colors from settings
        snake_colors = self._settings.get_snake_colors()
        head_color_hex = snake_colors.get("head")
        tail_color_hex = snake_colors.get("tail")

        # convert hex colors to RGB tuples
        head_color = hex_to_rgb(head_color_hex)
        # Check for rainbow mode (special marker in tail color)
        if tail_color_hex == "#rainbow":
            # Rainbow mode: use black (0,0,0) as marker for render system
            tail_color = (0, 0, 0)
        else:
            tail_color = hex_to_rgb(tail_color_hex)

        _ = create_snake(
            world=world,
            grid_size=grid_size,
            initial_speed=float(self._settings.get("initial_speed")),
            head_color=head_color,
            tail_color=tail_color,
            enable_hunger=bool(self._settings.get("enable_hunger")),
            cheese_mode=(self._game_mode == CHEESE_MODE_NAME),
            shrinking_mode=(self._game_mode == SHRINKING_MODE_NAME),
            autoplay_mode=(self._game_mode == AUTOPLAY_MODE_NAME),
        )

    def _create_pvp_snakes(self, world: World, grid_size: int) -> None:
        """Create two snakes for Player vs Player mode.

        Args:
            world: ECS world instance
            grid_size: Size of grid cells in pixels
        """
        from ecs.prefabs.snake import create_snake
        from ecs.components.lives import Lives
        from ecs.components.respawn_timer import RespawnTimer
        from ecs.components.player_id import PlayerID
        from ecs.entities.entity import EntityType

        # Player 1 (left side) - use color from settings
        from core.types.color_utils import hex_to_rgb

        player1_x = world.board.width // 4
        player1_y = world.board.height // 2

        # Get player 1 colors from settings
        p1_colors = self._settings.get_snake_colors()
        p1_head_color = hex_to_rgb(p1_colors["head"])
        p1_tail_color = hex_to_rgb(p1_colors["tail"])

        player1_id = create_snake(
            world=world,
            grid_size=grid_size,
            initial_speed=float(self._settings.get("initial_speed")),
            head_color=p1_head_color,
            tail_color=p1_tail_color,
            enable_hunger=False,  # Disable hunger in PvP
            cheese_mode=False,
            shrinking_mode=False,
            autoplay_mode=False,
            initial_x=player1_x,
            initial_y=player1_y,
        )

        # Add PvP components to Player 1
        snakes = world.registry.query_by_type(EntityType.SNAKE)
        for snake_id, snake in snakes.items():
            if snake_id == player1_id:
                snake.lives = Lives(remaining=3, max_lives=3)
                snake.respawn_timer = RespawnTimer()
                snake.player_id = PlayerID(player_number=1, score=0)
                break

        # Player 2 (right side) - use color from settings
        player2_x = (world.board.width * 3) // 4
        player2_y = world.board.height // 2

        # Get player 2 colors from settings
        p2_colors = self._settings.get_player2_colors()
        p2_head_color = hex_to_rgb(p2_colors["head"])
        p2_tail_color = hex_to_rgb(p2_colors["tail"])

        player2_id = create_snake(
            world=world,
            grid_size=grid_size,
            initial_speed=float(self._settings.get("initial_speed")),
            head_color=p2_head_color,
            tail_color=p2_tail_color,
            enable_hunger=False,  # Disable hunger in PvP
            cheese_mode=False,
            shrinking_mode=False,
            autoplay_mode=False,
            initial_x=player2_x,
            initial_y=player2_y,
        )

        # Add PvP components to Player 2
        snakes = world.registry.query_by_type(EntityType.SNAKE)
        for snake_id, snake in snakes.items():
            if snake_id == player2_id:
                snake.lives = Lives(remaining=3, max_lives=3)
                snake.respawn_timer = RespawnTimer()
                snake.player_id = PlayerID(player_number=2, score=0)
                break

    def _create_mirrored_snakes(self, world: World, grid_size: int) -> None:
        """Create two mirrored snakes for Mirrored mode."""
        from ecs.prefabs.snake import create_snake
        from ecs.entities.entity import EntityType
        from core.types.color_utils import hex_to_rgb
        
        # [FIX] Use proportional spacing (1/4 width) so it works on ANY board size
        snake1_x = world.board.width // 4
        snake1_y = world.board.height // 2
        
        # Snake 2 is mirrored: (Width - 1 - X)
        snake2_x = world.board.width - 1 - snake1_x
        snake2_y = world.board.height - 1 - snake1_y
        
        # Get snake colors
        snake_colors = self._settings.get_snake_colors()
        head_color = hex_to_rgb(snake_colors["head"])
        tail_color = hex_to_rgb(snake_colors["tail"])
        
        p2_colors = self._settings.get_player2_colors()
        p2_head_color = hex_to_rgb(p2_colors["head"])
        p2_tail_color = hex_to_rgb(p2_colors["tail"])
        
        # Create snake 1
        snake1_id = create_snake(
            world=world,
            grid_size=grid_size,
            initial_speed=4.0,  # [FIX] Hardcode slower start speed for Mirrored Mode
            head_color=head_color,
            tail_color=tail_color,
            enable_hunger=False,
            cheese_mode=False,
            shrinking_mode=False,
            autoplay_mode=False,
            initial_x=snake1_x,
            initial_y=snake1_y,
            mirrored_snake_id=None,
        )
        
        # Create snake 2
        snake2_id = create_snake(
            world=world,
            grid_size=grid_size,
            initial_speed=4.0,  # [FIX] Hardcode slower start speed for Mirrored Mode
            head_color=p2_head_color,
            tail_color=p2_tail_color,
            enable_hunger=False,
            cheese_mode=False,
            shrinking_mode=False,
            autoplay_mode=False,
            initial_x=snake2_x,
            initial_y=snake2_y,
            mirrored_snake_id=snake1_id,
        )
        
        # [FIX] Invert Snake 2's velocity to face LEFT (-1, 0)
        # Default is RIGHT (1, 0). If we don't fix this, the first "Left" input
        # is rejected as a 180-degree turn, causing Snake 2 to follow Snake 1.
        snake2 = world.registry.get(snake2_id)
        if snake2 and hasattr(snake2, "velocity"):
            snake2.velocity.dx = -1
            snake2.velocity.dy = 0
        
        # Update snake1's mirrored_pair
        snakes = world.registry.query_by_type(EntityType.SNAKE)
        for snake_id, snake in snakes.items():
            if snake_id == snake1_id:
                from ecs.components.mirrored_pair import MirroredPair
                snake.mirrored_pair = MirroredPair(partner_id=snake2_id)
                break

    def _create_pvp_apples(self, world: World, grid_size: int) -> None:
        """Create 2 apples for Player vs Player mode.

        Args:
            world: ECS world instance
            grid_size: Size of grid cells in pixels
        """
        from ecs.prefabs.apple import create_apple
        from ecs.entities.entity import EntityType

        # Get occupied positions (both snakes)
        occupied_positions = set()
        snakes = world.registry.query_by_type(EntityType.SNAKE)
        for _, snake in snakes.items():
            if hasattr(snake, "position"):
                occupied_positions.add((snake.position.x, snake.position.y))
                if hasattr(snake, "body"):
                    for segment in snake.body.segments:
                        occupied_positions.add((segment.x, segment.y))

        # Spawn 2 apples
        for _ in range(2):
            attempts = 0
            max_attempts = 1000
            while attempts < max_attempts:
                x = random.randint(0, world.board.width - 1)
                y = random.randint(0, world.board.height - 1)

                if (x, y) not in occupied_positions:
                    create_apple(world, x=x, y=y, grid_size=grid_size, color=None)
                    occupied_positions.add((x, y))
                    break

                attempts += 1

    def _create_apple_config(self, world: World) -> None:
        """Create AppleConfig entity to track desired apple count.

        Args:
            world: ECS world instance
        """
        from ecs.components.apple_config import AppleConfig

        class AppleConfigEntity:
            def __init__(self, desired_count: int):
                self.apple_config = AppleConfig(desired_count=desired_count)

            def get_type(self):
                return None  # config entity has no specific type

        desired_apples = self._settings.validate_apples_count(
            world.board.width * world.board.cell_size,
            world.board.cell_size,
            world.board.height * world.board.cell_size,
        )
        apple_config_entity = AppleConfigEntity(desired_apples)
        world.registry.add(apple_config_entity)

    def _create_initial_apples(self, world: World, grid_size: int) -> None:
        """Create initial apples at random valid positions.

        Args:
            world: ECS world instance
            grid_size: Size of grid cells in pixels
        """
        from ecs.prefabs.apple import create_apple
        from ecs.entities.entity import EntityType

        # get desired apple count from config entity
        apple_configs = world.registry.query_by_component("apple_config")
        if not apple_configs:
            return

        config_entity = list(apple_configs.values())[0]
        desired_apples = config_entity.apple_config.desired_count

        # get occupied positions (snake)
        occupied_positions = set()
        snakes = world.registry.query_by_type(EntityType.SNAKE)
        for _, snake in snakes.items():
            if hasattr(snake, "position"):
                occupied_positions.add((snake.position.x, snake.position.y))
                if hasattr(snake, "body"):
                    for segment in snake.body.segments:
                        occupied_positions.add((segment.x, segment.y))

        # spawn initial apples
        for _ in range(desired_apples):
            # try to find a valid position
            attempts = 0
            max_attempts = 1000
            while attempts < max_attempts:
                x = random.randint(0, world.board.width - 1)
                y = random.randint(0, world.board.height - 1)

                if (x, y) not in occupied_positions:
                    create_apple(world, x=x, y=y, grid_size=grid_size, color=None)
                    occupied_positions.add((x, y))
                    break

                attempts += 1

    def _create_obstacles(self, world: World, grid_size: int) -> None:
        """Create obstacles based on difficulty setting.

        Args:
            world: ECS world instance
            grid_size: Size of grid cells in pixels
        """
        difficulty = self._settings.get("obstacle_difficulty")
        dynamic_spawn = self._settings.get("dynamic_spawn_obstacles")
        if difficulty and difficulty != "None":
            from ecs.prefabs.obstacle_field import create_obstacles

            _ = create_obstacles(
                world=world,
                difficulty=difficulty,
                dynamic_spawn=dynamic_spawn,
                grid_size=grid_size,
                random_seed=None,  # use true randomness
            )

    def _create_box_and_hole(self, world: World, grid_size: int) -> None:
        """Create a box and hole for Box Mode."""
        from ecs.prefabs.box import create_box
        from ecs.prefabs.hole import create_hole
        from ecs.entities.entity import EntityType

        # get occupied positions (snake, apples, obstacles)
        occupied_positions = set()

        # snake positions
        snakes = world.registry.query_by_type(EntityType.SNAKE)
        for _, snake in snakes.items():
            if hasattr(snake, "position"):
                occupied_positions.add((snake.position.x, snake.position.y))
                if hasattr(snake, "body"):
                    for segment in snake.body.segments:
                        occupied_positions.add((segment.x, segment.y))

        # apple positions
        apples = world.registry.query_by_type(EntityType.APPLE)
        for _, apple in apples.items():
            if hasattr(apple, "position"):
                occupied_positions.add((apple.position.x, apple.position.y))

        # obstacle positions
        obstacles = world.registry.query_by_type(EntityType.OBSTACLE)
        for _, obstacle in obstacles.items():
            if hasattr(obstacle, "position"):
                occupied_positions.add((obstacle.position.x, obstacle.position.y))

        # find valid position for box (avoid borders)
        box_x, box_y = None, None
        attempts = 0
        max_attempts = 1000
        while attempts < max_attempts:
            # avoid borders - box must be at least 1 cell away from edges
            x = random.randint(1, world.board.width - 2)
            y = random.randint(1, world.board.height - 2)

            if (x, y) not in occupied_positions:
                box_x, box_y = x, y
                occupied_positions.add((x, y))
                break

            attempts += 1

        # find valid position for hole (different from box, not on borders)
        hole_x, hole_y = None, None
        attempts = 0
        while attempts < max_attempts:
            # avoid borders - hole must be at least 1 cell away from edges
            x = random.randint(1, world.board.width - 2)
            y = random.randint(1, world.board.height - 2)

            if (x, y) not in occupied_positions:
                hole_x, hole_y = x, y
                break

            attempts += 1

        # create box and hole if valid positions found
        if box_x is not None and hole_x is not None:
            create_box(world, x=box_x, y=box_y, grid_size=grid_size)
            create_hole(world, x=hole_x, y=hole_y, grid_size=grid_size)

    def _create_score_entity(self, world: World) -> None:
        """Create score entity to track apples eaten.

        Loads high score from scoreboard if available.

        Args:
            world: ECS world instance
        """
        from ecs.components.score import Score

        # load high score from scoreboard (same way as game over screen)
        loaded_high_score = 0
        if self._scoreboard and self._settings:
            try:
                # get sorted scores for current settings and game mode
                sorted_scores = self._scoreboard.sorted_scores(
                    self._settings, self._game_mode
                )
                # take the first (highest) score if available
                if sorted_scores:
                    loaded_high_score = sorted_scores[0]["value"]
            except Exception:
                # silently fail if scoreboard is not available
                pass

        # create a simple object to hold the score component
        # we don't use a specific entity type since this is just for UI tracking
        class ScoreEntity:
            def __init__(self, high_score):
                self.score = Score(current=0, high_score=high_score)

            def get_type(self):
                """Return a dummy type to satisfy registry interface."""
                return None  # no specific type for UI entities

        score_entity = ScoreEntity(loaded_high_score)
        world.registry.add(score_entity)

    @property
    def game_over(self) -> bool:
        """Check if game is over.

        Returns:
            True if game is over, False otherwise
        """
        return self._game_over

    @property
    def death_reason(self) -> str:
        """Get the reason for game over.

        Returns:
            Death reason string
        """
        return self._death_reason

    def set_game_over(self, reason: str) -> None:
        """Set game over state.

        Args:
            reason: Reason for game over (e.g., "wall collision", "self collision")
        """
        self._game_over = True
        self._death_reason = reason

    def _sync_board_with_settings(self, world: World) -> None:
        """Ensure board dimensions match current settings.

        This must be called before creating entities to ensure AppleConfig
        and other entities use the correct board dimensions.

        Fixes bug where apple distribution is incorrect on first game after
        changing cells_per_side setting.

        Args:
            world: ECS world instance
        """
        if not self._settings:
            return

        # get desired cells_per_side from settings
        desired_cells = self._settings.get("cells_per_side")
        actual_cells = world.board.width  # board is always square

        # if board doesn't match settings, recreate it
        if desired_cells != actual_cells:
            # need config to calculate optimal sizes
            if not self._config:
                from game.config import GameConfig

                config = GameConfig()
            else:
                config = self._config

            # ensure minimum size
            desired_cells = max(10, int(desired_cells))

            # Define modes that require even boards
            requires_even = self._game_mode in [AUTOPLAY_MODE_NAME, MIRRORED_MODE_NAME]

            # Trigger update if settings changed OR if mode needs even board but has odd
            if desired_cells != actual_cells or (requires_even and actual_cells % 2 != 0):
                desired_cells += 1  # Round up to nearest even number

            if requires_even:
                if new_width_cells % 2 != 0:
                    new_width_cells -= 1
                if new_height_cells % 2 != 0:
                    new_height_cells -= 1
                
                # CRITICAL: Recalculate pixels so window matches the board exactly
                new_width_pixels = new_width_cells * new_cell_size
                new_height_pixels = new_height_cells * new_cell_size
            
            # calculate optimal grid/cell size
            new_cell_size = config.get_optimal_grid_size(desired_cells)

            # calculate new window dimensions (must be multiple of cell size)
            new_width_pixels, new_height_pixels = config.calculate_window_size(
                new_cell_size
            )

            # calculate board dimensions in cells
            new_width_cells = new_width_pixels // new_cell_size
            new_height_cells = new_height_pixels // new_cell_size

            # create a new board with the new dimensions
            from ecs.board import Board

            new_board = Board(
                width=new_width_cells,
                height=new_height_cells,
                cell_size=new_cell_size,
            )

            # replace the board in the world
            world.board = new_board

            # update pygame display window to match new dimensions
            import pygame

            current_surface = pygame.display.get_surface()
            if current_surface:
                current_w, current_h = current_surface.get_size()
                if current_w != new_width_pixels or current_h != new_height_pixels:
                    pygame.display.set_mode((new_width_pixels, new_height_pixels))

                    # reload fonts with new dimensions if assets available
                    if self._assets:
                        self._assets.reload_fonts(new_width_pixels)

            print(
                f"[GameInitializer] Synced board to settings: {desired_cells}x{desired_cells} cells, "
                f"cell_size={new_cell_size}px, "
                f"board={new_width_cells}x{new_height_cells} cells, "
                f"window={new_width_pixels}x{new_height_pixels}px"
            )
