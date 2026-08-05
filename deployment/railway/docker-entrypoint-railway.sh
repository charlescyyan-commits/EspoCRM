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

# Runtime MPM guard: Debian layers / image inheritance can reintroduce
# mpm_event or mpm_worker after the Dockerfile build-time check. EspoCRM
# requires mod_php + mpm_prefork only. Enforce and fail closed via
# apache2ctl -M (effective modules), not only mods-enabled symlinks.
guard_apache_mpm_prefork() {
    log "enforcing Apache mpm_prefork at runtime"

    if [ -e /etc/apache2/mods-enabled/mpm_event.load ]; then
        a2dismod mpm_event
    fi
    if [ -e /etc/apache2/mods-enabled/mpm_worker.load ]; then
        a2dismod mpm_worker
    fi
    a2enmod mpm_prefork >/dev/null

    local modules_file="/tmp/dp-wp5-apache-modules-runtime.txt"
    if ! apache2ctl -M >"$modules_file" 2>/dev/null; then
        log "error: apache2ctl -M failed during MPM validation"
        exit 1
    fi

    local mpm_count
    mpm_count="$(grep -Ec 'mpm_(prefork|event|worker)_module' "$modules_file" || true)"

    if [ "$mpm_count" -ne 1 ]; then
        log "error: expected exactly one Apache MPM, found ${mpm_count}"
        grep -E 'mpm_' "$modules_file" >&2 || true
        exit 1
    fi
    if ! grep -q 'mpm_prefork_module' "$modules_file"; then
        log "error: mpm_prefork_module is not loaded"
        exit 1
    fi
    if grep -q 'mpm_event_module' "$modules_file"; then
        log "error: mpm_event_module must not be loaded"
        exit 1
    fi
    if grep -q 'mpm_worker_module' "$modules_file"; then
        log "error: mpm_worker_module must not be loaded"
        exit 1
    fi

    log "Apache MPM runtime guard passed: mpm_prefork only"
}

main() {
    log "starting DP-WP5 Railway service wrapper"
    guard_staging_isolation
    reject_full_application_volume
    configure_apache_port
    guard_apache_mpm_prefork

    # Start only the supplied service command.
    exec "$@"
}

main "$@"
