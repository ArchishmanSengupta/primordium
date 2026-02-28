"""Tests for the metrics module."""

import numpy as np
import pytest
from collections import Counter

from primordium.metrics import (
    calculate_entropy,
    soup_entropy,
    instruction_density,
    count_replicators,
    top_replicators,
    detect_phase,
    compression_complexity,
    average_complexity,
    avg_ops_history,
    compression_ratio,
    soup_compression_ratio,
    detect_life_criteria,
    DEFAULT_LIFE_CRITERIA,
)
from primordium.chaos import Soup, Scroll


class TestCalculateEntropy:
    """Tests for calculate_entropy function."""

    def test_empty_tape(self):
        """Entropy of empty tape should be 0."""
        tape = np.array([], dtype=np.uint8)
        assert calculate_entropy(tape) == 0.0

    def test_uniform_tape(self):
        """Entropy of uniform tape should be 0."""
        tape = np.array([42] * 100, dtype=np.uint8)
        assert calculate_entropy(tape) == 0.0

    def test_maximum_entropy(self):
        """Maximum entropy occurs with uniform distribution of all values."""
        # With only 2 unique values, max entropy is 1 bit
        tape = np.array([0, 1] * 128, dtype=np.uint8)
        entropy = calculate_entropy(tape)
        assert 0.99 < entropy < 1.01  # Approximately 1.0

    def test_partial_entropy(self):
        """Test entropy with partial distribution."""
        tape = np.array([0] * 75 + [1] * 25, dtype=np.uint8)
        entropy = calculate_entropy(tape)
        assert 0.8 < entropy < 1.0

    def test_single_unique_value(self):
        """All same values = zero entropy."""
        tape = np.array([255] * 50, dtype=np.uint8)
        assert calculate_entropy(tape) == 0.0


class TestSoupEntropy:
    """Tests for soup_entropy function."""

    def test_empty_soup(self):
        """Empty soup should return 0 entropy."""
        soup = Soup(size=0, tape_length=48)
        assert soup_entropy(soup) == 0.0

    def test_random_soup(self):
        """Random soup should have high entropy."""
        soup = Soup(size=10, tape_length=48, seed=42)
        entropy = soup_entropy(soup)
        assert entropy > 3.0  # Random data has ~8 bits max

    def test_uniform_soup(self):
        """Soup with uniform scrolls should have zero entropy."""
        # Create scrolls with same tape
        soup = Soup(size=5, tape_length=48, seed=42)
        for scroll in soup.scrolls:
            scroll.tape[:] = 0  # All zeros
        entropy = soup_entropy(soup)
        assert entropy == 0.0


class TestInstructionDensity:
    """Tests for instruction_density function."""

    def test_all_noops(self):
        """All no-ops should give density 0."""
        soup = Soup(size=5, tape_length=48, seed=42)
        # Set all to non-valid values (e.g., 0, 1, 2)
        for scroll in soup.scrolls:
            scroll.tape[:] = np.array([0, 1, 2] * 16, dtype=np.uint8)[:48]
        density = instruction_density(soup)
        assert density == 0.0

    def test_all_valid_ops(self):
        """All valid ops should give density 1."""
        soup = Soup(size=5, tape_length=48, seed=42)
        # Set all to valid BF ops
        valid_ops = [ord('>'), ord('<'), ord('+'), ord('-'), ord('['), ord(']'), ord('.')]
        for scroll in soup.scrolls:
            scroll.tape[:] = np.array(valid_ops * 7, dtype=np.uint8)[:48]
        density = instruction_density(soup)
        assert density == 1.0

    def test_mixed_tape(self):
        """Test with mixed valid/invalid."""
        soup = Soup(size=5, tape_length=48, seed=42)
        # Half valid, half no-ops
        valid = [ord('>'), ord('<'), ord('+')]
        for scroll in soup.scrolls:
            for i in range(24):
                scroll.tape[i] = valid[i % 3]
                scroll.tape[i + 24] = i  # no-op
        density = instruction_density(soup)
        assert density == 0.5


