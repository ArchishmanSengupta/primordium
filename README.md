# PRIMORDIUM

**Recursive self-improving AI through symbiogenetic computation**

> *"After a few million interactions something apparently magical happens... suddenly the entropy of the soup drops dramatically... programs emerge... they're reproducing."*
> — Blaise Agüera y Arcas, Google DeepMind

PRIMORDIUM is the first open-source framework for recursive self-improving AI through embodied symbiogenetic computation. Based on the BFF experiment by [Blaise Agüera y Arcas](https://youtu.be/M2iX6HQOoLg), PRIMORDIUM demonstrates that life and purpose can emerge from pure computation through symbiogenesis - without any mutation.

## Key Features

- **Symbiogenesis > Mutation**: Programs evolve through merger, not random mutation
- **Phase Transitions**: Detects emergence of life through entropy/compression metrics
- **Neural Encoding**: DEMIURGE layer transforms programs to neural networks
- **Fully Configurable**: Every parameter configurable via YAML
- **Scientifically Rigorous**: Operational definition of "life" with measurable criteria

## Quick Start

```bash
# Install
pip install -e .

# Validate a config
primordium validate configs/template_quick.yaml

# Run a quick test (1000 interactions, ~1 minute)
primordium run configs/template_quick.yaml

# Run extended phase transition test (500K interactions)
primordium run configs/phase_transition.yaml
```

## What is PRIMORDIUM?

PRIMORDIUM is based on a profound scientific discovery: **life can emerge from pure computation through symbiogenesis** (merger) without any mutation.

### The Core Idea

1. Start with random BrainFuck programs (the "primordial soup")
2. Randomly pair and merge programs (symbiogenesis)
3. Run the combined program
4. Split back into two programs
5. Repeat millions of times

**Something magical happens**: Programs that can copy themselves emerge spontaneously.

## Configuration

PRIMORDIUM is fully configurable via YAML. See templates in `configs/`:

| Config | Purpose |
|--------|---------|
| `template_full.yaml` | All configuration options |
| `template_quick.yaml` | Quick test (~1 minute) |
| `phase_transition.yaml` | Extended run for emergence |
| `scaling_study.yaml` | Test different soup sizes |
| `with_layers.yaml` | Enable evolutionary layers |

### Basic Configuration

```yaml
experiment:
  name: my_experiment
  seed: 42

chaos:
  size: 256
  tape_length: 48

aether:
  interactions_total: 100000
  backend: c

metrics:
  log_interval: 5000
  life_criteria_thresholds:
    instruction_density: 0.1
    replicator_fraction: 0.05
    compression_ratio: 0.8
```

## Metrics & Life Detection

PRIMORDIUM tracks key metrics for detecting phase transitions:

| Metric | Description |
|--------|-------------|
| **Entropy** | Shannon entropy (drops during emergence) |
| **Instruction Density** | Valid BrainFuck instructions |
| **Compression Ratio** | How compressible programs are |
| **Life Criteria** | Operational definition of life |

### Operational Definition of Life

Based on the BFF experiment, "life" requires all three:

1. **Structure**: Instruction density ≥ 10%
2. **Replication**: ≥ 5% are identical copies
3. **Purpose**: Compression ratio ≤ 80%

When running, watch for: `*** LIFE EMERGED ***`

## Architecture

```
primordium/
├── aether/          # BrainFuck interpreter (Python + C + CUDA)
├── chaos/           # Soup and scroll management
├── config/          # Pydantic configuration
├── metrics/         # Metrics tracking
├── layers/          # 7 evolutionary layers
│   ├── genesis/     # Phylogeny tracking
│   ├── gaia/       # Ecology & spatial
│   ├── hermes/     # Error correction
│   ├── mnemosyne/  # Memory
│   ├── prometheus/ # Tools
│   ├── nous/       # Meta-learning
│   └── demiurge/   # Neural encoding
├── scripts/        # Run scripts
├── configs/        # Configuration templates
└── FOUNDATION.md   # Scientific & technical details
```

## Recommended Build Order

PRIMORDIUM uses a **phased approach**. All evolutionary layers are disabled by default - enable them incrementally based on what emerges:

| Phase | Components | Goal |
|-------|------------|------|
| **Phase 1** | AETHER, CHAOS, METRICS | Demonstrate phase transition at scale |
| **Phase 2** | + GAIA | Add spatial dynamics (based on arXiv:2406.19108 Figure 8) |
| **Phase 3-6** | + HERMES, MNEMOSYNE, PROMETHEUS, NOUS | Add layers based on what emerged |
| **Phase 7+** | + DEMIURGE | Neural encoding after sufficient complexity |

**Key Principle**: Science must go bottom-up from observation, not top-down from theory. Build Phase 1 first, study what emerges, then design subsequent layers.

See [FOUNDATION.md](primordium/FOUNDATION.md#recommended-build-order) for full details.

## Scientific Foundations

### Why Symbiogenesis?

Traditional evolutionary algorithms use mutation + selection. But the BFF experiment showed:

- **Mutation is NOT required**: Life emerges even with mutation = 0
- **Merger is powerful**: Combining programs creates new complexity
- **Phase transitions are real**: Emergence happens suddenly

See [FOUNDATION.md](primordium/FOUNDATION.md) for:
- Complete scientific background
- Architecture details
- Technical implementation
- Layer descriptions
- Configuration reference

## Performance

| Backend | Speed |
|---------|-------|
| Python | ~26K int/s |
| C | ~114K int/s |
| CUDA | ~100M+ int/s |

## Development

```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/metrics/test_metrics.py -v

# Compile C backend (optional)
python -m primordium.aether.compiler

# Validate config
primordium validate configs/template_full.yaml
```

## Research Questions

PRIMORDIUM explores:

1. Can symbiogenesis produce more complex organisms than mutation alone?
2. What is the nature of the gelation transition in program space?
3. Can BF programs evolve to write neural networks?
4. Is life simply a thermodynamic inevitability?

## References

- Agüera y Arcas, B. (2024). *What is Intelligence?* MIT Press
- Margulis, L. (1970). *Origin of Eukaryotic Cells*
- Goldstein, A. (1995). *Dynamic Kinetic Stability*

## License

MIT

---

*PRIMORDIUM - From chaos, order. From noise, life.*
