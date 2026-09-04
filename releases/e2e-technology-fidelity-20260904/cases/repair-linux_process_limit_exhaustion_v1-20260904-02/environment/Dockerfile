FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl openssl procps psmisc util-linux postgresql-client redis-tools \
    systemd dbus kcat ca-certificates && rm -rf /var/lib/apt/lists/*
RUN groupadd --gid 10001 opsbench && useradd --uid 10001 --gid 10001 --create-home --shell /bin/bash opsbench
RUN install -d -m 755 /runtime /var/lib/opsbench/internal /run/user/10001 && chown -R opsbench:opsbench /runtime /run/user/10001
WORKDIR /agent
COPY agent/requirements.txt /agent/requirements.txt
RUN pip install --no-cache-dir -r /agent/requirements.txt && pip install --no-cache-dir pika
COPY agent /agent
COPY runtime/service.py /opt/opsbench/service.py
RUN chmod +x /agent/run.py /agent/run.sh
