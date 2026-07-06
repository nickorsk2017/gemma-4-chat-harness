# syntax=docker/dockerfile:1
# MCP — master_orchestrator plus its three sub-agents (web / doc / image).
# The orchestrator fans out to the sub-agents in-process over stdio, so all four
# distributions are installed into this single image. Install order matters:
# `agent_core` is a dependency of every agent and goes first.

FROM python:3.11-slim AS runtime
WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

COPY . .
RUN pip install --upgrade pip \
    && pip install ./agent_core \
    && pip install ./web_agent ./doc_analyzer ./image_analyzer ./master_orchestrator

EXPOSE 8100
# Serve the orchestrator over streamable-HTTP (path /mcp) so the gateway can reach it.
# Transport/host/port stay runtime configuration (env, read by main.py). main.py's
# HTTP mode also normalizes the Host header so the MCP SDK's DNS-rebinding
# protection (localhost-only allowlist) doesn't 421 in-docker calls to `mcp:8100`.
ENV ORCHESTRATOR_TRANSPORT=streamable-http \
    ORCHESTRATOR_HTTP_HOST=0.0.0.0 \
    ORCHESTRATOR_HTTP_PORT=8100
CMD ["python", "-m", "master_orchestrator.main"]
