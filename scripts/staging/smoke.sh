#!/usr/bin/env bash
# Run on the VPS after the Compose services are running.
set -euo pipefail
for endpoint in "http://127.0.0.1:8000/health/live" \
                "http://127.0.0.1:8000/health/ready" \
                "http://127.0.0.1:3000/" \
                "http://127.0.0.1:3000/valuation-lab" \
                "http://127.0.0.1:3000/screener"; do
  ok=0
  for attempt in $(seq 1 45); do
    if curl --silent --show-error --fail --max-time 6 --output /dev/null "$endpoint"; then
      ok=1; break
    fi
    sleep 2
  done
  if [ "$ok" -ne 1 ]; then
    echo "Staging smoke check failed: $endpoint" >&2
    exit 1
  fi
  echo "PASS $endpoint"
done
echo "Staging routes and DB readiness passed"
