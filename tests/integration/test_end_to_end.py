"""End-to-end integration tests.

These tests verify that the core simulation loop works correctly,
including layer integration, metrics persistence, and checkpointing.
"""

from __future__ import annotations

import json
import os

import pytest
import yaml
import numpy as np

from primordium.chaos import Soup
from primordium.metrics import (
    soup_entropy,
    instruction_density,
    soup_compression_ratio,
    detect_life_criteria,
)


class TestCoreSoupLoop:
    """Test that the core soup loop runs without errors."""

    def test_basic_run(self):
        """Run 100 interactions and check metrics change."""
        soup = Soup(size=32, tape_length=24, seed=42)

        initial_density = instruction_density(soup)

        for _ in range(100):
            soup.interact(max_steps=100)

        final_density = instruction_density(soup)

        # We don't assert direction of change -- just that it ran
        assert isinstance(final_density, float)
        assert 0.0 <= final_density <= 1.0

    def test_checkpoint_roundtrip(self, tmp_path):
        """Save and load a soup checkpoint."""
        soup = Soup(size=16, tape_length=24, seed=123)

        for _ in range(50):
            soup.interact(max_steps=100)

        save_path = str(tmp_path / "test_checkpoint.npy")
        soup.save(save_path)

        # Soup.save uses np.savez which appends .npz
        actual_path = save_path
        if not os.path.exists(actual_path):
            actual_path = save_path + ".npz"

        loaded = Soup.load(actual_path)

        assert loaded.size == soup.size
        assert loaded.tape_length == soup.tape_length
        for i in range(soup.size):
            np.testing.assert_array_equal(loaded.scrolls[i].tape, soup.scrolls[i].tape)

    def test_life_criteria_detection(self):
        """Detect life criteria returns correct structure."""
        soup = Soup(size=16, tape_length=24, seed=42)
        criteria = detect_life_criteria(soup)

        assert "is_life" in criteria
        assert "instruction_density" in criteria
        assert "replicator_fraction" in criteria
        assert "compression_ratio" in criteria
        assert "criteria_met" in criteria
        assert isinstance(criteria["criteria_met"], dict)


class TestLayerIntegration:
    """Test that layers can be instantiated and called."""

    def test_genesis_layer(self):
        from primordium.layers.genesis import GenesisLayer

        layer = GenesisLayer({"enabled": True, "track_phylogeny": True, "phylogeny_depth": 10})
        soup = Soup(size=16, tape_length=24, seed=42)

        # Should not raise
        layer.after_interaction(soup, 0, 1, 50)
        stats = layer.after_epoch(soup, 0)
        assert isinstance(stats, dict)

    def test_gaia_layer(self):
        from primordium.layers.gaia import GaiaLayer

        layer = GaiaLayer({"enabled": True, "grid_size": 8, "spatial_radius": 2})
        layer.initialize(16)
        soup = Soup(size=16, tape_length=24, seed=42)

        layer.before_interaction(soup, 0, 1)
        layer.after_interaction(soup, 0, 1, 50)
        stats = layer.after_epoch(soup, 0)
        assert isinstance(stats, dict)

    def test_hermes_layer(self):
        from primordium.layers.hermes import HermesLayer

        layer = HermesLayer({"enabled": True})
        soup = Soup(size=16, tape_length=24, seed=42)

        layer.before_interaction(soup, 0, 1)
        layer.after_interaction(soup, 0, 1, 50)
        stats = layer.after_epoch(soup, 0)
        assert "hermes_corrections" in stats

    def test_mnemosyne_layer(self):
        from primordium.layers.mnemosyne import MnemosyneLayer

        layer = MnemosyneLayer({"enabled": True, "store_frequency": 1})
        soup = Soup(size=16, tape_length=24, seed=42)

        layer.after_interaction(soup, 0, 1, 50)
        stats = layer.after_epoch(soup, 0)
        assert "mnemosyne_pattern_count" in stats

    def test_prometheus_layer(self):
        from primordium.layers.prometheus import PrometheusLayer

        layer = PrometheusLayer({"enabled": True})
        soup = Soup(size=16, tape_length=24, seed=42)

        layer.before_interaction(soup, 0, 1)
        layer.after_interaction(soup, 0, 1, 50)
        stats = layer.after_epoch(soup, 0)
        assert "prometheus_tools" in stats

    def test_nous_layer(self):
        from primordium.layers.nous import NousLayer

        layer = NousLayer({"enabled": True})
        soup = Soup(size=16, tape_length=24, seed=42)

        layer.before_interaction(soup, 0, 1)
        layer.after_interaction(soup, 0, 1, 50)
        stats = layer.after_epoch(soup, 0)
        assert "nous_avg_fitness" in stats


