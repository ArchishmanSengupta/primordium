"""Layers for PRIMORDIUM.

This module contains the evolutionary layers that can be applied to the soup.
"""

from typing import Any, Dict


class Layer:
    """Base class for all evolutionary layers."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config

    def before_interaction(self, soup, i: int, j: int) -> None:
        """Called before each interaction."""
        pass

    def after_interaction(self, soup, i: int, j: int, steps: int) -> None:
        """Called after each interaction."""
        pass

    def after_epoch(self, soup, epoch: int) -> Dict[str, Any]:
        """Called after each epoch (checkpoint interval)."""
        return {}
