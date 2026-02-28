# PRIMORDIUM

**Recursive self-improving AI through symbiogenetic computation**

PRIMORDIUM is the first open-source framework for recursive self-improving AI through embodied symbiogenetic computation. It uses a modified BrainFuck language as the substrate for evolving programs that can write neural networks.

## Overview

PRIMORDIUM implements a novel approach to artificial life and AI:

- **Unified Tape Model**: BrainFuck programs where code and data share the same memory space
- **Symbiogenesis**: Programs evolve through merger and recombination (not just mutation)
- **Phase Transitions**: System exhibits gelation - a phase transition from noise to life
- **Neural Encoding**: DEMIURGE layer transforms programs to neural network weights
- **Multi-Layer Evolution**: Six evolutionary layers (GENESIS → GAIA → HERMES → MNEMOSYNE → PROMETHEUS → NOUS)

## Quick Start

```bash
# Install
pip install -e .

# Run a quick experiment
primordium run configs/test_phase.yaml

# Validate a config
primordium validate configs/test_phase.yaml

# Run benchmarks
primordium benchmark
```

## Architecture

```
primordium/
├── aether/          # BrainFuck interpreter (Python + C + CUDA)
├── chaos/           # Soup and scroll management
├── config/          # Pydantic configuration
├── layers/          # Evolutionary layers
│   ├── genesis/     # Phylogeny tracking
│   ├── gaia/        # Ecology & spatial topology
│   ├── hermes/      # Error correction & signals
│   ├── mnemosyne/   # Long-term memory
│   ├── prometheus/  # Tool use & external memory
│   ├── nous/        # Meta-learning & theory of mind
│   └── demiurge/   # Neural encoding
└── cli.py           # Command-line interface
```

## Configuration

Edit `genesis.yaml` to configure experiments:

```yaml
experiment:
  name: my_experiment
  seed: 42

chaos:
  size: 256
  tape_length: 48

aether:
  interactions_total: 10000
  backend: c  # python, c, or cuda
```

## Performance

- **Python backend**: ~26K interactions/second
- **C backend**: ~114K interactions/second (4.4x faster)
- **CUDA backend**: ~100M+ interactions/second (target, requires GPU)

## Development

```bash
# Run tests
pytest tests/

# Compile C backend
python -m primordium.aether.compiler

# Run experiment
primordium run configs/test_phase.yaml
```

## Theory

See [THEORY.md](THEORY.md) for scientific background and [ARCHITECTURE.md](ARCHITECTURE.md) for implementation details.

## License

MIT
