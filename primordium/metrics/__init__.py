"""Metrics system for PRIMORDIUM.

This module provides various metrics to measure the state of the soup.
"""

from typing import Dict
import numpy as np


def calculate_entropy(tape: np.ndarray) -> float:
    """Calculate Shannon entropy of a tape.

    Args:
        tape: numpy array of bytes

    Returns:
        Entropy value (0 to 8 for 8-bit bytes)
    """
    if len(tape) == 0:
        return 0.0

    counts = np.bincount(tape, minlength=256)
    p = counts[counts > 0] / len(tape)
    return float(-(p * np.log2(p)).sum())


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
    if total_bytes == 0:
        return 0.0

    arr = soup.to_array()
    valid_count = int(np.isin(arr, list(VALID_OPS)).sum())
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

    if len(tape) == 0:
        return 0

    # Compress the tape
    compressed = zlib.compress(tape.tobytes())
    return len(compressed)


def average_complexity(soup, sample_size: int = 50) -> float:
    """Calculate average complexity of a sample of scrolls.

    Args:
        soup: Soup object
        sample_size: Number of scrolls to sample

    Returns:
        Average compressed size, or 0.0 if soup is empty
    """
    import random

    if len(soup.scrolls) == 0:
        return 0.0

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


def compression_ratio(tape: np.ndarray) -> float:
    """Calculate compression ratio for a tape.

    This measures how compressible the tape is. A ratio < 1.0 means
    the tape is more compressible than random data.

    Args:
        tape: numpy array of bytes

    Returns:
        Compression ratio (compressed_size / original_size)
        Lower = more repetitive/structured
    """
    import zlib

    if len(tape) == 0:
        return 1.0

    original_size = len(tape)
    compressed = zlib.compress(tape.tobytes())
    compressed_size = len(compressed)

    return compressed_size / original_size


def soup_compression_ratio(soup, sample_size: int = 50) -> float:
    """Calculate average compression ratio across a sample of scrolls.

    This is a key metric for detecting phase transitions. When the
    system undergoes gelation, entropy drops and compression ratio
    decreases significantly.

    Args:
        soup: Soup object
        sample_size: Number of scrolls to sample

    Returns:
        Average compression ratio, or 1.0 if soup is empty
    """
    import random

    if len(soup.scrolls) == 0:
        return 1.0

    if len(soup.scrolls) <= sample_size:
        scrolls = soup.scrolls
    else:
        scrolls = random.sample(soup.scrolls, sample_size)

    ratios = [compression_ratio(scroll.tape) for scroll in scrolls]
    return np.mean(ratios)


def detect_life_criteria(
    soup,
    instruction_density_threshold: float = 0.1,
    replicator_fraction_threshold: float = 0.05,
    compression_ratio_threshold: float = 0.8,
) -> dict:
    """Evaluate operational criteria for "life" in the system.

    This defines what we mean by "life" operationally, based on
    Blaise Agüera y Arcas's BFF experiment findings:

    1. Structure: Must have meaningful instruction density
    2. Replication: Must have replicators (identical copies)
    3. Purpose: Must have low entropy (compressible = functional)

    Args:
        soup: Soup object
        instruction_density_threshold: Min instruction density for "structure"
        replicator_fraction_threshold: Min fraction of soup that must be replicators
        compression_ratio_threshold: Max compression ratio for "purpose"

    Returns:
        Dictionary with:
        - is_life: Boolean - does system meet life criteria?
        - instruction_density: Current instruction density
        - replicator_fraction: Fraction of soup that are replicators
        - compression_ratio: Average compression ratio
        - criteria_met: Which individual criteria are met
    """
    # Handle empty soup
    if len(soup.scrolls) == 0:
        return {
            "is_life": False,
            "instruction_density": 0.0,
            "replicator_fraction": 0.0,
            "compression_ratio": 1.0,
            "criteria_met": {
                "structure": False,
                "replication": False,
                "purpose": False,
            },
        }

    # Calculate metrics
    inst_density = instruction_density(soup)

    # Count replicators
    replicators = count_replicators(soup)
    total_replicator_count = sum(replicators.values())
    replicator_fraction = total_replicator_count / len(soup.scrolls) if soup.scrolls else 0

    # Calculate compression
    comp_ratio = soup_compression_ratio(soup)

    # Evaluate criteria
    criteria_met = {
        "structure": bool(inst_density >= instruction_density_threshold),
        "replication": bool(replicator_fraction >= replicator_fraction_threshold),
        "purpose": bool(comp_ratio <= compression_ratio_threshold),
    }

    is_life = all(criteria_met.values())

    return {
        "is_life": is_life,
        "instruction_density": inst_density,
        "replicator_fraction": replicator_fraction,
        "compression_ratio": comp_ratio,
        "criteria_met": criteria_met,
    }


# Default thresholds based on BFF experiment observations
DEFAULT_LIFE_CRITERIA = {
    "instruction_density_threshold": 0.1,  # ~10% valid instructions
    "replicator_fraction_threshold": 0.05,  # At least 5% are replicators
    "compression_ratio_threshold": 0.8,  # Compresses to <80% of original
}
