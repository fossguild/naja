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

"""Abstract Entity base class."""

from abc import ABC, abstractmethod
from enum import Enum, auto


class EntityType(Enum):
    """Types of entities in the game.
    
    Used for type-specific queries and filtering.
    """

    SNAKE = auto()
    APPLE = auto()
    OBSTACLE = auto()

class Entity(ABC):
    """Abstract base class for all game entities.
    
    All entities must implement get_type() to return their EntityType.
    Entities are composed of components (dataclass fields).
    """

    @abstractmethod
    def get_type(self) -> EntityType:
        """Get the type of this entity.
        
        Returns:
            EntityType: Type identifier for this entity
        """


