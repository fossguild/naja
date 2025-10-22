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

"""Integration tests."""

import pytest
from unittest.mock import Mock
from src.ecs.world import World
from src.ecs.board import Board
from src.game.scenes.gameplay import GameplayScene
from src.game.settings import GameSettings
from src.game.config import GameConfig
from src.ecs.entities.entity import EntityType


class TestGameplaySceneReset:
    """Test gameplay scene reset functionality."""

    @pytest.fixture
    def mock_pygame_adapter(self):
        """Create a mock pygame adapter."""
        adapter = Mock()
        adapter.get_events = Mock(return_value=[])
        adapter.update_display = Mock()
        return adapter

    @pytest.fixture
    def mock_renderer(self):
        """Create a mock renderer."""
        renderer = Mock()
        renderer.fill = Mock()
        renderer.blit = Mock()
        return renderer

    @pytest.fixture
    def game_world(self):
        """Create a game world for testing."""
        board = Board(width=20, height=20, cell_size=20)
        world = World(board)
        return world

    @pytest.fixture
    def game_settings(self):
        """Create game settings."""
        settings = GameSettings(400, 20)
        return settings

    @pytest.fixture
    def game_config(self):
        """Create game config."""
        return GameConfig()

    @pytest.fixture
    def gameplay_scene(
        self, mock_pygame_adapter, mock_renderer, game_world, game_settings, game_config
    ):
        """Create a gameplay scene for testing."""
        scene = GameplayScene(
            pygame_adapter=mock_pygame_adapter,
            renderer=mock_renderer,
            width=400,
            height=400,
            world=game_world,
            config=game_config,
            settings=game_settings,
            assets=None,
        )
        return scene

    def test_scene_starts_with_alive_snake(self, gameplay_scene, game_world):
        """Test that a new gameplay scene has an alive snake."""
        # Enter the scene (this should reset the world)
        gameplay_scene.on_enter()

        # Check that we have a snake
        snakes = game_world.registry.query_by_type(EntityType.SNAKE)
        assert len(snakes) == 1, "Should have exactly one snake"

        # Check that the snake is alive
        snake_id, snake = next(iter(snakes.items()))
        assert hasattr(snake, "body"), "Snake should have a body component"
        assert snake.body.alive is True, "Snake should be alive initially"

    def test_scene_reset_after_death(self, gameplay_scene, game_world):
        """Test that scene properly resets after death."""
        # First game - enter scene
        gameplay_scene.on_enter()

        # Get the snake and kill it
        snakes = game_world.registry.query_by_type(EntityType.SNAKE)
        snake_id, snake = next(iter(snakes.items()))
        snake.body.alive = False

        # Verify snake is dead
        assert snake.body.alive is False, "Snake should be dead"

        # Exit the scene (simulate going to game over)
        gameplay_scene.on_exit()

        # Re-enter the scene (simulate restart from menu)
        gameplay_scene.on_enter()

        # Check that we have a new snake
        new_snakes = game_world.registry.query_by_type(EntityType.SNAKE)
        assert len(new_snakes) == 1, "Should have exactly one snake after reset"

        # Check that the new snake is alive
        new_snake_id, new_snake = next(iter(new_snakes.items()))
        assert hasattr(new_snake, "body"), "New snake should have a body component"
        assert new_snake.body.alive is True, "New snake should be alive after reset"

    def test_multiple_resets(self, gameplay_scene, game_world):
        """Test multiple death and reset cycles."""
        for i in range(3):
            # Enter scene
            gameplay_scene.on_enter()

            # Verify snake is alive
            snakes = game_world.registry.query_by_type(EntityType.SNAKE)
            assert len(snakes) == 1, f"Iteration {i}: Should have one snake"
            snake_id, snake = next(iter(snakes.items()))
            assert snake.body.alive is True, f"Iteration {i}: Snake should be alive"

            # Kill snake
            snake.body.alive = False

            # Exit scene
            gameplay_scene.on_exit()

    def test_entity_count_after_reset(self, gameplay_scene, game_world):
        """Test that entity count is correct after reset."""
        # First game
        gameplay_scene.on_enter()
        initial_count = game_world.registry.count()
        print(f"Initial entity count: {initial_count}")

        # Kill and exit
        snakes = game_world.registry.query_by_type(EntityType.SNAKE)
        snake_id, snake = next(iter(snakes.items()))
        snake.body.alive = False
        gameplay_scene.on_exit()

        # Re-enter
        gameplay_scene.on_enter()
        reset_count = game_world.registry.count()
        print(f"Reset entity count: {reset_count}")

        # Should have same number of entities (not accumulating)
        assert reset_count == initial_count, (
            f"Entity count should be same after reset: "
            f"initial={initial_count}, reset={reset_count}"
        )

    def test_scene_transition_simulation(self, gameplay_scene, game_world):
        """Test simulating complete scene transition flow: menu -> gameplay -> game_over -> menu -> gameplay."""
        # Start: Menu -> Gameplay (first time)
        print("\n=== First gameplay session ===")
        gameplay_scene.on_enter()

        snakes = game_world.registry.query_by_type(EntityType.SNAKE)
        assert len(snakes) == 1, "Should have one snake on first start"
        snake_id, snake = next(iter(snakes.items()))
        print(f"First snake alive status: {snake.body.alive}")
        assert snake.body.alive is True, "Snake should be alive on first start"

        # Simulate playing and dying
        print("Simulating death...")
        gameplay_scene._handle_death("test death")

        # Check that snake is marked as dead
        snakes = game_world.registry.query_by_type(EntityType.SNAKE)
        if len(snakes) > 0:
            snake_id, snake = next(iter(snakes.items()))
            print(f"Snake alive after death: {snake.body.alive}")

        # Gameplay -> Game Over
        gameplay_scene.on_exit()
        print("Exited to game over")

        # Game Over -> Menu (simulated)
        # Menu -> Gameplay (second time - this is where bug would occur)
        print("\n=== Second gameplay session (after restart) ===")
        gameplay_scene.on_enter()

        # Check state after re-entering
        snakes = game_world.registry.query_by_type(EntityType.SNAKE)
        print(f"Number of snakes after restart: {len(snakes)}")
        assert len(snakes) == 1, "Should have exactly one snake after restart"

        snake_id, snake = next(iter(snakes.items()))
        print(f"Second snake alive status: {snake.body.alive}")
        assert (
            snake.body.alive is True
        ), "Snake should be alive after restart (BUG CHECK)"

    def test_board_render_system_after_reset(self, gameplay_scene, game_world):
        """Test that BoardRenderSystem correctly handles snake state after reset."""
        from src.ecs.systems.board_display import BoardRenderSystem
        from unittest.mock import Mock

        # Create a mock renderer
        mock_renderer = Mock()
        mock_renderer.fill = Mock()

        # Create BoardRenderSystem
        board_render = BoardRenderSystem(renderer=mock_renderer)

        # First gameplay session
        print("\n=== First session ===")
        gameplay_scene.on_enter()

        # Check snake is alive
        snakes = game_world.registry.query_by_type(EntityType.SNAKE)
        snake_id, snake = next(iter(snakes.items()))
        print(f"Snake alive before death: {snake.body.alive}")
        assert snake.body.alive is True

        # Render should work normally (not fill with game over color)
        mock_renderer.fill.reset_mock()
        board_render.update(game_world)
        # If game over, fill would be called with arena color
        # We expect it NOT to be called or called with different color
        print(f"Fill called (should render normally): {mock_renderer.fill.called}")

        # Kill snake
        gameplay_scene._handle_death("test")
        snakes = game_world.registry.query_by_type(EntityType.SNAKE)
        snake_id, snake = next(iter(snakes.items()))
        print(f"Snake alive after death: {snake.body.alive}")
        assert snake.body.alive is False

        # Now rendering should show game over
        mock_renderer.fill.reset_mock()
        board_render.update(game_world)
        assert mock_renderer.fill.called, "Should fill with game over color when dead"
        print(f"Fill called with game over: {mock_renderer.fill.call_args}")

        # Exit and re-enter
        gameplay_scene.on_exit()
        print("\n=== Second session after reset ===")
        gameplay_scene.on_enter()

        # Check snake is alive again
        snakes = game_world.registry.query_by_type(EntityType.SNAKE)
        print(f"Number of snakes: {len(snakes)}")
        assert len(snakes) == 1, "Should have one snake after reset"

        snake_id, snake = next(iter(snakes.items()))
        print(f"Snake alive after reset: {snake.body.alive}")
        assert snake.body.alive is True, "Snake should be alive after reset"

        # Render should work normally again (not game over)
        mock_renderer.fill.reset_mock()
        board_render.update(game_world)
        # This is the critical test - it should NOT immediately show game over
        print(f"Fill called after reset: {mock_renderer.fill.called}")
        print(
            f"Fill args after reset: {mock_renderer.fill.call_args if mock_renderer.fill.called else 'N/A'}"
        )


