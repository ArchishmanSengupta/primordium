# Scripts

Run from the **repository root**:

| Script | Purpose |
|--------|---------|
| `run_quick.sh` | Quick smoke test via CLI |
| `run_phase_transition.sh` | Long phase-transition config via CLI |
| `run_phase_transition.py` | Standalone timed experiment + inline HTML in `chronicle/` |
| `run_task.py` | Copy-task fitness evaluation |
| `generate_viz.py` | Build standalone HTML in `outputs/viz/` from a `chronicle/` run |

```bash
python scripts/generate_viz.py chronicle/my_run
python scripts/run_phase_transition.py
```
