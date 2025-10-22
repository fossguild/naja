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

"""Gameplay scene that coordinates all ECS systems.

This scene registers and manages all game systems in the correct execution order.
It acts as the integration point for the ECS architecture, ensuring all systems
work together harmoniously.
"""

from typing import Optional, Any, List

import pygame

from src.game.scenes.base_scene import BaseScene
from src.ecs.world import World
from src.ecs.systems.base_system import BaseSystem
from src.ecs.systems.input import InputSystem
from src.ecs.systems.movement import MovementSystem
from src.ecs.systems.collision import CollisionSystem
from src.ecs.systems.spawn import SpawnSystem
from src.ecs.systems.scoring import ScoringSystem
from src.ecs.systems.audio import AudioSystem
from src.ecs.systems.interpolation import InterpolationSystem
from src.ecs.systems.board_display import BoardRenderSystem
from src.ecs.systems.validation import ValidationSystem
from src.ecs.systems.obstacle_generation import ObstacleGenerationSystem


class GameplayScene(BaseScene):
    """Gameplay scene that manages all game systems.

    This scene is responsible for:
    - Initializing all game systems with proper dependencies
    - Maintaining system execution order (critical for correctness)
    - Calling system lifecycle hooks (on_attach, on_detach)
    - Coordinating system updates each frame
    - Managing scene transitions

    System Execution Order (from ECS architecture docs):
    1. InputSystem - read user input
    2. MovementSystem - update positions
    3. CollisionSystem - detect collisions, emit events
    4. AppleSpawnSystem - maintain correct number of apples
    5. SpawnSystem - create new entities
    6. ScoringSystem - update score from events
    7. ObstacleGenerationSystem - generate obstacles (on demand)
    8. SettingsApplySystem - apply runtime settings changes
    9. ValidationSystem - verify game state integrity
    10. ResizeSystem - handle window resize
    11. InterpolationSystem - calculate smooth positions
    12. AudioSystem - play sounds and music
    13. BoardRenderSystem - draw everything
    14. UISystem - draw HUD and overlays (TODO: not yet implemented)
    """

    def __init__(
        self,
        pygame_adapter,
        renderer,
        width: int,
        height: int,
        world: World,
        config: Optional[Any] = None,
        settings: Optional[Any] = None,
        assets: Optional[Any] = None,
    ):
        """Initialize the gameplay scene.

        Args:
            pygame_adapter: Pygame IO adapter for input/output
            renderer: Renderer for drawing (RenderEnqueue view)
            width: Scene width
            height: Scene height
            world: ECS world instance
            config: Game configuration
            settings: Game settings
            assets: Game assets (fonts, sounds, etc.)
        """
        super().__init__(pygame_adapter, renderer, width, height)
        self._world = world
        self._config = config
        self._settings = settings
        self._assets = assets
        self._systems: List[BaseSystem] = []
        self._attached = False
        self._paused = False
        self._board_render_system: Optional[BoardRenderSystem] = None
        self._game_over = False
        self._death_reason = ""

    def on_attach(self) -> None:
        """Initialize and register all game systems.

        This method is called when the scene becomes active.
        It creates and registers all systems in the correct order.
        """
        if self._attached:
            return

        # clear any existing systems
        self._systems.clear()

        # 1. InputSystem - convert user input to commands/component changes
        input_system = InputSystem(
            pygame_adapter=self._pygame_adapter,
            direction_callback=self._handle_direction_change,
            get_current_direction_callback=self._get_current_direction,
            quit_callback=self._handle_quit,
            pause_callback=self._handle_pause,
            menu_callback=self._handle_menu,
            music_toggle_callback=self._handle_music_toggle,
            palette_randomize_callback=self._handle_palette_randomize,
        )
        self._systems.append(input_system)

        # 2. MovementSystem - update entity positions based on velocity
        movement_system = MovementSystem(get_electric_walls=self._get_electric_walls)
        self._systems.append(movement_system)

        # 3. CollisionSystem - detect collisions and emit events
        collision_system = CollisionSystem(
            get_snake_head_position=self._get_snake_head_position,
            get_snake_tail_positions=self._get_snake_tail_positions,
            get_snake_next_position=self._get_snake_next_position,
            get_electric_walls=self._get_electric_walls,
            get_grid_dimensions=self._get_grid_dimensions,
            get_current_speed=self._get_current_speed,
            get_max_speed=self._get_max_speed,
            death_callback=self._handle_death,
            apple_eaten_callback=self._handle_apple_eaten,
            speed_increase_callback=self._handle_speed_increase,
        )
        self._systems.append(collision_system)

        # 4. AppleSpawnSystem - maintain correct number of apples
        from src.ecs.systems.apple_spawn import AppleSpawnSystem
        apple_spawn_system = AppleSpawnSystem(max_spawn_attempts=1000)
        self._systems.append(apple_spawn_system)

        # 5. SpawnSystem - create new entities at valid positions
        spawn_system = SpawnSystem(
            max_spawn_attempts=1000,
            apple_color=(255, 0, 0),  # default red, will be overridden by palette
            random_seed=None,  # use true randomness for gameplay
        )
        self._systems.append(spawn_system)

        # 6. ScoringSystem - track score and high score
        scoring_system = ScoringSystem(
            score_callback=None,  # TODO: wire to UI score update
        )
        self._systems.append(scoring_system)

        # 7. ObstacleGenerationSystem - generate obstacles with connectivity guarantees
        obstacle_generation_system = ObstacleGenerationSystem(
            max_retries=100,
            safe_zone_width=8,
            safe_zone_height=2,
            random_seed=None,  # use true randomness for gameplay
        )
        self._systems.append(obstacle_generation_system)

        # 8. SettingsApplySystem - apply runtime settings changes
        # TODO: implement SettingsApplySystem and wire it here
        # settings_apply_system = SettingsApplySystem(...)
        # self._systems.append(settings_apply_system)

        # 9. ValidationSystem - debug validation (can be disabled in production)
        validation_system = ValidationSystem(
            enabled=True,  # TODO: make configurable via debug flag
            expected_apple_count=1,  # TODO: read from settings
            log_level=20,  # WARNING level
        )
        self._systems.append(validation_system)

        # 10. ResizeSystem - handle window resize events
        # TODO: implement ResizeSystem and wire it here
        # resize_system = ResizeSystem(...)
        # self._systems.append(resize_system)

        # 11. InterpolationSystem - calculate smooth positions for rendering
        interpolation_system = InterpolationSystem(
            electric_walls=True,  # TODO: read from settings
        )
        self._systems.append(interpolation_system)

        # 12. AudioSystem - play sounds and music
        audio_system = AudioSystem(
            sound_assets=None,  # TODO: wire to assets.sound_assets
            music_tracks=None,  # TODO: wire to assets.music_tracks
            default_volume=0.2,
        )
        self._systems.append(audio_system)

        # 13. BoardRenderSystem - render game world (board, entities)
        if self._renderer:
            self._board_render_system = BoardRenderSystem(
                renderer=self._renderer, settings=self._settings
            )
            self._systems.append(self._board_render_system)
        else:
            self._board_render_system = None

        # 14. UISystem - render UI overlays (score, menus, etc.)
        # TODO: implement UISystem and wire it here
        # ui_system = UISystem(...)
        # self._systems.append(ui_system)

        self._attached = True

    def on_detach(self) -> None:
        """Clean up systems when scene becomes inactive.

        This method is called when transitioning to another scene.
        It performs cleanup and releases resources.
        """
        if not self._attached:
            return

        # call cleanup on systems that need it
        # note: most systems don't need explicit cleanup since they don't own resources
        # but we clear the list to release references
        self._systems.clear()
        self._attached = False

    def update(self, dt_ms: float) -> Optional[str]:
        """Update all systems in execution order.

        This method is called every frame/tick to update the game state.

        Args:
            dt_ms: Delta time in milliseconds since last update
                   (currently unused, systems get delta time from world.clock)

        Returns:
            Next scene name or None to stay in current scene
        """
        if not self._attached:
            return None

        # update world's delta time for systems that need it (e.g., InterpolationSystem)
        self._world.set_dt_ms(dt_ms)

        # update all systems in order
        # note: input and rendering systems run even when paused
        for i, system in enumerate(self._systems):
            # skip game logic systems when paused
            if self._paused and i >= 1 and i <= 7:
                # skip movement, collision, apple spawn, spawn, scoring, obstacles, settings
                continue

            system.update(self._world)

        # draw pause overlay if paused
        if self._paused and self._board_render_system and self._renderer:
            surface = pygame.display.get_surface()
            if surface:
                self._board_render_system.draw_pause_overlay(
                    surface.get_width(), surface.get_height()
                )

        # return next scene if set
        return self.get_next_scene()

    def on_enter(self) -> None:
        """Called when entering gameplay scene."""
        print("Entering GameplayScene")

        # Clear any pending scene transition from previous session
        self.set_next_scene(None)

        # Apply settings before resetting world (including grid size changes)
        self._apply_settings_to_world()

        # Reset world state for new game
        self._reset_game_world()

        # Restore background music (in case we're coming from game over)
        try:
            if self._settings and self._settings.get("background_music"):
                # Load and play background music
                pygame.mixer.music.load("assets/sound/BoxCat_Games_CPU_Talk.ogg")
                pygame.mixer.music.play(-1)  # loop
        except Exception as e:
            print(f"Warning: Could not load background music: {e}")
            pass  # ignore if music fails to load

        self.on_attach()
        print("GameplayScene attached")

    def on_exit(self) -> None:
        """Called when exiting gameplay scene."""
        print("Exiting GameplayScene")
        self.on_detach()
        print("GameplayScene detached")

    def _apply_settings_to_world(self) -> None:
        """Apply current settings to the game world.
        
        This updates the world board dimensions based on cells_per_side setting.
        Should be called before resetting the game world.
        """
        if not self._settings or not self._config:
            return
        
        # Get desired cells per side from settings
        desired_cells = max(10, int(self._settings.get("cells_per_side")))
        
        # Calculate optimal grid/cell size
        new_cell_size = self._config.get_optimal_grid_size(desired_cells)
        
        # Calculate new window dimensions (must be multiple of cell size)
        new_width_pixels, new_height_pixels = self._config.calculate_window_size(new_cell_size)
        
        # Calculate board dimensions in cells
        new_width_cells = new_width_pixels // new_cell_size
        new_height_cells = new_height_pixels // new_cell_size
        
        # Create a new board with the new dimensions
        from src.ecs.board import Board
        new_board = Board(
            width=new_width_cells,
            height=new_height_cells,
            cell_size=new_cell_size
        )
        
        # Replace the board in the world
        self._world.board = new_board
        
        # Update pygame display if dimensions changed
        current_surface = pygame.display.get_surface()
        if current_surface:
            current_w, current_h = current_surface.get_size()
            if current_w != new_width_pixels or current_h != new_height_pixels:
                pygame.display.set_mode((new_width_pixels, new_height_pixels))
                
                # Reload fonts with new dimensions if assets available
                if self._assets:
                    self._assets.reload_fonts(new_width_pixels)
        
        print(f"Applied settings: {desired_cells}x{desired_cells} cells, cell_size={new_cell_size}px, board={new_width_cells}x{new_height_cells} cells, window={new_width_pixels}x{new_height_pixels}px")
        
        # Apply snake palette in case it changed
        self._apply_snake_palette()

    def _reset_game_world(self) -> None:
        """Reset the game world for a new game.

        This clears all existing entities and recreates them with fresh state.
        Called when entering gameplay scene to ensure clean state.
        """
        # Clear all entities from the world
        self._world.registry.clear()

        # Reset game over state
        self._game_over = False
        self._death_reason = ""

        # Recreate initial entities
        grid_size = self._world.board.cell_size

        # Create snake at center of board
        from src.ecs.prefabs.snake import create_snake

        # Get snake colors from settings
        snake_colors = self._settings.get_snake_colors()
        head_color_hex = snake_colors.get("head")
        tail_color_hex = snake_colors.get("tail")
        
        # Convert hex colors to RGB tuples
        head_color = self._hex_to_rgb(head_color_hex)
        tail_color = self._hex_to_rgb(tail_color_hex)

        _ = create_snake(
            world=self._world,
            grid_size=grid_size,
            initial_speed=float(self._settings.get("initial_speed")),
            head_color=head_color,
            tail_color=tail_color,
        )

        # Create AppleConfig entity to track desired apple count
        from src.ecs.components.apple_config import AppleConfig
        
        class AppleConfigEntity:
            def __init__(self, desired_count: int):
                self.apple_config = AppleConfig(desired_count=desired_count)
            
            def get_type(self):
                return None  # Config entity has no specific type
        
        desired_apples = self._settings.validate_apples_count(
            self._world.board.width * self._world.board.cell_size,
            self._world.board.cell_size,
            self._world.board.height * self._world.board.cell_size
        )
        apple_config_entity = AppleConfigEntity(desired_apples)
        self._world.registry.add(apple_config_entity)

        # Create initial apples
        from src.ecs.prefabs.apple import create_apple
        from src.ecs.entities.entity import EntityType
        import random
        
        # Get occupied positions (snake)
        occupied_positions = set()
        snakes = self._world.registry.query_by_type(EntityType.SNAKE)
        for _, snake in snakes.items():
            if hasattr(snake, "position"):
                occupied_positions.add((snake.position.x, snake.position.y))
                if hasattr(snake, "body"):
                    for segment in snake.body.segments:
                        occupied_positions.add((segment.x, segment.y))
        
        # Spawn initial apples
        for _ in range(desired_apples):
            # Try to find a valid position
            attempts = 0
            max_attempts = 1000
            while attempts < max_attempts:
                x = random.randint(0, self._world.board.width - 1)
                y = random.randint(0, self._world.board.height - 1)
                
                if (x, y) not in occupied_positions:
                    create_apple(self._world, x=x, y=y, grid_size=grid_size, color=None)
                    occupied_positions.add((x, y))
                    break
                
                attempts += 1

        # Create obstacles based on difficulty
        difficulty = self._settings.get("obstacle_difficulty")
        if difficulty and difficulty != "None":
            from src.ecs.prefabs.obstacle_field import create_obstacles

            _ = create_obstacles(
                world=self._world,
                difficulty=difficulty,
                grid_size=grid_size,
                random_seed=None,  # use true randomness
            )

        # Create score entity to track apples eaten
        from src.ecs.components.score import Score

        # Create a simple object to hold the score component
        # We don't use a specific entity type since this is just for UI tracking
        class ScoreEntity:
            def __init__(self):
                self.score = Score(current=0, high_score=0)

            def get_type(self):
                """Return a dummy type to satisfy registry interface."""
                return None  # No specific type for UI entities

        score_entity = ScoreEntity()
        self._world.registry.add(score_entity)

    def render(self) -> None:
        """Render the gameplay scene."""
        # Rendering is handled by the BoardRenderSystem in update()
        # This method is here for BaseScene compatibility
        pass

    def get_systems(self) -> List[BaseSystem]:
        """Get list of all registered systems.

        Returns:
            List of all systems in execution order
        """
        return self._systems.copy()

    @property
    def world(self) -> World:
        """Get the ECS world.

        Returns:
            World instance
        """
        return self._world

    @property
    def is_attached(self) -> bool:
        """Check if scene is currently attached.

        Returns:
            True if scene is active and systems are registered
        """
        return self._attached

    # Input handling callbacks

    def _handle_direction_change(self, dx: int, dy: int) -> None:
        """Handle direction change from input.

        Args:
            dx: X direction (-1, 0, 1)
            dy: Y direction (-1, 0, 1)
        """
        from src.ecs.entities.entity import EntityType

        # find snake entity and update its velocity
        snakes = self._world.registry.query_by_type(EntityType.SNAKE)
        for _, snake in snakes.items():
            if hasattr(snake, "velocity"):
                snake.velocity.dx = dx
                snake.velocity.dy = dy
                break

    def _get_current_direction(self) -> tuple[int, int]:
        """Get current snake direction.

        Returns:
            Tuple of (dx, dy) for current direction
        """
        from src.ecs.entities.entity import EntityType

        # find snake entity and return its velocity
        snakes = self._world.registry.query_by_type(EntityType.SNAKE)
        for _, snake in snakes.items():
            if hasattr(snake, "velocity"):
                return (snake.velocity.dx, snake.velocity.dy)

        return (0, 0)

    def _handle_quit(self) -> None:
        """Handle quit request."""
        # transition to menu instead of quitting
        self.set_next_scene("menu")

    def _handle_pause(self) -> None:
        """Handle pause toggle."""
        self._paused = not self._paused

    def _handle_menu(self) -> None:
        """Handle menu open request."""
        # pause game and transition to settings scene
        self._paused = True
        self.set_next_scene("settings")

    def _handle_music_toggle(self) -> None:
        """Handle music toggle - mutes/unmutes ALL game audio (music + sound effects)."""
        # Toggle both background_music and sound_effects settings
        current_music = self._settings.get("background_music")
        current_sfx = self._settings.get("sound_effects")
        
        # If either is on, turn both off. If both are off, turn both on.
        new_state = not (current_music or current_sfx)
        
        self._settings.set("background_music", new_state)
        self._settings.set("sound_effects", new_state)

        # Apply immediately to both music and sound effects
        if new_state:
            # Unmute: restore music and sound effects
            # Check if music is currently loaded and playing
            try:
                # Try to unpause first (in case music was paused)
                pygame.mixer.music.unpause()
                # Check if music is actually playing
                if not pygame.mixer.music.get_busy():
                    # Music not playing, load and start it
                    pygame.mixer.music.load("assets/sound/BoxCat_Games_CPU_Talk.ogg")
                    pygame.mixer.music.play(-1)  # loop
            except Exception:
                # If unpause failed, try loading and playing
                try:
                    pygame.mixer.music.load("assets/sound/BoxCat_Games_CPU_Talk.ogg")
                    pygame.mixer.music.play(-1)  # loop
                except Exception:
                    pass  # ignore if music fails to load

            pygame.mixer.unpause()  # Unpause all sound effect channels
        else:
            # Mute: pause music and sound effects
            pygame.mixer.music.pause()
            pygame.mixer.pause()  # Pause all sound effect channels

    def _handle_palette_randomize(self) -> None:
        """Handle palette randomization."""
        if not self._settings:
            return

        # Randomize the palette in settings
        self._settings.randomize_snake_colors()

        # Apply the new palette to the snake
        self._apply_snake_palette()

    # Collision callbacks

    def _get_snake_head_position(self) -> tuple[int, int]:
        """Get current snake head position."""
        from src.ecs.entities.entity import EntityType

        snakes = self._world.registry.query_by_type(EntityType.SNAKE)
        for _, snake in snakes.items():
            if hasattr(snake, "position"):
                return (snake.position.x, snake.position.y)
        return (0, 0)

    def _get_snake_tail_positions(self) -> list[tuple[int, int]]:
        """Get snake tail segment positions."""
        from src.ecs.entities.entity import EntityType

        snakes = self._world.registry.query_by_type(EntityType.SNAKE)
        for _, snake in snakes.items():
            if hasattr(snake, "body"):
                return [(seg.x, seg.y) for seg in snake.body.segments]
        return []

    def _get_snake_next_position(self) -> tuple[int, int]:
        """Get next snake position based on current position and velocity."""
        from src.ecs.entities.entity import EntityType

        snakes = self._world.registry.query_by_type(EntityType.SNAKE)
        for _, snake in snakes.items():
            if hasattr(snake, "position") and hasattr(snake, "velocity"):
                # Calculate raw next position
                next_x = snake.position.x + snake.velocity.dx
                next_y = snake.position.y + snake.velocity.dy

                electric_walls = self._get_electric_walls()

                # Only wrap if electric walls are disabled
                # If electric walls are enabled, collision system will detect out-of-bounds
                if not electric_walls:
                    next_x = next_x % self._world.board.width
                    next_y = next_y % self._world.board.height

                return (next_x, next_y)
        return (0, 0)

    def _get_electric_walls(self) -> bool:
        """Check if electric walls are enabled."""
        return self._settings.get("electric_walls") if self._settings else True

    def _get_grid_dimensions(self) -> tuple[int, int, int]:
        """Get grid dimensions in cells.

        Returns:
            Tuple of (grid_width_cells, grid_height_cells, cell_size_pixels)
        """
        board = self._world.board
        # Return grid dimensions in CELLS, not pixels
        # board.width and board.height are already in cells
        return (
            board.width,
            board.height,
            board.cell_size,
        )

    def _get_current_speed(self) -> float:
        """Get current snake speed."""
        from src.ecs.entities.entity import EntityType

        snakes = self._world.registry.query_by_type(EntityType.SNAKE)
        for _, snake in snakes.items():
            if hasattr(snake, "velocity"):
                return snake.velocity.speed
        return 4.0

    def _get_max_speed(self) -> float:
        """Get maximum allowed speed."""
        return float(self._settings.get("max_speed")) if self._settings else 20.0

    def _handle_death(self, reason: str) -> None:
        """Handle snake death."""
        from src.ecs.entities.entity import EntityType

        # kill the snake
        snakes = self._world.registry.query_by_type(EntityType.SNAKE)
        for _, snake in snakes.items():
            if hasattr(snake, "body"):
                snake.body.alive = False
                break

        # play death sound (only if sound effects are enabled)
        if self._settings and self._settings.get("sound_effects"):
            try:
                import pygame

                pygame.mixer.Sound("assets/sound/gameover.wav").play()
            except Exception:
                pass  # ignore if sound file not found
        
        # play death music (only if background music is enabled)
        if self._settings and self._settings.get("background_music"):
            try:
                import pygame

                pygame.mixer.music.load("assets/sound/death_song.mp3")
                pygame.mixer.music.play(-1)  # loop death music
            except Exception:
                pass  # ignore if music file not found

        # set game over state
        self._game_over = True
        self._death_reason = reason

        print(f"GAME OVER: {reason}")

        # transition to game over scene
        self.set_next_scene("game_over")

    def _handle_apple_eaten(
        self, apple_entity, apple_position: tuple[int, int]
    ) -> None:
        """Handle apple being eaten.

        Args:
            apple_entity: Apple entity ID or object
            apple_position: Position of eaten apple (unused, required)
        """
        from src.ecs.entities.entity import EntityType
        import random

        _ = apple_position  # suppress unused warning

        # play apple eating sound (only if sound effects are enabled)
        if self._settings and self._settings.get("sound_effects"):
            try:
                import pygame

                pygame.mixer.Sound("assets/sound/eat.flac").play()
            except Exception:
                pass  # ignore if sound file not found

        # grow snake
        snakes = self._world.registry.query_by_type(EntityType.SNAKE)
        for _, snake in snakes.items():
            if hasattr(snake, "body"):
                snake.body.size += 1
                break

        # increment score
        score_entities = self._world.registry.query_by_component("score")
        if score_entities:
            score_entity = list(score_entities.values())[0]
            if hasattr(score_entity, "score"):
                score_entity.score.current += 1

        # remove eaten apple
        if apple_entity:
            self._world.registry.remove(apple_entity)

        # Note: AppleSpawnSystem will automatically spawn a new apple
        # to maintain the desired count, so we don't need to spawn here

    def _handle_speed_increase(self, new_speed: float) -> None:
        """Handle speed increase when apple is eaten."""
        from src.ecs.entities.entity import EntityType

        snakes = self._world.registry.query_by_type(EntityType.SNAKE)
        for _, snake in snakes.items():
            if hasattr(snake, "velocity"):
                snake.velocity.speed = new_speed
                break

    def _apply_snake_palette(self) -> None:
        """Apply current palette colors to snake entity."""
        if not self._settings:
            return

        # Get the colors from the current palette
        snake_colors = self._settings.get_snake_colors()
        head_color_hex = snake_colors.get("head")
        tail_color_hex = snake_colors.get("tail")

        # Convert hex colors to RGB tuples
        head_color = self._hex_to_rgb(head_color_hex)
        tail_color = self._hex_to_rgb(tail_color_hex)

        # Find the snake entity and update its palette
        from src.ecs.entities.entity import EntityType

        snakes = self._world.registry.query_by_type(EntityType.SNAKE)
        for _, snake in snakes.items():
            if hasattr(snake, "palette"):
                # Update the palette colors
                snake.palette.primary_color = head_color
                snake.palette.secondary_color = tail_color
                break

    def _hex_to_rgb(self, hex_color: str) -> tuple[int, int, int]:
        """Convert hex color string to RGB tuple.
        
        Args:
            hex_color: Hex color string (e.g., "#00aa00")
            
        Returns:
            RGB tuple (r, g, b)
        """
        hex_color = hex_color.lstrip("#")
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