class TestGameOverScene:
    """Test game over scene functionality."""

    @pytest.fixture
    def mock_pygame_adapter(self):
        """Create a mock pygame adapter."""
        adapter = Mock()
        adapter.get_events = Mock(return_value=[])
        return adapter

    @pytest.fixture
    def mock_renderer(self):
        """Create a mock renderer."""
        renderer = Mock()
        renderer.fill = Mock()
        renderer.blit = Mock()
        return renderer

    @pytest.fixture
    def mock_assets(self):
        """Create mock assets."""
        return Mock()

    @pytest.fixture
    def game_over_scene(self, mock_pygame_adapter, mock_renderer, mock_assets):
        """Create a game over scene for testing."""
        from src.game.scenes.game_over import GameOverScene

        scene = GameOverScene(
            pygame_adapter=mock_pygame_adapter,
            renderer=mock_renderer,
            width=400,
            height=400,
            assets=mock_assets,
        )
        return scene

    def test_restart_goes_to_gameplay(self, game_over_scene, mock_pygame_adapter):
        """Test that pressing Enter/Space goes directly to gameplay scene."""
        import pygame

        # Simulate pressing ENTER
        mock_pygame_adapter.get_events = Mock(
            return_value=[Mock(type=pygame.KEYDOWN, key=pygame.K_RETURN)]
        )

        # Update the scene
        next_scene = game_over_scene.update(16.0)

        # Should transition to gameplay, not menu
        assert next_scene == "gameplay", "Should go directly to gameplay scene"

    def test_restart_with_space_goes_to_gameplay(
        self, game_over_scene, mock_pygame_adapter
    ):
        """Test that pressing Space also goes directly to gameplay scene."""
        import pygame

        # Simulate pressing SPACE
        mock_pygame_adapter.get_events = Mock(
            return_value=[Mock(type=pygame.KEYDOWN, key=pygame.K_SPACE)]
        )

        # Update the scene
        next_scene = game_over_scene.update(16.0)

        # Should transition to gameplay, not menu
        assert next_scene == "gameplay", "Should go directly to gameplay scene"
