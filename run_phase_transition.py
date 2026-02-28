"""Phase Transition Mapping Experiment.

This script runs PRIMORDIUM for an extended period to map the gelation
phase transition - how the system evolves from random noise to structured programs.

Visualizations:
- Real-time ASCII progress bars
- Checkpoint data for later analysis
- Metrics logged to file
"""

import numpy as np
import time
import os
import sys
from datetime import datetime
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from primordium.chaos import Soup
from primordium.aether import engine

# ============================================================================
# CONFIGURATION
# ============================================================================

EXPERIMENT_NAME = "phase_transition_map"
DURATION_MINUTES = 90  # Run for 90 minutes (1.5 hours)
SOUP_SIZE = 256        # More scrolls = better statistics
TAPE_LENGTH = 48
CHECKPOINT_INTERVAL = 500_000  # Save every 500K
LOG_INTERVAL = 50_000  # Log every 50K

# ============================================================================
# METRICS TRACKING
# ============================================================================

class MetricsTracker:
    """Track and visualize metrics over time."""

    def __init__(self):
        self.history = {
            'interaction': [],
            'time': [],
            'density': [],
            'avg_ops': [],
            'rate': [],
            'instr_right': [],
            'instr_left': [],
            'instr_inc': [],
            'instr_dec': [],
            'instr_loop_start': [],
            'instr_loop_end': [],
            'instr_copy': [],
            'unique_patterns': [],
            'max_complexity': [],
        }
        self.start_time = None
        self.ops_buffer = []
        self.instr_counts = {}

    def reset_instr_counts(self):
        """Reset instruction counters."""
        self.instr_counts = {
            62: 0,  # >
            60: 0,  # <
            43: 0,  # +
            45: 0,  # -
            91: 0,  # [
            93: 0,  # ]
            46: 0,  # .
        }

    def count_instructions(self, tapes):
        """Count instructions in all tapes."""
        self.reset_instr_counts()
        for tape in tapes:
            for code in self.instr_counts:
                self.instr_counts[code] += np.sum(tape == code)

    def record(self, interaction, soup, ops_count):
        """Record metrics at current point."""
        if self.start_time is None:
            self.start_time = time.time()

        # Basic metrics
        density = soup.instruction_density()
        elapsed = time.time() - self.start_time

        # Rate calculation
        self.ops_buffer.append(ops_count)
        if len(self.ops_buffer) > 100:
            self.ops_buffer.pop(0)
        avg_ops = np.mean(self.ops_buffer) if self.ops_buffer else 0
        rate = interaction / elapsed if elapsed > 0 else 0

        # Instruction counts
        tapes = np.array([s.tape for s in soup.scrolls])
        self.count_instructions(tapes)

        # Complexity
        complexities = [np.sum(np.isin(s.tape, list(self.instr_counts.keys()))) for s in soup.scrolls]
        max_complex = max(complexities)

        # Unique patterns (approximate)
        unique = len(np.unique(tapes.view(np.dtype((np.void, tapes.itemsize)))))

        # Store
        self.history['interaction'].append(interaction)
        self.history['time'].append(elapsed)
        self.history['density'].append(density)
        self.history['avg_ops'].append(avg_ops)
        self.history['rate'].append(rate)
        self.history['instr_right'].append(self.instr_counts.get(62, 0))
        self.history['instr_left'].append(self.instr_counts.get(60, 0))
        self.history['instr_inc'].append(self.instr_counts.get(43, 0))
        self.history['instr_dec'].append(self.instr_counts.get(45, 0))
        self.history['instr_loop_start'].append(self.instr_counts.get(91, 0))
        self.history['instr_loop_end'].append(self.instr_counts.get(93, 0))
        self.history['instr_copy'].append(self.instr_counts.get(46, 0))
        self.history['unique_patterns'].append(unique)
        self.history['max_complexity'].append(max_complex)

        return {
            'density': density,
            'avg_ops': avg_ops,
            'rate': rate,
            'elapsed': elapsed,
            'unique': unique,
            'max_complex': max_complex,
        }

# ============================================================================
# VISUALIZATION
# ============================================================================

