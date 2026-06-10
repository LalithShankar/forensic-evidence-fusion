#!/usr/bin/env bash
# Live API smoke test for Epics 10–12 against a running backend (default :8000).
#
# Prerequisites:
#   - Backend running on epic-12 branch (or later): uvicorn app.main:app --port 8000
#   - DB migrated: cd backend && alembic upgrade head
#   - Seeded user: LOCAL_DEV_PASSWORD=... python scripts/seed_local_users.py
#
# Usage:
#   ./scripts/smoke_pipeline_live.sh
#   BASE_URL=http://127.0.0.1:8000 SMOKE_EMAIL=analyst@local.dev ./scripts/smoke_pipeline_live.sh

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BASE_URL="${BASE_URL:-http://localhost:8000}"
SMOKE_EMAIL="${SMOKE_EMAIL:-analyst@local.dev}"
SMOKE_PASSWORD="${SMOKE_PASSWORD:-${LOCAL_DEV_PASSWORD:-DevPassword123!}}"

json_get() {
  local expr="$1"
  python3 -c "import json,sys; data=json.load(sys.stdin); print($expr)"
}

auth_header() {
  echo "Authorization: Bearer $1"
}

step() {
  echo ""
  echo "==> $1"
}

fail() {
  echo "LIVE SMOKE FAILED: $1" >&2
  exit 1
}

step "Health check ($BASE_URL/health)"
health_code="$(curl -sS -o /tmp/smoke_health.json -w "%{http_code}" "$BASE_URL/health")"
[[ "$health_code" == "200" ]] || fail "health returned $health_code"
status="$(json_get "data['status']" < /tmp/smoke_health.json)"
[[ "$status" == "ok" ]] || fail "health status=$status"

step "Login ($SMOKE_EMAIL)"
login_code="$(curl -sS -o /tmp/smoke_login.json -w "%{http_code}" \
  -X POST "$BASE_URL/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$SMOKE_EMAIL\",\"password\":\"$SMOKE_PASSWORD\"}")"
[[ "$login_code" == "200" ]] || fail "login returned $login_code ($(cat /tmp/smoke_login.json))"
token="$(json_get "data['access_token']" < /tmp/smoke_login.json)"

step "Auth me + protected ping"
me_code="$(curl -sS -o /tmp/smoke_me.json -w "%{http_code}" \
  -H "$(auth_header "$token")" "$BASE_URL/auth/me")"
[[ "$me_code" == "200" ]] || fail "/auth/me returned $me_code"
ping_code="$(curl -sS -o /tmp/smoke_ping.json -w "%{http_code}" \
  -H "$(auth_header "$token")" "$BASE_URL/auth/protected/ping")"
[[ "$ping_code" == "200" ]] || fail "/auth/protected/ping returned $ping_code"

step "Create case"
case_code="$(curl -sS -o /tmp/smoke_case.json -w "%{http_code}" \
  -X POST "$BASE_URL/cases" \
  -H "$(auth_header "$token")" \
  -H "Content-Type: application/json" \
  -d '{"name":"Live smoke case","scenario_type":"general_investigation"}')"
[[ "$case_code" == "201" ]] || fail "create case returned $case_code ($(cat /tmp/smoke_case.json))"
case_id="$(json_get "data['id']" < /tmp/smoke_case.json)"

tmpdir="$(mktemp -d)"
trap 'rm -rf "$tmpdir"' EXIT
printf 'name,amount\nAlice,10' >"$tmpdir/ledger.csv"
printf 'messages' >"$tmpdir/WhatsApp Chat with Bob.txt"
printf '\x00\x01' >"$tmpdir/mystery.bin"
: >"$tmpdir/empty.txt"

step "Bulk upload (Epic 10)"
bulk_code="$(curl -sS -o /tmp/smoke_bulk.json -w "%{http_code}" \
  -X POST "$BASE_URL/cases/$case_id/artifacts/bulk-upload" \
  -H "$(auth_header "$token")" \
  -F "files=@$tmpdir/ledger.csv;type=text/csv" \
  -F "files=@$tmpdir/WhatsApp Chat with Bob.txt;type=text/plain" \
  -F "files=@$tmpdir/mystery.bin;type=application/octet-stream" \
  -F "files=@$tmpdir/empty.txt;type=text/plain")"
[[ "$bulk_code" == "201" ]] || fail "bulk upload returned $bulk_code ($(cat /tmp/smoke_bulk.json))"

