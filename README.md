# PRIMORDIUM

[![CI](https://github.com/ArchishmanSengupta/primordium/actions/workflows/ci.yml/badge.svg)](https://github.com/ArchishmanSengupta/primordium/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

**Open-source symbiogenetic computation framework** — reproduce and extend the Brainfuck “primordial soup” experiment from [Blaise Agüera y Arcas](https://youtu.be/M2iX6HQOoLg).

## Requirements

- Python 3.10+
- ~2 GB disk for PyTorch (install pulls `torch`)
- Optional: `gcc` for the C backend (`python -m primordium.aether.compiler`)

## Quick start

```bash
git clone https://github.com/ArchishmanSengupta/primordium.git
cd primordium
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"

primordium validate configs/template_quick.yaml
primordium run configs/template_quick.yaml
```

Or: `bash scripts/run_quick.sh`

**Expected:** run finishes in seconds, writes `chronicle/quick_test_<timestamp>/` with `metrics.jsonl` and `genesis.yaml`. `Life emerged: False` is normal at 1,000 interactions.

**Emergence runs** (minutes to hours; may print `*** LIFE EMERGED ***`):

```bash
primordium run configs/phase_transition.yaml
```

## Key features

- Symbiogenesis (merger), not mutation-driven evolution
- Phase-transition metrics (entropy, compression, replication)
- YAML configuration for all experiments
- Optional evolutionary layers (disabled by default)
- Python / C / CUDA backends

See [primordium/FOUNDATION.md](primordium/FOUNDATION.md) for science, architecture, and layer design.

## Configs

| File | Purpose |
|------|---------|
| `configs/template_quick.yaml` | Smoke test (1k interactions) |
| `configs/template_full.yaml` | All options documented |
| `configs/phase_transition.yaml` | Long run for emergence |
| `configs/scaling_study.yaml` | Soup size sweep |
| `configs/with_layers.yaml` | Enable optional layers |

## Life detection

Operational criteria (from the BFF experiment):

1. **Structure** — instruction density ≥ 10%
2. **Replication** — ≥ 5% identical copies in the soup
3. **Purpose** — compression ratio ≤ 80%

All three must hold for `*** LIFE EMERGED ***`.

## Visualization

After a run:

```bash
python scripts/generate_viz.py chronicle/<your_run_dir>
```

See [docs/visualization.md](docs/visualization.md).

## Project layout

```
primordium/          # Python package (aether, chaos, config, metrics, layers, …)
configs/             # YAML templates
scripts/             # run_quick.sh, generate_viz.py, …
docs/                # User guides
tests/               # pytest suite
chronicle/           # Run outputs (gitignored)
```

## Development

```bash
pytest tests/ -q
ruff check primordium/ --select E,F,W --ignore E501
primordium validate configs/template_full.yaml
```

## Performance (approximate)

| Backend | Speed |
|---------|-------|
| Python | ~25–35K int/s |
| C | ~100K+ int/s |
| CUDA | varies (GPU) |

## References

- Agüera y Arcas, B. (2024). *What is Intelligence?* MIT Press
- Margulis, L. (1970). *Origin of Eukaryotic Cells*
- Goldstein, A. (1995). *Dynamic Kinetic Stability*

## License

MIT — see [LICENSE](LICENSE).
