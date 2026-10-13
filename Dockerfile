# Runtime image for the Python 3.13 dependency migration.
# No reconnaissance scans or native tool installations are run during build.
FROM python:3.13-slim-bookworm

ENV LC_ALL=C.UTF-8 \
    LANG=C.UTF-8 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/opt/recon-pipeline \
    RECON_PIPELINE_MASSCAN_IFACE=eth0 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

EXPOSE 8082
WORKDIR /opt/recon-pipeline

COPY requirements-modern.txt ./
RUN apt-get update \
    && apt-get install --yes --no-install-recommends ca-certificates chromium less nmap sudo vim \
    && rm -rf /var/lib/apt/lists/* \
    && python -m pip install --no-cache-dir -r requirements-modern.txt

COPY pipeline ./pipeline
COPY luigid.service ./

# The legacy user-facing command is retained for docker exec -it ... pipeline.
RUN printf '#!/bin/sh\nexec python /opt/recon-pipeline/pipeline/recon-pipeline.py "$@"\n' > /usr/local/bin/pipeline \
    && chmod +x /usr/local/bin/pipeline \
    && mkdir -p /root/.local/recon-pipeline/files /var/log

WORKDIR /root/.local/recon-pipeline/files
CMD ["luigid", "--pidfile", "/tmp/luigid.pid", "--logdir", "/var/log"]
