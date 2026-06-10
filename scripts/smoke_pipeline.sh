#!/usr/bin/env bash
# Full pipeline smoke test (Epics 10–12): bulk upload → review → transform.
# Uses pytest TestClient + vitest UI smoke — no running server required.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "==> Backend API smoke (pytest -m smoke)"
cd "$ROOT/backend"
.venv/bin/pytest -m smoke -v --tb=short

echo ""
echo "==> Frontend UI smoke"
cd "$ROOT/frontend"
npm run test -- --run src/smoke/pipelineSmoke.test.tsx

echo ""
echo "Smoke pipeline passed."
