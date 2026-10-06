FROM ghcr.io/home-assistant/home-assistant:stable

# Pinned so the local install does not drift between runs.
ARG HACS_VERSION=2.0.5
ADD https://github.com/hacs/integration/releases/download/${HACS_VERSION}/hacs.zip /tmp/hacs.zip
RUN python3 -c "import zipfile; zipfile.ZipFile('/tmp/hacs.zip').extractall('/opt/hacs')" \
    && rm /tmp/hacs.zip

COPY entrypoint.sh /odecet-entrypoint.sh
RUN chmod +x /odecet-entrypoint.sh
ENTRYPOINT ["/odecet-entrypoint.sh"]
