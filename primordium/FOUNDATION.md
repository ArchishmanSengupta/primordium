# PRIMORDIUM Foundation

This document contains the scientific foundations, architecture, and technical details of PRIMORDIUM.

---

## Table of Contents

1. [Scientific Foundations](#scientific-foundations)
2. [The BFF Experiment](#the-bff-experiment)
3. [Core Concepts](#core-concepts)
4. [Architecture](#architecture)
5. [Technical Details](#technical-details)
6. [Metrics & Life Detection](#metrics--life-detection)
7. [Evolutionary Layers](#evolutionary-layers)
8. [Testing Guide](#testing-guide)
9. [Recommended Build Order](#recommended-build-order)
10. [Configuration Reference](#configuration-reference)
11. [Research Questions](#research-questions)
12. [References](#references)

---

## Scientific Foundations

PRIMORDIUM is based on a novel approach to artificial life that combines several key ideas:

1. **Symbiogenesis** - Life evolves through merger, not just mutation
2. **Unified Tape** - Code and data share the same memory
3. **Phase Transitions** - Systems undergo gelation from chaos to life
4. **Dynamic Kinetic Stability** - Thermodynamic basis for emergence

### Why Symbiogenesis?

Traditional evolutionary algorithms use mutation + selection. But the BFF experiment showed:

- **Mutation is NOT required**: Life emerges even with mutation = 0
- **Merger is powerful**: Combining programs creates new complexity
- **Phase transitions are real**: Emergence happens suddenly, not gradually

---

## The BFF Experiment

PRIMORDIUM is directly inspired by Blaise Agüera y Arcas's BFF (BrainFuck Friend) experiment at Google DeepMind, which demonstrated that life and purpose can emerge from pure computation through symbiogenesis alone - without any mutation.

### Key Findings

1. **Emergence Without Mutation**: Programs that copy themselves emerge even when mutation rate = 0. This contradicts the Darwinian assumption that mutation is necessary for evolution.

2. **Phase Transition**: After a few million interactions, the system undergoes a sudden phase transition:
   - Entropy drops dramatically (from incompressible to highly compressible)
   - Programs begin replicating
   - Purpose emerges from pure computation

3. **Symbiogenesis > Mutation**: Merging (concatenation) is more powerful than random mutation for creating complexity.

4. **Thermodynamic Foundation**: The emergence of purpose is explained by "dynamic kinetic stability" (Adi Goldstein) - systems that can make more copies of themselves are more stable.

### PRIMORDIUM's Relationship to BFF

| Aspect | BFF Experiment | PRIMORDIUM |
|--------|---------------|------------|
| Scale | ~1,000 tapes | Up to millions |
| Language | BrainFuck (7 ops) | BrainFuck (7 ops) |
| Operation | Merge → Run → Split | APEIRON rule |
| Mutation | Can be zero | Intentionally absent |
| Extension | Basic replication | + Evolutionary layers |
| Neural Encoding | Not implemented | DEMIURGE layer |

---

## Core Concepts

### BrainFuck as Universal Substrate

We use a modified BrainFuck (BF) language because:

#### Minimalism
BF has only 7 instructions, making it easy to merge and recombine. Each instruction is a single byte.

#### Turing Completeness
BF is Turing-complete with loops and increment/decrement. Any computation can be expressed.

#### Unified Tape Model
Instructions AND data occupy the same memory. Programs can modify their own code.

### The APEIRON Rule

The fundamental interaction rule:

```
Given two scrolls A and B:
1. Concatenate: [A | B]
2. Run BF interpreter
3. Split: [A' | B']
```

This is inspired by **symbiogenesis** - the theory that new life forms arise from merger of distinct lineages.

### Phase Transitions

As interactions accumulate, the system undergoes a **phase transition**:

| Phase | Characteristics |
|-------|----------------|
| **Noise** | Random, unstructured programs, low instruction density |
| **Transition** | Instruction density increases, loops form |
| **Life** | High instruction density, stable replicators emerge |

This is analogous to **gelation** in polymers - when monomers cross-link to form a connected component.

---

## Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────┐
│                      CLI (cli.py)                        │
├─────────────────────────────────────────────────────────┤
│  Config Validation (Pydantic genesis.yaml)              │
├──────────┬──────────┬──────────┬──────────┬──────────────┤
│  AETHER  │   CHAOS  │ METRICS  │  LAYERS  │    CONFIG    │
│Interpreter│  Soup    │ Tracking │ (7 layers)│  Validation │
└──────────┴──────────┴──────────┴──────────┴──────────────┘
```

### Core Components

#### AETHER - Interpreter Layer

The BrainFuck interpreter that runs program interactions.

**Files:**
- `primordium/aether/interpreter.py` - Pure Python implementation
- `primordium/aether/engine.c` - C backend (~5x faster)
- `primordium/aether/engine_cuda.py` - CUDA backend (GPU)

**Instruction Set:**
| Byte | Symbol | Description |
|------|--------|-------------|
| 62 | `>` | Move data pointer right |
| 60 | `<` | Move data pointer left |
| 43 | `+` | Increment cell |
| 45 | `-` | Decrement cell |
| 91 | `[` | Loop start (matches `]`) |
| 93 | `]` | Loop end (matches `[`) |
| 46 | `.` | Copy current cell to next |

#### CHAOS - Environment Layer

Manages the soup of scrolls (programs).

```python
class Scroll:
    tape: np.ndarray      # Program bytes (48 by default)
    id: str              # Unique identifier
    generation: int      # Birth generation
    parent_id: str       # Parent scroll ID
    fitness: float       # Evaluation score

class Soup:
    scrolls: List[Scroll]
    size: int            # Number of scrolls
    tape_length: int     # Bytes per scroll
```

#### METRICS - Tracking Layer

Tracks key metrics for detecting phase transitions:

- `soup_entropy()` - Shannon entropy
- `instruction_density()` - Valid BF instructions fraction
- `compression_ratio()` - Compressibility measure
- `detect_life_criteria()` - Operational life definition

#### ORACLE - Post-hoc Analysis (Essential, Not External Guidance)

ORACLE is **not** external guidance. It is a read-only analysis toolkit that runs **after** the simulation completes:

- Reads completed runs from the chronicle directory
- Generates entropy curves, phylogenetic trees, species diversity metrics
- Produces phase transition visualizations
- Creates plain-language summaries

**ORACLE does NOT:**
- Interact with the running soup
- Modify any tape
- Apply any selection pressure
- Influence emergence in any way

This is the same category of tool that produced the figures in the original BFF paper (entropy curves, phase transition scatter plots, instruction density graphs). Every serious experiment requires analysis tooling.

---

## Technical Details

### Data Flow

```
1. Load config (genesis.yaml)
   ↓
2. Initialize Soup with random scrolls
   ↓
3. Main loop (interactions_total times):
   a. Select pair of scrolls (i, j)
   b. Concatenate tapes [scroll_i | scroll_j]
   c. Run BF interpreter on combined tape
   d. Split result back into two scrolls
   e. Log metrics
   ↓
4. Checkpoint soup periodically
   ↓
5. Save final state and metrics
```

### Performance Optimization

| Backend | Speed | Requirements |
|---------|-------|--------------|
| Python | ~26K int/s | None |
| C | ~114K int/s | gcc |
| CUDA | ~100M+ int/s | GPU + nvcc |

### Backend Selection

The CLI auto-selects the fastest available backend:
1. CUDA - Requires GPU + nvcc
2. C - Requires gcc
3. Python - Pure Python

### Checkpointing

```python
soup.save('checkpoint.npy')  # Saves all scrolls
soup = Soup.load('checkpoint.npy')  # Loads state
```

---

## Metrics & Life Detection

### Metrics Tracked

| Metric | Description | Phase Transition Indicator |
|--------|-------------|---------------------------|
| **Entropy** | Shannon entropy | Drops during emergence |
| **Instruction Density** | Valid BF ops fraction | Increases |
| **Compression Ratio** | Compressibility | Decreases |
| **Replicators** | Identical programs | Appears |

### Operational Definition of Life

Based on the BFF experiment, PRIMORDIUM defines "life" through three criteria:

1. **Structure**: Instruction density ≥ 10%
2. **Replication**: ≥ 5% of population are replicators
3. **Purpose**: Compression ratio ≤ 80%

When all three criteria are met, the system has achieved "life"!

### Customizing Thresholds

```yaml
metrics:
  life_criteria_thresholds:
    instruction_density: 0.1   # Min instruction density
    replicator_fraction: 0.05  # Min replicator fraction
    compression_ratio: 0.8     # Max compression ratio
```

---

## Evolutionary Layers

Seven layers that can be stacked. **Important: These should be built sequentially, not all at once.** The correct scientific order is: demonstrate Layer 1 (phase transition) first, then build each subsequent layer based on what actually emerges, not on theory alone.

| Layer | Purpose | Status |
|-------|---------|--------|
| **GENESIS** | Phylogeny | Build after phase transition confirmed |
| **GAIA** | Ecology | Based on Figure 8 of arXiv:2406.19108, not speculative |
| **HERMES** | Error Correction | Substrate provision — defer |
| **MNEMOSYNE** | Memory | Substrate provision — defer |
| **PROMETHEUS** | Tools | Substrate provision — redesign bonus mechanism |
| **NOUS** | Intelligence | Valid long-term target per Agüera y Arcas — defer |
| **DEMIURGE** | Neural Encoding | Valid scientific question — defer to late phase |

### Philosophy: Substrate Provision vs Behavioral Imposition

A critical distinction guides our layer design:

- **Substrate provision** (valid): Making memory available, creating conditions where prediction improves survival, designing interaction structures where communication is beneficial. Programs *can* use these; they are not *forced* to.

- **Behavioral imposition** (invalid): Forcing programs to use memory, emit predictions, or communicate regardless of adaptiveness.

PRIMORDIUM provides substrates, not mandates. Whether programs evolve to use available capabilities is an empirical question, not an architectural assumption.

### Layer Descriptions

#### GENESIS - Phylogeny Tracking
Tracks ancestry and lineage. This can be built early alongside METRICS — it's observation of what already emerges, not an imposed behavior.

#### GAIA - Spatial Ecology
**Based on published research**, not speculation. Figure 8 of arXiv:2406.19108 shows a 2D spatial experiment with 32,400 programs on a 240x135 grid with radius-2 interaction constraints. The phase transition wave is directly visible. GAIA scales this to larger soups.

#### HERMES - Error Correction
Substrate provision: making bracket balancing and signal propagation available. Programs may or may not evolve to use these — that's the empirical question.

#### MNEMOSYNE - Long-term Memory
Substrate provision: persistent pattern storage across generations. The tape already serves as memory; this layer makes cross-generational memory available.

#### PROMETHEUS - Tools and External Memory
Substrate provision with a caveat: the replication bonus mechanism for accurate prediction crosses from substrate provision into behavioral nudging. If prediction is genuinely adaptive, programs will evolve it without the bonus. **Redesign required.**

#### NOUS - Theory of Mind
Agüera y Arcas explicitly states in ALIFE 2025 that recursive self-modeling emerges under selection pressure and is fundamental to intelligence. This is the correct long-term target. Do not build infrastructure until Layers 1-4 have produced ecologically differentiated, communicating programs.

#### DEMIURGE - Neural Encoding
Asks whether evolved BF programs, when decoded as neural architecture blueprints, produce capable networks. This is a **measurement operation**, not a replacement of BF dynamics. The genome-to-enzyme analogy applies: asking if a gene produces a functional enzyme is not a category error. Requires Layers 1-5 to produce sufficient complexity first.

### Enabling Layers

**Phase 1 Default: Only AETHER, CHAOS, METRICS, ORACLE.** Do not enable layers by default.

```yaml
# Phase 1: Core foundation only
layers:
  genesis:
    enabled: false  # Enable after phase transition confirmed
    track_phylogeny: false
  gaia:
    enabled: false  # Build after Layer 1 solid
  hermes:
    enabled: false
  mnemosyne:
    enabled: false
  prometheus:
    enabled: false
  nous:
    enabled: false
  demiurge:
    enabled: false  # Build only after Layers 1-5 produce complexity
```

---

## Configuration Reference

### Complete Configuration Structure

```yaml
experiment:
  name: my_experiment
  seed: 42
  output_dir: "./chronicle/{name}_{timestamp}"

chaos:
  size: 256
  tape_length: 48
  initialisation: random

aether:
  backend: c
  interactions_total: 100000
  max_steps_per_interaction: 350
  checkpoint_every: 10000

apeiron:
  rule: standard
  selection: uniform

layers:
  genesis:
    enabled: false  # Enable after phase transition confirmed
  gaia:
    enabled: false
  hermes:
    enabled: false
  mnemosyne:
    enabled: false
  prometheus:
    enabled: false
  nous:
    enabled: false
  demiurge:
    enabled: false

kratos:
  # IMPORTANT: Fitness functions do NOT belong in the core soup dynamics.
  # The BFF experiment proves emergence happens without any fitness pressure.
  # Thermodynamic selection (programs that copy get copied more) is sufficient.
  #
  # Fitness signals ARE valid ONLY for DEMIURGE architecture evaluation:
  # when decoding BF programs as neural network blueprints, you must measure
  # capability somehow. That measurement is a fitness signal.
  fitness_function: replication
  selection_pressure: 0.5

metrics:
  log_interval: 5000
  life_criteria_thresholds:
    instruction_density: 0.1
    replicator_fraction: 0.05
    compression_ratio: 0.8

logging:
  level: info
  live_display: true
```

### Configuration Templates

| File | Purpose |
|------|---------|
| `configs/template_full.yaml` | All options |
| `configs/template_quick.yaml` | Quick test |
| `configs/phase_transition.yaml` | Extended run |
| `configs/scaling_study.yaml` | Size experiments |
| `configs/with_layers.yaml` | Layer testing |

---

## Testing Guide

PRIMORDIUM supports multiple testing approaches, from quick verification to full research experiments.

### 1. Smoke Test (~1 minute)

**Purpose**: Verify the system installs and runs correctly.

```bash
primordium run configs/quick_test.yaml
```

Expected output: Basic metrics showing entropy, instruction density over 1,000 interactions. No phase transition expected at this scale.

### 2. Quick Verification (~5 minutes)

**Purpose**: Verify metrics are working and system is stable.

```bash
primordium run configs/5min_test.yaml
```

Expected output: Full metrics including compression ratio and life criteria. Soup remains in "noise" phase.

### 3. Phase Transition Detection (30+ minutes)

**Purpose**: The core scientific experiment — demonstrate emergence of life.

```bash
primordium run configs/phase_transition.yaml
```

Expected output:
- Entropy starts high (~7.0 for random data)
- After ~100K-300K interactions, entropy drops sharply
- Instruction density increases from ~3% to >10%
- Compression ratio drops below 80%
- Replicators appear (>5% identical copies)
- `life_criteria` metric shows all three criteria met

This replicates the BFF experiment finding: life emerges from pure computation through symbiogenesis.

### 4. Scaling Studies (Variable)

**Purpose**: Understand how system behavior changes with soup size.

Run multiple experiments with different `chaos.size` values:

```bash
# Small soup
sed 's/size: 64/size: 32/' configs/scaling_study.yaml > configs/scaling_small.yaml
primordium run configs/scaling_small.yaml

# Medium soup (default)
primordium run configs/scaling_study.yaml

# Large soup
sed 's/size: 64/size: 512/' configs/scaling_study.yaml > configs/scaling_large.yaml
primordium run configs/scaling_large.yaml
```

Expected: Larger soups show more consistent phase transitions due to better statistics.

### 5. Spatial Dynamics - GAIA (After Phase 1)

**Purpose**: Test spatial ecology (based on Figure 8 of arXiv:2406.19108).

```bash
# First, confirm Phase 1 works
primordium run configs/phase_transition.yaml

# Then enable GAIA (only after Phase 1 is solid)
# Edit configs/template_full.yaml:
#   layers.gaia.enabled: true
#   layers.gaia.spatial_topology: grid
#   layers.gaia.grid_width: 16
#   layers.gaia.grid_height: 16
primordium run configs/template_full.yaml
```

Expected: Phase transition wave propagates across the grid, visible in spatial metrics.

### 6. Layer Experimentation (Advanced)

**Purpose**: Test evolutionary layers (GAIA, HERMES, MNEMOSYNE, PROMETHEUS, NOUS).

⚠️ **WARNING**: This is NOT the recommended build order. Only use after Phase 1 is fully validated.

```bash
# Use with_layers.yaml but understand it's for exploration, not validation
primordium run configs/with_layers.yaml
```

Expected: Results will vary. These layers are speculative extensions — their value is an empirical question, not a certainty.

### 7. Custom Experiments

Create your own config based on `template_full.yaml`:

```bash
cp configs/template_full.yaml configs/my_experiment.yaml
# Edit my_experiment.yaml with your parameters
primordium run configs/my_experiment.yaml
```

Common parameters to vary:
- `chaos.size`: Soup size (more = better statistics, slower)
- `chaos.tape_length`: Tape length (longer = more complex programs)
- `aether.interactions_total`: More interactions = more evolution
- `aether.max_steps_per_interaction`: Longer runs = more program execution

### 8. Analysis (ORACLE)

After running experiments, analyze results:

```bash
# Analyze a completed run
primordium analyse ./chronicle/my_experiment_20240101/

# ORACLE generates:
# - Entropy curves over time
# - Instruction density plots
# - Phylogenetic trees (if genesis enabled)
# - Phase transition scatter plots
# - Species diversity metrics
```

---

## Interpreting Results

### What Success Looks Like (Phase 1)

| Metric | Before | After Phase Transition |
|--------|--------|------------------------|
| Entropy | ~7.0 (random) | <5.0 (structured) |
| Instruction Density | ~3% | >10% |
| Compression Ratio | ~100% | <80% |
| Replicators | 0% | >5% |

### What Failure Looks Like

| Symptom | Likely Cause |
|---------|--------------|
| Entropy never drops | Not enough interactions |
| No replicators appear | Soup too small |
| System crashes | Check memory, try smaller soup |
| Metrics NaN | Check config validity |

---

## Reproducibility

For scientific reproducibility:

1. **Always set a seed**:
   ```yaml
   experiment:
     seed: 42  # Any integer
   ```

2. **Checkpoint frequently**:
   ```yaml
   aether:
     checkpoint_every: 10000
   ```

3. **Log everything**:
   ```yaml
   metrics:
     metrics_enabled:
       - entropy
       - instruction_density
       - compression_ratio
       - life_criteria
       - top_replicators
   ```

4. **Save scroll state**:
   ```yaml
   logging:
     save_scroll_format: true
   ```

---

## Research Enhancements

This section documents the research enhancements built on top of PRIMORDIUM based on recent papers from paradigms-of-intelligence.

### 1. DiffLogic DEMIURGE

**Paper**: "Differentiable Logic Cellular Automata" (Google Research)

**File**: `primordium/layers/demiurge/difflogic.py`

Implements differentiable logic gates for encoding BrainFuck programs as neural network weights. This enables gradient-based optimization of BF programs.

**Key Features**:
- 16 differentiable logic operations (AND, OR, XOR, NAND, etc.)
- MPS acceleration on Apple Silicon
- Fault-tolerant: small perturbations don't break functionality

**Usage**:
```python
from primordium.layers.demiurge.difflogic import DiffLogicDemiurgeLayer

config = {
    'enabled': True,
    'tape_length': 48,
    'hidden_size': 64,
    'device': 'mps'
}
layer = DiffLogicDemiurgeLayer(config)
```

---

### 2. Mesa-Optimization Detection (NOUS)

**Paper**: "Uncovering mesa-optimization algorithms in Transformers" (arXiv:2410.18636)

**File**: `primordium/layers/nous/mesa.py`

Detects if emergent programs develop internal optimization - a key indicator of self-improving AI.

**Detection Mechanisms**:
- **Learning Signal**: Tracks fitness improvements over time via linear regression
- **Goal Representation**: Detects reserved tape cells encoding target states
- **Planning**: Identifies nested loops indicating lookahead behavior

**Usage**:
```python
from primordium.layers.nous.mesa import MesaNousLayer

config = {
    'enabled': True,
    'mesa_detection_enabled': True
}
layer = MesaNousLayer(config)
```

---

### 3. State Soup MNEMOSYNE

**Paper**: "State Soup: In-Context Skill Learning" (arXiv:2410.13989)

**File**: `primordium/layers/mnemosyne/statesoup.py`

Implements linear state interpolation for in-context learning without parameter updates.

**Key Features**:
- Treats scroll states as "task vectors" that can be mixed
- Cosine-similarity retrieval of similar states
- Enables skill mixing: combine behaviors from different epochs

**Usage**:
```python
from primordium.layers.mnemosyne.statesoup import StateSoupMnemosyneLayer

config = {
    'enabled': True,
    'state_dim': 32,
    'store_frequency': 100
}
layer = StateSoupMnemosyneLayer(config)
```

---

### 4. Replication Tracking

**File**: `primordium/chaos/soup.py`

Added replication detection to track when programs successfully copy themselves. This is critical for measuring emergence.

**Detection**: Output tape contains original input pattern

---

## Research Questions

1. **Can symbiogenesis produce more complex organisms than mutation alone?**
2. **What is the nature of the gelation transition in program space?**
3. **Can BF programs evolve to write neural networks?**
4. **Do emergent layers (GAIA, NOUS) accelerate evolution?**
5. **Is life simply a thermodynamic inevitability?**

---

## Recommended Build Order

**The core principle: demonstrate Layer 1 at scale before designing Layer 2.**

The engineering mistake is building infrastructure for all layers before demonstrating GPU-accelerated abiogenesis at scale. This inverts the correct scientific order.

### Phase 1: Core Foundation (Build First)

| Component | Description |
|-----------|-------------|
| **AETHER** | BrainFuck interpreter — the computational substrate |
| **CHAOS** | Soup + interaction rule — the dynamics |
| **METRICS** | Entropy, compression, replicator detection |
| **GENESIS** | Optional — track ancestry alongside METRICS |
| **ORACLE** | Post-hoc analysis — essential for science |

**Goal:** Demonstrate clean, reproducible, GPU-accelerated phase transition at scale (100K+ interactions).

### Phase 2: Spatial Dynamics (Build After Phase Transition)

| Component | Description |
|-----------|-------------|
| **GAIA** | Spatial topology — based on Figure 8 of arXiv:2406.19108 |

### Phase 3-6: Progressive Layers (Design Based on What Emerged)

Layers should be designed based on what Layer 1 actually produces, not on theory alone:
- **HERMES** — if bracket errors become limiting
- **MNEMOSYNE** — if cross-generational patterns emerge
- **PROMETHEUS** — if external memory becomes advantageous (redesign bonus mechanism)
- **NOUS** — if ecologically differentiated programs emerge and need to model each other

### Phase 7+: DEMIURGE (Build Only After Sufficient Complexity)

Only when programs have evolved sufficient internal structure (likely after Layers 1-5+):
- Decode BF programs as neural architecture blueprints
- Evaluate whether evolved structure encodes functional capability
- Ask: do geographically isolated programs converge on similar motifs?

---

## References

1. Margulis, L. (1970). *Origin of Eukaryotic Cells*
2. Tyler, C. (1992). Cellular automata models in biology
3. Stanley, K.O. (2007). Compositional Pattern Producing Networks
4. Bak, P. (1996). *How Nature Works: The Science of Self-Organized Criticality*
5. Agüera y Arcas, B. et al. (2024). "Life from the machine: emergence in self-replicating automata." arXiv:2406.19108
6. Agüera y Arcas, B. (2024). *What is Intelligence?* MIT Press
7. Goldstein, A. (1995). Dynamic Kinetic Stability
8. Von Neumann, J. (1966). *Theory of Self-Reproducing Automata*
9. Margulis & Sagan (2002). *Acquiring Genomes*

---

*PRIMORDIUM - From chaos, order. From noise, life.*
