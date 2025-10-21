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
        # note: callbacks will be wired when integrating with old code
        input_system = InputSystem(
            pygame_adapter=self._pygame_adapter,
            direction_callback=None,  # TODO: wire to snake velocity update
            get_current_direction_callback=None,  # TODO: wire to snake velocity query
            quit_callback=None,  # TODO: wire to app quit
            pause_callback=None,  # TODO: wire to pause flag toggle
            menu_callback=None,  # TODO: wire to menu open
            music_toggle_callback=None,  # TODO: wire to music toggle
            palette_randomize_callback=None,  # TODO: wire to palette randomization
        )
        self._systems.append(input_system)

        # 2. MovementSystem - update entity positions based on velocity
        movement_system = MovementSystem()
        self._systems.append(movement_system)

        # 3. CollisionSystem - detect collisions and emit events
        # note: callbacks will be wired when integrating with old code
        collision_system = CollisionSystem(
            get_snake_head_position=None,  # TODO: wire to snake head query
            get_snake_tail_positions=None,  # TODO: wire to snake tail query
            get_snake_next_position=None,  # TODO: wire to snake next position
            get_electric_walls=None,  # TODO: wire to settings query
            get_grid_dimensions=None,  # TODO: wire to board dimensions
            get_current_speed=None,  # TODO: wire to snake speed query
            get_max_speed=None,  # TODO: wire to settings query
            death_callback=None,  # TODO: wire to game over handler
            apple_eaten_callback=None,  # TODO: wire to apple eaten handler
            speed_increase_callback=None,  # TODO: wire to speed increase
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
            board_render_system = BoardRenderSystem(renderer=self._renderer)
            self._systems.append(board_render_system)

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

        # update all systems in order
        for system in self._systems:
            system.update(self._world)

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
