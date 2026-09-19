#!/usr/bin/env python3
"""PRIMORDIUM Visualization Generator.

Loads checkpoint data from a chronicle run and generates a self-contained
HTML visualization with cinematic aesthetic.

Usage:
    python scripts/generate_viz.py chronicle/5min_test
    python scripts/generate_viz.py chronicle/phase_transition_map_20260227_093854
    python scripts/generate_viz.py chronicle/5min_test -o outputs/viz/5min_test.html
"""

import argparse
import json
import math
import os
import re
import sys
import zlib
from collections import Counter
from pathlib import Path

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_VIZ_DIR = PROJECT_ROOT / "outputs" / "viz"
TEMPLATE_PATH = Path(__file__).parent / "templates" / "viz.html"

# BrainFuck valid operations
VALID_OPS = {62, 60, 43, 45, 91, 93, 46}
OP_NAMES = {
    62: ">", 60: "<", 43: "+", 45: "-",
    91: "[", 93: "]", 46: "."
}


def natural_sort_key(s):
    """Sort strings with embedded numbers naturally."""
    return [
        int(text) if text.isdigit() else text.lower()
        for text in re.split(r"(\d+)", str(s))
    ]


def load_checkpoint(path):
    """Load a checkpoint .npz file and return the scrolls array."""
    data = np.load(path, allow_pickle=True)
    return data["scrolls"].astype(np.uint8)


def compute_entropy(tape):
    """Shannon entropy of a single tape."""
    if len(tape) == 0:
        return 0.0
    counts = Counter(tape)
    total = len(tape)
    entropy = 0.0
    for count in counts.values():
        if count > 0:
            p = count / total
            entropy -= p * math.log2(p)
    return entropy


