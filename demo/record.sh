#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if ! command -v vhs >/dev/null 2>&1; then
  echo "Install VHS: brew install vhs"
  exit 1
fi

if [[ -x "${ROOT}/.venv-ci/bin/primordium" ]]; then
  BIN="${ROOT}/.venv-ci/bin/primordium"
elif command -v primordium >/dev/null 2>&1; then
  BIN="$(command -v primordium)"
else
  echo "Install primordium first: pip install -e \".[dev]\""
  exit 1
fi

chmod +x "${ROOT}/scripts/demo_analyse_last.sh" "${ROOT}/scripts/demo.sh"

mkdir -p demo
TAPE="$(mktemp)"
sed -e "s|REPO_ROOT|${ROOT}|g" -e "s|PRIMORDIUM_BIN|${BIN}|g" \
  "${ROOT}/demo/primordium-demo.tape" > "${TAPE}"
trap 'rm -f "${TAPE}"' EXIT

echo "Recording terminal demo..."
vhs "${TAPE}"

echo ""
ls -lh demo/primordium-demo.gif demo/primordium-demo.mp4 2>/dev/null
