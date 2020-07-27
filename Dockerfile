FROM python:latest

ENV LC_ALL=C.UTF-8 \
    LANG=C.UTF-8

# 8082 is the default port for luigi

EXPOSE 8082

# Copy in required files

COPY pipeline /opt/recon-pipeline/pipeline
COPY Pipfile* /opt/recon-pipeline/
COPY luigid.service /opt/recon-pipeline/

# Install dependencies

WORKDIR /opt/recon-pipeline/

RUN pip3 install pipenv && \
    pipenv install --system --deploy && \
    apt update && \
    apt install -y chromium less nmap sudo vim

# Setup Workarounds
# systemctl because systemd is required for luigid setup and is more trouble than it is worth
# Moving because default location causes issues with `tools install all`
# Symbolic link to more easily enter with `docker exec`
# Default interface for Docker Container should be eth0

RUN touch /usr/bin/systemctl && \
    chmod 755 /usr/bin/systemctl && \
    mv /usr/local/bin/luigid /bin/luigid && \
    ln -s /opt/recon-pipeline/pipeline/recon-pipeline.py /bin/pipeline && \
    sed -i 's/tun0/eth0/g' /opt/recon-pipeline/pipeline/recon/config.py

# Run luigi

WORKDIR /root/.local/recon-pipeline/files

CMD ["/bin/luigid", "--pidfile", "/var/run/luigid.pid", "--logdir", "/var/log"]
