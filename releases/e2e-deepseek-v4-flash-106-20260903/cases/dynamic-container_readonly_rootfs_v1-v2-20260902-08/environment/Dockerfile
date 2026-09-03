FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
RUN apt-get update && apt-get install -y --no-install-recommends curl procps openssl     && rm -rf /var/lib/apt/lists/*
RUN useradd --create-home --uid 10001 --shell /usr/sbin/nologin opsbench
WORKDIR /agent
COPY agent/requirements.txt /agent/requirements.txt
RUN pip install --no-cache-dir -r /agent/requirements.txt
COPY agent /agent
RUN chmod +x /agent/run.py /agent/run.sh
RUN mkdir -p /opt/opsbench /var/lib/opsbench/internal && chmod 700 /opt/opsbench /var/lib/opsbench/internal
COPY runtime/service.py /opt/opsbench/service.py
RUN chown -R root:root /opt/opsbench && chmod 700 /opt/opsbench
