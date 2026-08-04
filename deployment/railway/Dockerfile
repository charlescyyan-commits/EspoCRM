# Phase3C25 Railway staging image — EspoCRM + crm-extension overlay
#
# Build context MUST be the repository root (not this directory).
# Railway settings:
#   Root Directory:    (repository root / empty)
#   Dockerfile Path:   deployment/railway/Dockerfile
#   Start Command:     (leave empty — image ENTRYPOINT/CMD)
#
# Pin matches historical local validation stack (docs/PHASE3B03_ENVIRONMENT_AUDIT_REPORT.md).

ARG ESPOCRM_VERSION=10.0.1
FROM espocrm/espocrm:${ESPOCRM_VERSION}

LABEL org.opencontainers.image.title="EspoCRM C25 Staging"
LABEL org.opencontainers.image.description="Staging-only EspoCRM with crm-extension overlay for Railway"
LABEL com.espocrm.environment="staging"
LABEL com.espocrm.extension.path="crm-extension/files"

ENV APP_ENV=staging \
    ESPOCRM_STAGING=1 \
    # Default listen port for local runs; Railway injects PORT at runtime.
    PORT=8080 \
    # Safety defaults — providers must stay disabled on staging.
    C25_STAGING_DISABLE_PROVIDERS=1

# Pristine overlay (survives volume mounts of custom/ or client/custom/).
COPY crm-extension/files/ /opt/crm-extension-overlay/

# Bake into image so first boot (no custom volume) already has the extension.
COPY crm-extension/files/custom/ /var/www/html/custom/
COPY crm-extension/files/client/custom/ /var/www/html/client/custom/

COPY deployment/railway/docker-entrypoint-railway.sh /usr/local/bin/docker-entrypoint-railway.sh
COPY deployment/railway/healthcheck.sh /usr/local/bin/healthcheck.sh

RUN sed -i 's/\r$//' \
        /usr/local/bin/docker-entrypoint-railway.sh \
        /usr/local/bin/healthcheck.sh \
    && chmod +x /usr/local/bin/docker-entrypoint-railway.sh /usr/local/bin/healthcheck.sh \
    && chown -R www-data:www-data /var/www/html/custom /var/www/html/client/custom \
    && test -d /opt/crm-extension-overlay/custom/Espo/Modules/Prospecting \
    && test -f /var/www/html/custom/Espo/Modules/Prospecting/Resources/metadata/scopes/ProspectPool.json

WORKDIR /var/www/html

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=15s --start-period=180s --retries=5 \
    CMD ["/usr/local/bin/healthcheck.sh"]

ENTRYPOINT ["/usr/local/bin/docker-entrypoint-railway.sh"]
CMD ["apache2-foreground"]
