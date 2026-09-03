        FROM python:3.12-slim
        ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
        RUN apt-get update && apt-get install -y --no-install-recommends curl procps iproute2 && rm -rf /var/lib/apt/lists/*
        COPY agent/requirements.txt /agent/requirements.txt
        RUN pip install --no-cache-dir -r /agent/requirements.txt
        RUN useradd --create-home --uid 10001 --shell /bin/sh opsbench
        COPY agent /agent
        COPY runtime/service.py /opt/opsbench/service.py
        COPY runtime/downstream.py /opt/opsbench/downstream.py
RUN chmod +x /agent/run.py /agent/run.sh && mkdir -p /runtime /opsbench/public /opsbench/trace
