#!/bin/bash
# Container healthcheck for Railway / Docker.
# Prefer HTTP on $PORT; fall back to EspoCRM app-check when installed.
set -euo pipefail

PORT="${PORT:-8080}"
URL="http://127.0.0.1:${PORT}/"

if command -v curl >/dev/null 2>&1; then
    code="$(curl -s -o /dev/null -w '%{http_code}' --max-time 10 "$URL" || true)"
    case "$code" in
        200|301|302|303|307|308)
            exit 0
            ;;
    esac
fi

if [ -x /var/www/html/bin/command ] && {
    [ -f /var/www/html/data/config.php ] || [ -f /var/www/html/data/config-internal.php ]
}; then
    cd /var/www/html
    if bin/command app-check >/dev/null 2>&1; then
        exit 0
    fi
fi

# During first-boot install Apache may briefly be unavailable; fail soft for start-period.
exit 1
