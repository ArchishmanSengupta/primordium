"""APEIRON: Interaction rules for PRIMORDIUM."""

from typing import Any, Dict

class InteractionRule:
    """Base class for interaction rules."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config

    def interact(self, scroll_a, scroll_b, max_steps: int):
        """Run interaction between two scrolls."""
        from primordium.aether.interpreter import run_bf
        return run_bf(scroll_a, scroll_b, max_steps=max_steps)
