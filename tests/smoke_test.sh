#!/usr/bin/env bash
# Dynamic integration smoke test: builds the real images, brings the real
# stack up with `docker compose`, and hits it through nginx exactly as a
# browser would — proving the FE/BE/nginx wiring actually works end to end,
# not just that the config files are internally consistent (see
# test_compose_config.py for the fast static checks).
#
# Needs a Docker daemon. First run also downloads the VieNeu-TTS model from
# Hugging Face, so the backend healthcheck can take several minutes — this
# script polls for it rather than assuming a fixed sleep.
#
# Usage: ./tests/smoke_test.sh   (run from Voice-Infra/, or anywhere)
set -euo pipefail
cd "$(dirname "$0")/.."

cleanup() { docker compose down --volumes; }
trap cleanup EXIT

echo "== docker compose up --build -d =="
docker compose up --build -d

echo "== waiting for backend healthcheck =="
for _ in $(seq 1 60); do
  status=$(docker compose ps --format '{{.Health}}' backend 2>/dev/null || echo "")
  if [ "$status" = "healthy" ]; then
    break
  fi
  sleep 5
done
if [ "$status" != "healthy" ]; then
  echo "FAIL: backend never became healthy" >&2
  docker compose logs backend >&2
  exit 1
fi

echo "== GET / through nginx serves the built frontend =="
index_status=$(curl -s -o /dev/null -w '%{http_code}' http://localhost/)
if [ "$index_status" != "200" ]; then
  echo "FAIL: GET / returned $index_status" >&2
  exit 1
fi

echo "== GET /api/health through nginx reaches the backend =="
health_body=$(curl -s http://localhost/api/health)
echo "$health_body" | grep -q '"status":"ok"' || {
  echo "FAIL: /api/health via nginx did not report ok: $health_body" >&2
  exit 1
}

echo "== GET /api/voices through nginx returns a non-empty list =="
voices_body=$(curl -s http://localhost/api/voices)
echo "$voices_body" | grep -q '"id"' || {
  echo "FAIL: /api/voices via nginx returned no voices: $voices_body" >&2
  exit 1
}

echo "ALL SMOKE CHECKS PASSED"
