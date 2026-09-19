"""MNEMOSYNE: Memory layer.

Adds persistent long-term memory and pattern storage to scrolls.
Named after the Greek goddess of memory - stores patterns across generations.
"""

from __future__ import annotations

from typing import Any, Dict, List
import numpy as np
from collections import deque


class PatternMemory:
    """Store and retrieve patterns from memory."""

    def __init__(self, memory_size: int = 1000, pattern_length: int = 48):
        self.memory_size = memory_size
        self.pattern_length = pattern_length
        self.patterns = deque(maxlen=memory_size)
        self.pattern_frequencies = {}

    def store_pattern(self, tape: np.ndarray, fitness: float):
        """Store a pattern in memory.

        Args:
            tape: The tape pattern to store
            fitness: Fitness score of the pattern
        """
        # Convert tape to hashable form
        pattern_hash = tuple(tape[:self.pattern_length].tolist())

        if pattern_hash in self.pattern_frequencies:
            self.pattern_frequencies[pattern_hash] += 1
        else:
            if self.patterns.maxlen is not None and len(self.patterns) == self.patterns.maxlen:
                evicted = self.patterns[0]
                self.pattern_frequencies.pop(evicted['hash'], None)
            self.pattern_frequencies[pattern_hash] = 1
            self.patterns.append({
                'tape': tape.copy(),
                'fitness': fitness,
                'hash': pattern_hash,
            })

    def retrieve_similar(self, tape: np.ndarray, top_k: int = 5) -> List[Dict]:
        """Retrieve similar patterns from memory.

        Args:
            tape: Reference tape
            top_k: Number of patterns to retrieve

        Returns:
            List of similar patterns
        """
        if not self.patterns:
            return []

        # Compute similarity to each stored pattern
        similarities = []
        for p in self.patterns:
            # Simple Hamming similarity
            diff = np.sum(p['tape'][:self.pattern_length] != tape[:self.pattern_length])
            similarity = 1.0 - (diff / self.pattern_length)
            similarities.append((similarity, p))

        # Sort by similarity and return top k
        similarities.sort(reverse=True, key=lambda x: x[0])
        return [p for _, p in similarities[:top_k]]

    def get_most_frequent(self, top_k: int = 10) -> List[Dict]:
        """Get most frequently stored patterns."""
        sorted_patterns = sorted(
            self.pattern_frequencies.items(),
            key=lambda x: x[1],
            reverse=True
        )
        results = []
        for hash_val, freq in sorted_patterns[:top_k]:
            for p in self.patterns:
                if p['hash'] == hash_val:
                    results.append({**p, 'frequency': freq})
                    break
        return results


class LongTermMemory:
    """Cross-generational memory storage."""

    def __init__(self, max_size: int = 10000):
        self.max_size = max_size
        self.best_patterns = deque(maxlen=max_size)
        self.epoch_best = {}

    def store_best(self, epoch: int, tape: np.ndarray, fitness: float):
        """Store best pattern from an epoch.

        Args:
            epoch: Epoch number
            tape: Best tape from epoch
            fitness: Fitness of best tape
        """
        self.epoch_best[epoch] = {
            'tape': tape.copy(),
            'fitness': fitness,
        }

        entry = {
            'epoch': epoch,
            'tape': tape.copy(),
            'fitness': fitness,
        }

        if len(self.best_patterns) < self.max_size:
            self.best_patterns.append(entry)
            return

        worst = min(self.best_patterns, key=lambda p: p.get('fitness', 0.0))
        if fitness > worst.get('fitness', 0.0):
            self.best_patterns.remove(worst)
            self.best_patterns.append(entry)

    def get_best_overall(self, top_k: int = 10) -> List[Dict]:
        """Get top k best patterns overall."""
        sorted_best = sorted(
            self.best_patterns,
            key=lambda x: x.get('fitness', 0),
            reverse=True
        )
        return sorted_best[:top_k]


class MnemosyneLayer:
    """MNEMOSYNE layer for long-term memory.

    Adds:
    - Pattern memory for each scroll
    - Cross-generational memory
    - Pattern retrieval and similarity matching
    """

    def __init__(self, config: Dict[str, Any]):
        self.enabled = config.get('enabled', True)

        # Memory settings
        self.memory_size = config.get('memory_size', 1000)
        self.pattern_length = config.get('pattern_length', 48)
        self.long_term_size = config.get('long_term_size', 10000)

        # Pattern storage settings
        self.store_frequency = config.get('store_frequency', 100)  # Store every N interactions
        self.retrieve_enabled = config.get('retrieve_enabled', True)

        # Initialize memory systems
        self.pattern_memory = PatternMemory(
            self.memory_size, self.pattern_length
        )
        self.long_term_memory = LongTermMemory(self.long_term_size)

        self.interaction_count = 0

    def after_interaction(self, soup, i: int, j: int, steps: int) -> None:
        """After interaction, store patterns in memory."""
        if not self.enabled:
            return

        self.interaction_count += 1

        # Periodically store patterns
        if self.interaction_count % self.store_frequency == 0:
            scroll_i = soup.scrolls[i]
            scroll_j = soup.scrolls[j]

            # Store both scrolls if they have good fitness
            if scroll_i.fitness > 0.3:
                self.pattern_memory.store_pattern(scroll_i.tape, scroll_i.fitness)

            if scroll_j.fitness > 0.3:
                self.pattern_memory.store_pattern(scroll_j.tape, scroll_j.fitness)

    def after_epoch(self, soup, epoch: int) -> Dict[str, Any]:
        """After epoch, update long-term memory and return stats."""
        if not self.enabled:
            return {}

        # Find best scroll from this epoch
        if soup.scrolls:
            best_scroll = max(soup.scrolls, key=lambda s: s.fitness)
            self.long_term_memory.store_best(
                epoch, best_scroll.tape, best_scroll.fitness
            )

        stats = {
            'mnemosyne_pattern_count': len(self.pattern_memory.patterns),
            'mnemosyne_unique_patterns': len(self.pattern_memory.pattern_frequencies),
            'mnemosyne_long_term_size': len(self.long_term_memory.best_patterns),
        }

        return stats

    def retrieve_patterns(self, tape: np.ndarray, top_k: int = 5) -> List[Dict]:
        """Retrieve similar patterns from memory.

        Args:
            tape: Reference tape
            top_k: Number of patterns to retrieve

        Returns:
            List of similar patterns
        """
        if not self.retrieve_enabled:
            return []
        return self.pattern_memory.retrieve_similar(tape, top_k)

    def get_best_patterns(self, top_k: int = 10) -> List[Dict]:
        """Get best patterns from long-term memory."""
        return self.long_term_memory.get_best_overall(top_k)


def create_mnemosyne(config: Dict[str, Any]) -> MnemosyneLayer:
    """Factory function to create MNEMOSYNE layer."""
    return MnemosyneLayer(config)