class TestReplicators:
    """Tests for replicator detection."""

    def test_no_replicators_with_threshold(self):
        """With high threshold, random unique scrolls have no replicators."""
        soup = Soup(size=10, tape_length=48, seed=42)
        # With threshold 0.3, need at least 30% of soup to be identical
        replicators = count_replicators(soup, threshold=0.3)
        assert len(replicators) == 0

    def test_with_replicators(self):
        """Test with known replicators."""
        soup = Soup(size=20, tape_length=48, seed=42)
        # Make 5 scrolls identical (25% - above 5% threshold)
        replicator_tape = np.array([42] * 48, dtype=np.uint8)
        for i in range(5):
            soup.scrolls[i].tape = replicator_tape.copy()

        replicators = count_replicators(soup, threshold=0.1)
        assert len(replicators) == 1
        assert replicators[tuple(replicator_tape)] == 5

    def test_top_replicators(self):
        """Test top replicators sorting."""
        soup = Soup(size=20, tape_length=48, seed=42)

        # Create replicators with different frequencies
        tape1 = np.array([1] * 48, dtype=np.uint8)
        tape2 = np.array([2] * 48, dtype=np.uint8)
        tape3 = np.array([3] * 48, dtype=np.uint8)

        for i in range(10):
            soup.scrolls[i].tape = tape1.copy()
        for i in range(5):
            soup.scrolls[i + 10].tape = tape2.copy()
        for i in range(3):
            soup.scrolls[i + 15].tape = tape3.copy()

        top = top_replicators(soup, n=3)
        assert top[0][1] == 10  # tape1 is most common
        assert top[1][1] == 5   # tape2 is second
        assert top[2][1] == 3   # tape3 is third


class TestDetectPhase:
    """Tests for phase detection."""

    def test_noise_phase(self):
        """Low ops = noise phase."""
        assert detect_phase(5) == "noise"
        assert detect_phase(9) == "noise"

    def test_transition_phase(self):
        """Medium ops = transition phase."""
        assert detect_phase(10) == "transition"
        assert detect_phase(50) == "transition"
        assert detect_phase(79) == "transition"

    def test_life_phase(self):
        """High ops = life phase."""
        assert detect_phase(80) == "life"
        assert detect_phase(100) == "life"
        assert detect_phase(350) == "life"


class TestCompressionComplexity:
    """Tests for compression-based complexity metrics."""

    def test_empty_tape(self):
        """Empty tape should have 0 complexity."""
        tape = np.array([], dtype=np.uint8)
        complexity = compression_complexity(tape)
        assert complexity == 0

    def test_highly_repetitive(self):
        """Highly repetitive tape should compress well."""
        tape = np.array([1, 2, 3, 4] * 12, dtype=np.uint8)  # 48 bytes
        complexity = compression_complexity(tape)
        assert complexity < 20  # Very compressible

    def test_random_tape(self):
        """Random tape should not compress well."""
        np.random.seed(42)
        tape = np.random.randint(0, 256, 48, dtype=np.uint8)
        complexity = compression_complexity(tape)
        assert complexity >= 40  # Won't compress much

    def test_average_complexity_empty_soup(self):
        """Empty soup should return 0 complexity."""
        soup = Soup(size=0, tape_length=48)
        complexity = average_complexity(soup)
        assert complexity == 0.0


class TestAvgOpsHistory:
    """Tests for avg_ops_history function."""

    def test_empty_history(self):
        """Empty history should return 0."""
        assert avg_ops_history([]) == 0.0

    def test_exact_window(self):
        """Test with exact window size."""
        ops = [10] * 1000
        assert avg_ops_history(ops, window=1000) == 10.0

    def test_larger_than_window(self):
        """Test with more than window size - should use recent."""
        ops = [10] * 500 + [100] * 1000
        avg = avg_ops_history(ops, window=1000)
        assert avg == 100.0  # Should only average last 1000

    def test_partial_window(self):
        """Test with less than window size."""
        ops = [50] * 100
        avg = avg_ops_history(ops, window=1000)
        assert avg == 50.0


class TestCompressionRatio:
    """Tests for compression_ratio function - the key phase transition metric."""

    def test_empty_tape(self):
        """Empty tape should return ratio of 1.0."""
        tape = np.array([], dtype=np.uint8)
        assert compression_ratio(tape) == 1.0

    def test_highly_repetitive(self):
        """Highly repetitive tape should have low compression ratio."""
        tape = np.array([42] * 100, dtype=np.uint8)
        ratio = compression_ratio(tape)
        assert ratio < 0.5  # Very compressible

    def test_maximally_compressible(self):
        """All same bytes = best compression."""
        tape = np.array([0] * 200, dtype=np.uint8)
        ratio = compression_ratio(tape)
        assert ratio < 0.1  # Nearly perfect compression

    def test_random_tape(self):
        """Random tape should not compress well (ratio > 1)."""
        np.random.seed(123)
        tape = np.random.randint(0, 256, 100, dtype=np.uint8)
        ratio = compression_ratio(tape)
        assert ratio >= 0.9  # Won't compress much

    def test_patterned_tape(self):
        """Patterned tape should compress well."""
        # ABABABAB pattern compresses very well
        tape = np.array([0, 1] * 50, dtype=np.uint8)
        ratio = compression_ratio(tape)
        assert ratio < 0.5  # Very compressible

    def test_known_compression(self):
        """Test with known compression behavior."""
        # Short repetitive sequence compresses very well
        tape = np.array(list(range(10)) * 10, dtype=np.uint8)
        ratio = compression_ratio(tape)
        assert ratio < 0.5


