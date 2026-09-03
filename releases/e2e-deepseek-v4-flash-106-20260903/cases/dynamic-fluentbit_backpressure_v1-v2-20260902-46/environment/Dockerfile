FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
RUN apt-get update && apt-get install -y --no-install-recommends curl procps iproute2 && rm -rf /var/lib/apt/lists/*
RUN useradd --create-home --uid 10001 --shell /bin/sh opsbench
WORKDIR /agent
COPY agent/requirements.txt /agent/requirements.txt
RUN pip install --no-cache-dir -r /agent/requirements.txt
COPY agent /agent
RUN chmod +x /agent/run.py /agent/run.sh
