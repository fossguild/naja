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
"""

from __future__ import annotations

from typing import Optional, Dict
import pygame

from src.ecs.systems.base_system import BaseSystem
from src.ecs.world import World


class AudioSystem(BaseSystem):
    """System for managing audio playback (SFX and music).

    Reads: AudioQueue (sfx_queue), MusicState (enabled, current_track)
    Writes: AudioQueue (clears after processing), MusicState (is_playing, is_paused)
    Queries: entities with AudioQueue or MusicState components

    Responsibilities:
    - Process SFX queue and play sounds
    - Handle multiple simultaneous SFX (mixer channels)
    - Control background music (play, pause, stop, next)
    - Respect music enabled flag from settings
    - Manage volume levels
    - Clear SFX queue after processing

    Note: This system uses pygame.mixer for audio playback.
    Music and SFX are handled separately.
    """

    def __init__(
        self,
        sound_assets: Optional[Dict[str, pygame.mixer.Sound]] = None,
        music_tracks: Optional[Dict[str, str]] = None,
        default_volume: float = 0.2,
    ):
        """Initialize the AudioSystem.

        Args:
            sound_assets: Dictionary of sound name -> pygame.mixer.Sound
            music_tracks: Dictionary of track name -> file path
            default_volume: Default music volume (0.0 to 1.0)
        """
        self._sound_assets = sound_assets or {}
        self._music_tracks = music_tracks or {}
        self._default_volume = default_volume

    def update(self, world: World) -> None:
        """Process audio queue and update music state.

        This method is called every tick. It:
        - Processes SFX queue
        - Updates music playback state
        - Clears processed SFX

        Args:
            world: ECS world containing entities and components
        """
        # process SFX queue
        self._process_sfx_queue(world)

        # update music state (handled by music control methods)
        # stub - will be triggered by events/commands in future

    def _process_sfx_queue(self, world: World) -> None:
        """Process and play all queued sound effects.

        Args:
            world: ECS world
        """
        # find audio queue entities
        audio_queue_entities = world.registry.query_by_component("sfx_queue")

        for entity_id in audio_queue_entities:
            entity = world.registry.get(entity_id)

            if not hasattr(entity, "sfx_queue"):
                continue

            # process each sound in queue
            for sfx_name in entity.sfx_queue:
                self.play_sfx(sfx_name)

            # clear queue after processing
            entity.sfx_queue.clear()

    def play_sfx(self, sfx_name: str) -> bool:
        """Play a sound effect.

        Uses pygame mixer channels for simultaneous playback.

        Args:
            sfx_name: Name of sound effect to play

        Returns:
            True if sound was played, False if sound not found or error
        """
        if sfx_name not in self._sound_assets:
            return False

        sound = self._sound_assets[sfx_name]
        if sound is None:
            return False

        try:
            # pygame mixer automatically manages channels
            # allows multiple simultaneous SFX
            sound.play()
            return True
        except pygame.error:
            return False

    def queue_sfx(self, world: World, sfx_name: str) -> None:
        """Add a sound effect to the queue.

        Args:
            world: ECS world
            sfx_name: Name of sound effect to queue
        """
        # find audio queue entity
        audio_queue_entities = world.registry.query_by_component("sfx_queue")

        if not audio_queue_entities:
            return

        # get first audio queue entity (singleton pattern)
        entity_id = list(audio_queue_entities.keys())[0]
        entity = world.registry.get(entity_id)

        if hasattr(entity, "sfx_queue"):
            entity.sfx_queue.append(sfx_name)

    def play_music(
        self,
        world: World,
        track_name: str = "background",
        loop: bool = True,
    ) -> bool:
        """Play background music track.

        Args:
            world: ECS world
            track_name: Name of track to play
            loop: Whether to loop the track

        Returns:
            True if music started, False if track not found or error
        """
        if track_name not in self._music_tracks:
            return False

        track_path = self._music_tracks[track_name]

        # check if music is enabled
        music_state_entities = world.registry.query_by_component("enabled")

        if music_state_entities:
            entity_id = list(music_state_entities.keys())[0]
            entity = world.registry.get(entity_id)

            if hasattr(entity, "enabled") and not entity.enabled:
                return False

        try:
            pygame.mixer.music.load(track_path)
            pygame.mixer.music.set_volume(self._default_volume)
            pygame.mixer.music.play(-1 if loop else 0)

            # update music state
            if music_state_entities:
                entity_id = list(music_state_entities.keys())[0]
                entity = world.registry.get(entity_id)

                if hasattr(entity, "is_playing"):
                    entity.is_playing = True
                    entity.is_paused = False
                    entity.current_track = track_name

            return True
        except pygame.error:
            return False

    def pause_music(self, world: World) -> None:
        """Pause background music.

        Args:
            world: ECS world
        """
        pygame.mixer.music.pause()

        # update music state
        music_state_entities = world.registry.query_by_component("enabled")

        if music_state_entities:
            entity_id = list(music_state_entities.keys())[0]
            entity = world.registry.get(entity_id)

            if hasattr(entity, "is_paused"):
                entity.is_paused = True

    def unpause_music(self, world: World) -> None:
        """Unpause background music.

        Args:
            world: ECS world
        """
        pygame.mixer.music.unpause()

        # update music state
        music_state_entities = world.registry.query_by_component("enabled")

        if music_state_entities:
            entity_id = list(music_state_entities.keys())[0]
            entity = world.registry.get(entity_id)

            if hasattr(entity, "is_paused"):
                entity.is_paused = False

    def stop_music(self, world: World) -> None:
        """Stop background music.

        Args:
            world: ECS world
        """
        pygame.mixer.music.stop()

        # update music state
        music_state_entities = world.registry.query_by_component("enabled")

        if music_state_entities:
            entity_id = list(music_state_entities.keys())[0]
            entity = world.registry.get(entity_id)

            if hasattr(entity, "is_playing"):
                entity.is_playing = False
                entity.is_paused = False

    def next_track(self, world: World, track_name: str, loop: bool = True) -> bool:
        """Switch to next music track.

        Args:
            world: ECS world
            track_name: Name of next track
            loop: Whether to loop the track

        Returns:
            True if track switched, False if error
        """
        self.stop_music(world)
        return self.play_music(world, track_name, loop)

    def set_music_enabled(self, world: World, enabled: bool) -> None:
        """Enable or disable background music.

        Args:
            world: ECS world
            enabled: Whether to enable music
        """
        music_state_entities = world.registry.query_by_component("enabled")

        if not music_state_entities:
            return

        entity_id = list(music_state_entities.keys())[0]
        entity = world.registry.get(entity_id)

        if hasattr(entity, "enabled"):
            entity.enabled = enabled

            # pause or unpause based on flag
            if enabled:
                self.unpause_music(world)
            else:
                self.pause_music(world)

    def get_music_enabled(self, world: World) -> bool:
        """Get music enabled status.

        Args:
            world: ECS world

        Returns:
            True if music is enabled, False otherwise
        """
        music_state_entities = world.registry.query_by_component("enabled")

        if not music_state_entities:
            return True  # default to enabled

        entity_id = list(music_state_entities.keys())[0]
        entity = world.registry.get(entity_id)

        if hasattr(entity, "enabled"):
            return entity.enabled

        return True

    def set_music_volume(self, volume: float) -> None:
        """Set music volume.

        Args:
            volume: Volume level (0.0 to 1.0)
        """
        volume = max(0.0, min(1.0, volume))  # clamp to valid range
        pygame.mixer.music.set_volume(volume)
        self._default_volume = volume

    def set_sfx_volume(self, sfx_name: str, volume: float) -> None:
        """Set volume for a specific sound effect.

        Args:
            sfx_name: Name of sound effect
            volume: Volume level (0.0 to 1.0)
        """
        if sfx_name not in self._sound_assets:
            return

        sound = self._sound_assets[sfx_name]
        if sound is None:
            return

        volume = max(0.0, min(1.0, volume))  # clamp to valid range
        sound.set_volume(volume)

    def load_sound(self, sfx_name: str, file_path: str) -> bool:
        """Load a sound effect from file.

        Args:
            sfx_name: Name to identify the sound
            file_path: Path to sound file

        Returns:
            True if loaded successfully, False otherwise
        """
        try:
            sound = pygame.mixer.Sound(file_path)
            self._sound_assets[sfx_name] = sound
            return True
        except pygame.error:
            return False

    def load_music_track(self, track_name: str, file_path: str) -> None:
        """Register a music track.

        Args:
            track_name: Name to identify the track
            file_path: Path to music file
        """
        self._music_tracks[track_name] = file_path

    def is_music_playing(self) -> bool:
        """Check if music is currently playing.

        Returns:
            True if music is playing, False otherwise
        """
        return pygame.mixer.music.get_busy()

    def get_available_sfx(self) -> list[str]:
        """Get list of available sound effects.

        Returns:
            List of sound effect names
        """
        return list(self._sound_assets.keys())

    def get_available_tracks(self) -> list[str]:
        """Get list of available music tracks.

        Returns:
            List of track names
        """
        return list(self._music_tracks.keys())
