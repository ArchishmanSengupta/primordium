# PRIMORDIUM Architecture

## System Overview

PRIMORDIUM is organized into several key components:

```
┌─────────────────────────────────────────────────────────┐
│                      CLI (cli.py)                        │
├─────────────────────────────────────────────────────────┤
│  Config Validation (Pydantic genesis.yaml)              │
├──────────┬──────────┬──────────┬──────────┬──────────┤
│  AETHER  │   CHAOS  │  METRICS │  LAYERS  │   etc.   │
│ Interpreter│ Soup    │  Tracking│  (6 of them)        │
└──────────┴──────────┴──────────┴──────────┴──────────┘
```

## Core Components

### AETHER - Interpreter Layer

The BrainFuck interpreter that runs program interactions.

**Files:**
- `primordium/aether/interpreter.py` - Pure Python implementation
- `primordium/aether/engine.c` - C backend (~5x faster)
- `primordium/aether/engine_cuda.cu` - CUDA backend (GPU, ~100M+ int/s)
- `primordium/aether/compiler.py` - Build system

**Instruction Set:**
```
>  Move data pointer right
<  Move data pointer left
+  Increment cell
-  Decrement cell
[  Loop start (matches ])
]  Loop end (matches [)
.  Copy current cell to next
```

### CHAOS - Environment Layer

Manages the soup of scrolls (programs).

**Files:**
- `primordium/chaos/scroll.py` - Individual program
- `primordium/chaos/soup.py` - Collection of scrolls

**Key Classes:**
```python
class Scroll:
    tape: np.ndarray      # Program bytes
    id: str              # Unique identifier
    generation: int      # Birth generation
    parent_id: str       # Parent scroll ID
    fitness: float       # Evaluation score

class Soup:
    scrolls: List[Scroll]
    select_pair() -> (i, j)
    interact(max_steps=350) -> steps
    instruction_density() -> float
```

### Layers

Six evolutionary layers that can be stacked:

1. **GENESIS** - Phylogeny tracking, ancestry graph
2. **GAIA** - Spatial ecology, carrying capacity
3. **HERMES** - Error correction, signal propagation
4. **MNEMOSYNE** - Long-term pattern memory
5. **PROMETHEUS** - Tool use, external memory
6. **NOUS** - Meta-learning, theory of mind
7. **DEMIURGE** - Neural encoding (PyTorch)

### Configuration

Pydantic-based configuration system:

```python
# primordium/config/schema.py
class ChaosConfig:
    size: int          # Number of scrolls
    tape_length: int   # Bytes per scroll

class AetherConfig:
    backend: Literal["python", "c", "cuda"]
    interactions_total: int
    max_steps_per_interaction: int
```

## Data Flow

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
   e. Run layer hooks (before/after interaction)
   f. Log metrics
   ↓
4. Checkpoint soup periodically
   ↓
5. Save final state and metrics
```

## Performance Optimization

### Backend Selection

The CLI auto-selects the fastest available backend:

1. **CUDA** - Requires GPU + nvcc (fastest)
2. **C** - Requires gcc (default fallback)
3. **Python** - Pure Python (slowest)

### ctypes Integration

The C backend uses ctypes for zero-overhead FFI:

```python
lib.run_bf_c.argtypes = [
    np.ctypeslib.ndpointer(dtype=np.uint8),  # scroll_a
    np.ctypeslib.ndpointer(dtype=np.uint8),  # scroll_b
    ...
]
lib.run_bf_c.restype = ctypes.c_int32
```

### Checkpointing

State saved as NumPy arrays:

```python
soup.save('checkpoint.npy')  # Uses np.save with allow_pickle
soup = Soup.load('checkpoint.npy')
```

## Extension Points

### Adding a New Layer

```python
from primordium.layers import Layer

class MyLayer(Layer):
    def __init__(self, config):
        self.enabled = config.get('enabled', True)

    def before_interaction(self, soup, i, j):
        # Called before each interaction
        pass

    def after_interaction(self, soup, i, j, steps):
        # Called after each interaction
        pass

    def after_epoch(self, soup, epoch):
        # Called after each checkpoint interval
        return {'stats': 'values'}
```

### Adding a New Backend

1. Create `engine_newbackend.py`
2. Implement `run_bf()` function
3. Add to `compiler.py` build system
4. Update CLI backend detection

## Testing

Tests use pytest with fixtures:

```python
def test_interpret_increment():
    tape = np.array([43, 0], dtype=np.uint8)  # '+' at pos 0
    result = run_bf(tape, max_steps=10)
    assert result[0] == 1  # Cell should be incremented
```

Run tests:
```bash
pytest tests/ -v
```

## File Structure

```
primordium/
├── __init__.py           # Package init
├── cli.py                 # CLI entry point
├── aether/
│   ├── __init__.py
│   ├── interpreter.py     # Python BF
│   ├── engine.py          # C wrapper
│   ├── engine.c           # C implementation
│   ├── engine_cuda.py     # CUDA wrapper
│   ├── engine_cuda.cu    # CUDA kernel
│   └── compiler.py        # Build system
├── chaos/
│   ├── __init__.py
│   ├── scroll.py
│   └── soup.py
├── config/
│   ├── __init__.py
│   ├── schema.py
│   └── yaml_loader.py
├── metrics/
│   ├── __init__.py
│   └── tracker.py
└── layers/
    ├── __init__.py       # Base Layer class
    ├── genesis/
    ├── gaia/
    ├── hermes/
    ├── mnemosyne/
    ├── prometheus/
    ├── nous/
    └── demiurge/
```
