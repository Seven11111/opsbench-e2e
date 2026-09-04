FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
RUN apt-get update && apt-get install -y --no-install-recommends curl openssl postgresql-client redis-tools procps && rm -rf /var/lib/apt/lists/*
WORKDIR /agent
COPY agent/requirements.txt /agent/requirements.txt
RUN pip install --no-cache-dir -r /agent/requirements.txt && pip install --no-cache-dir pika
COPY agent /agent
COPY runtime/service.py /opt/opsbench/service.py
RUN chmod +x /agent/run.py /agent/run.sh
