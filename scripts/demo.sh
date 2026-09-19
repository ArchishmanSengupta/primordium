#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if ! command -v primordium >/dev/null 2>&1; then
  echo "Install first: pip install -e \".[dev]\""
  exit 1
fi

pause() { sleep "${1:-2}"; }

echo ""
echo "========================================"
echo "  PRIMORDIUM — symbiogenetic soup demo"
echo "========================================"
echo ""
pause 1

echo ">> Validate experiment config"
primordium validate configs/template_quick.yaml
echo ""
pause 2

echo ">> Run primordial soup (1000 interactions, ~1 second)"
primordium run configs/template_quick.yaml
echo ""
pause 2

RUN_DIR="$(ls -td chronicle/quick_test_* 2>/dev/null | head -1)"
if [[ -z "${RUN_DIR}" || ! -d "${RUN_DIR}" ]]; then
  echo "No run directory found under chronicle/"
  exit 1
fi

echo ">> Analyse run: ${RUN_DIR}"
primordium analyse "${RUN_DIR}"
echo ""
pause 2

if [[ -f "${RUN_DIR}/metrics.jsonl" ]]; then
  echo ">> Metrics timeline (entropy + life flag)"
  python3 - "${RUN_DIR}/metrics.jsonl" <<'PY'
import json, sys
path = sys.argv[1]
for line in open(path):
    r = json.loads(line)
    if r.get("event") not in ("initial", "log", "final"):
        continue
    life = "LIFE" if r.get("is_life") else "----"
    print(
        f"  i={r['interaction']:>5}  "
        f"entropy={r.get('entropy', 0):.3f}  "
        f"density={r.get('instruction_density', 0):.4f}  "
        f"compress={r.get('compression_ratio', 0):.3f}  "
        f"{life}"
    )
PY
  echo ""
fi

pause 1

echo ">> Optional: HTML visualization"
echo "   python scripts/generate_viz.py ${RUN_DIR}"
echo ""
echo "Done. Share this terminal session or run: vhs demo/primordium-demo.tape"
echo ""