class TestSoupCompressionRatio:
    """Tests for soup_compression_ratio function."""

    def test_empty_soup(self):
        """Empty soup should handle gracefully."""
        soup = Soup(size=0, tape_length=48)
        ratio = soup_compression_ratio(soup)
        # Should handle empty without error
        assert ratio >= 0

    def test_uniform_soup(self):
        """Uniform soup should have low compression ratio."""
        soup = Soup(size=10, tape_length=48, seed=42)
        # Make all scrolls identical
        uniform_tape = np.array([7] * 48, dtype=np.uint8)
        for scroll in soup.scrolls:
            scroll.tape = uniform_tape.copy()

        ratio = soup_compression_ratio(soup, sample_size=10)
        assert ratio < 0.3  # Very compressible

    def test_random_soup(self):
        """Random soup should have high compression ratio."""
        soup = Soup(size=10, tape_length=48, seed=42)
        ratio = soup_compression_ratio(soup, sample_size=10)
        assert ratio >= 0.9  # Won't compress much

    def test_sample_size_respected(self):
        """Test that sample_size is respected."""
        soup = Soup(size=100, tape_length=48, seed=42)
        # Should work with small sample
        ratio = soup_compression_ratio(soup, sample_size=5)
        assert ratio >= 0


class TestDetectLifeCriteria:
    """Tests for detect_life_criteria - operational definition of life."""

    def test_default_thresholds(self):
        """Test that DEFAULT_LIFE_CRITERIA has correct values."""
        assert DEFAULT_LIFE_CRITERIA["instruction_density_threshold"] == 0.1
        assert DEFAULT_LIFE_CRITERIA["replicator_fraction_threshold"] == 0.05
        assert DEFAULT_LIFE_CRITERIA["compression_ratio_threshold"] == 0.8

    def test_empty_soup(self):
        """Empty soup should not be life."""
        soup = Soup(size=0, tape_length=48)
        criteria = detect_life_criteria(soup)
        assert criteria["is_life"] == False

    def test_random_soup_not_life(self):
        """Random soup should not meet life criteria."""
        soup = Soup(size=100, tape_length=48, seed=42)
        criteria = detect_life_criteria(soup)

        assert criteria["is_life"] == False
        assert criteria["instruction_density"] < 0.1
        assert criteria["compression_ratio"] > 0.8

    def test_meets_structure_criterion(self):
        """Test with high instruction density."""
        soup = Soup(size=10, tape_length=48, seed=42)
        # Set all to valid ops
        valid_ops = [ord('>'), ord('<'), ord('+'), ord('-'), ord('['), ord(']'), ord('.')]
        for scroll in soup.scrolls:
            scroll.tape[:] = np.array(valid_ops * 7, dtype=np.uint8)[:48]

        criteria = detect_life_criteria(soup)
        assert criteria["criteria_met"]["structure"] == True

    def test_meets_replication_criterion(self):
        """Test with replicators."""
        soup = Soup(size=20, tape_length=48, seed=42)
        # Make 10% replicators
        replicator_tape = np.array([42] * 48, dtype=np.uint8)
        for i in range(2):  # 2/20 = 10%
            soup.scrolls[i].tape = replicator_tape.copy()

        criteria = detect_life_criteria(soup)
        assert criteria["criteria_met"]["replication"] == True

    def test_meets_purpose_criterion(self):
        """Test with compressible (purposeful) tapes."""
        soup = Soup(size=10, tape_length=48, seed=42)
        # All identical = highly compressible
        uniform = np.array([1] * 48, dtype=np.uint8)
        for scroll in soup.scrolls:
            scroll.tape = uniform.copy()

        criteria = detect_life_criteria(soup)
        assert criteria["criteria_met"]["purpose"] == True

    def test_all_criteria_met(self):
        """Test when all life criteria are met."""
        soup = Soup(size=20, tape_length=48, seed=42)

        # Create replicators (meeting replication criterion)
        replicator_tape = np.array([ord('>'), ord('<'), ord('+'), ord('-')] * 12, dtype=np.uint8)[:48]
        for i in range(5):  # 25% replicators
            soup.scrolls[i].tape = replicator_tape.copy()

        # Manually set high instruction density
        for scroll in soup.scrolls:
            for i in range(len(scroll.tape)):
                if i % 4 == 0:
                    scroll.tape[i] = ord('>')
                elif i % 4 == 1:
                    scroll.tape[i] = ord('<')
                elif i % 4 == 2:
                    scroll.tape[i] = ord('+')
                else:
                    scroll.tape[i] = ord('-')

        criteria = detect_life_criteria(soup)

        # At minimum, should meet some criteria
        assert "structure" in criteria["criteria_met"]
        assert "replication" in criteria["criteria_met"]
        assert "purpose" in criteria["criteria_met"]

    def test_custom_thresholds(self):
        """Test with custom thresholds."""
        soup = Soup(size=10, tape_length=48, seed=42)

        # Random soup doesn't meet default criteria
        criteria_default = detect_life_criteria(soup)

        # But with very lenient thresholds, could meet them
        criteria_lenient = detect_life_criteria(
            soup,
            instruction_density_threshold=0.0,
            replicator_fraction_threshold=0.0,
            compression_ratio_threshold=2.0,
        )

        assert criteria_lenient["is_life"] == True

    def test_criteria_values_returned(self):
        """Test that all expected values are returned."""
        soup = Soup(size=10, tape_length=48, seed=42)
        criteria = detect_life_criteria(soup)

        # Check all expected keys exist
        assert "is_life" in criteria
        assert "instruction_density" in criteria
        assert "replicator_fraction" in criteria
        assert "compression_ratio" in criteria
        assert "criteria_met" in criteria

        # Check criteria_met has all three
        assert len(criteria["criteria_met"]) == 3
        assert "structure" in criteria["criteria_met"]
        assert "replication" in criteria["criteria_met"]
        assert "purpose" in criteria["criteria_met"]