def print_progress_bar(iteration, total, prefix='', suffix='', length=50, fill='█'):
    """Print a progress bar."""
    percent = f"{100 * (iteration / float(total)):.1f}"
    filled_length = int(length * iteration // total)
    bar = fill * filled_length + '-' * (length - filled_length)
    return f'\r{prefix} |{bar}| {percent}% {suffix}'

def visualize_soup_ascii(soup, width=40, height=10):
    """Create ASCII visualization of the soup.

    Shows instruction density as a heatmap-like representation.
    """
    tapes = np.array([s.tape for s in soup.scrolls])

    # Calculate instruction density per scroll
    instr_codes = [62, 60, 43, 45, 91, 93, 46]
    densities = []
    for tape in tapes:
        count = sum(np.sum(tape == c) for c in instr_codes)
        densities.append(count / len(tape))

    # Create visualization grid
    grid = []
    rows = min(height, len(densities))
    cols = min(width, len(densities[0]) if densities else 1)

    for i in range(rows):
        row_densities = densities[i::rows][:cols] if i < len(densities) else []
        row_str = ""
        for d in row_densities:
            if d < 0.02:
                row_str += " "
            elif d < 0.05:
                row_str += "."
            elif d < 0.10:
                row_str += "░"
            elif d < 0.20:
                row_str += "▒"
            elif d < 0.40:
                row_str += "▓"
            else:
                row_str += "█"
        grid.append(row_str)

    return "\n".join(grid)

def print_instruction_distribution(instr_counts, total_cells):
    """Print instruction distribution as bar chart."""
    labels = {
        62: '>',   # right
        60: '<',   # left
        43: '+',   # inc
        45: '-',   # dec
        91: '[',   # loop start
        93: ']',   # loop end
        46: '.',   # copy
    }

    lines = []
    for code, label in labels.items():
        count = instr_counts.get(code, 0)
        pct = count / total_cells * 100
        bar_len = int(pct / 2)  # Scale for display
        bar = '█' * bar_len
        lines.append(f"  {label}: {bar} {pct:.2f}% ({count})")

    return "\n".join(lines)

def generate_html_visualization(metrics, output_dir):
    """Generate HTML file with interactive charts."""
    import json

    # Convert numpy arrays to lists for JSON
    history = {}
    for k, v in metrics.history.items():
        history[k] = [float(x) if hasattr(x, 'item') else x for x in v]

    html = f"""<!DOCTYPE html>
<html>
<head>
    <title>PRIMORDIUM Phase Transition</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {{ font-family: -apple-system, sans-serif; margin: 20px; background: #1a1a2e; color: #eee; }}
        h1 {{ color: #00d4ff; }}
        .chart-container {{ background: #16213e; padding: 20px; margin: 20px 0; border-radius: 10px; }}
        .stats {{ display: flex; gap: 20px; flex-wrap: wrap; }}
        .stat-box {{ background: #0f3460; padding: 15px; border-radius: 8px; min-width: 150px; }}
        .stat-value {{ font-size: 24px; font-weight: bold; color: #00d4ff; }}
        .stat-label {{ font-size: 12px; color: #aaa; }}
    </style>
</head>
<body>
    <h1>🧬 PRIMORDIUM Phase Transition Analysis</h1>

    <div class="stats">
        <div class="stat-box">
            <div class="stat-value">{len(history.get('interaction', []))}</div>
            <div class="stat-label">Total Data Points</div>
        </div>
        <div class="stat-box">
            <div class="stat-value">{history.get('interaction', [0])[-1]:,.0f}</div>
            <div class="stat-label">Interactions</div>
        </div>
        <div class="stat-box">
            <div class="stat-value">{history.get('density', [0])[-1]:.4f}</div>
            <div class="stat-label">Final Density</div>
        </div>
        <div class="stat-box">
            <div class="stat-value">{history.get('density', [1])[0]:.4f}</div>
            <div class="stat-label">Initial Density</div>
        </div>
    </div>

    <div class="chart-container">
        <canvas id="densityChart"></canvas>
    </div>

    <div class="chart-container">
        <canvas id="instructionsChart"></canvas>
    </div>

    <div class="chart-container">
        <canvas id="rateChart"></canvas>
    </div>

    <script>
        const history = {json.dumps(history)};

        // Density over time
        new Chart(document.getElementById('densityChart'), {{
            type: 'line',
            data: {{
                labels: history.interaction.map(i => i.toLocaleString()),
                datasets: [{{
                    label: 'Instruction Density',
                    data: history.density,
                    borderColor: '#00d4ff',
                    backgroundColor: 'rgba(0,212,255,0.1)',
                    fill: true
                }}]
            }},
            options: {{
                responsive: true,
                plugins: {{ title: {{ display: true, text: 'Instruction Density Over Time' }} }}
            }}
        }});

        // Instructions over time
        new Chart(document.getElementById('instructionsChart'), {{
            type: 'line',
            data: {{
                labels: history.interaction.map(i => i.toLocaleString()),
                datasets: [
                    {{ label: 'Loops [', data: history.instr_loop_start, borderColor: '#ff6b6b' }},
                    {{ label: 'Loops ]', data: history.instr_loop_end, borderColor: '#feca57' }},
                    {{ label: 'Right >', data: history.instr_right, borderColor: '#48dbfb' }},
                    {{ label: 'Left <', data: history.instr_left, borderColor: '#1dd1a1' }}
                ]
            }},
            options: {{
                responsive: true,
                plugins: {{ title: {{ display: true, text: 'Key Instructions Over Time' }} }}
            }}
        }});

        // Rate over time
        new Chart(document.getElementById('rateChart'), {{
            type: 'line',
            data: {{
                labels: history.interaction.map(i => i.toLocaleString()),
                datasets: [{{
                    label: 'Interactions/sec',
                    data: history.rate,
                    borderColor: '#ff9ff3',
                    borderDash: [5, 5]
                }}]
            }},
            options: {{
                responsive: true,
                plugins: {{ title: {{ display: true, text: 'Execution Rate Over Time' }} }}
            }}
        }});
    </script>
</body>
</html>"""

    output_path = Path(output_dir) / "visualization.html"
    with open(output_path, 'w') as f:
        f.write(html)
    print(f"  📊 Generated visualization: {output_path}")

# ============================================================================
# MAIN EXPERIMENT
# ============================================================================

def run_phase_transition_experiment():
    """Run the phase transition mapping experiment."""

    # Setup output directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path(f"./chronicle/{EXPERIMENT_NAME}_{timestamp}")
    output_dir.mkdir(parents=True, exist_ok=True)
    checkpoint_dir = output_dir / "checkpoints"
    checkpoint_dir.mkdir(exist_ok=True)

    print("=" * 70)
    print("🧬 PRIMORDIUM Phase Transition Mapping Experiment")
    print("=" * 70)
    print(f"📁 Output: {output_dir}")
    print(f"⏱️  Duration: {DURATION_MINUTES} minutes")
    print(f"📊 Soup size: {SOUP_SIZE} scrolls")
    print(f"📏 Tape length: {TAPE_LENGTH} bytes")
    print("=" * 70)

    # Initialize soup
    print("\n🔬 Initializing soup...")
    soup = Soup(size=SOUP_SIZE, tape_length=TAPE_LENGTH, seed=42)

    # Initial metrics
    metrics = MetricsTracker()
    initial_tapes = np.array([s.tape for s in soup.scrolls])
    metrics.count_instructions(initial_tapes)

    initial_density = soup.instruction_density()
    print(f"✅ Initialized {len(soup.scrolls)} scrolls")
    print(f"📊 Initial density: {initial_density:.4f}")

    # Save initial state
    initial_path = checkpoint_dir / "soup_0.npy"
    soup.save(str(initial_path))

    # Calculate total interactions
    # At ~100K int/s, 30 min = ~180M interactions
    # Let's target a reasonable number based on time
    target_interactions = int(100_000 * 60 * DURATION_MINUTES)

    print(f"🎯 Target: {target_interactions:,} interactions")
    print(f"⏱️  Estimated time: {target_interactions / 100_000 / 60:.1f} minutes")
    print("=" * 70)

    # Main loop
    start_time = time.time()
    last_log_time = start_time
    interaction = 0

    try:
        while interaction < target_interactions:
            # Run a batch
            batch_size = 10_000
            for _ in range(batch_size):
                ops = soup.interact(max_steps=350)
                interaction += 1

                # Check for checkpoint
                if interaction % CHECKPOINT_INTERVAL == 0:
                    checkpoint_path = checkpoint_dir / f"soup_{interaction}.npy"
                    soup.save(str(checkpoint_path))

                # Log metrics
                if interaction % LOG_INTERVAL == 0:
                    m = metrics.record(interaction, soup, ops)

                    # Time elapsed
                    elapsed = time.time() - start_time
                    remaining = (target_interactions - interaction) / m['rate'] if m['rate'] > 0 else 0

                    # Clear and print status
                    print("\033[H\033[J", end="")  # Clear screen

                    print("=" * 70)
                    print("🧬 PRIMORDIUM Phase Transition - Live Dashboard")
                    print("=" * 70)

                    # Progress bar
                    progress = interaction / target_interactions
                    bar_len = 40
                    filled = int(bar_len * progress)
                    bar = '█' * filled + '░' * (bar_len - filled)

                    print(f"\nProgress: |{bar}| {progress*100:.1f}%")
                    print(f"Time: {elapsed/60:.1f} min elapsed | ~{remaining/60:.1f} min remaining")

                    print(f"\n📊 Core Metrics:")
                    print(f"  Interactions: {interaction:,} / {target_interactions:,}")
                    print(f"  Rate: {m['rate']:,.0f} int/s")
                    print(f"  Density: {m['density']:.4f} (started: {initial_density:.4f}, ×{m['density']/initial_density:.2f})")
                    print(f"  Avg ops: {m['avg_ops']:.1f}")
                    print(f"  Unique patterns: {m['unique']}")
                    print(f"  Max complexity: {m['max_complex']}")

                    print(f"\n📈 Instruction Distribution:")
                    total_cells = SOUP_SIZE * TAPE_LENGTH
                    print(print_instruction_distribution(metrics.instr_counts, total_cells))

                    print(f"\n📁 Checkpoints: {checkpoint_dir}")
                    print("=" * 70)

                    # Save metrics
                    import pickle
                    metrics_path = output_dir / "metrics.pkl"
                    with open(metrics_path, 'wb') as f:
                        pickle.dump(metrics.history, f)

            # Check if time's up
            elapsed = time.time() - start_time
            if elapsed >= DURATION_MINUTES * 60:
                break

    except KeyboardInterrupt:
        print("\n\n⚠️  Experiment interrupted by user")

    # Final save
    print("\n💾 Saving final state...")
    final_path = checkpoint_dir / "soup_final.npy"
    soup.save(str(final_path))

    # Generate visualization
    print("\n🎨 Generating visualization...")
    generate_html_visualization(metrics, output_dir)

    # Final summary
    elapsed = time.time() - start_time

    print("\n" + "=" * 70)
    print("📊 EXPERIMENT COMPLETE - FINAL RESULTS")
    print("=" * 70)
    print(f"Total interactions: {interaction:,}")
    print(f"Total time: {elapsed/60:.1f} minutes")
    print(f"Average rate: {interaction/elapsed:,.0f} int/s")
    print(f"\nDensity evolution:")
    print(f"  Initial: {initial_density:.4f}")
    print(f"  Final: {metrics.history['density'][-1]:.4f}")
    print(f"  Change: ×{metrics.history['density'][-1]/initial_density:.2f}")
    print(f"\nComplexity evolution:")
    print(f"  Initial max: {metrics.history['max_complexity'][0]}")
    print(f"  Final max: {metrics.history['max_complexity'][-1]}")
    print(f"\n📁 Output: {output_dir}")
    print("=" * 70)

    return metrics, output_dir

if __name__ == '__main__':
    metrics, output_dir = run_phase_transition_experiment()
