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

from src.game.scenes.base_scene import BaseScene
from src.game.services.game_initializer import GameInitializer
from src.game.services.audio_service import AudioService
from src.game.services.sfx_queue_service import SfxQueueService
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
from src.ecs.systems.overlay_render import OverlayRenderSystem
from src.ecs.systems.obstacle_generation import ObstacleGenerationSystem
from src.ecs.systems.settings_apply import SettingsApplySystem


class GameplayScene(BaseScene):
    """Gameplay scene that coordinates all ECS systems.

    Registers and updates systems in proper execution order.
    Systems 0-7 are game logic (paused during pause).
    Systems 8+ are rendering/audio (always run).
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
        self._overlay_render_system: Optional[OverlayRenderSystem] = None
        self._game_initializer = GameInitializer(settings=settings)
        self._audio_service = AudioService(settings=settings)
        self._sfx_queue_service = SfxQueueService()

    def on_attach(self) -> None:
        """Initialize and register all game systems in execution order.

        Systems 0-7 are game logic (paused when game is paused).
        Systems 8+ are rendering/audio (always run).
        """
        if self._attached:
            return

        self._systems.clear()

        # game logic systems (indices 0-7, paused during pause)
        from src.ecs.systems.apple_spawn import AppleSpawnSystem
        from src.ecs.systems.fruit_spawn import FruitSpawnSystem

        # determine which spawn system to use based on game mode
        game_mode = self._get_game_mode()
        from src.ecs.components.game_mode import GameModeType

        if game_mode == GameModeType.MORE_FRUITS:
            spawn_system = FruitSpawnSystem(
                1000
            )  # multi-fruit spawn with probabilities
        else:
            spawn_system = AppleSpawnSystem(1000)  # classic apple-only spawn

        self._systems.extend(
            [
                InputSystem(
                    self._pygame_adapter, self._settings
                ),  # 0: read user input and update velocity/game state
                MovementSystem(
                    self._get_electric_walls
                ),  # 1: update entity positions based on velocity
                CollisionSystem(
                    self._settings, self._audio_service
                ),  # 2: detect collisions (wall, self-bite, obstacles, apples)
                spawn_system,  # 3: maintain correct number of fruits/apples on board
                SpawnSystem(
                    1000, (255, 0, 0), None
                ),  # 4: create new entities at valid positions
                ScoringSystem(),  # 5: track score and high score
                ObstacleGenerationSystem(
                    100, 8, 2, None
                ),  # 6: generate obstacles with connectivity guarantees
                SettingsApplySystem(
                    self._settings, self._config, self._assets
                ),  # 7: apply runtime settings changes (colors, difficulty, etc)
            ]
        )

        # rendering and audio systems (indices 8+, always run even when paused)
        self._systems.extend(
            [
                InterpolationSystem(
                    self._get_electric_walls(), self._get_electric_walls
                ),  # 8: calculate smooth positions for rendering
                AudioSystem(
                    self._sfx_queue_service, None, None, 0.2
                ),  # 9: play sounds and music
            ]
        )

        # render systems (10-13: draw board, entities, snake, UI)
        if self._renderer:
            self._board_render_system = BoardRenderSystem(self._renderer)
            self._entity_render_system = EntityRenderSystem(self._renderer)
            self._snake_render_system = SnakeRenderSystem(self._renderer)
            self._ui_render_system = UIRenderSystem(self._renderer, self._settings)
            self._overlay_render_system = OverlayRenderSystem(
                self._renderer, self._settings, self._config
            )
            self._systems.extend(
                [
                    self._board_render_system,
                    self._entity_render_system,
                    self._snake_render_system,
                    self._ui_render_system,
                ]
            )

        self._attached = True

    def on_detach(self) -> None:
        """Clean up systems when scene becomes inactive."""
        if self._attached:
            self._systems.clear()
            self._attached = False

    def update(self, dt_ms: float) -> Optional[str]:
        """Update all systems in execution order.

        Args:
            dt_ms: Delta time in milliseconds since last update

        Returns:
            Next scene name or None to stay in current scene
        """
        if not self._attached:
            return None

        self._world.set_dt_ms(dt_ms)

        # check if game is paused from GameState component
        game_state = self._get_game_state()
        is_paused = game_state.paused if game_state else False

        # pause game logic systems (1-7) but keep input (0) and rendering (8+) running
        GAME_LOGIC_START = 1
        GAME_LOGIC_END = 7

        for i, system in enumerate(self._systems):
            # skip game logic when paused (movement, collision, spawning, etc.)
            if is_paused and GAME_LOGIC_START <= i <= GAME_LOGIC_END:
                continue
            system.update(self._world)

        # draw settings overlay if settings menu is open
        if game_state and game_state.settings_menu_open and self._overlay_render_system:
            self._overlay_render_system.draw_settings_overlay(
                self._renderer.width,
                self._renderer.height,
                game_state.settings_selected_index,
            )
        # draw pause overlay on top of frozen game (if not showing settings)
        elif is_paused and self._overlay_render_system:
            self._overlay_render_system.draw_pause_overlay(
                self._renderer.width, self._renderer.height
            )

        # handle scene transitions from GameState.next_scene
        if game_state and game_state.next_scene:
            next_scene = game_state.next_scene
            game_state.next_scene = None
            return next_scene

        return None

    def on_enter(self) -> None:
        """Called when entering gameplay scene."""
        self.set_next_scene(None)
        self._game_initializer.reset_world(self._world)
        self._audio_service.play_music("assets/sound/BoxCat_Games_CPU_Talk.ogg")
        self.on_attach()

    def on_exit(self) -> None:
        """Called when exiting gameplay scene."""
        self.on_detach()

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

    def _get_game_state(self):
        """Get GameState component from world."""
        game_state_entities = self._world.registry.query_by_component("game_state")
        if game_state_entities:
            entity = next(iter(game_state_entities.values()))
            if hasattr(entity, "game_state"):
                return entity.game_state
        return None

    def _get_electric_walls(self) -> bool:
        """Get electric walls setting for MovementSystem."""
        return self._settings.get("electric_walls") if self._settings else True

    def _get_game_mode(self):
        """Get selected game mode from game state or default to classic.

        Returns:
            GameModeType enum value
        """
        from src.ecs.components.game_mode import GameModeType
        from src.game.scenes.game_modes import get_selected_game_mode

        # query for game mode component
        game_mode_entities = self._world.registry.query_by_component("game_mode")
        if game_mode_entities:
            entity = next(iter(game_mode_entities.values()))
            if hasattr(entity, "game_mode"):
                return entity.game_mode.mode

        # fallback to module-level selection
        try:
            return get_selected_game_mode()
        except Exception:
            pass

        # default to classic mode
        return GameModeType.CLASSIC
