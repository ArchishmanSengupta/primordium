"""Scroll: Individual program tape with metadata.

This module contains the Scroll class.
"""

from __future__ import annotations

import numpy as np
import uuid
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class Scroll:
    """A single program tape in the soup.

    Each scroll contains:
    - tape: numpy array of bytes (the program)
    - id: unique identifier
    - generation: how many replication cycles ago this was created
    - parent_id: the scroll this was copied from (if any)
    - copy_count: how many times this scroll has been copied
    - fitness: current fitness score
    """

    def __init__(
        self,
        tape: Optional[np.ndarray] = None,
        tape_length: int = 48,
        seed: Optional[int] = None,
        generation: int = 0,
        parent_id: Optional[str] = None,
    ):
        """Initialize a scroll.

        Args:
            tape: Initial tape data (if None, random initialize)
            tape_length: Length of tape if creating random
            seed: Random seed for initialization
            generation: Generation number
            parent_id: Parent scroll ID
        """
        if tape is not None:
            self.tape = tape.astype(np.uint8)
        else:
            if seed is not None:
                rng = np.random.RandomState(seed)
            else:
                rng = np.random.RandomState()
            self.tape = rng.randint(0, 256, size=tape_length, dtype=np.uint8)

        self.id = str(uuid.uuid4())
        self.generation = generation
        self.parent_id = parent_id
        self.copy_count = 0
        self.fitness = 0.0

    def copy(self) -> Scroll:
        """Create a copy of this scroll.

        Returns:
            New scroll with identical tape and updated metadata
        """
        new_tape = self.tape.copy()
        new_scroll = Scroll(
            tape=new_tape,
            generation=self.generation + 1,
            parent_id=self.id,
        )
        return new_scroll

    def increment_copy_count(self) -> None:
        """Increment the copy count."""
        self.copy_count += 1

    def __hash__(self) -> int:
        """Hash based on scroll ID."""
        return hash(self.id)

    def __eq__(self, other: object) -> bool:
        """Equality based on scroll ID."""
        if not isinstance(other, Scroll):
            return False
        return self.id == other.id