def compute_metrics_for_snapshot(scrolls):
    """Compute all metrics for a soup snapshot (2D numpy array)."""
    n_scrolls, tape_length = scrolls.shape
    total_bytes = n_scrolls * tape_length

    # Instruction density per scroll
    per_scroll_density = []
    total_valid = 0
    for i in range(n_scrolls):
        valid = sum(1 for b in scrolls[i] if b in VALID_OPS)
        total_valid += valid
        per_scroll_density.append(valid / tape_length)

    instruction_density = total_valid / total_bytes

    # Entropy per scroll, then average
    entropies = [compute_entropy(scrolls[i]) for i in range(n_scrolls)]
    avg_entropy = float(np.mean(entropies))

    # Compression ratio (sample up to 50)
    sample_idx = np.random.choice(n_scrolls, size=min(50, n_scrolls), replace=False)
    comp_ratios = []
    for idx in sample_idx:
        raw = scrolls[idx].tobytes()
        compressed = zlib.compress(raw)
        comp_ratios.append(len(compressed) / len(raw))
    avg_compression = float(np.mean(comp_ratios))

    # Replicator detection
    tape_counts = Counter()
    for i in range(n_scrolls):
        key = scrolls[i].tobytes()
        tape_counts[key] += 1

    # Count scrolls that are part of a replicator group (count >= 2)
    replicator_count = sum(c for c in tape_counts.values() if c >= 2)
    replicator_fraction = replicator_count / n_scrolls

    # Unique programs
    unique_count = len(tape_counts)

    # Top replicators (top 10 by count)
    sorted_reps = sorted(tape_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    top_reps = [{"count": c, "density": sum(1 for b in k if b in VALID_OPS) / tape_length}
                for k, c in sorted_reps]

    # Instruction distribution
    instr_dist = {OP_NAMES[op]: 0 for op in VALID_OPS}
    for i in range(n_scrolls):
        for b in scrolls[i]:
            if b in VALID_OPS:
                instr_dist[OP_NAMES[b]] += 1

    # Per-scroll density as flat list (for heatmap)
    # Reshape into grid dimensions
    grid_side = int(math.ceil(math.sqrt(n_scrolls)))
    padded_density = per_scroll_density + [0.0] * (grid_side * grid_side - n_scrolls)

    return {
        "instruction_density": instruction_density,
        "entropy": avg_entropy,
        "compression_ratio": avg_compression,
        "replicator_fraction": replicator_fraction,
        "unique_programs": unique_count,
        "top_replicators": top_reps,
        "instr_dist": instr_dist,
        "per_scroll_density": padded_density,
        "grid_side": grid_side,
    }


def extract_tape_visualization(scrolls, index=0):
    """Extract a tape as categorized bytes for visualization."""
    tape = scrolls[index]
    result = []
    for b in tape:
        if b in VALID_OPS:
            result.append({"value": int(b), "type": OP_NAMES[b], "is_op": True})
        else:
            result.append({"value": int(b), "type": "nop", "is_op": False})
    return result


def find_most_replicated(scrolls):
    """Find the index of the most-replicated scroll."""
    tape_counts = Counter()
    tape_to_idx = {}
    for i in range(scrolls.shape[0]):
        key = scrolls[i].tobytes()
        tape_counts[key] += 1
        if key not in tape_to_idx:
            tape_to_idx[key] = i
    if not tape_counts:
        return 0
    most_common_key = tape_counts.most_common(1)[0][0]
    return tape_to_idx[most_common_key]


def process_run(run_dir):
    """Process an entire run directory and return visualization data."""
    run_path = Path(run_dir)
    checkpoint_dir = run_path / "checkpoints"

    if not checkpoint_dir.exists():
        print(f"Error: No checkpoints directory found in {run_dir}")
        sys.exit(1)

    # Find all checkpoint files
    checkpoint_files = sorted(
        checkpoint_dir.glob("soup_*.npy.npz"),
        key=natural_sort_key
    )

    if not checkpoint_files:
        print(f"Error: No checkpoint files found in {checkpoint_dir}")
        sys.exit(1)

    print(f"Found {len(checkpoint_files)} checkpoints in {run_dir}")

    # Extract interaction counts from filenames
    timeline = []
    all_heatmaps = []
    np.random.seed(42)  # Reproducible sampling for compression

    for i, cp_file in enumerate(checkpoint_files):
        name = cp_file.stem.replace(".npy", "")
        # Extract number from filename like soup_1000000
        match = re.search(r"soup_(\d+)", name)
        if match:
            interaction = int(match.group(1))
        elif "final" in name:
            # Use the previous interaction count + estimated step
            if timeline:
                interaction = timeline[-1]["interaction"] + 1000000
            else:
                interaction = 0
        else:
            interaction = i

        print(f"  [{i+1}/{len(checkpoint_files)}] Processing {name} (interaction {interaction:,})...")

        scrolls = load_checkpoint(str(cp_file))
        metrics = compute_metrics_for_snapshot(scrolls)

        timeline.append({
            "interaction": interaction,
            "instruction_density": metrics["instruction_density"],
            "entropy": metrics["entropy"],
            "compression_ratio": metrics["compression_ratio"],
            "replicator_fraction": metrics["replicator_fraction"],
            "unique_programs": metrics["unique_programs"],
            "top_replicators": metrics["top_replicators"],
            "instr_dist": metrics["instr_dist"],
        })

        all_heatmaps.append({
            "interaction": interaction,
            "density_grid": metrics["per_scroll_density"],
            "grid_side": metrics["grid_side"],
        })

    # Tape diff: first checkpoint scroll 0 vs last checkpoint most-replicated
    first_scrolls = load_checkpoint(str(checkpoint_files[0]))
    last_scrolls = load_checkpoint(str(checkpoint_files[-1]))

    tape_before = extract_tape_visualization(first_scrolls, index=0)
    most_rep_idx = find_most_replicated(last_scrolls)
    tape_after = extract_tape_visualization(last_scrolls, index=most_rep_idx)

    # Run metadata
    n_scrolls = first_scrolls.shape[0]
    tape_length = first_scrolls.shape[1]

    return {
        "meta": {
            "run_dir": str(run_path.name),
            "n_scrolls": n_scrolls,
            "tape_length": tape_length,
            "n_checkpoints": len(checkpoint_files),
            "total_interactions": timeline[-1]["interaction"] if timeline else 0,
        },
        "timeline": timeline,
        "heatmaps": all_heatmaps,
        "tape_diff": {
            "before": tape_before,
            "after": tape_after,
            "after_index": most_rep_idx,
            "after_copies": Counter(
                last_scrolls[i].tobytes() for i in range(last_scrolls.shape[0])
            ).most_common(1)[0][1] if last_scrolls.shape[0] > 0 else 0,
        },
    }


def generate_html(data, output_path):
    """Generate the self-contained HTML visualization."""
    if not TEMPLATE_PATH.exists():
        print(f"Error: Template not found at {TEMPLATE_PATH}")
        sys.exit(1)

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(TEMPLATE_PATH, "r") as f:
        html = f.read()

    # Inject data
    data_json = json.dumps(data, separators=(",", ":"))
    html = html.replace("/*__PRIMORDIUM_DATA__*/", f"const DATA = {data_json};")

    with open(output_path, "w") as f:
        f.write(html)

    print(f"\nVisualization written to: {output_path}")
    print(f"Open in browser: file://{Path(output_path).resolve()}")


def main():
    parser = argparse.ArgumentParser(description="Generate PRIMORDIUM visualizations")
    parser.add_argument("run_dir", help="Path to chronicle run directory")
    parser.add_argument("--output", "-o", default=None, help="Output HTML path")
    args = parser.parse_args()

    run_dir = Path(args.run_dir)
    if not run_dir.is_absolute():
        run_dir = (PROJECT_ROOT / run_dir).resolve()

    if args.output is None:
        run_name = run_dir.name
        args.output = str(DEFAULT_VIZ_DIR / f"{run_name}.html")
    else:
        out = Path(args.output)
        if not out.is_absolute():
            args.output = str((PROJECT_ROOT / out).resolve())

    data = process_run(str(run_dir))
    generate_html(data, args.output)


if __name__ == "__main__":
    main()
