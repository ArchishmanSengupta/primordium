"""CLI for PRIMORDIUM.

Command-line interface for running experiments and analyzing results.
"""

from __future__ import annotations

import click
import logging
import os
import sys
import time
from typing import Any, Dict, Optional

from primordium.metrics.writer import MetricsWriter

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def _metrics_record(
    interaction: int,
    event: str,
    soup,
    thresholds: Dict[str, float],
    **extra: Any,
) -> Dict[str, Any]:
    from primordium.metrics import soup_entropy, detect_life_criteria

    criteria = detect_life_criteria(
        soup,
        instruction_density_threshold=thresholds.get("instruction_density", 0.1),
        replicator_fraction_threshold=thresholds.get("replicator_fraction", 0.05),
        compression_ratio_threshold=thresholds.get("compression_ratio", 0.8),
    )
    record: Dict[str, Any] = {
        "interaction": interaction,
        "event": event,
        "instruction_density": criteria["instruction_density"],
        "entropy": soup_entropy(soup),
        "compression_ratio": criteria["compression_ratio"],
        "is_life": criteria["is_life"],
        "criteria_met": criteria["criteria_met"],
    }
    record.update(extra)
    return record


def setup_logging(level: str) -> None:
    """Set up logging configuration.

    Args:
        level: Log level (debug, info, warning, error)
    """
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(
        level=numeric_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


@click.group()
def cli():
    """PRIMORDIUM - Recursive self-improving AI through symbiogenetic computation."""
    pass


@cli.command()
@click.argument('config_file', type=click.Path(exists=True))
@click.option('--resume', is_flag=True, help='Resume from checkpoint')
def run(config_file: str, resume: bool):
    """Run a PRIMORDIUM experiment.

    CONFIG_FILE: Path to genesis.yaml configuration file
    """
    from primordium.config import load_config
    from primordium.chaos import Soup
    from primordium.metrics import (
        soup_entropy,
        instruction_density as calc_instruction_density,
        soup_compression_ratio,
        detect_life_criteria,
    )

    # Load configuration
    try:
        config = load_config(config_file)
    except Exception as e:
        click.echo(f"Error loading config: {e}", err=True)
        sys.exit(1)

    # Set up logging
    setup_logging(config.logging.level)

    # Create output directory
    output_dir = config.experiment.output_dir
    os.makedirs(output_dir, exist_ok=True)
    logger.info(f"Output directory: {output_dir}")

    # Determine backend
    backend = config.aether.backend
    device = config.aether.device

    # Check backend availability and use best available
    if backend == 'python':
        # Try to use C backend for speed
        try:
            from primordium.aether import engine
            if engine.get_engine() is not None:
                logger.info("C backend available, using C backend")
                backend = 'c'
        except Exception:
            pass

    if backend == 'cuda':
        try:
            import torch
            if not torch.cuda.is_available():
                logger.warning("CUDA not available, falling back to C backend")
                backend = 'c'
        except ImportError:
            logger.warning("PyTorch not available, falling back to C backend")
            backend = 'c'

    # For C backend, patch the Soup class
    use_c_backend = (backend == 'c')

    logger.info(f"Using backend: {backend}")
    if backend == 'cuda':
        logger.info(f"CUDA device: {device}")

    # Initialize soup
    seed = config.experiment.seed
    logger.info(f"Initializing soup with {config.chaos.size} scrolls, tape_length={config.chaos.tape_length}")
    soup = Soup(
        size=config.chaos.size,
        tape_length=config.chaos.tape_length,
        seed=seed,
        mutation_rate=config.apeiron.mutation_rate,
    )

    # Patch to use C backend if available
    if use_c_backend:
        from primordium.aether import engine as c_engine


        def c_interact(self, max_steps=350):
            i, j = self.select_pair()
            scroll_i = self.scrolls[i]
            scroll_j = self.scrolls[j]

            new_i, new_j, steps = c_engine.run_bf_c(
                scroll_i.tape,
                scroll_j.tape,
                max_steps=max_steps,
                tape_length=self.tape_length
            )

            self.scrolls[i].tape = new_i
            self.scrolls[j].tape = new_j
            return steps

        Soup.interact = c_interact
        logger.info("Using C backend for interactions")

    # Get thresholds from config
    thresholds = config.metrics.life_criteria_thresholds

    # Calculate initial metrics
    initial_density = soup.instruction_density()
    initial_entropy = soup_entropy(soup)
    initial_comp_ratio = soup_compression_ratio(soup, sample_size=min(50, config.chaos.size))
    initial_criteria = detect_life_criteria(
        soup,
        instruction_density_threshold=thresholds.get("instruction_density", 0.1),
        replicator_fraction_threshold=thresholds.get("replicator_fraction", 0.05),
        compression_ratio_threshold=thresholds.get("compression_ratio", 0.8),
    )

    logger.info("=" * 60)
    logger.info("INITIAL STATE")
    logger.info("=" * 60)
    logger.info(f"Instruction density: {initial_density:.4f}")
    logger.info(f"Entropy: {initial_entropy:.4f}")
    logger.info(f"Compression ratio: {initial_comp_ratio:.4f}")
    logger.info(f"Life criteria met: {initial_criteria['criteria_met']}")

    metrics_writer = MetricsWriter(output_dir)
    metrics_writer.open(append=False)
    metrics_writer.write(
        _metrics_record(0, "initial", soup, thresholds)
    )

    # Save initial checkpoint
    checkpoint_dir = os.path.join(output_dir, 'checkpoints')
    os.makedirs(checkpoint_dir, exist_ok=True)
    initial_path = os.path.join(checkpoint_dir, 'soup_0.npz')
    soup.save(initial_path)
    logger.info(f"Saved initial state to {initial_path}")

    # Run main loop
    interactions_total = config.aether.interactions_total
    checkpoint_every = config.aether.checkpoint_every
    max_steps = config.aether.max_steps_per_interaction
    log_interval = config.metrics.log_interval

    logger.info(f"Running {interactions_total} interactions...")

    start_time = time.time()
    ops_history = []

    for i in range(interactions_total):
        steps = soup.interact(max_steps=max_steps)
        ops_history.append(steps)

        # Log progress
        if (i + 1) % log_interval == 0:
            avg_ops = sum(ops_history[-log_interval:]) / log_interval
            elapsed = time.time() - start_time
            rate = (i + 1) / elapsed

            current_density = calc_instruction_density(soup)
            current_entropy = soup_entropy(soup)
            current_comp_ratio = soup_compression_ratio(soup, sample_size=min(50, config.chaos.size))
            current_criteria = detect_life_criteria(
                soup,
                instruction_density_threshold=thresholds.get("instruction_density", 0.1),
                replicator_fraction_threshold=thresholds.get("replicator_fraction", 0.05),
                compression_ratio_threshold=thresholds.get("compression_ratio", 0.8),
            )

            # Build log message
            log_msg = (
                f"Interaction {i+1}/{interactions_total} | "
                f"Avg ops: {avg_ops:.1f} | "
                f"Density: {current_density:.4f} | "
                f"Entropy: {current_entropy:.4f} | "
                f"Comp ratio: {current_comp_ratio:.4f} | "
                f"Life: {current_criteria['is_life']} | "
                f"Rate: {rate:.1f} int/s"
            )

            # Add criteria details
            if current_criteria['is_life']:
                log_msg += " *** LIFE EMERGED ***"

            logger.info(log_msg)
            metrics_writer.write(
                _metrics_record(
                    i + 1,
                    "log",
                    soup,
                    thresholds,
                    avg_ops=avg_ops,
                    rate=rate,
                    elapsed_s=elapsed,
                )
            )

        # Checkpoint
        if (i + 1) % checkpoint_every == 0:
            checkpoint_path = os.path.join(checkpoint_dir, f'soup_{i+1}.npz')
            soup.save(checkpoint_path)

    # Save final checkpoint
    final_path = os.path.join(checkpoint_dir, 'soup_final.npz')
    soup.save(final_path)

    # Final metrics
    final_density = calc_instruction_density(soup)
    final_entropy = soup_entropy(soup)
    final_comp_ratio = soup_compression_ratio(soup, sample_size=min(50, config.chaos.size))
    final_criteria = detect_life_criteria(
        soup,
        instruction_density_threshold=thresholds.get("instruction_density", 0.1),
        replicator_fraction_threshold=thresholds.get("replicator_fraction", 0.05),
        compression_ratio_threshold=thresholds.get("compression_ratio", 0.8),
    )

    total_ops = sum(ops_history)
    avg_ops_final = total_ops / interactions_total
    elapsed = time.time() - start_time

    logger.info("=" * 60)
    logger.info("EXPERIMENT COMPLETE")
    logger.info("=" * 60)
    logger.info(f"Total interactions: {interactions_total}")
    logger.info(f"Total operations: {total_ops}")
    logger.info(f"Average ops/interaction: {avg_ops_final:.2f}")
    logger.info("")
    logger.info("FINAL STATE:")
    logger.info(f"  Instruction density: {initial_density:.4f} -> {final_density:.4f}")
    logger.info(f"  Entropy: {initial_entropy:.4f} -> {final_entropy:.4f}")
    logger.info(f"  Compression ratio: {initial_comp_ratio:.4f} -> {final_comp_ratio:.4f}")
    logger.info(f"  Life criteria: {final_criteria['criteria_met']}")
    logger.info(f"  Life emerged: {final_criteria['is_life']}")
    logger.info("")
    logger.info(f"Elapsed time: {elapsed:.1f}s")
    logger.info(f"Rate: {interactions_total/elapsed:.1f} int/s")
    logger.info(f"Output: {output_dir}")
    metrics_writer.write(
        _metrics_record(
            interactions_total,
            "final",
            soup,
            thresholds,
            total_ops=total_ops,
            avg_ops=avg_ops_final,
            elapsed_s=elapsed,
            rate=interactions_total / elapsed if elapsed > 0 else 0.0,
            layer_stats={},
        )
    )
    metrics_writer.close()
    logger.info(f"Metrics log: {metrics_writer.path}")

    # Save config copy
    from primordium.config import save_config
    config_path = os.path.join(output_dir, 'genesis.yaml')
    save_config(config, config_path)

    click.echo(f"\nExperiment complete! Results saved to: {output_dir}")


@cli.command()
@click.argument('results_dir', type=click.Path(exists=True))
@click.option('--interactive', is_flag=True, help='Open interactive dashboard')
def analyse(results_dir: str, interactive: bool):
    """Analyze experiment results.

    RESULTS_DIR: Path to experiment output directory
    """
    from primordium.oracle import ExperimentRun

    run = ExperimentRun(results_dir)
    run.load()
    report = run.generate_report()
    click.echo(report)
    if interactive:
        click.echo("(Interactive dashboard not yet implemented)")


@cli.command()
@click.argument('results_dir', type=click.Path(exists=True))
@click.option('--at', type=int, help='Interaction count to replay')
def replay(results_dir: str, at: Optional[int]):
    """Replay experiment at specific interaction.

    RESULTS_DIR: Path to experiment output directory
    """
    if at is None:
        click.echo("Error: --at option required", err=True)
        sys.exit(1)

    click.echo(f"Replaying at interaction {at}")
    click.echo("(Replay not yet implemented)")


@cli.command()
@click.argument('result1', type=click.Path(exists=True))
@click.argument('result2', type=click.Path(exists=True))
def compare(result1: str, result2: str):
    """Compare two experiment results."""
    click.echo(f"Comparing {result1} and {result2}")
    click.echo("(Comparison not yet implemented)")


@cli.command()
def benchmark():
    """Run speed benchmarks on all available backends."""
    click.echo("Running benchmarks...")

    from primordium.chaos import Soup
    import time

    soup = Soup(size=256, tape_length=48, seed=42)

    start = time.time()
    for _ in range(1000):
        soup.interact(max_steps=350)
    elapsed = time.time() - start

    rate = 1000 / elapsed
    click.echo(f"Python backend: {rate:.1f} interactions/second")

    from primordium.aether import engine as c_engine

    if c_engine.get_engine() is None:
        click.echo("C backend: unavailable (gcc or engine.c missing)")
        return

    original_interact = Soup.interact

    def c_interact(self, max_steps=350):
        i, j = self.select_pair()
        scroll_i = self.scrolls[i]
        scroll_j = self.scrolls[j]
        new_i, new_j, steps = c_engine.run_bf_c(
            scroll_i.tape,
            scroll_j.tape,
            max_steps=max_steps,
            tape_length=self.tape_length,
        )
        self.scrolls[i].tape = new_i
        self.scrolls[j].tape = new_j
        return steps

    Soup.interact = c_interact
    try:
        soup_c = Soup(size=256, tape_length=48, seed=42)
        start = time.time()
        for _ in range(1000):
            soup_c.interact(max_steps=350)
        elapsed = time.time() - start
        click.echo(f"C backend: {1000 / elapsed:.1f} interactions/second")
    finally:
        Soup.interact = original_interact


@cli.command()
@click.argument('config_file', type=click.Path(exists=True))
def validate(config_file: str):
    """Validate a configuration file.

    CONFIG_FILE: Path to genesis.yaml configuration file
    """
    from primordium.config import load_config

    try:
        config = load_config(config_file)
        click.echo("Configuration is valid!")
        click.echo(f"  Experiment: {config.experiment.name}")
        click.echo(f"  Soup size: {config.chaos.size}")
        click.echo(f"  Tape length: {config.chaos.tape_length}")
        click.echo(f"  Interactions: {config.aether.interactions_total}")
        click.echo(f"  Backend: {config.aether.backend}")
    except Exception as e:
        click.echo(f"Configuration error: {e}", err=True)
        sys.exit(1)


def main():
    """Main entry point."""
    cli()


if __name__ == '__main__':
    main()
