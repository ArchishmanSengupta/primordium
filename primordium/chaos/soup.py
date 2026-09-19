"""CHAOS: The soup environment.

This module contains the Soup class that manages the collection
of programs (scrolls) and their interactions.
"""

from __future__ import annotations

import logging
from typing import Iterator, Optional, Tuple

import numpy as np

from primordium.chaos.scroll import Scroll

logger = logging.getLogger(__name__)


class Soup:
    """The soup environment containing all scrolls.

    Manages:
    - Initialization of scrolls
    - Selection of pairs for interaction
    - Running interactions via APEIRON
    - Checkpointing
    """

    def __init__(
        self,
        size: int = 256,
        tape_length: int = 48,
        seed: Optional[int] = None,
        mutation_rate: float = 0.0,
    ):
        """Initialize the soup.

        Args:
            size: Number of scrolls in the soup
            tape_length: Length of each scroll's tape
            seed: Random seed for reproducibility
            mutation_rate: Per-byte probability of random background mutation
        """
        self.size = size
        self.tape_length = tape_length
        self.mutation_rate = mutation_rate

        # Initialize random state
        if seed is not None:
            self.rng = np.random.RandomState(seed)
        else:
            self.rng = np.random.RandomState()

        # Create scrolls
        self.scrolls: list[Scroll] = []
        for i in range(size):
            scroll_seed = None if seed is None else seed + i
            scroll = Scroll(tape_length=tape_length, seed=scroll_seed)
            self.scrolls.append(scroll)

    def select_pair(self) -> Tuple[int, int]:
        """Select two distinct scroll indices for interaction.

        Returns:
            Tuple of (i, j) with i != j
        """
        i = self.rng.randint(0, self.size)
        j = self.rng.randint(0, self.size)
        while j == i:
            j = self.rng.randint(0, self.size)
        return i, j

    def interact(self, max_steps: int = 350) -> int:
        """Run a single interaction between two scrolls (APEIRON rule).

        1. Select two scrolls i and j at random
        2. Concatenate them: combined = scroll_i + scroll_j
        3. Run the BrainFuck interpreter
        4. Split back at midpoint
        5. Write both back to soup

        Args:
            max_steps: Maximum steps per interaction

        Returns:
            Number of steps executed
        """
        from primordium.aether.interpreter import run_bf

        i, j = self.select_pair()
        scroll_i = self.scrolls[i]
        scroll_j = self.scrolls[j]

        new_i, new_j, steps = run_bf(
            scroll_i.tape,
            scroll_j.tape,
            max_steps=max_steps,
            tape_length=self.tape_length,
        )

        orig_i = scroll_i.tape.tobytes()
        orig_j = scroll_j.tape.tobytes()
        new_i_bytes = new_i.tobytes()
        new_j_bytes = new_j.tobytes()

        if orig_i in new_j_bytes:
            scroll_i.increment_copy_count()
        if orig_j in new_i_bytes:
            scroll_j.increment_copy_count()

        if self.mutation_rate > 0.0:
            new_i = self._mutate_tape(new_i)
            new_j = self._mutate_tape(new_j)

        self.scrolls[i].tape = new_i
        self.scrolls[j].tape = new_j

        return steps

    def _mutate_tape(self, tape: np.ndarray) -> np.ndarray:
        """Apply random background mutation to a tape.

        Each byte is replaced with a uniformly random byte with
        probability ``mutation_rate`` (arXiv:2406.19108 background
        mutations; arXiv:2607.01483 studies this operator directly).

        Args:
            tape: The tape to mutate (modified in place)

        Returns:
            The mutated tape
        """
        mask = self.rng.random_sample(len(tape)) < self.mutation_rate
        n = int(mask.sum())
        if n:
            tape[mask] = self.rng.randint(0, 256, size=n).astype(np.uint8)
        return tape

    def instruction_density(self) -> float:
        """Calculate the fraction of valid instructions in the soup.

        Returns:
            Fraction of tape bytes that are valid BF instructions
        """
        from primordium.aether.interpreter import VALID_OPS

        total_bytes = self.size * self.tape_length
        valid_count = 0

        for scroll in self.scrolls:
            for byte in scroll.tape:
                if byte in VALID_OPS:
                    valid_count += 1

        return valid_count / total_bytes

    def total_bytes(self) -> int:
        """Total number of bytes in the soup.

        Returns:
            size * tape_length
        """
        return self.size * self.tape_length

    def to_array(self) -> np.ndarray:
        """Convert soup to numpy array.

        Returns:
            Array of shape (size, tape_length)
        """
        result = np.zeros((self.size, self.tape_length), dtype=np.uint8)
        for i, scroll in enumerate(self.scrolls):
            result[i] = scroll.tape
        return result

    def get_scroll(self, index: int) -> Scroll:
        """Get scroll by index.

        Args:
            index: Scroll index

        Returns:
            The scroll at that index
        """
        return self.scrolls[index]

    def __iter__(self) -> Iterator[Scroll]:
        """Iterate over all scrolls."""
        return iter(self.scrolls)

    def save(self, path: str) -> None:
        """Save soup to file.

        Args:
            path: Path to save to
        """
        data = {
            'scrolls': self.to_array(),
            'size': self.size,
            'tape_length': self.tape_length,
            'ids': np.array([s.id for s in self.scrolls]),
            'generations': np.array([s.generation for s in self.scrolls]),
            'parent_ids': np.array([s.parent_id if s.parent_id else '' for s in self.scrolls]),
            'copy_counts': np.array([s.copy_count for s in self.scrolls]),
            'fitness': np.array([s.fitness for s in self.scrolls]),
        }
        np.savez(path, **data)

    @classmethod
    def load(cls, path: str) -> Soup:
        """Load soup from file.

        Args:
            path: Path to load from

        Returns:
            Loaded soup
        """
        data = np.load(path, allow_pickle=True)
        size = int(data['size'])
        tape_length = int(data['tape_length'])

        # Create soup (scrolls will be replaced)
        soup = cls(size=size, tape_length=tape_length, seed=None)

        # Load scroll data
        tapes = data['scrolls']
        ids = data['ids']
        generations = data['generations']
        parent_ids = data['parent_ids']
        copy_counts = data['copy_counts']
        fitness = data['fitness']

        for i in range(size):
            soup.scrolls[i].tape = tapes[i].astype(np.uint8)
            soup.scrolls[i].id = str(ids[i])
            soup.scrolls[i].generation = int(generations[i])
            parent_id = str(parent_ids[i])
            soup.scrolls[i].parent_id = parent_id if parent_id else None
            soup.scrolls[i].copy_count = int(copy_counts[i])
            soup.scrolls[i].fitness = float(fitness[i])

        return soup