class TestMetricsWriter:
    """Test the MetricsWriter used by the CLI."""

    def test_write_and_read(self, tmp_path):
        from primordium.cli import MetricsWriter

        writer = MetricsWriter(str(tmp_path))
        writer.open()
        writer.write({"interaction": 0, "event": "initial", "value": 1.0})
        writer.write({"interaction": 100, "event": "log", "value": 2.0})
        writer.close()

        records = writer.read_all()
        assert len(records) == 2
        assert records[0]["event"] == "initial"
        assert records[1]["value"] == 2.0

    def test_append_mode(self, tmp_path):
        from primordium.cli import MetricsWriter

        writer = MetricsWriter(str(tmp_path))
        writer.open(append=False)
        writer.write({"a": 1})
        writer.close()

        writer2 = MetricsWriter(str(tmp_path))
        writer2.open(append=True)
        writer2.write({"a": 2})
        writer2.close()

        records = writer2.read_all()
        assert len(records) == 2


class TestApeiron:
    """Test interaction rules."""

    def test_standard_rule(self):
        from primordium.apeiron import StandardRule

        rule = StandardRule({})
        tape_a = np.random.randint(0, 256, size=24, dtype=np.uint8)
        tape_b = np.random.randint(0, 256, size=24, dtype=np.uint8)

        new_a, new_b, steps = rule.interact(tape_a, tape_b, max_steps=100, tape_length=24)
        assert len(new_a) == 24
        assert len(new_b) == 24
        assert isinstance(steps, (int, np.integer))

    def test_get_rule(self):
        from primordium.apeiron import get_rule

        rule = get_rule({"rule": "standard"})
        assert rule is not None

        with pytest.raises(ValueError):
            get_rule({"rule": "nonexistent_rule"})


class TestKratos:
    """Test fitness functions."""

    def test_replication_fitness(self):
        from primordium.kratos import replication_fitness

        soup = Soup(size=16, tape_length=24, seed=42)
        fitnesses = replication_fitness(soup)
        assert len(fitnesses) == 16
        assert all(0.0 <= f <= 1.0 for f in fitnesses)

    def test_instruction_density_fitness(self):
        from primordium.kratos import instruction_density_fitness

        soup = Soup(size=16, tape_length=24, seed=42)
        fitnesses = instruction_density_fitness(soup)
        assert len(fitnesses) == 16
        assert all(0.0 <= f <= 1.0 for f in fitnesses)

    def test_update_scroll_fitness(self):
        from primordium.kratos import update_scroll_fitness

        soup = Soup(size=16, tape_length=24, seed=42)
        update_scroll_fitness(soup, fitness_fn="replication")

        for scroll in soup.scrolls:
            assert isinstance(scroll.fitness, float)


class TestDemiurgeEncoding:
    """Test neural architecture encoding/decoding."""

    def test_encode_decode_roundtrip(self):
        from primordium.demiurge import encode_architecture, decode_architecture

        arch = {
            "layers": [
                {"width": 128, "activation": "relu", "skip": False},
                {"width": 64, "activation": "tanh", "skip": True},
                {"width": 32, "activation": "gelu", "skip": False},
            ]
        }

        encoded = encode_architecture(arch)
        assert isinstance(encoded, bytes)
        assert len(encoded) > 0

        decoded = decode_architecture(encoded)
        assert len(decoded["layers"]) == 3
        assert decoded["layers"][0]["width"] == 128
        assert decoded["layers"][0]["activation"] == "relu"
        assert decoded["layers"][1]["skip"] is True

    def test_decode_empty(self):
        from primordium.demiurge import decode_architecture

        result = decode_architecture(b"")
        assert result == {}
