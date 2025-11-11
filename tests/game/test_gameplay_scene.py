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

"""Tests for gameplay scene and system registration."""

import pytest

from src.ecs.world import World
from src.ecs.board import Board
from src.game.scenes.gameplay import GameplayScene
from src.ecs.systems.input import InputSystem
from src.ecs.systems.movement import MovementSystem
from src.ecs.systems.collision import CollisionSystem
from src.ecs.systems.spawn import SpawnSystem
from src.ecs.systems.scoring import ScoringSystem
from src.ecs.systems.audio import AudioSystem
from src.ecs.systems.interpolation import InterpolationSystem
from src.ecs.systems.board_render import BoardRenderSystem
from src.ecs.systems.obstacle_generation import ObstacleGenerationSystem


class TestGameplayScene:
    """Test suite for gameplay scene."""

    def test_scene_creation(self):
        """Test that gameplay scene can be created."""
        board = Board(20, 20)
        world = World(board)
        scene = GameplayScene(world)

        assert scene is not None
        assert scene.world is world
        assert not scene.is_attached

    def test_scene_attach(self):
        """Test that scene attaches and registers systems."""
        board = Board(20, 20)
        world = World(board)
        scene = GameplayScene(world)

        # attach scene
        scene.on_attach()

        assert scene.is_attached
        systems = scene.get_systems()
        assert len(systems) > 0

    def test_scene_detach(self):
        """Test that scene detaches and cleans up systems."""
        board = Board(20, 20)
        world = World(board)
        scene = GameplayScene(world)

        # attach then detach
        scene.on_attach()
        assert scene.is_attached

        scene.on_detach()
        assert not scene.is_attached
        assert len(scene.get_systems()) == 0

    def test_systems_registered_in_correct_order(self):
        """Test that systems are registered in the correct execution order."""
        board = Board(20, 20)
        world = World(board)

        # create mock renderer so BoardRenderSystem is registered
        mock_renderer = object()
        scene = GameplayScene(world, renderer=mock_renderer)

        scene.on_attach()
        systems = scene.get_systems()

        # verify system order matches architecture specification
        # order should be: Input, Movement, Collision, Spawn, Scoring,
        # ObstacleGeneration, Interpolation, Audio, BoardRender

        expected_types = [
            InputSystem,
            MovementSystem,
            CollisionSystem,
            SpawnSystem,
            ScoringSystem,
            ObstacleGenerationSystem,
            InterpolationSystem,
            AudioSystem,
            BoardRenderSystem,
        ]

        # check that we have at least the core systems
        # note: some systems may be commented out as TODOs

        # verify each expected system type appears in actual types
        for expected_type in expected_types:
            found = any(isinstance(system, expected_type) for system in systems)
            assert found, f"{expected_type.__name__} not found in registered systems"

        # verify order is preserved for registered systems
        indices = {}
        for i, system in enumerate(systems):
            for expected_type in expected_types:
                if isinstance(system, expected_type):
                    indices[expected_type] = i

        # verify systems appear in correct relative order
        # InputSystem should come before MovementSystem
        if InputSystem in indices and MovementSystem in indices:
            assert indices[InputSystem] < indices[MovementSystem]

        # MovementSystem should come before CollisionSystem
        if MovementSystem in indices and CollisionSystem in indices:
            assert indices[MovementSystem] < indices[CollisionSystem]

        # CollisionSystem should come before SpawnSystem
        if CollisionSystem in indices and SpawnSystem in indices:
            assert indices[CollisionSystem] < indices[SpawnSystem]

        # InterpolationSystem should come before BoardRenderSystem
        if InterpolationSystem in indices and BoardRenderSystem in indices:
            assert indices[InterpolationSystem] < indices[BoardRenderSystem]

    def test_scene_update_without_attach(self):
        """Test that update does nothing when scene is not attached."""
        board = Board(20, 20)
        world = World(board)
        scene = GameplayScene(world)

        # should not crash when updating unattached scene
        scene.update(16.0)

    def test_scene_update_with_attach(self):
        """Test that update runs when scene is attached."""
        board = Board(20, 20)
        world = World(board)
        scene = GameplayScene(world)

        scene.on_attach()

        # should not crash when updating attached scene
        scene.update(16.0)

    def test_double_attach_is_safe(self):
        """Test that calling on_attach twice is safe."""
        board = Board(20, 20)
        world = World(board)
        scene = GameplayScene(world)

        scene.on_attach()
        first_systems_count = len(scene.get_systems())

        # second attach should be no-op
        scene.on_attach()
        second_systems_count = len(scene.get_systems())

        assert first_systems_count == second_systems_count

    def test_double_detach_is_safe(self):
        """Test that calling on_detach twice is safe."""
        board = Board(20, 20)
        world = World(board)
        scene = GameplayScene(world)

        scene.on_attach()
        scene.on_detach()

        # second detach should be no-op
        scene.on_detach()
        assert not scene.is_attached

    def test_scene_with_renderer(self):
        """Test that scene registers BoardRenderSystem when renderer is provided."""
        board = Board(20, 20)
        world = World(board)

        # create mock renderer (just needs to exist for this test)
        mock_renderer = object()

        scene = GameplayScene(world, renderer=mock_renderer)
        scene.on_attach()

        systems = scene.get_systems()
        has_render_system = any(isinstance(s, BoardRenderSystem) for s in systems)

        assert has_render_system

    def test_scene_without_renderer(self):
        """Test that scene works without renderer (headless mode)."""
        board = Board(20, 20)
        world = World(board)

        scene = GameplayScene(world, renderer=None)
        scene.on_attach()

        # should still work, just without render system
        scene.update(16.0)

    def test_skip_when_paused_flags_are_correct(self):
        """Verify that each system correctly defines whether it should pause or continue when the game is paused."""
        from src.ecs.systems import (
            input,
            movement,
            collision,
            apple_spawn,
            spawn,
            scoring,
            obstacle_generation,
            settings_apply,
            interpolation,
            audio,
        )

        # Systems that SHOULD be skipped when the game is paused
        expected_skipped = [
            movement.MovementSystem,
            collision.CollisionSystem,
            apple_spawn.AppleSpawnSystem,
            spawn.SpawnSystem,
            scoring.ScoringSystem,
            obstacle_generation.ObstacleGenerationSystem,
            settings_apply.SettingsApplySystem,
        ]

        # Systems that SHOULD NOT be skipped
        expected_not_skipped = [
            input.InputSystem,
            interpolation.InterpolationSystem,
            audio.AudioSystem,
        ]

        # Check that all paused systems are correctly marked
        for system_cls in expected_skipped:
            assert getattr(
                system_cls, "skip_when_paused", False
            ), "System should have skip_when_paused=True"

        # Check that non-paused systems remain active
        for system_cls in expected_not_skipped:
            assert not getattr(
                system_cls, "skip_when_paused", False
            ), "System should NOT have skip_when_paused=True"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
