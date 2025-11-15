from dataclasses import dataclass, field
from typing import List, Tuple


@dataclass
class InputBuffer:
    """Buffered directions for an entity (snake). Each entry is (dx, dy)."""

    moves: List[Tuple[int, int]] = field(default_factory=list)
    max_len: int = 2  # maximum number of buffered moves