python3 - <<'PY' /tmp/smoke_bulk.json || exit 1
import json, sys
data = json.load(open(sys.argv[1]))
assert data["succeeded_count"] == 3, data
assert data["failed_count"] == 1, data
assert data["upload_batch_id"]
by_name = {r["filename"]: r for r in data["results"]}
assert by_name["ledger.csv"]["artifact"]["status"] == "preserved"
assert by_name["WhatsApp Chat with Bob.txt"]["artifact"]["suggested_source_family"] == "WhatsApp"
assert by_name["mystery.bin"]["artifact"]["status"] == "needs_review"
assert by_name["empty.txt"]["error"] is not None
csv_id = by_name["ledger.csv"]["artifact"]["id"]
mystery_id = by_name["mystery.bin"]["artifact"]["id"]
json.dump({"csv_id": csv_id, "mystery_id": mystery_id, "batch_id": data["upload_batch_id"]}, open("/tmp/smoke_ids.json", "w"))
PY

csv_id="$(json_get "data['csv_id']" < /tmp/smoke_ids.json)"
mystery_id="$(json_get "data['mystery_id']" < /tmp/smoke_ids.json)"

step "Review queue (Epic 11)"
queue_code="$(curl -sS -o /tmp/smoke_queue.json -w "%{http_code}" \
  -H "$(auth_header "$token")" "$BASE_URL/cases/$case_id/review-queue")"
[[ "$queue_code" == "200" ]] || fail "review queue returned $queue_code"
python3 - <<'PY' /tmp/smoke_queue.json "$mystery_id" || exit 1
import json, sys
data = json.load(open(sys.argv[1]))
mystery_id = sys.argv[2]
ids = {item["artifact"]["id"] for item in data["items"]}
assert mystery_id in ids, (mystery_id, ids)
assert data["total"] >= 1
PY

preserve_code="$(curl -sS -o /tmp/smoke_preserve.json -w "%{http_code}" \
  -X PATCH "$BASE_URL/cases/$case_id/review-queue/$mystery_id" \
  -H "$(auth_header "$token")" \
  -H "Content-Type: application/json" \
  -d '{"action":"preserve_only"}')"
[[ "$preserve_code" == "200" ]] || fail "preserve_only returned $preserve_code"

approve_code="$(curl -sS -o /tmp/smoke_approve.json -w "%{http_code}" \
  -X PATCH "$BASE_URL/cases/$case_id/review-queue/$csv_id" \
  -H "$(auth_header "$token")" \
  -H "Content-Type: application/json" \
  -d '{"action":"approve"}')"
[[ "$approve_code" == "200" ]] || fail "approve returned $approve_code"
approved_status="$(json_get "data['artifact']['status']" < /tmp/smoke_approve.json)"
[[ "$approved_status" == "ready_for_transformation" ]] || fail "unexpected status $approved_status"

step "Transform CSV (Epic 12)"
transform_code="$(curl -sS -o /tmp/smoke_transform.json -w "%{http_code}" \
  -X POST "$BASE_URL/cases/$case_id/artifacts/$csv_id/transformations/start" \
  -H "$(auth_header "$token")")"
[[ "$transform_code" == "201" ]] || fail "transform returned $transform_code ($(cat /tmp/smoke_transform.json))"
python3 - <<'PY' /tmp/smoke_transform.json || exit 1
import json, sys
data = json.load(open(sys.argv[1]))
record = data["record"]
assert record["status"] == "completed"
assert "structured_generated" in data["stages_completed"]
assert record["readable_path"]
assert record["structured_path"]
json.dump({"record_id": record["id"]}, open("/tmp/smoke_record.json", "w"))
PY
record_id="$(json_get "data['record_id']" < /tmp/smoke_record.json)"

latest_code="$(curl -sS -o /tmp/smoke_latest.json -w "%{http_code}" \
  -H "$(auth_header "$token")" \
  "$BASE_URL/cases/$case_id/artifacts/$csv_id/transformations/latest")"
[[ "$latest_code" == "200" ]] || fail "transform latest returned $latest_code"
latest_id="$(json_get "data['id']" < /tmp/smoke_latest.json)"
[[ "$latest_id" == "$record_id" ]] || fail "latest record mismatch"

step "Manifest (Epic 9)"
manifest_code="$(curl -sS -o /tmp/smoke_manifest.json -w "%{http_code}" \
  -H "$(auth_header "$token")" \
  "$BASE_URL/cases/$case_id/artifacts/manifest")"
[[ "$manifest_code" == "200" ]] || fail "manifest returned $manifest_code"
python3 - <<'PY' /tmp/smoke_manifest.json || exit 1
import json, sys
entries = {e["original_filename"]: e for e in json.load(open(sys.argv[1]))["artifacts"]}
assert entries["ledger.csv"]["source_group"] == "Generic"
assert entries["WhatsApp Chat with Bob.txt"]["source_family"] == "WhatsApp"
PY

echo ""
echo "Live smoke pipeline passed ($BASE_URL)."
