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

"""Sound effects queue service.

This service provides centralized management of sound effects queue
without relying on ECS components. It's a simple stateful service
that maintains the queue of sounds to be played by AudioSystem.
"""

from __future__ import annotations
from typing import List


class SfxQueueService:
    """Service for managing sound effects queue.
    
    This replaces the AudioQueue component, transforming what was
    misused as a global state component into a proper service.
    """

    def __init__(self):
        """Initialize SFX queue service with empty queue."""
        self._sfx_queue: List[str] = []

    def queue_sound(self, sound_name: str) -> None:
        """Add a sound effect to the queue.

        Args:
            sound_name: Name of the sound effect to queue.
        """
        self._sfx_queue.append(sound_name)

    def get_all_queued_sounds(self) -> List[str]:
        """Get all queued sounds and clear the queue.

        Returns:
            List of all queued sound names.
        """
        sounds = self._sfx_queue.copy()
        self._sfx_queue.clear()
        return sounds

    def clear_queue(self) -> None:
        """Clear all queued sounds."""
        self._sfx_queue.clear()

    def has_sounds(self) -> bool:
        """Check if there are sounds in the queue.

        Returns:
            True if queue has sounds, False otherwise.
        """
        return len(self._sfx_queue) > 0

    def get_queue_size(self) -> int:
        """Get the number of sounds in queue.

        Returns:
            Number of queued sounds.
        """
        return len(self._sfx_queue)
