"""Tests for the configuration system."""

from __future__ import annotations

import os
import tempfile

import pytest
import yaml

from primordium.config.schema import (
    GenesisConfig,
    ExperimentConfig,
    ChaosConfig,
    AetherConfig,
    LayersConfig,
    MetricsConfig,
)
from primordium.config.loader import load_config, save_config, merge_configs


# ---------------------------------------------------------------------------
# Schema validation
# ---------------------------------------------------------------------------

class TestGenesisConfig:
    """Test Pydantic schema validation."""

    def test_minimal_config(self):
        config = GenesisConfig(experiment={"name": "test"})
        assert config.experiment.name == "test"
        assert config.chaos.size == 256
        assert config.aether.backend == "python"

    def test_full_config(self):
        config = GenesisConfig(
            experiment={"name": "full", "seed": 42, "output_dir": "./out"},
            chaos={"size": 512, "tape_length": 64},
            aether={"backend": "c", "interactions_total": 50000},
        )
        assert config.chaos.size == 512
        assert config.chaos.tape_length == 64
        assert config.aether.backend == "c"

    def test_layers_disabled_by_default(self):
        config = GenesisConfig(experiment={"name": "test"})
        assert config.layers.genesis.enabled is False
        assert config.layers.gaia.enabled is False
        assert config.layers.hermes.enabled is False
        assert config.layers.mnemosyne.enabled is False
        assert config.layers.prometheus.enabled is False
        assert config.layers.nous.enabled is False

    def test_layers_can_be_enabled(self):
        config = GenesisConfig(
            experiment={"name": "test"},
            layers={
                "genesis": {"enabled": True},
                "gaia": {"enabled": True, "grid_width": 32},
            },
        )
        assert config.layers.genesis.enabled is True
        assert config.layers.gaia.enabled is True
        assert config.layers.gaia.grid_width == 32

    def test_invalid_backend_rejected(self):
        with pytest.raises(Exception):
            GenesisConfig(
                experiment={"name": "test"},
                aether={"backend": "invalid_backend"},
            )

    def test_default_life_criteria_thresholds(self):
        config = GenesisConfig(experiment={"name": "test"})
        thresholds = config.metrics.life_criteria_thresholds
        assert thresholds["instruction_density"] == 0.1
        assert thresholds["replicator_fraction"] == 0.05
        assert thresholds["compression_ratio"] == 0.8

    def test_demiurge_config_defaults(self):
        config = GenesisConfig(experiment={"name": "test"})
        assert config.demiurge.enabled is False
        assert config.demiurge.encoding_scheme == "direct"
        assert "relu" in config.demiurge.activation_set


# ---------------------------------------------------------------------------
# YAML loading
# ---------------------------------------------------------------------------

class TestLoadConfig:
    """Test YAML loading and template variable substitution."""

    def test_load_minimal_yaml(self, tmp_path):
        config_file = tmp_path / "genesis.yaml"
        config_file.write_text(yaml.dump({
            "experiment": {"name": "loadtest", "output_dir": str(tmp_path / "out")},
        }))

        config = load_config(str(config_file))
        assert config.experiment.name == "loadtest"

    def test_template_variable_substitution(self, tmp_path):
        config_file = tmp_path / "genesis.yaml"
        config_file.write_text(yaml.dump({
            "experiment": {
                "name": "myexp",
                "output_dir": str(tmp_path / "{name}_{timestamp}"),
            },
        }))

        config = load_config(str(config_file))
        assert "myexp" in config.experiment.output_dir
        # timestamp should be replaced (no literal {timestamp})
        assert "{timestamp}" not in config.experiment.output_dir

    def test_load_nonexistent_file(self):
        with pytest.raises(FileNotFoundError):
            load_config("/nonexistent/path/genesis.yaml")

    def test_load_with_layers(self, tmp_path):
        config_file = tmp_path / "genesis.yaml"
        config_file.write_text(yaml.dump({
            "experiment": {"name": "layertest", "output_dir": str(tmp_path)},
            "layers": {
                "genesis": {"enabled": True},
                "gaia": {"enabled": True, "grid_width": 16},
            },
        }))

        config = load_config(str(config_file))
        assert config.layers.genesis.enabled is True
        assert config.layers.gaia.enabled is True
        assert config.layers.gaia.grid_width == 16


# ---------------------------------------------------------------------------
# Config save/load round-trip
# ---------------------------------------------------------------------------

class TestSaveConfig:
    """Test saving config back to YAML."""

    def test_save_and_reload(self, tmp_path):
        original = GenesisConfig(
            experiment={"name": "roundtrip", "output_dir": str(tmp_path)},
            chaos={"size": 128, "tape_length": 32},
        )

        save_path = str(tmp_path / "saved.yaml")
        save_config(original, save_path)

        assert os.path.exists(save_path)

        # Reload and verify
        reloaded = load_config(save_path)
        assert reloaded.experiment.name == "roundtrip"
        assert reloaded.chaos.size == 128
        assert reloaded.chaos.tape_length == 32


# ---------------------------------------------------------------------------
# Config merging
# ---------------------------------------------------------------------------

class TestMergeConfigs:
    """Test config dictionary merging."""

    def test_simple_merge(self):
        base = {"a": 1, "b": 2}
        override = {"b": 3, "c": 4}
        result = merge_configs(base, override)
        assert result == {"a": 1, "b": 3, "c": 4}

    def test_nested_merge(self):
        base = {"outer": {"a": 1, "b": 2}}
        override = {"outer": {"b": 3}}
        result = merge_configs(base, override)
        assert result == {"outer": {"a": 1, "b": 3}}

    def test_override_replaces_non_dict(self):
        base = {"a": 1}
        override = {"a": {"nested": True}}
        result = merge_configs(base, override)
        assert result == {"a": {"nested": True}}
