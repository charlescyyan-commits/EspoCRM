# DP-WP5 Railway staging image. Build context MUST be the repository root.
# The caller MUST provide an immutable base-image reference, for example:
# espocrm/espocrm:10.0.1@sha256:<64-lowercase-hex-digest>
ARG ESPOCRM_BASE_IMAGE
FROM ${ESPOCRM_BASE_IMAGE}

ARG ESPOCRM_BASE_IMAGE
ARG DP_WP0_MANIFEST_SHA256=9ff763f5f517d14f7e0e8c15dca0c846febe471cc1d78c599ef02b8476ee2649
ARG DP_WP0_SOURCE_COMMIT=6ef712134f581a12a18da5c98691884e73388b78

LABEL org.opencontainers.image.title="EspoCRM DP-WP5 staging"
LABEL org.opencontainers.image.description="Execution-only Railway image with verified DP-WP0 overlay"
LABEL com.espocrm.environment="staging"
LABEL com.espocrm.extension.path="crm-extension/files"
LABEL io.chitu.dp-wp0.manifest-sha256="${DP_WP0_MANIFEST_SHA256}"
LABEL io.chitu.dp-wp0.source-commit="${DP_WP0_SOURCE_COMMIT}"
LABEL io.chitu.dp-wp0.extension-name="Chitu Prospecting Integration"
LABEL io.chitu.dp-wp0.extension-version="1.9.13-alpha"

ENV APP_ENV=staging \
    ESPOCRM_STAGING=1 \
    PORT=8080 \
    C25_STAGING_DISABLE_PROVIDERS=1

# Fail a future build closed if the supplied base is a mutable tag.
RUN printf '%s' "${ESPOCRM_BASE_IMAGE}" | grep -Eq '^.+@sha256:[0-9a-f]{64}$'

# The verified overlay and identity records are immutable image inputs.
COPY crm-extension/files/ /opt/crm-extension-overlay/
COPY crm-extension/manifest.json /opt/dp-wp0/extension-manifest.json
COPY deployment/railway/full-application-artifact-manifest.json /opt/dp-wp0/full-application-artifact-manifest.json
COPY crm-extension/files/custom/ /var/www/html/custom/
COPY crm-extension/files/client/custom/ /var/www/html/client/custom/

# The copied identity record must be the frozen DP-WP0 manifest. A mismatched
# working-tree file cannot be embedded under the frozen image label.
RUN test "$(sha256sum /opt/dp-wp0/full-application-artifact-manifest.json | awk '{print $1}')" = "${DP_WP0_MANIFEST_SHA256}"

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
