from __future__ import annotations

from typing import Callable, List

from primordium.aether.interpreter import VALID_OPS


def _tape_counts(soup) -> dict:
    counts: dict = {}
    for scroll in soup.scrolls:
        key = scroll.tape.tobytes()
        counts[key] = counts.get(key, 0) + 1
    return counts


def replication_fitness(soup) -> List[float]:
    counts = _tape_counts(soup)
    n = len(soup.scrolls)
    if n == 0:
        return []
    threshold = max(1, int(n * 0.05))
    fitnesses: List[float] = []
    for scroll in soup.scrolls:
        key = scroll.tape.tobytes()
        count = counts[key]
        fitnesses.append(min(1.0, count / threshold))
    return fitnesses


def instruction_density_fitness(soup) -> List[float]:
    fitnesses: List[float] = []
    for scroll in soup.scrolls:
        valid = sum(1 for byte in scroll.tape if byte in VALID_OPS)
        fitnesses.append(valid / len(scroll.tape))
    return fitnesses


_FITNESS_FNS: dict[str, Callable] = {
    "replication": replication_fitness,
    "instruction_density": instruction_density_fitness,
}


def update_scroll_fitness(soup, fitness_fn: str = "replication") -> None:
    fn = _FITNESS_FNS.get(fitness_fn)
    if fn is None:
        raise ValueError(f"Unknown fitness function: {fitness_fn}")
    for scroll, value in zip(soup.scrolls, fn(soup)):
        scroll.fitness = float(value)
