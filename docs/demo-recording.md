# Record a PRIMORDIUM demo (macOS screen video)

## Before you record

1. Install and verify once (off camera):

```bash
cd primordium
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
primordium validate configs/template_quick.yaml
```

2. Prepare Terminal:
   - **Settings → Profiles → [your profile] → Text**: font 14–18 (Menlo or SF Mono), dark background
   - Window as wide as your capture area; hide unrelated tabs
   - **System Settings → Notifications → Focus** → turn on Do Not Disturb

3. Clear the window: `clear` or `Cmd + K`

## Record with macOS

1. Open Terminal in the project folder:

```bash
cd /path/to/primordium
source .venv/bin/activate
```

2. Start recording:
   - Press **⌘ ⇧ 5**
   - Click **Record Selected Portion**
   - Drag a box around the terminal (leave a small margin)
   - Click **Record** on the toolbar

3. Compile the fast C backend once per session:

```bash
python -m primordium.aether.compiler
```

4. Run a **long** demo (quick 1k run will not show life):

```bash
./scripts/demo_long.sh                          # default: 20M interactions (~2-3 min)
./scripts/demo_long.sh configs/demo_record.yaml           # 5M (~40s), visible metric drift
./scripts/demo_long.sh configs/demo_record_emergence.yaml # 34M (~5 min), best local chance for life
```

For the original smoke test only: `./scripts/demo.sh`

Optional fourth beat — open viz in browser after the script prints the path:

```bash
python scripts/generate_viz.py chronicle/quick_test_<timestamp>
open outputs/viz/<name>.html
```

4. Stop recording: click the **Stop** icon in the menu bar (or **⌃ ⌘ ⎋** if enabled).

5. The video saves to **Desktop** by default (`.mov`). Open in **QuickTime Player** → **Edit → Trim** to cut dead air at start/end → **File → Export As** → 1080p if you need MP4 for social.

## What the demo shows (~45–60 seconds)

| Order | What runs | What to say (optional) |
|-------|-----------|-------------------------|
| 1 | `primordium validate` | YAML-driven experiment config |
| 2 | `primordium run` | Random Brainfuck programs merge; metrics each step |
| 3 | `primordium analyse` | Results land in `chronicle/` as `metrics.jsonl` |

`Life emerged: False` on `template_quick.yaml` is expected (1,000 interactions). For recording, use `demo_record*.yaml` via `demo_long.sh`. Life is stochastic; if it does not appear in one take, you can still narrate entropy/density trends, or re-run with another seed (`experiment.seed` in the YAML).

## Checklist

- [ ] No notifications during capture
- [ ] Terminal text readable at 1080p after crop
- [ ] First frame is not mid-typing (pause 2s after hitting Record, then run script)
- [ ] Trim so the clip starts on your first command and ends after “Done”

## Manual commands (if you prefer not to use the script)

```bash
primordium validate configs/template_quick.yaml
primordium run configs/template_quick.yaml
RUN=$(ls -td chronicle/quick_test_* | head -1)
primordium analyse "$RUN"
```
