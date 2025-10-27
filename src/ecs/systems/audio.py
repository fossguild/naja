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

"""Audio system for managing sound effects and background music.

This system handles SFX queue processing and music control.
It manages pygame mixer channels for simultaneous sound effects
and respects music enabled flag from settings.

The system now uses SfxQueueService for managing the sound effects
queue instead of relying on ECS components (anti-pattern).
"""

from __future__ import annotations

from typing import Optional, Dict
import pygame

from src.ecs.systems.base_system import BaseSystem
from src.ecs.world import World
from src.game.services.sfx_queue_service import SfxQueueService


class AudioSystem(BaseSystem):
    """System for managing audio playback (SFX and music)."""

    def __init__(
        self,
        sfx_queue_service: SfxQueueService,
        sound_assets: Optional[Dict[str, pygame.mixer.Sound]] = None,
        music_tracks: Optional[Dict[str, str]] = None,
        default_volume: float = 0.2,
    ):
        self._sfx_queue_service = sfx_queue_service
        self._sound_assets = sound_assets or {}
        self._music_tracks = music_tracks or {}
        self._default_volume = default_volume

    def _get_music_state(self, world: World):
        """Get first music state entity (singleton pattern)."""
        entities = world.registry.query_by_component("enabled")
        if entities:
            entity_id = list(entities.keys())[0]
            return world.registry.get(entity_id)
        return None

    def update(self, world: World) -> None:
        """Process audio queue and update music state."""
        self._process_sfx_queue(world)

    def _process_sfx_queue(self, world: World) -> None:
        """Process and play all queued sound effects."""
        queued_sounds = self._sfx_queue_service.get_all_queued_sounds()
        for sfx_name in queued_sounds:
            self.play_sfx(sfx_name)

    def play_sfx(self, sfx_name: str) -> bool:
        """Play a sound effect."""
        if sfx_name not in self._sound_assets or not self._sound_assets[sfx_name]:
            return False
        try:
            self._sound_assets[sfx_name].play()
            return True
        except pygame.error:
            return False

    def queue_sfx(self, sfx_name: str) -> None:
        """Add sound effect to queue.
        
        Args:
            sfx_name: Name of the sound effect to queue.
        """
        self._sfx_queue_service.queue_sound(sfx_name)

    def play_music(
        self, world: World, track_name: str = "background", loop: bool = True
    ) -> bool:
        """Play background music track."""
        if track_name not in self._music_tracks:
            return False

        state = self._get_music_state(world)
        if state and hasattr(state, "enabled") and not state.enabled:
            return False

        try:
            pygame.mixer.music.load(self._music_tracks[track_name])
            pygame.mixer.music.set_volume(self._default_volume)
            pygame.mixer.music.play(-1 if loop else 0)

            if state and hasattr(state, "is_playing"):
                state.is_playing = True
                state.is_paused = False
                state.current_track = track_name
            return True
        except pygame.error:
            return False

    def pause_music(self, world: World) -> None:
        """Pause background music."""
        pygame.mixer.music.pause()
        state = self._get_music_state(world)
        if state and hasattr(state, "is_paused"):
            state.is_paused = True

    def unpause_music(self, world: World) -> None:
        """Unpause background music."""
        pygame.mixer.music.unpause()
        state = self._get_music_state(world)
        if state and hasattr(state, "is_paused"):
            state.is_paused = False

    def stop_music(self, world: World) -> None:
        """Stop background music."""
        pygame.mixer.music.stop()
        state = self._get_music_state(world)
        if state and hasattr(state, "is_playing"):
            state.is_playing = False
            state.is_paused = False

    def next_track(self, world: World, track_name: str, loop: bool = True) -> bool:
        """Switch to next music track."""
        self.stop_music(world)
        return self.play_music(world, track_name, loop)

    def set_music_enabled(self, world: World, enabled: bool) -> None:
        """Enable or disable background music."""
        state = self._get_music_state(world)
        if state and hasattr(state, "enabled"):
            state.enabled = enabled
            if enabled:
                self.unpause_music(world)
            else:
                self.pause_music(world)

    def get_music_enabled(self, world: World) -> bool:
        """Get music enabled status."""
        state = self._get_music_state(world)
        return state.enabled if state and hasattr(state, "enabled") else True

    def set_music_volume(self, volume: float) -> None:
        """Set music volume."""
        volume = max(0.0, min(1.0, volume))
        pygame.mixer.music.set_volume(volume)
        self._default_volume = volume

    def set_sfx_volume(self, sfx_name: str, volume: float) -> None:
        """Set volume for specific sound effect."""
        if sfx_name in self._sound_assets and self._sound_assets[sfx_name]:
            self._sound_assets[sfx_name].set_volume(max(0.0, min(1.0, volume)))

    def load_sound(self, sfx_name: str, file_path: str) -> bool:
        """Load sound effect from file."""
        try:
            self._sound_assets[sfx_name] = pygame.mixer.Sound(file_path)
            return True
        except pygame.error:
            return False

    def load_music_track(self, track_name: str, file_path: str) -> None:
        """Register music track."""
        self._music_tracks[track_name] = file_path

    def is_music_playing(self) -> bool:
        """Check if music is playing."""
        return pygame.mixer.music.get_busy()

    def get_available_sfx(self) -> list[str]:
        """Get list of available sound effects."""
        return list(self._sound_assets.keys())

    def get_available_tracks(self) -> list[str]:
        """Get list of available music tracks."""
        return list(self._music_tracks.keys())
