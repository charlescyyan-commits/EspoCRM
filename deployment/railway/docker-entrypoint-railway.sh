#!/bin/bash
# Railway / local staging process wrapper.
set -euo pipefail

log() {
    echo >&2 "railway-staging: $*"
}

guard_staging_isolation() {
    if [ "${APP_ENV:-staging}" = "production" ] || [ "${ESPOCRM_ALLOW_PRODUCTION:-0}" = "1" ]; then
        log "error: production promotion is forbidden for this image"
        exit 1
    fi

    local forbidden_vars=(
        INSTANTLY_API_KEY
        APOLLO_API_KEY
        APIFY_TOKEN
        APIFY_API_TOKEN
        SMTP_PASSWORD
        BREVO_API_KEY
    )
    local name
    for name in "${forbidden_vars[@]}"; do
        if [ -n "${!name-}" ]; then
            log "error: refusing to start with provider credential env set: ${name}"
            exit 1
        fi
    done
}

reject_full_application_volume() {
    if awk '{print $2}' /proc/mounts | grep -qxE "/var/www/html"; then
        log "error: full /var/www/html volume mount is forbidden; mount /var/www/html/data only"
        exit 1
    fi
}

configure_apache_port() {
    local port="${PORT:-8080}"

    if ! [[ "$port" =~ ^[0-9]+$ ]]; then
        log "error: PORT must be numeric, got: $port"
        exit 1
    fi

    log "configuring Apache to listen on PORT=${port}"
    if [ -f /etc/apache2/ports.conf ]; then
        sed -i -E "s/^Listen[[:space:]]+[0-9]+/Listen ${port}/" /etc/apache2/ports.conf
    fi
    if [ -f /etc/apache2/sites-available/000-default.conf ]; then
        sed -i -E "s/<VirtualHost \\*:[0-9]+>/<VirtualHost *:${port}>/" \
            /etc/apache2/sites-available/000-default.conf
    fi

    export APACHE_PORT="$port"
    export PORT="$port"
}

main() {
    log "starting DP-WP5 Railway service wrapper"
    guard_staging_isolation
    reject_full_application_volume
    configure_apache_port

    # Start only the supplied service command.
    exec "$@"
}

main "$@"
