"""Tests for the CHAOS soup and scroll classes.

Tests the soup environment that holds all scrolls and manages interactions.
"""

import pytest
import numpy as np
from typing import Tuple


class TestSoupInitialisation:
    """Tests for soup initialization."""

    def test_initialise_random(self):
        """Soup of size N has N scrolls of correct tape_length."""
        from primordium.chaos.soup import Soup
        soup = Soup(size=100, tape_length=48, seed=None)
        assert soup.size == 100
        assert soup.tape_length == 48
        assert len(soup.scrolls) == 100
        for scroll in soup.scrolls:
            assert len(scroll.tape) == 48

    def test_initialise_seeded(self):
        """Same seed produces identical soup."""
        from primordium.chaos.soup import Soup
        soup1 = Soup(size=50, tape_length=48, seed=12345)
        soup2 = Soup(size=50, tape_length=48, seed=12345)
        for s1, s2 in zip(soup1.scrolls, soup2.scrolls):
            assert np.array_equal(s1.tape, s2.tape)

    def test_different_seeds_different_soups(self):
        """Different seeds produce different soups."""
        from primordium.chaos.soup import Soup
        soup1 = Soup(size=50, tape_length=48, seed=12345)
        soup2 = Soup(size=50, tape_length=48, seed=54321)
        different = False
        for s1, s2 in zip(soup1.scrolls, soup2.scrolls):
            if not np.array_equal(s1.tape, s2.tape):
                different = True
                break
        assert different


class TestSoupInstructionDensity:
    """Tests for instruction density."""

    def test_instruction_density_random(self):
        """Random soup has density between 0.01 and 0.05."""
        from primordium.chaos.soup import Soup
        soup = Soup(size=256, tape_length=48, seed=None)
        density = soup.instruction_density()
        assert 0.01 <= density <= 0.05, f"Density {density} outside expected range"

    def test_instruction_density_seeded(self):
        """Seeded soup has expected instruction density."""
        from primordium.chaos.soup import Soup
        soup = Soup(size=100, tape_length=48, seed=42)
        density = soup.instruction_density()
        # Should be deterministic for a given seed
        density2 = Soup(size=100, tape_length=48, seed=42).instruction_density()
        assert density == density2


class TestSoupInteraction:
    """Tests for soup interactions (APEIRON)."""

    def test_interact_modifies_soup(self):
        """After interaction, at least one scroll differs from initial."""
        from primordium.chaos.soup import Soup
        soup = Soup(size=100, tape_length=48, seed=42)
        # Get copies of initial state
        initial_tapes = [scroll.tape.copy() for scroll in soup.scrolls]
        # Run multiple interactions to ensure we get modification
        for _ in range(100):
            soup.interact(max_steps=350)
        # Check that at least one scroll changed
        changed = False
        for i, scroll in enumerate(soup.scrolls):
            if not np.array_equal(scroll.tape, initial_tapes[i]):
                changed = True
                break
        assert changed, "No scrolls were modified after 100 interactions"

    def test_interact_preserves_size(self):
        """Soup size and tape_length unchanged after interaction."""
        from primordium.chaos.soup import Soup
        soup = Soup(size=100, tape_length=48, seed=42)
        original_size = soup.size
        original_tape_length = soup.tape_length
        # Run multiple interactions
        for _ in range(100):
            soup.interact(max_steps=350)
        assert soup.size == original_size
        assert soup.tape_length == original_tape_length
        assert len(soup.scrolls) == original_size

    def test_interaction_returns_steps(self):
        """Interaction returns the number of steps executed."""
        from primordium.chaos.soup import Soup
        soup = Soup(size=100, tape_length=48, seed=42)
        steps = soup.interact(max_steps=350)
        assert isinstance(steps, (int, np.integer))
        assert steps >= 0


class TestSoupCheckpoint:
    """Tests for checkpoint save/load."""

    def test_checkpoint_save_load(self):
        """Saved soup reloaded is identical to original."""
        from primordium.chaos.soup import Soup
        import tempfile
        import os
        soup1 = Soup(size=50, tape_length=48, seed=12345)
        # Run some interactions
        for _ in range(10):
            soup1.interact(max_steps=350)
        # Save to temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.npz') as f:
            temp_path = f.name
        try:
            soup1.save(temp_path)
            soup2 = Soup.load(temp_path)
            assert soup2.size == soup1.size
            assert soup2.tape_length == soup1.tape_length
            for s1, s2 in zip(soup1.scrolls, soup2.scrolls):
                assert np.array_equal(s1.tape, s2.tape)
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)


class TestSoupSelection:
    """Tests for scroll pair selection."""

    def test_select_pair_uniform(self):
        """Over 10000 selections, all scroll indices selected with roughly equal frequency."""
        from primordium.chaos.soup import Soup
        soup = Soup(size=50, tape_length=48, seed=42)
        counts = np.zeros(50)
        selections = 10000
        for _ in range(selections):
            i, j = soup.select_pair()
            counts[i] += 1
            counts[j] += 1
        # Each index should be selected roughly (selections * 2) / 50 times
        expected = (selections * 2) / 50
        tolerance = expected * 0.2  # 20% tolerance
        for count in counts:
            assert abs(count - expected) < tolerance, \
                f"Index selected {count} times, expected around {expected}"

    def test_select_pair_no_self(self):
        """i and j are never equal."""
        from primordium.chaos.soup import Soup
        soup = Soup(size=100, tape_length=48, seed=42)
        for _ in range(10000):
            i, j = soup.select_pair()
            assert i != j, f"Self-selection detected: i={i}, j={j}"

    def test_select_pair_returns_valid_indices(self):
        """Selected indices are always within valid range."""
        from primordium.chaos.soup import Soup
        soup = Soup(size=50, tape_length=48, seed=42)
        for _ in range(1000):
            i, j = soup.select_pair()
            assert 0 <= i < 50
            assert 0 <= j < 50


class TestSoupMetrics:
    """Tests for soup-level metrics."""

    def test_total_bytes(self):
        """Total bytes in soup is correct."""
        from primordium.chaos.soup import Soup
        soup = Soup(size=100, tape_length=48, seed=42)
        assert soup.total_bytes() == 100 * 48

    def test_to_array(self):
        """Soup converts to numpy array correctly."""
        from primordium.chaos.soup import Soup
        soup = Soup(size=50, tape_length=48, seed=12345)
        arr = soup.to_array()
        assert arr.shape == (50, 48)
        assert arr.dtype == np.uint8


class TestSoupIteration:
    """Tests for soup iteration."""

    def test_iterate_scrolls(self):
        """Can iterate over all scrolls."""
        from primordium.chaos.soup import Soup
        soup = Soup(size=10, tape_length=48, seed=42)
        count = 0
        for scroll in soup:
            count += 1
            assert len(scroll.tape) == 48
        assert count == 10

    def test_get_scroll(self):
        """Can get scroll by index."""
        from primordium.chaos.soup import Soup
        soup = Soup(size=10, tape_length=48, seed=42)
        scroll = soup.get_scroll(5)
        assert len(scroll.tape) == 48

