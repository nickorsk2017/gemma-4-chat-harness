# syntax=docker/dockerfile:1
# guardrails — its own image. It no longer carries presidio, spaCy or any downloaded
# language model (TASK A9-1): structured PII is regex plus checksum, unstructured PII is
# the model's job. The image is now ordinary.
# Build context is ./mcp so agent_core (a dependency) is reachable.

FROM python:3.14-slim AS runtime
WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

COPY agent_core ./agent_core
COPY guardrails ./guardrails

RUN pip install --upgrade pip \
    && pip install ./agent_core \
    && pip install ./guardrails

EXPOSE 8200
# Reached by the orchestrator AND by doc_analyzer, so it serves over streamable-HTTP
# (path /mcp) rather than being spawned over stdio like the other sub-agents.
ENV GUARDRAILS_TRANSPORT=streamable-http \
    GUARDRAILS_HTTP_HOST=0.0.0.0 \
    GUARDRAILS_HTTP_PORT=8200
CMD ["python", "-m", "guardrails.main"]
