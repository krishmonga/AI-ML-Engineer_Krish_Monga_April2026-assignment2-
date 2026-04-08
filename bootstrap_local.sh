#!/usr/bin/env bash
# Install deps into ./.deps (avoids PEP 668 "externally managed" system Python).
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"
python3 -m pip install --upgrade -t .deps -r requirements.txt
echo ""
echo "Dependencies installed under $ROOT/.deps"
echo "Run the swarm with:"
echo "  export PYTHONPATH=\"$ROOT:$ROOT/.deps\""
echo "  python3 -m bug_fix_swarm"
