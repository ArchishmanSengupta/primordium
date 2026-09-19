"""GAIA: Ecology layer.

Adds spatial topology and ecological dynamics to the soup.
Manages carrying capacity, population dynamics, and environmental pressures.
"""

from __future__ import annotations

from typing import Any, Dict, List

import numpy as np


class SpatialGrid:
    """Spatial organization of scrolls in 2D grid."""

    def __init__(self, size: int, grid_size: int = 16):
        self.size = size  # Total number of scrolls
        self.grid_size = grid_size  # Grid dimension

        # Grid stores indices into scroll list
        self.grid = [[None for _ in range(grid_size)] for _ in range(grid_size)]
        self.scroll_positions = {}  # scroll_idx -> (x, y)

        # Initialize with random positions
        self._initialize_positions()

    def _initialize_positions(self):
        """Initialize random positions for all scrolls."""
        positions = [(x, y) for x in range(self.grid_size)
                           for y in range(self.grid_size)]
        np.random.shuffle(positions)

        for i in range(self.size):
            x, y = positions[i % len(positions)]
            self.grid[x][y] = i
            self.scroll_positions[i] = (x, y)

    def get_neighbors(self, scroll_idx: int, radius: int = 1) -> List[int]:
        """Get neighboring scrolls within radius."""
        if scroll_idx not in self.scroll_positions:
            return []

        x, y = self.scroll_positions[scroll_idx]
        neighbors = []

        for dx in range(-radius, radius + 1):
            for dy in range(-radius, radius + 1):
                if dx == 0 and dy == 0:
                    continue
                nx, ny = (x + dx) % self.grid_size, (y + dy) % self.grid_size
                neighbor_idx = self.grid[nx][ny]
                if neighbor_idx is not None:
                    neighbors.append(neighbor_idx)

        return neighbors

    def move_scroll(self, scroll_idx: int, new_x: int, new_y: int):
        """Move a scroll to a new position."""
        if scroll_idx in self.scroll_positions:
            old_x, old_y = self.scroll_positions[scroll_idx]
            self.grid[old_x][old_y] = None

        self.grid[new_x][new_y] = scroll_idx
        self.scroll_positions[scroll_idx] = (new_x, new_y)


class CarryingCapacity:
    """Manages population carrying capacity."""

    def __init__(self, max_capacity: int = 1000, growth_rate: float = 0.01):
        self.max_capacity = max_capacity
        self.growth_rate = growth_rate
        self.current_capacity = max_capacity

    def adjust(self, population_size: int, avg_fitness: float) -> int:
        """Adjust carrying capacity based on population and fitness.

        Args:
            population_size: Current number of scrolls
            avg_fitness: Average fitness of population

        Returns:
            New carrying capacity
        """
        # Higher fitness -> increase capacity
        # Lower fitness -> decrease capacity
        fitness_factor = 1.0 + self.growth_rate * (avg_fitness - 0.5)

        target_capacity = int(self.max_capacity * fitness_factor)
        target_capacity = max(100, min(self.max_capacity, target_capacity))

        # Smooth transition
        self.current_capacity = int(
            0.9 * self.current_capacity + 0.1 * target_capacity
        )

        return self.current_capacity


class GaiaLayer:
    """GAIA layer for ecological dynamics.

    Adds:
    - Spatial topology (2D grid)
    - Carrying capacity management
    - Ecological niches
    - Environmental pressures
    """

    def __init__(self, config: Dict[str, Any]):
        self.enabled = config.get('enabled', True)

        # Grid settings
        self.grid_size = config.get('grid_size', 16)
        self.spatial_radius = config.get('spatial_radius', 2)

        # Carrying capacity
        self.max_capacity = config.get('max_capacity', 1000)
        self.growth_rate = config.get('growth_rate', 0.01)

        # Track if initialized
        self.spatial_grid = None
        self.carrying_capacity = None

    def initialize(self, soup_size: int):
        """Initialize spatial structures."""
        self.spatial_grid = SpatialGrid(soup_size, self.grid_size)
        self.carrying_capacity = CarryingCapacity(
            self.max_capacity, self.growth_rate
        )

    def before_interaction(self, soup, i: int, j: int) -> None:
        """Before interaction, consider spatial proximity."""
        if not self.enabled or self.spatial_grid is None:
            return

        # Can add bias toward interacting with neighbors
        # For now, just track that interaction happened
        pass

    def after_interaction(self, soup, i: int, j: int, steps: int) -> None:
        """After interaction, handle population dynamics."""
        if not self.enabled:
            return

        # Track successful interactions for population dynamics
        soup.scrolls[i]
        soup.scrolls[j]

        # Record that these scrolls interacted
        if not hasattr(soup, '_gaia_interactions'):
            soup._gaia_interactions = []
        soup._gaia_interactions.append((i, j, steps))

    def after_epoch(self, soup, epoch: int) -> Dict[str, Any]:
        """After epoch, return ecological statistics.

        Args:
            soup: The soup
            epoch: Current epoch number

        Returns:
            Dictionary of ecological statistics
        """
        if not self.enabled:
            return {}

        # Get fitness values
        fitnesses = [s.fitness for s in soup.scrolls]
        avg_fitness = np.mean(fitnesses) if fitnesses else 0.0

        # Adjust carrying capacity
        new_capacity = self.carrying_capacity.adjust(
            len(soup.scrolls), avg_fitness
        )

        stats = {
            'gaia_carrying_capacity': new_capacity,
            'gaia_population': len(soup.scrolls),
            'gaia_avg_fitness': avg_fitness,
        }

        # Count interactions
        if hasattr(soup, '_gaia_interactions'):
            stats['gaia_interactions'] = len(soup._gaia_interactions)
            avg_steps = np.mean([s for _, _, s in soup._gaia_interactions])
            stats['gaia_avg_steps'] = avg_steps
            soup._gaia_interactions = []  # Reset

        return stats


def create_gaia(config: Dict[str, Any]) -> GaiaLayer:
    """Factory function to create GAIA layer."""
    return GaiaLayer(config)
