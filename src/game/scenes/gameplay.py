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
from src.game.services.game_initializer import GameInitializer
from src.game.services.audio_service import AudioService
from src.ecs.world import World
from src.ecs.systems.base_system import BaseSystem
from src.ecs.systems.input import InputSystem
from src.ecs.systems.movement import MovementSystem
from src.ecs.systems.collision import CollisionSystem
from src.ecs.systems.spawn import SpawnSystem
from src.ecs.systems.scoring import ScoringSystem
from src.ecs.systems.audio import AudioSystem
from src.ecs.systems.interpolation import InterpolationSystem
from src.ecs.systems.board_render import BoardRenderSystem
from src.ecs.systems.snake_render import SnakeRenderSystem
from src.ecs.systems.entity_render import EntityRenderSystem
from src.ecs.systems.ui_render import UIRenderSystem
from src.ecs.systems.validation import ValidationSystem
from src.ecs.systems.obstacle_generation import ObstacleGenerationSystem
from src.ecs.systems.settings_apply import SettingsApplySystem


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
    13. BoardRenderSystem - draw board foundation (grid, background)
    14. EntityRenderSystem - draw generic entities (apples, obstacles)
    15. SnakeRenderSystem - draw snake with interpolation
    16. UIRenderSystem - draw HUD overlays (score, speed bar, music indicator)
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
        self._board_render_system: Optional[BoardRenderSystem] = None
        self._snake_render_system: Optional[SnakeRenderSystem] = None
        self._entity_render_system: Optional[EntityRenderSystem] = None
        self._ui_render_system: Optional[UIRenderSystem] = None
        self._game_initializer = GameInitializer(settings=settings)
        self._audio_service = AudioService(settings=settings)

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
            settings=self._settings,
        )
        self._systems.append(input_system)

        # 2. MovementSystem - update entity positions based on velocity
        movement_system = MovementSystem(get_electric_walls=self._get_electric_walls)
        self._systems.append(movement_system)

        # 3. CollisionSystem - detect collisions and handle game logic
        collision_system = CollisionSystem(
            settings=self._settings,
            audio_service=self._audio_service,
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
        settings_apply_system = SettingsApplySystem(
            settings=self._settings,
            config=self._config,
            assets=self._assets,
        )
        self._systems.append(settings_apply_system)

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
            electric_walls=self._get_electric_walls(),
            get_electric_walls=self._get_electric_walls,
        )
        self._systems.append(interpolation_system)

        # 12. AudioSystem - play sounds and music
        audio_system = AudioSystem(
            sound_assets=None,  # TODO: wire to assets.sound_assets
            music_tracks=None,  # TODO: wire to assets.music_tracks
            default_volume=0.2,
        )
        self._systems.append(audio_system)

        # 13. BoardRenderSystem - render board foundation (background, grid, tiles)
        if self._renderer:
            self._board_render_system = BoardRenderSystem(renderer=self._renderer)
            self._systems.append(self._board_render_system)
        else:
            self._board_render_system = None

        # 14. EntityRenderSystem - render generic entities (apples, obstacles)
        if self._renderer:
            self._entity_render_system = EntityRenderSystem(renderer=self._renderer)
            self._systems.append(self._entity_render_system)
        else:
            self._entity_render_system = None

        # 15. SnakeRenderSystem - render snake with smooth interpolation
        if self._renderer:
            self._snake_render_system = SnakeRenderSystem(renderer=self._renderer)
            self._systems.append(self._snake_render_system)
        else:
            self._snake_render_system = None

        # 16. UIRenderSystem - render UI overlays (score, speed bar, music indicator)
        if self._renderer:
            self._ui_render_system = UIRenderSystem(
                renderer=self._renderer, settings=self._settings
            )
            self._systems.append(self._ui_render_system)
        else:
            self._ui_render_system = None

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

        # get game state from world
        game_state = self._get_game_state()
        is_paused = game_state.paused if game_state else False

        # Define which systems should pause
        # Systems 1-8 are game logic (movement, collision, spawning, scoring, etc.)
        # Systems 0 (input) and 9+ (rendering, audio) always run
        GAME_LOGIC_START = 1
        GAME_LOGIC_END = 8

        # update all systems in order
        for i, system in enumerate(self._systems):
            # skip game logic systems when paused
            if is_paused and GAME_LOGIC_START <= i <= GAME_LOGIC_END:
                continue

            system.update(self._world)

        # draw pause overlay if paused
        if is_paused and self._ui_render_system and self._renderer:
            surface = pygame.display.get_surface()
            if surface:
                self._ui_render_system.draw_pause_overlay(
                    surface.get_width(), surface.get_height()
                )

        # check for scene transitions from GameState
        if game_state and game_state.next_scene:
            next_scene = game_state.next_scene
            game_state.next_scene = None  # clear the transition
            return next_scene

        return None

    def on_enter(self) -> None:
        """Called when entering gameplay scene."""
        print("Entering GameplayScene")

        # Clear any pending scene transition from previous session
        self.set_next_scene(None)

        # Reset world state for new game using GameInitializer service
        self._game_initializer.reset_world(self._world)

        # Restore background music (in case we're coming from game over)
        self._audio_service.play_music("assets/sound/BoxCat_Games_CPU_Talk.ogg")

        self.on_attach()
        print("GameplayScene attached")

    def on_exit(self) -> None:
        """Called when exiting gameplay scene."""
        print("Exiting GameplayScene")
        self.on_detach()
        print("GameplayScene detached")

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

    # Helper methods for querying world state

    def _get_game_state(self):
        """Get the GameState component from world.

        Returns:
            GameState component or None if not found
        """
        game_state_entities = self._world.registry.query_by_component("game_state")
        if game_state_entities:
            entity = next(iter(game_state_entities.values()))
            if hasattr(entity, "game_state"):
                return entity.game_state
        return None

    def _get_snake_entity(self):
        """Get the snake entity from the world.

        This helper method reduces code duplication across callbacks
        that need to access the snake entity.

        Returns:
            Snake entity or None if not found
        """
        from src.ecs.entities.entity import EntityType

        snakes = self._world.registry.query_by_type(EntityType.SNAKE)
        for _, snake in snakes.items():
            return snake
        return None

    # MovementSystem helper callback
    # This is still needed by MovementSystem for grid wrapping logic
    # TODO: Refactor MovementSystem to query settings directly

    def _get_electric_walls(self) -> bool:
        """Check if electric walls are enabled.

        Helper for MovementSystem. Returns electric walls setting.

        Returns:
            True if electric walls are enabled, False otherwise
        """
        return self._settings.get("electric_walls") if self._settings else True
