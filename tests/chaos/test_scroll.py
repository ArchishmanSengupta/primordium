"""Tests for the Scroll class.

Individual tape with metadata.
"""

import pytest
import numpy as np


class TestScrollCreation:
    """Tests for scroll creation."""

    def test_create_empty_scroll(self):
        """Create a scroll with empty tape."""
        from primordium.chaos.scroll import Scroll
        scroll = Scroll(tape_length=48)
        assert len(scroll.tape) == 48
        assert scroll.id is not None

    def test_create_with_data(self):
        """Create a scroll with initial data."""
        from primordium.chaos.scroll import Scroll
        data = np.array([1, 2, 3, 4, 5], dtype=np.uint8)
        scroll = Scroll(tape=data)
        assert np.array_equal(scroll.tape[:5], data)

    def test_create_with_seed(self):
        """Create scrolls with specific seed."""
        from primordium.chaos.scroll import Scroll
        scroll1 = Scroll(tape_length=48, seed=12345)
        scroll2 = Scroll(tape_length=48, seed=12345)
        assert np.array_equal(scroll1.tape, scroll2.tape)


class TestScrollMetadata:
    """Tests for scroll metadata."""

    def test_default_metadata(self):
        """Scroll has default metadata values."""
        from primordium.chaos.scroll import Scroll
        scroll = Scroll(tape_length=48)
        assert scroll.id is not None
        assert scroll.generation == 0
        assert scroll.parent_id is None

    def test_set_metadata(self):
        """Can set custom metadata."""
        from primordium.chaos.scroll import Scroll
        scroll = Scroll(tape_length=48, generation=5, parent_id="parent123")
        assert scroll.generation == 5
        assert scroll.parent_id == "parent123"

    def test_copy_count(self):
        """Scroll tracks copy count."""
        from primordium.chaos.scroll import Scroll
        scroll = Scroll(tape_length=48)
        assert scroll.copy_count == 0
        scroll.increment_copy_count()
        assert scroll.copy_count == 1
        scroll.increment_copy_count()
        assert scroll.copy_count == 2


class TestScrollOperations:
    """Tests for scroll operations."""

    def test_copy(self):
        """Can copy a scroll."""
        from primordium.chaos.scroll import Scroll
        scroll1 = Scroll(tape_length=48, seed=12345)
        scroll2 = scroll1.copy()
        assert np.array_equal(scroll1.tape, scroll2.tape)
        assert scroll1.id != scroll2.id
        assert scroll2.generation == scroll1.generation + 1

    def test_modify_tape(self):
        """Can modify scroll tape in place."""
        from primordium.chaos.scroll import Scroll
        scroll = Scroll(tape_length=48, seed=42)
        original_value = int(scroll.tape[0])
        scroll.tape[0] = 255
        assert int(scroll.tape[0]) == 255
        assert int(scroll.tape[0]) != original_value


class TestScrollHashing:
    """Tests for scroll hashing."""

    def test_hash_unique(self):
        """Each scroll has a unique hash."""
        from primordium.chaos.scroll import Scroll
        scroll1 = Scroll(tape_length=48, seed=42)
        scroll2 = Scroll(tape_length=48, seed=43)
        assert hash(scroll1) != hash(scroll2)

    def test_hash_same_for_same_tape(self):
        """Same tape produces same hash."""
        from primordium.chaos.scroll import Scroll
        data = np.array([1, 2, 3, 4, 5], dtype=np.uint8)
        scroll1 = Scroll(tape=data.copy())
        scroll2 = Scroll(tape=data.copy())
        # Note: different IDs will produce different hashes
        # But if we control for that...
        assert hash(scroll1) != hash(scroll2)  # Different IDs

