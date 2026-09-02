ARG OPSBENCH_BASE_IMAGE=python:3.12-slim
FROM ${OPSBENCH_BASE_IMAGE}
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PYTHONPATH=/opt/opsbench
RUN if command -v curl >/dev/null 2>&1 && command -v getent >/dev/null 2>&1     && command -v ps >/dev/null 2>&1 && command -v ss >/dev/null 2>&1; then true;     else apt-get update && apt-get install -y --no-install-recommends       ca-certificates curl iproute2 iptables jq lsof openssl procps util-linux       && rm -rf /var/lib/apt/lists/*; fi
RUN (id demo >/dev/null 2>&1 || useradd --create-home --uid 1000 demo)     && (id opsbench >/dev/null 2>&1 || useradd --create-home --uid 10001 --shell /usr/sbin/nologin opsbench)
COPY agent/requirements.txt /tmp/agent-requirements.txt
RUN python3 -c "import langchain_core, langchain_openai, langgraph" >/dev/null 2>&1     || pip install --no-cache-dir -r /tmp/agent-requirements.txt
COPY agent /agent
COPY runtime /opt/opsbench/runtime
RUN chmod +x /opt/opsbench/runtime/*.sh /opt/opsbench/runtime/*.py 2>/dev/null || true     && python3 -m compileall -q -b /opt/opsbench/runtime     && mkdir -p /opt/opsbench/certs     && /opt/opsbench/runtime/generate-certs.sh     && rm -f /opt/opsbench/runtime/generate-certs.sh     && mkdir -p /agent-runtime /etc/opsbench /opt/opsbench/certs /var/log/demo     && chmod +x /agent/run.sh /agent/run.py
WORKDIR /agent-runtime
EXPOSE 8080 8443 9001 9002
ENTRYPOINT ["/opt/opsbench/runtime/entrypoint.sh"]
