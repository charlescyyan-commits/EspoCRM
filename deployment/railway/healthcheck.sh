#!/bin/bash
# Read-only HTTP availability check for Railway / Docker.
set -euo pipefail

PORT="${PORT:-8080}"
URL="http://127.0.0.1:${PORT}/"

if ! command -v curl >/dev/null 2>&1; then
    exit 1
fi

code="$(curl -s -o /dev/null -w '%{http_code}' --max-time 10 "$URL" || true)"
case "$code" in
    200|301|302|303|307|308)
        exit 0
        ;;
esac

# Unavailable is a failed healthcheck. No application command is run.
exit 1
