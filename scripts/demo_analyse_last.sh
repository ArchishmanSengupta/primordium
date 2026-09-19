#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
RUN="$(ls -td "${ROOT}"/chronicle/*/ 2>/dev/null | head -1 || true)"
RUN="${RUN%/}"

if [[ -z "${RUN}" || ! -d "${RUN}" ]]; then
  echo "No run found under chronicle/"
  exit 1
fi

if [[ -x "${ROOT}/.venv-ci/bin/primordium" ]]; then
  PRIMORDIUM="${ROOT}/.venv-ci/bin/primordium"
else
  PRIMORDIUM="primordium"
fi

"${PRIMORDIUM}" analyse "${RUN}"
echo ""
echo "Artifacts: ${RUN}/metrics.jsonl"
echo "Viz: python scripts/generate_viz.py ${RUN}"
