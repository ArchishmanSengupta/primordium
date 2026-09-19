from __future__ import annotations

from typing import Any, Dict, Tuple

import numpy as np

from primordium.aether.interpreter import run_bf


class InteractionRule:
    def __init__(self, config: Dict[str, Any]):
        self.config = config

    def interact(
        self,
        scroll_a: np.ndarray,
        scroll_b: np.ndarray,
        max_steps: int = 350,
        tape_length: int | None = None,
    ) -> Tuple[np.ndarray, np.ndarray, int]:
        raise NotImplementedError


class StandardRule(InteractionRule):
    def interact(
        self,
        scroll_a: np.ndarray,
        scroll_b: np.ndarray,
        max_steps: int = 350,
        tape_length: int | None = None,
    ) -> Tuple[np.ndarray, np.ndarray, int]:
        if tape_length is None:
            tape_length = len(scroll_a)
        return run_bf(
            scroll_a,
            scroll_b,
            max_steps=max_steps,
            tape_length=tape_length,
        )


_RULES = {
    "standard": StandardRule,
}


def get_rule(config: Dict[str, Any]) -> InteractionRule:
    name = config.get("rule", "standard")
    cls = _RULES.get(name)
    if cls is None:
        raise ValueError(f"Unknown interaction rule: {name}")
    return cls(config)
