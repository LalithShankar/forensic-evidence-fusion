#!/usr/bin/env bash
# Full pipeline smoke test (Epics 10–15): upload → review → transform → previews → events.
# Mirrors CI checks locally — no running server required.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "==> Backend (full CI parity: ruff, black, mypy, pytest — no deselect)"
cd "$ROOT/backend"
.venv/bin/ruff check .
.venv/bin/black --check .
.venv/bin/mypy app
.venv/bin/pytest -v --tb=short

echo ""
echo "==> Backend R2 + artifact API smoke (explicit epic 13–15 coverage)"
.venv/bin/pytest -v --tb=short \
  tests/test_smoke_r2.py \
  tests/test_readable_views.py \
  tests/test_structured_datasets.py \
  tests/test_normalization_service.py

echo ""
echo "==> Frontend (full CI parity: lint, typecheck, vitest, build)"
cd "$ROOT/frontend"
npm run lint
npm run typecheck
npm run test -- --run
npm run build

echo ""
echo "==> Frontend artifact + pipeline UI smoke"
npm run test -- --run \
  src/smoke/pipelineSmoke.test.tsx \
  src/components/previews/ReadablePreviewPanel.test.tsx \
  src/components/datasets/StructuredDatasetPanel.test.tsx \
  src/pages/ArtifactDetail.test.tsx \
  src/pages/CaseEvents.test.tsx

echo ""
echo "Smoke pipeline passed (Epics 10–15, full test suite)."
