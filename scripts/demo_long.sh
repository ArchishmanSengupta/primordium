#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

CONFIG="${1:-configs/demo_record_long.yaml}"

if ! command -v primordium >/dev/null 2>&1; then
  echo "Install first: pip install -e \".[dev]\""
  exit 1
fi

echo "Compiling C backend (for ~100k+ interactions/sec)..."
python -m primordium.aether.compiler

echo ""
echo "Config: ${CONFIG}"
case "$(basename "${CONFIG}")" in
  demo_record.yaml) echo "Scale: 5M interactions (~40s with C backend)" ;;
  demo_record_long.yaml) echo "Scale: 20M interactions (~2-3 min with C backend)" ;;
  demo_record_emergence.yaml) echo "Scale: 34M interactions (~5 min with C backend)" ;;
  phase_transition.yaml) echo "Scale: 500k interactions (use demo_record_* for recording)" ;;
esac
echo ""
echo "Life is not guaranteed. Watch for entropy drop, rising density, and *** LIFE EMERGED ***."
echo ""

primordium validate "${CONFIG}"
primordium run "${CONFIG}"

RUN="$(ls -td chronicle/*/ 2>/dev/null | head -1)"
RUN="${RUN%/}"
echo ""
primordium analyse "${RUN}"

if [[ -f "${RUN}/metrics.jsonl" ]]; then
  echo ""
  echo "Metrics summary:"
  python3 - "${RUN}/metrics.jsonl" <<'PY'
import json, sys
path = sys.argv[1]
rows = []
for line in open(path):
    r = json.loads(line)
    if r.get("event") in ("initial", "log", "final"):
        rows.append(r)
if not rows:
    sys.exit(0)
first, last = rows[0], rows[-1]
print(f"  interactions: {first['interaction']} -> {last['interaction']}")
print(f"  entropy:      {first.get('entropy', 0):.3f} -> {last.get('entropy', 0):.3f}")
print(f"  density:      {first.get('instruction_density', 0):.4f} -> {last.get('instruction_density', 0):.4f}")
print(f"  compression:  {first.get('compression_ratio', 0):.3f} -> {last.get('compression_ratio', 0):.3f}")
print(f"  life (final): {last.get('is_life', False)}")
life_hits = [r["interaction"] for r in rows if r.get("is_life")]
if life_hits:
    print(f"  life first at interaction: {life_hits[0]}")
PY
fi

echo ""
echo "Viz: python scripts/generate_viz.py ${RUN}"
