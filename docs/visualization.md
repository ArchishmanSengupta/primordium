# Visualizations

PRIMORDIUM produces HTML visualizations in two places:

| Location | Source | Contents |
|----------|--------|----------|
| `chronicle/<run>/visualization.html` | `scripts/run_phase_transition.py` or CLI run | Inline viz bundled with that experiment |
| `outputs/viz/<run_name>.html` | `scripts/generate_viz.py` | Standalone viz from checkpoint data |

## Generate from a completed run

```bash
# Default: writes outputs/viz/<run_name>.html
python scripts/generate_viz.py chronicle/5min_test

# Custom path
python scripts/generate_viz.py chronicle/5min_test -o outputs/viz/my_run.html
```

Open the file in a browser (`file://` URL printed by the script).

## Template

The HTML shell lives at `scripts/templates/viz.html`. Data is injected at build time by `scripts/generate_viz.py`.

Both `chronicle/` and `outputs/` are gitignored (local experiment artifacts).