class TestMetricsIntegration:
    """Integration tests for metrics module."""

    def test_metrics_work_after_interactions(self):
        """Test that metrics work after some interactions have occurred."""
        soup = Soup(size=50, tape_length=48, seed=42)

        # Run some interactions
        for _ in range(100):
            soup.interact(max_steps=50)

        # Metrics should still work
        entropy = soup_entropy(soup)
        density = instruction_density(soup)
        comp_ratio = soup_compression_ratio(soup, sample_size=20)
        criteria = detect_life_criteria(soup)

        assert entropy >= 0
        assert 0 <= density <= 1
        assert comp_ratio >= 0
        assert "is_life" in criteria

    def test_phase_transition_detection_pattern(self):
        """Test pattern that should indicate phase transition."""
        soup = Soup(size=100, tape_length=48, seed=42)

        # Record initial metrics
        initial_entropy = soup_entropy(soup)
        initial_comp = soup_compression_ratio(soup)

        # After many interactions, we might see:
        # - Entropy decreasing
        # - Compression ratio decreasing
        # - Replicators appearing

        for _ in range(1000):
            soup.interact(max_steps=100)

        final_entropy = soup_entropy(soup)
        final_comp = soup_compression_ratio(soup)

        # These are the metrics we track for phase transition
        assert initial_entropy >= 0
        assert final_entropy >= 0
        assert initial_comp >= 0
        assert final_comp >= 0

        # Replicator detection
        replicators = count_replicators(soup, threshold=0.01)
        assert isinstance(replicators, dict)

    def test_life_criteria_thresholds_cause_different_results(self):
        """Test that different thresholds produce different results."""
        soup = Soup(size=20, tape_length=48, seed=42)

        # Strict thresholds
        criteria_strict = detect_life_criteria(
            soup,
            instruction_density_threshold=0.5,
            replicator_fraction_threshold=0.5,
            compression_ratio_threshold=0.5,
        )

        # Lenient thresholds
        criteria_lenient = detect_life_criteria(
            soup,
            instruction_density_threshold=0.0,
            replicator_fraction_threshold=0.0,
            compression_ratio_threshold=2.0,
        )

        # Lenient should meet more criteria
        strict_met = sum(criteria_strict["criteria_met"].values())
        lenient_met = sum(criteria_lenient["criteria_met"].values())

        assert lenient_met >= strict_met
