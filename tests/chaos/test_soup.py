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


class TestSoupReplicationAttribution:
    """Tests for per-scroll replication attribution in interactions."""

    def test_copy_count_attribution(self, monkeypatch):
        """Only the scroll whose content appears in the other output gains a count."""
        from primordium.chaos.soup import Soup

        soup = Soup(size=10, tape_length=48, seed=7)
        monkeypatch.setattr(soup, "select_pair", lambda: (3, 4))

        def fake_run_bf(scroll_a, scroll_b, max_steps=350, tape_length=None):
            new_a = np.array(scroll_a, dtype=np.uint8).copy()
            new_b = np.array(scroll_a, dtype=np.uint8).copy()
            return new_a, new_b, 5

        monkeypatch.setattr("primordium.aether.interpreter.run_bf", fake_run_bf)
        soup.interact(max_steps=350)
        assert soup.scrolls[3].copy_count == 1
        assert soup.scrolls[4].copy_count == 0


class TestSoupMutation:
    """Tests for random background mutation."""

    def test_zero_rate_preserves_tapes(self, monkeypatch):
        """mutation_rate=0 leaves interaction output untouched."""
        from primordium.chaos.soup import Soup

        soup = Soup(size=10, tape_length=48, seed=7, mutation_rate=0.0)
        monkeypatch.setattr(soup, "select_pair", lambda: (3, 4))

        def fake_run_bf(scroll_a, scroll_b, max_steps=350, tape_length=None):
            new_a = np.array(scroll_a, dtype=np.uint8).copy()
            new_b = np.array(scroll_b, dtype=np.uint8).copy()
            return new_a, new_b, 5

        monkeypatch.setattr("primordium.aether.interpreter.run_bf", fake_run_bf)
        before_3 = soup.scrolls[3].tape.copy()
        before_4 = soup.scrolls[4].tape.copy()
        soup.interact(max_steps=350)
        assert np.array_equal(soup.scrolls[3].tape, before_3)
        assert np.array_equal(soup.scrolls[4].tape, before_4)

    def test_full_rate_rewrites_bytes(self, monkeypatch):
        """mutation_rate=1 rewrites every byte of the interacting pair."""
        from primordium.chaos.soup import Soup

        soup = Soup(size=10, tape_length=48, seed=7, mutation_rate=1.0)
        monkeypatch.setattr(soup, "select_pair", lambda: (3, 4))

        def fake_run_bf(scroll_a, scroll_b, max_steps=350, tape_length=None):
            return (
                np.zeros(48, dtype=np.uint8),
                np.zeros(48, dtype=np.uint8),
                5,
            )

        monkeypatch.setattr("primordium.aether.interpreter.run_bf", fake_run_bf)
        soup.interact(max_steps=350)
        assert soup.scrolls[3].tape.any()
        assert soup.scrolls[4].tape.any()
        assert (soup.scrolls[3].tape != 0).all()

    def test_mutation_uses_soup_rng(self, monkeypatch):
        """Mutation draws from the soup RNG so runs stay reproducible."""
        from primordium.chaos.soup import Soup

        def run_once(seed):
            soup = Soup(size=10, tape_length=48, seed=seed, mutation_rate=1.0)
            monkeypatch.setattr(soup, "select_pair", lambda: (3, 4))

            def fake_run_bf(scroll_a, scroll_b, max_steps=350, tape_length=None):
                return (
                    np.zeros(48, dtype=np.uint8),
                    np.zeros(48, dtype=np.uint8),
                    5,
                )

            monkeypatch.setattr("primordium.aether.interpreter.run_bf", fake_run_bf)
            soup.interact(max_steps=350)
            return soup.scrolls[3].tape.copy()

        assert np.array_equal(run_once(99), run_once(99))
        assert not np.array_equal(run_once(99), run_once(100))


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
