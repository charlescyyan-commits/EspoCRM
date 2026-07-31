#!/bin/bash
# Railway / local staging wrapper around official espocrm docker-entrypoint.sh
set -euo pipefail

log() {
    echo >&2 "railway-staging: $*"
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
        sed -i -E "s/<VirtualHost \*:[0-9]+>/<VirtualHost *:${port}>/" \
            /etc/apache2/sites-available/000-default.conf
    fi

    # Ensure apache2-foreground / envvars do not force :80 for Railway.
    export APACHE_PORT="$port"
    export PORT="$port"
}

sync_extension_overlay() {
    local overlay="/opt/crm-extension-overlay"
    local html="/var/www/html"

    if [ ! -d "${overlay}/custom" ]; then
        log "error: missing extension overlay at ${overlay}/custom"
        exit 1
    fi

    log "syncing crm-extension overlay into ${html}"

    mkdir -p "${html}/custom" "${html}/client/custom"

    # Prefer rsync when available; fall back to cp -a.
    if command -v rsync >/dev/null 2>&1; then
        rsync -a --delete "${overlay}/custom/" "${html}/custom/"
        if [ -d "${overlay}/client/custom" ]; then
            rsync -a --delete "${overlay}/client/custom/" "${html}/client/custom/"
        fi
    else
        # cp -a cannot --delete; remove known module trees then copy.
        rm -rf "${html}/custom/Espo/Modules/Prospecting" \
               "${html}/custom/Espo/Modules/AIPlatform" \
               "${html}/custom/Espo/Modules/CommercialIntelligence" \
               "${html}/custom/Espo/Custom" 2>/dev/null || true
        cp -a "${overlay}/custom/." "${html}/custom/"
        if [ -d "${overlay}/client/custom" ]; then
            cp -a "${overlay}/client/custom/." "${html}/client/custom/"
        fi
    fi

    chown -R www-data:www-data "${html}/custom" "${html}/client/custom" || true

    if [ ! -d "${html}/custom/Espo/Modules/Prospecting" ]; then
        log "error: Prospecting module missing after overlay sync"
        exit 1
    fi

    log "overlay sync complete (Prospecting present)"
}

clear_metadata_cache_if_installed() {
    local html="/var/www/html"

    # After extension sync on an already-installed instance, drop cache so
    # metadata/scopes from the overlay are picked up. Avoid rebuild here —
    # rebuild is expensive and belongs to first install / explicit ops.
    if [ -f "${html}/data/config.php" ] || [ -f "${html}/data/config-internal.php" ]; then
        if [ -d "${html}/data/cache" ]; then
            log "clearing data/cache after overlay sync (installed instance)"
            rm -rf "${html}/data/cache"/* 2>/dev/null || true
        fi
    fi
}

guard_staging_isolation() {
    if [ "${APP_ENV:-staging}" = "production" ] || [ "${ESPOCRM_ALLOW_PRODUCTION:-0}" = "1" ]; then
        log "error: production promotion is forbidden for this image"
        exit 1
    fi

    # Refuse known real-provider env names if accidentally injected.
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
            log "error: staging must not connect to real Instantly/Apollo/Apify/SMTP providers"
            exit 1
        fi
    done
}

warn_volume_layout() {
    if awk '{print $2}' /proc/mounts | grep -qxE "/var/www/html"; then
        log "warning: full /var/www/html volume mount detected (legacy)"
        log "warning: prefer Volume Mount Path=/var/www/html/data so image upgrades and overlays apply"
    fi
}

main() {
    log "starting C25 staging entrypoint"
    guard_staging_isolation
    warn_volume_layout
    configure_apache_port
    sync_extension_overlay
    clear_metadata_cache_if_installed

    # Hand off to official EspoCRM entrypoint (install/migrate/config + exec CMD).
    exec /usr/local/bin/docker-entrypoint.sh "$@"
}

main "$@"
