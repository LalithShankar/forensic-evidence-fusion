#!/usr/bin/env bash
# Validate infra templates — safe for CI without Azure credentials.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
INFRA="$ROOT/infra"

required_files=(
  "$INFRA/main.bicep"
  "$INFRA/modules/core.bicep"
  "$INFRA/README.md"
  "$ROOT/backend/Dockerfile"
  "$ROOT/docs/deployment.md"
)

echo "Checking required deployment artifacts..."
for file in "${required_files[@]}"; do
  if [[ ! -f "$file" ]]; then
    echo "Missing: $file"
    exit 1
  fi
  echo "  ok: $file"
done

if command -v az >/dev/null 2>&1; then
  echo "Running az bicep build..."
  az bicep build --file "$INFRA/main.bicep" --outfile /tmp/forensic-main.json
  az bicep build --file "$INFRA/modules/core.bicep" --outfile /tmp/forensic-core.json
  echo "Bicep syntax OK"
else
  echo "az CLI not found — skipping bicep build (structural checks passed)"
fi

echo "Infra validation complete"
