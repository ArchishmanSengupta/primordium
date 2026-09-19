from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml


class ExperimentRun:
    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        self.config: Optional[Dict[str, Any]] = None
        self.metrics: List[Dict[str, Any]] = []
        self.checkpoints: List[str] = []

    def load(self) -> None:
        root = Path(self.output_dir)
        if not root.exists():
            raise FileNotFoundError(f"Experiment directory not found: {self.output_dir}")

        config_path = root / "genesis.yaml"
        if config_path.exists():
            with open(config_path, encoding="utf-8") as handle:
                self.config = yaml.safe_load(handle)
        else:
            self.config = None

        metrics_path = root / "metrics.jsonl"
        self.metrics = []
        if metrics_path.exists():
            with open(metrics_path, encoding="utf-8") as handle:
                for line in handle:
                    line = line.strip()
                    if line:
                        self.metrics.append(json.loads(line))

        ckpt_dir = root / "checkpoints"
        self.checkpoints = []
        if ckpt_dir.is_dir():
            self.checkpoints = sorted(p.name for p in ckpt_dir.iterdir() if p.is_file())

    def get_final_metrics(self) -> Optional[Dict[str, Any]]:
        for record in reversed(self.metrics):
            if record.get("event") == "final":
                return record
        return None

    def get_initial_metrics(self) -> Optional[Dict[str, Any]]:
        for record in self.metrics:
            if record.get("event") == "initial":
                return record
        return None

    def get_log_records(self) -> List[Dict[str, Any]]:
        return [r for r in self.metrics if r.get("event") == "log"]

    def get_metric_series(self, key: str) -> List[Any]:
        return [r[key] for r in self.get_log_records() if key in r]

    def detect_life_emergence(self) -> Optional[Dict[str, Any]]:
        for record in self.metrics:
            if record.get("is_life"):
                return record
        return None

    def generate_report(self) -> str:
        name = "unknown"
        if self.config and "experiment" in self.config:
            name = self.config["experiment"].get("name", name)

        lines = [
            "PRIMORDIUM EXPERIMENT REPORT",
            "=" * 40,
            f"Experiment: {name}",
            f"Directory: {self.output_dir}",
            "",
            "FINAL STATE",
            "-" * 40,
        ]

        final = self.get_final_metrics()
        if final:
            lines.append(f"Interactions: {final.get('interaction', '?')}")
            lines.append(f"Instruction density: {final.get('instruction_density', 0):.4f}")
            lines.append(f"Entropy: {final.get('entropy', 0):.4f}")
            lines.append(f"Compression ratio: {final.get('compression_ratio', 0):.4f}")
            lines.append(f"Life emerged: {final.get('is_life', False)}")
        else:
            lines.append("No final metrics recorded.")

        lines.extend(["", "LIFE EMERGENCE", "-" * 40])
        life = self.detect_life_emergence()
        if life:
            lines.append(f"First detected at interaction {life.get('interaction', '?')}")
        else:
            lines.append("Life did not emerge during this run.")

        if self.checkpoints:
            lines.extend(["", f"Checkpoints: {len(self.checkpoints)}"])

        return "\n".join(lines)
