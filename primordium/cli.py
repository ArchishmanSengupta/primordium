"""CLI for PRIMORDIUM.

Command-line interface for running experiments and analyzing results.
"""

from __future__ import annotations

import click
import logging
import os
import sys
import time
from pathlib import Path
from typing import Optional

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


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
    )

    # Patch to use C backend if available
    if use_c_backend:
        from primordium.aether import engine as c_engine

        original_interact = Soup.interact

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

    # Calculate initial metrics
    initial_density = soup.instruction_density()
    logger.info(f"Initial instruction density: {initial_density:.4f}")

    # Save initial checkpoint
    checkpoint_dir = os.path.join(output_dir, 'checkpoints')
    os.makedirs(checkpoint_dir, exist_ok=True)
    initial_path = os.path.join(checkpoint_dir, 'soup_0.npy')
    soup.save(initial_path)
    logger.info(f"Saved initial state to {initial_path}")

    # Run main loop
    interactions_total = config.aether.interactions_total
    checkpoint_every = config.aether.checkpoint_every
    max_steps = config.aether.max_steps_per_interaction

    logger.info(f"Running {interactions_total} interactions...")

    start_time = time.time()
    ops_history = []

    for i in range(interactions_total):
        steps = soup.interact(max_steps=max_steps)
        ops_history.append(steps)

        # Log progress
        if (i + 1) % config.metrics.log_interval == 0:
            avg_ops = sum(ops_history[-config.metrics.log_interval:]) / config.metrics.log_interval
            elapsed = time.time() - start_time
            rate = (i + 1) / elapsed

            current_density = soup.instruction_density()

            logger.info(
                f"Interaction {i+1}/{interactions_total} | "
                f"Avg ops: {avg_ops:.1f} | "
                f"Density: {current_density:.4f} | "
                f"Rate: {rate:.1f} int/s"
            )

        # Checkpoint
        if (i + 1) % checkpoint_every == 0:
            checkpoint_path = os.path.join(checkpoint_dir, f'soup_{i+1}.npy')
            soup.save(checkpoint_path)

    # Save final checkpoint
    final_path = os.path.join(checkpoint_dir, 'soup_final.npy')
    soup.save(final_path)

    # Final metrics
    final_density = soup.instruction_density()
    total_ops = sum(ops_history)
    avg_ops_final = total_ops / interactions_total
    elapsed = time.time() - start_time

    logger.info("=" * 60)
    logger.info("EXPERIMENT COMPLETE")
    logger.info("=" * 60)
    logger.info(f"Total interactions: {interactions_total}")
    logger.info(f"Total operations: {total_ops}")
    logger.info(f"Average ops/interaction: {avg_ops_final:.2f}")
    logger.info(f"Initial density: {initial_density:.4f}")
    logger.info(f"Final density: {final_density:.4f}")
    logger.info(f"Elapsed time: {elapsed:.1f}s")
    logger.info(f"Rate: {interactions_total/elapsed:.1f} int/s")
    logger.info(f"Output: {output_dir}")

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
    click.echo(f"Analyzing results in: {results_dir}")
    click.echo("(Analysis dashboard not yet implemented)")


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

    # Benchmark Python backend
    from primordium.chaos import Soup
    import time

    soup = Soup(size=256, tape_length=48, seed=42)

    start = time.time()
    for _ in range(1000):
        soup.interact(max_steps=350)
    elapsed = time.time() - start

    rate = 1000 / elapsed
    click.echo(f"Python backend: {rate:.1f} interactions/second")


@cli.command()
@click.argument('config_file', type=click.Path(exists=True))
def validate(config_file: str):
    """Validate a configuration file.

    CONFIG_FILE: Path to genesis.yaml configuration file
    """
    from primordium.config import load_config

    try:
        config = load_config(config_file)
        click.echo(f"Configuration is valid!")
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
