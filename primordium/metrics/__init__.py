"""Metrics system for PRIMORDIUM.

This module provides various metrics to measure the state of the soup.
"""

from typing import Dict, Any
import numpy as np
from collections import Counter


def calculate_entropy(tape: np.ndarray) -> float:
    """Calculate Shannon entropy of a tape.

    Args:
        tape: numpy array of bytes

    Returns:
        Entropy value (0 to 8 for 8-bit bytes)
    """
    if len(tape) == 0:
        return 0.0

    # Count byte frequencies
    counts = Counter(tape)
    total = len(tape)

    # Calculate entropy
    entropy = 0.0
    for count in counts.values():
        if count > 0:
            p = count / total
            entropy -= p * np.log2(p)

    return entropy


def soup_entropy(soup) -> float:
    """Calculate average entropy across all scrolls.

    Args:
        soup: Soup object

    Returns:
        Average entropy
    """
    if len(soup.scrolls) == 0:
        return 0.0

    entropies = [calculate_entropy(scroll.tape) for scroll in soup.scrolls]
    return np.mean(entropies)


def instruction_density(soup) -> float:
    """Calculate fraction of valid instructions in soup.

    Args:
        soup: Soup object

    Returns:
        Fraction of valid BF instructions (0.0 to 1.0)
    """
    from primordium.aether.interpreter import VALID_OPS

    total_bytes = soup.size * soup.tape_length
    valid_count = 0

    for scroll in soup.scrolls:
        for byte in scroll.tape:
            if byte in VALID_OPS:
                valid_count += 1

    return valid_count / total_bytes


def count_replicators(soup, threshold: float = 0.05) -> Dict[int, int]:
    """Count replicators in the soup.

    A replicator is a scroll that appears multiple times (identical tape).

    Args:
        soup: Soup object
        threshold: Minimum fraction of soup to be considered a replicator

    Returns:
        Dictionary mapping tape tuple to count
    """
    tape_counts: Dict[tuple, int] = {}

    for scroll in soup.scrolls:
        key = tuple(scroll.tape)
        tape_counts[key] = tape_counts.get(key, 0) + 1

    min_count = int(soup.size * threshold)
    replicators = {k: v for k, v in tape_counts.items() if v >= min_count}

    return replicators


def top_replicators(soup, n: int = 10) -> list:
    """Get top N replicators by count.

    Args:
        soup: Soup object
        n: Number of top replicators to return

    Returns:
        List of (tape, count) tuples, sorted by count descending
    """
    tape_counts: Dict[tuple, int] = {}

    for scroll in soup.scrolls:
        key = tuple(scroll.tape)
        tape_counts[key] = tape_counts.get(key, 0) + 1

    sorted_counts = sorted(tape_counts.items(), key=lambda x: x[1], reverse=True)
    return sorted_counts[:n]


def detect_phase(avg_ops: float) -> str:
    """Detect the current phase of the system.

    Args:
        avg_ops: Average operations per interaction

    Returns:
        Phase string: "noise", "transition", or "life"
    """
    if avg_ops < 10:
        return "noise"
    elif avg_ops < 80:
        return "transition"
    else:
        return "life"


def compression_complexity(tape: np.ndarray) -> int:
    """Estimate Kolmogorov complexity using compression.

    Args:
        tape: numpy array of bytes

    Returns:
        Compressed size (lower = more repetitive, higher = more complex)
    """
    import zlib

    # Compress the tape
    compressed = zlib.compress(tape.tobytes())
    return len(compressed)


def average_complexity(soup, sample_size: int = 50) -> float:
    """Calculate average complexity of a sample of scrolls.

    Args:
        soup: Soup object
        sample_size: Number of scrolls to sample

    Returns:
        Average compressed size
    """
    import random

    if len(soup.scrolls) <= sample_size:
        scrolls = soup.scrolls
    else:
        scrolls = random.sample(soup.scrolls, sample_size)

    complexities = [compression_complexity(scroll.tape) for scroll in scrolls]
    return np.mean(complexities)


def avg_ops_history(ops_list: list, window: int = 1000) -> float:
    """Calculate average ops from history.

    Args:
        ops_list: List of operations per interaction
        window: Window size for rolling average

    Returns:
        Average ops
    """
    if len(ops_list) == 0:
        return 0.0

    recent = ops_list[-window:]
    return np.mean(recent)
