"""Integration tests for the ORACLE analysis module."""

from __future__ import annotations

import json
import os

import pytest
import yaml

from primordium.oracle import ExperimentRun


@pytest.fixture
def mock_experiment(tmp_path):
    """Create a mock experiment directory with config and metrics."""
    # Write config
    config = {
        "experiment": {"name": "mock_run", "seed": 42, "output_dir": str(tmp_path)},
        "chaos": {"size": 64, "tape_length": 24},
        "aether": {"backend": "python", "interactions_total": 1000},
        "layers": {"genesis": {"enabled": False}},
    }
    config_path = tmp_path / "genesis.yaml"
    with open(config_path, "w") as f:
        yaml.dump(config, f)

    # Write metrics
    metrics_path = tmp_path / "metrics.jsonl"
    records = [
        {"interaction": 0, "event": "initial", "instruction_density": 0.03, "entropy": 7.9, "compression_ratio": 1.05, "is_life": False, "criteria_met": {"structure": False, "replication": False, "purpose": False}},
        {"interaction": 200, "event": "log", "avg_ops": 5.0, "instruction_density": 0.04, "entropy": 7.8, "compression_ratio": 1.03, "is_life": False, "criteria_met": {"structure": False, "replication": False, "purpose": False}, "rate": 500.0, "elapsed_s": 0.4},
        {"interaction": 400, "event": "log", "avg_ops": 12.0, "instruction_density": 0.08, "entropy": 7.5, "compression_ratio": 0.95, "is_life": False, "criteria_met": {"structure": False, "replication": False, "purpose": False}, "rate": 480.0, "elapsed_s": 0.8},
        {"interaction": 600, "event": "log", "avg_ops": 45.0, "instruction_density": 0.12, "entropy": 6.8, "compression_ratio": 0.72, "is_life": True, "criteria_met": {"structure": True, "replication": True, "purpose": True}, "rate": 460.0, "elapsed_s": 1.3},
        {"interaction": 800, "event": "log", "avg_ops": 55.0, "instruction_density": 0.15, "entropy": 6.2, "compression_ratio": 0.68, "is_life": True, "criteria_met": {"structure": True, "replication": True, "purpose": True}, "rate": 450.0, "elapsed_s": 1.8},
        {"interaction": 1000, "event": "final", "total_ops": 25000, "avg_ops": 50.0, "instruction_density": 0.14, "entropy": 6.5, "compression_ratio": 0.70, "is_life": True, "criteria_met": {"structure": True, "replication": True, "purpose": True}, "elapsed_s": 2.2, "rate": 454.0, "layer_stats": {}},
    ]
    with open(metrics_path, "w") as f:
        for rec in records:
            f.write(json.dumps(rec) + "\n")

    # Create checkpoints dir
    ckpt_dir = tmp_path / "checkpoints"
    ckpt_dir.mkdir()
    # Create empty checkpoint files for inventory
    for name in ["soup_0.npy.npz", "soup_500.npy.npz", "soup_final.npy.npz"]:
        (ckpt_dir / name).touch()

    return tmp_path


class TestExperimentRun:
    """Test ExperimentRun loading and analysis."""

    def test_load(self, mock_experiment):
        run = ExperimentRun(str(mock_experiment))
        run.load()
        assert run.config is not None
        assert run.config["experiment"]["name"] == "mock_run"
        assert len(run.metrics) == 6

    def test_get_final_metrics(self, mock_experiment):
        run = ExperimentRun(str(mock_experiment))
        run.load()
        final = run.get_final_metrics()
        assert final is not None
        assert final["event"] == "final"
        assert final["is_life"] is True

    def test_get_initial_metrics(self, mock_experiment):
        run = ExperimentRun(str(mock_experiment))
        run.load()
        initial = run.get_initial_metrics()
        assert initial is not None
        assert initial["event"] == "initial"
        assert initial["instruction_density"] == 0.03

    def test_get_log_records(self, mock_experiment):
        run = ExperimentRun(str(mock_experiment))
        run.load()
        logs = run.get_log_records()
        assert len(logs) == 4  # 4 log records (not initial/final)

    def test_get_metric_series(self, mock_experiment):
        run = ExperimentRun(str(mock_experiment))
        run.load()
        densities = run.get_metric_series("instruction_density")
        assert len(densities) == 4
        assert densities[0] == 0.04
        assert densities[-1] == 0.15

    def test_detect_life_emergence(self, mock_experiment):
        run = ExperimentRun(str(mock_experiment))
        run.load()
        life = run.detect_life_emergence()
        assert life is not None
        assert life["interaction"] == 600

    def test_generate_report(self, mock_experiment):
        run = ExperimentRun(str(mock_experiment))
        run.load()
        report = run.generate_report()

        assert "PRIMORDIUM EXPERIMENT REPORT" in report
        assert "mock_run" in report
        assert "FINAL STATE" in report
        assert "LIFE EMERGENCE" in report

    def test_load_missing_dir(self):
        run = ExperimentRun("/nonexistent/path")
        with pytest.raises(FileNotFoundError):
            run.load()

    def test_load_empty_dir(self, tmp_path):
        run = ExperimentRun(str(tmp_path))
        run.load()  # Should not raise
        assert run.config is None
        assert run.metrics == []

    def test_checkpoint_discovery(self, mock_experiment):
        run = ExperimentRun(str(mock_experiment))
        run.load()
        assert len(run.checkpoints) == 3


class TestExperimentRunNoLife:
    """Test analysis when life did not emerge."""

    def test_no_life_report(self, tmp_path):
        config_path = tmp_path / "genesis.yaml"
        with open(config_path, "w") as f:
            yaml.dump({"experiment": {"name": "nolife"}}, f)

        metrics_path = tmp_path / "metrics.jsonl"
        records = [
            {"interaction": 0, "event": "initial", "instruction_density": 0.03, "entropy": 7.9, "compression_ratio": 1.05, "is_life": False, "criteria_met": {"structure": False, "replication": False, "purpose": False}},
            {"interaction": 1000, "event": "final", "avg_ops": 3.0, "instruction_density": 0.03, "entropy": 7.9, "compression_ratio": 1.04, "is_life": False, "criteria_met": {"structure": False, "replication": False, "purpose": False}, "elapsed_s": 2.0, "rate": 500.0, "layer_stats": {}},
        ]
        with open(metrics_path, "w") as f:
            for rec in records:
                f.write(json.dumps(rec) + "\n")

        run = ExperimentRun(str(tmp_path))
        run.load()

        assert run.detect_life_emergence() is None

        report = run.generate_report()
        assert "Life did not emerge" in report
