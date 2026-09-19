#!/usr/bin/env python3
"""Generate README figure assets from a chronicle run's metrics.jsonl.

Reads the metrics log of a completed experiment run and renders two PNGs:

  - metrics_evolution.png: entropy, instruction density, compression ratio
    and throughput over interactions
  - life_criteria.png: the three operational life criteria against their
    thresholds

Usage:
    python scripts/generate_readme_figures.py chronicle/<run_dir> -o docs/assets
"""

import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def load_metrics(run_dir: Path) -> list[dict]:
    metrics_path = run_dir / "metrics.jsonl"
    if not metrics_path.exists():
        raise SystemExit(f"No metrics.jsonl found in {run_dir}")
    records = []
    with open(metrics_path, encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def plot_metrics_evolution(records: list[dict], run_name: str, out_path: Path) -> None:
    log = [r for r in records if r.get("event") == "log"]
    x = [r["interaction"] for r in log]

    fig, axes = plt.subplots(2, 2, figsize=(11, 7.5))
    fig.suptitle(f"PRIMORDIUM run: {run_name}", fontsize=13, fontweight="bold")

    panels = [
        ("entropy", "Shannon entropy (bits/byte)", axes[0][0]),
        ("instruction_density", "Instruction density", axes[0][1]),
        ("compression_ratio", "Compression ratio (zlib)", axes[1][0]),
        ("rate", "Throughput (interactions/s)", axes[1][1]),
    ]
    for key, label, ax in panels:
        y = [r.get(key) for r in log]
        ax.plot(x, y, color="#0f766e", linewidth=1.6)
        ax.set_title(label, fontsize=10)
        ax.set_xlabel("Interactions", fontsize=9)
        ax.grid(alpha=0.25)
        if key == "instruction_density":
            ax.axhline(0.1, color="#dc2626", linestyle="--", linewidth=1, label="life threshold (0.10)")
            ax.legend(fontsize=8)
        if key == "compression_ratio":
            ax.axhline(0.8, color="#dc2626", linestyle="--", linewidth=1, label="life threshold (0.80)")
            ax.legend(fontsize=8)

    fig.tight_layout(rect=[0, 0, 1, 0.96])
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def plot_life_criteria(records: list[dict], run_name: str, out_path: Path) -> None:
    log = [r for r in records if r.get("event") == "log"]
    x = [r["interaction"] for r in log]

    density = [r.get("instruction_density", 0.0) for r in log]
    comp = [r.get("compression_ratio", 1.0) for r in log]

    replicator_values = []
    for r in log:
        criteria = r.get("criteria_met", {})
        replicator_values.append(1.0 if criteria.get("replication") else 0.0)

    fig, axes = plt.subplots(1, 3, figsize=(12, 3.6))
    fig.suptitle(f"Operational life criteria: {run_name}", fontsize=12, fontweight="bold")

    axes[0].plot(x, density, color="#0f766e", linewidth=1.6)
    axes[0].axhline(0.1, color="#dc2626", linestyle="--", linewidth=1)
    axes[0].set_title("Structure: density >= 0.10", fontsize=9)

    axes[1].plot(x, replicator_values, color="#7c3aed", linewidth=1.2)
    axes[1].set_title("Replication: fraction >= 0.05", fontsize=9)
    axes[1].set_yticks([0, 1])
    axes[1].set_yticklabels(["not met", "met"])

    axes[2].plot(x, comp, color="#0f766e", linewidth=1.6)
    axes[2].axhline(0.8, color="#dc2626", linestyle="--", linewidth=1)
    axes[2].set_title("Purpose: compression <= 0.80", fontsize=9)

    for ax in axes:
        ax.set_xlabel("Interactions", fontsize=8)
        ax.grid(alpha=0.25)

    fig.tight_layout(rect=[0, 0, 1, 0.92])
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description="Generate README figures from a run")
    parser.add_argument("run_dir", help="Path to chronicle run directory")
    parser.add_argument("--output-dir", "-o", default="docs/assets", help="Output directory for PNGs")
    args = parser.parse_args()

    run_dir = Path(args.run_dir)
    if not run_dir.is_absolute():
        run_dir = (PROJECT_ROOT / run_dir).resolve()
    out_dir = Path(args.output_dir)
    if not out_dir.is_absolute():
        out_dir = PROJECT_ROOT / out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    records = load_metrics(run_dir)
    run_name = run_dir.name

    plot_metrics_evolution(records, run_name, out_dir / "metrics_evolution.png")
    plot_life_criteria(records, run_name, out_dir / "life_criteria.png")
    print(f"Wrote {out_dir / 'metrics_evolution.png'}")
    print(f"Wrote {out_dir / 'life_criteria.png'}")


if __name__ == "__main__":
    main()
