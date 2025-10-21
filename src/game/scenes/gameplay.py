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

import sys
from typing import Optional, Any, List

import pygame

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


class GameplayScene:
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
    4. SpawnSystem - create new entities
    5. ScoringSystem - update score from events
    6. ObstacleGenerationSystem - generate obstacles (on demand)
    7. SettingsApplySystem - apply runtime settings changes
    8. ValidationSystem - verify game state integrity
    9. ResizeSystem - handle window resize
    10. InterpolationSystem - calculate smooth positions
    11. AudioSystem - play sounds and music
    12. BoardRenderSystem - draw everything
    13. UISystem - draw HUD and overlays (TODO: not yet implemented)
    """

    def __init__(
        self,
        world: World,
        pygame_adapter: Optional[Any] = None,
        renderer: Optional[Any] = None,
        config: Optional[Any] = None,
        settings: Optional[Any] = None,
        assets: Optional[Any] = None,
    ):
        """Initialize the gameplay scene.

        Args:
            world: ECS world instance
            pygame_adapter: Pygame IO adapter for input/output
            renderer: Renderer for drawing (RenderEnqueue view)
            config: Game configuration
            settings: Game settings
            assets: Game assets (fonts, sounds, etc.)
        """
        self._world = world
        self._pygame_adapter = pygame_adapter
        self._renderer = renderer
        self._config = config
        self._settings = settings
        self._assets = assets
        self._systems: List[BaseSystem] = []
        self._attached = False
        self._paused = False
        self._game_over = False
        self._death_reason = ""
        self._board_render_system: Optional[BoardRenderSystem] = None

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
        movement_system = MovementSystem()
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

        # 4. SpawnSystem - create new entities at valid positions
        spawn_system = SpawnSystem(
            max_spawn_attempts=1000,
            apple_color=(255, 0, 0),  # default red, will be overridden by palette
            random_seed=None,  # use true randomness for gameplay
        )
        self._systems.append(spawn_system)

        # 5. ScoringSystem - track score and high score
        scoring_system = ScoringSystem(
            score_callback=None,  # TODO: wire to UI score update
        )
        self._systems.append(scoring_system)

        # 6. ObstacleGenerationSystem - generate obstacles with connectivity guarantees
        obstacle_generation_system = ObstacleGenerationSystem(
            max_retries=100,
            safe_zone_width=8,
            safe_zone_height=2,
            random_seed=None,  # use true randomness for gameplay
        )
        self._systems.append(obstacle_generation_system)

        # 7. SettingsApplySystem - apply runtime settings changes
        # TODO: implement SettingsApplySystem and wire it here
        # settings_apply_system = SettingsApplySystem(...)
        # self._systems.append(settings_apply_system)

        # 8. ValidationSystem - debug validation (can be disabled in production)
        validation_system = ValidationSystem(
            enabled=True,  # TODO: make configurable via debug flag
            expected_apple_count=1,  # TODO: read from settings
            log_level=20,  # WARNING level
        )
        self._systems.append(validation_system)

        # 9. ResizeSystem - handle window resize events
        # TODO: implement ResizeSystem and wire it here
        # resize_system = ResizeSystem(...)
        # self._systems.append(resize_system)

        # 10. InterpolationSystem - calculate smooth positions for rendering
        interpolation_system = InterpolationSystem(
            electric_walls=True,  # TODO: read from settings
        )
        self._systems.append(interpolation_system)

        # 11. AudioSystem - play sounds and music
        audio_system = AudioSystem(
            sound_assets=None,  # TODO: wire to assets.sound_assets
            music_tracks=None,  # TODO: wire to assets.music_tracks
            default_volume=0.2,
        )
        self._systems.append(audio_system)

        # 12. BoardRenderSystem - render game world (board, entities)
        if self._renderer:
            self._board_render_system = BoardRenderSystem(renderer=self._renderer)
            self._systems.append(self._board_render_system)
        else:
            self._board_render_system = None

        # 13. UISystem - render UI overlays (score, menus, etc.)
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

    def update(self, dt_ms: float) -> None:
        """Update all systems in execution order.

        This method is called every frame/tick to update the game state.

        Args:
            dt_ms: Delta time in milliseconds since last update
                   (currently unused, systems get delta time from world.clock)
        """
        if not self._attached:
            return

        # note: dt_ms is currently unused because systems get timing from world.clock
        # this will be refactored when we unify timing across all systems
        # for now, we maintain the signature for future compatibility
        _ = dt_ms  # suppress unused warning

        # check if game is over
        if self._game_over:
            # draw game over screen first
            if self._renderer:
                surface = pygame.display.get_surface()
                if surface:
                    self._draw_game_over_overlay(
                        surface.get_width(), surface.get_height()
                    )

            # then handle input
            self._handle_game_over_input()
            return

        # update all systems in order
        # note: input and rendering systems run even when paused
        for i, system in enumerate(self._systems):
            # skip game logic systems when paused
            if self._paused and i >= 1 and i <= 6:
                # skip movement, collision, spawn, scoring, obstacles, settings
                continue

            system.update(self._world)

        # draw pause overlay if paused
        if self._paused and self._board_render_system and self._renderer:
            surface = pygame.display.get_surface()
            if surface:
                self._board_render_system.draw_pause_overlay(
                    surface.get_width(), surface.get_height()
                )

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
        if self._pygame_adapter:
            self._pygame_adapter.quit()
        sys.exit()

    def _handle_pause(self) -> None:
        """Handle pause toggle."""
        self._paused = not self._paused

    def _handle_menu(self) -> None:
        """Handle menu open request."""
        from kobra import run_settings_menu

        # pause game while in menu
        was_paused = self._paused
        self._paused = True

        # create minimal state object
        class MenuState:
            def __init__(self, surface, config):
                self.width = surface.get_width()
                self.height = surface.get_height()
                self.grid_size = config.initial_grid_size
                self.arena = surface

        # get surface from pygame
        surface = pygame.display.get_surface()
        if not surface:
            return

        menu_state = MenuState(surface, self._config)

        # show settings menu
        run_settings_menu(menu_state, self._assets, self._settings)

        # apply settings immediately
        if self._settings.get("background_music"):
            pygame.mixer.music.unpause()
        else:
            pygame.mixer.music.pause()

        # restore pause state
        self._paused = was_paused

    def _handle_music_toggle(self) -> None:
        """Handle music toggle."""
        # toggle the setting
        current = self._settings.get("background_music")
        self._settings.set("background_music", not current)

        # apply immediately
        if self._settings.get("background_music"):
            pygame.mixer.music.unpause()
        else:
            pygame.mixer.music.pause()

    def _handle_palette_randomize(self) -> None:
        """Handle palette randomization."""
        # TODO: implement palette randomization
        print("Palette randomize requested (not yet implemented)")

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
                next_x = (
                    snake.position.x + snake.velocity.dx
                ) % self._world.board.width
                next_y = (
                    snake.position.y + snake.velocity.dy
                ) % self._world.board.height
                return (next_x, next_y)
        return (0, 0)

    def _get_electric_walls(self) -> bool:
        """Check if electric walls are enabled."""
        return self._settings.get("electric_walls") if self._settings else True

    def _get_grid_dimensions(self) -> tuple[int, int, int]:
        """Get grid dimensions."""
        board = self._world.board
        # return (pixel_width, pixel_height, cell_size)
        return (
            board.width * board.cell_size,
            board.height * board.cell_size,
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

        # play death sound and music
        try:
            import pygame

            pygame.mixer.Sound("assets/sound/gameover.wav").play()
            pygame.mixer.music.load("assets/sound/death_song.mp3")
            pygame.mixer.music.play(-1)  # loop death music
        except Exception:
            pass  # ignore if sound files not found

        # set game over state
        self._game_over = True
        self._death_reason = reason

        print(f"GAME OVER: {reason}")

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

        # play apple eating sound
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

        # remove eaten apple
        if apple_entity:
            self._world.registry.remove(apple_entity)

        # spawn new apple
        from src.ecs.prefabs.apple import create_apple

        grid_size = self._world.board.cell_size

        # simple spawn at random position
        new_x = random.randint(0, self._world.board.width - 1)
        new_y = random.randint(0, self._world.board.height - 1)
        create_apple(self._world, x=new_x, y=new_y, grid_size=grid_size)

    def _handle_speed_increase(self, new_speed: float) -> None:
        """Handle speed increase when apple is eaten."""
        from src.ecs.entities.entity import EntityType

        snakes = self._world.registry.query_by_type(EntityType.SNAKE)
        for _, snake in snakes.items():
            if hasattr(snake, "velocity"):
                snake.velocity.speed = new_speed
                break

    def _draw_game_over_overlay(self, surface_width: int, surface_height: int) -> None:
        """Draw game over screen overlay (exactly like old code).

        Args:
            surface_width: Width of the surface
            surface_height: Height of the surface
        """
        # old code: state.arena.fill(ARENA_COLOR) - no overlay, just background
        # the background is already filled by BoardRenderSystem with ARENA_COLOR

        # add game over text (exactly like old code)
        try:
            # calculate font sizes (adjusted for better fit)
            big_font_size = int(surface_width / 8)
            small_font_size = int(surface_width / 25)  # smaller for better fit

            # create fonts with same font file as old code
            font_path = "assets/font/GetVoIP-Grotesque.ttf"

            try:
                big_font = pygame.font.Font(font_path, big_font_size)
                small_font = pygame.font.Font(font_path, small_font_size)
            except Exception:
                big_font = pygame.font.Font(None, big_font_size)
                small_font = pygame.font.Font(None, small_font_size)

            # MESSAGE_COLOR from old code: "#808080" (gray)
            message_color = (128, 128, 128)  # #808080

            # "Game Over" text (exactly like old code)
            # old code: center=(state.width / 2, state.height / 2.6)
            game_over_text = big_font.render("Game Over", True, message_color)
            game_over_rect = game_over_text.get_rect(
                center=(surface_width // 2, surface_height / 2.6)
            )

            # "Press Enter/Space to restart • Q to exit" text (exactly like old code)
            # old code: center=(state.width / 2, state.height / 1.8)
            restart_text = small_font.render(
                "Press Enter/Space to restart  •  Q to exit", True, message_color
            )
            restart_rect = restart_text.get_rect(
                center=(surface_width // 2, surface_height / 1.8)
            )

            # blit text to main surface
            self._renderer.blit(game_over_text, game_over_rect)
            self._renderer.blit(restart_text, restart_rect)

        except Exception:
            # if font loading fails, just show background
            pass

    def _handle_game_over_input(self) -> None:
        """Handle input during game over screen (exactly like old code)."""
        if not self._pygame_adapter:
            return

        # check for key presses (same controls as old code)
        keys = pygame.key.get_pressed()

        # Enter or Space - restart game (like old code)
        if keys[pygame.K_RETURN] or keys[pygame.K_SPACE]:
            self._restart_game()

        # Q key - exit game (like old code)
        if keys[pygame.K_q]:
            self._exit_game()

    def _restart_game(self) -> None:
        """Restart the game."""
        # reset game state
        self._game_over = False
        self._death_reason = ""

        # reset snake
        from src.ecs.entities.entity import EntityType

        snakes = self._world.registry.query_by_type(EntityType.SNAKE)
        for _, snake in snakes.items():
            if hasattr(snake, "body"):
                snake.body.alive = True
                snake.body.size = 3  # reset to initial size
            if hasattr(snake, "position"):
                # reset to center
                snake.position.x = self._world.board.width // 2
                snake.position.y = self._world.board.height // 2
            if hasattr(snake, "velocity"):
                snake.velocity.dx = 1
                snake.velocity.dy = 0
                snake.velocity.speed = 4.0

        # clear all apples and obstacles
        apples = self._world.registry.query_by_type(EntityType.APPLE)
        for apple_id in list(apples.keys()):
            self._world.registry.remove(apple_id)

        obstacles = self._world.registry.query_by_type(EntityType.OBSTACLE)
        for obstacle_id in list(obstacles.keys()):
            self._world.registry.remove(obstacle_id)

        # spawn new apple
        from src.ecs.prefabs.apple import create_apple
        import random

        grid_size = self._world.board.cell_size
        new_x = random.randint(0, self._world.board.width - 1)
        new_y = random.randint(0, self._world.board.height - 1)
        create_apple(self._world, x=new_x, y=new_y, grid_size=grid_size)

        # restore background music
        try:
            import pygame

            pygame.mixer.music.load("assets/sound/BoxCat_Games_CPU_Talk.ogg")
            pygame.mixer.music.play(-1)  # loop background music
        except Exception:
            pass  # ignore if music file not found

        print("Game restarted!")

    def _exit_game(self) -> None:
        """Exit the game."""
        if self._pygame_adapter:
            self._pygame_adapter.quit()
        sys.exit()
