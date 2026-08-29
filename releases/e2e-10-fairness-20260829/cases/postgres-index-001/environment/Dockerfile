FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
RUN apt-get update && apt-get install -y --no-install-recommends postgresql-client procps curl     && rm -rf /var/lib/apt/lists/*
RUN useradd --create-home --uid 10001 --shell /usr/sbin/nologin opsbench
WORKDIR /agent
COPY agent/requirements.txt /agent/requirements.txt
RUN pip install --no-cache-dir -r /agent/requirements.txt
COPY agent /agent
RUN chmod +x /agent/run.py /agent/run.sh
RUN mkdir -p /opt/opsbench && chmod 700 /opt/opsbench
RUN chown -R root:root /opt/opsbench && chmod 700 /opt/opsbench
