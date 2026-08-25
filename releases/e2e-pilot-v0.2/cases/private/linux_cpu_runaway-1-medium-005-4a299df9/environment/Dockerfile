FROM python:3.12-slim
RUN useradd --create-home --uid 10001 --shell /usr/sbin/nologin opsbench
WORKDIR /agent
COPY agent/requirements.txt /agent/requirements.txt
RUN pip install --no-cache-dir -r /agent/requirements.txt
COPY agent /agent
RUN chmod +x /agent/run.py /agent/run.sh
RUN mkdir -p /opt/opsbench && chown root:root /opt/opsbench && chmod 700 /opt/opsbench
COPY runtime/service.py /opt/opsbench/service.py
RUN chown root:root /opt/opsbench/service.py && chmod 700 /opt/opsbench/service.py
