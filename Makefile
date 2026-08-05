# agent-chat — one-command control of the full stack (frontend + backend + mcp).
# Two ways to run everything:
#   make up    — the whole stack in Docker (requires Compose v2: `docker compose`).
#   make dev   — the whole stack natively on the host (no Docker for the services;
#                only postgres is started as a container, since every agent's
#                checkpointer needs it).

SHELL := /bin/bash

COMPOSE ?= docker compose
PYTHON ?= python3
PNPM ?= pnpm
# Local venv for the (docker-free) Gemma health-check. The agents get LangChain from the
# mcp image; on the host we bootstrap just what the probe needs into this venv.
GEMMA_VENV ?= .venv-gemma
GEMMA_PY = $(GEMMA_VENV)/bin/python
GEMMA_DEPS = langchain langchain-openai pydantic-settings

# --- docker-free local stack ---------------------------------------------------
# Per-subsystem virtualenvs + a scratch dir holding pid files and logs.
BACKEND_VENV ?= backend/.venv
MCP_VENV ?= mcp/.venv
BACKEND_PY = $(abspath $(BACKEND_VENV))/bin/python
MCP_PY = $(abspath $(MCP_VENV))/bin/python
DEV_DIR ?= .dev
DEV_LOGS = $(DEV_DIR)/logs
DEV_PIDS = $(DEV_DIR)/pids
# Loopback only: these processes are for local development, not for exposure.
DEV_HOST ?= 127.0.0.1
DEV_FRONTEND_PORT ?= 3000
DEV_BACKEND_PORT ?= 8000
DEV_MCP_PORT ?= 8100
DEV_GUARDRAILS_PORT ?= 8200
DEV_SERVICES = guardrails mcp backend frontend

# Source the root .env (if present) so the same overrides drive both stacks.
LOAD_ENV = set -a; [ -f .env ] && . ./.env; set +a
# Postgres reachable from the host (compose publishes ${POSTGRES_PORT:-5432}).
DEV_DB_URL = postgresql://$${POSTGRES_USER:-agent}:$${POSTGRES_PASSWORD:-agent}@$(DEV_HOST):$${POSTGRES_PORT:-5432}/$${POSTGRES_DB:-agent_chat}
# The guardrails gate reachable from the host. Spelled ONCE: `dev`, `run-mcp` and
# `run-guardrails` all expand this, so a foreground mcp can never disagree with the
# background one about where the gate lives. The compose hostname (guardrails:8200)
# resolves only inside the Compose network and must never leak into a host process —
# check_input is fail-closed, so a wrong URL rejects every turn.
DEV_GUARDRAILS_PORT_EXPR = $${GUARDRAILS_PORT:-$(DEV_GUARDRAILS_PORT)}
DEV_GUARDRAILS_URL = http://$(DEV_HOST):$(DEV_GUARDRAILS_PORT_EXPR)/mcp

.DEFAULT_GOAL := help

.PHONY: help up up-fg down build rebuild logs ps restart clean \
        gemma-check news-check mcp-check tools-check \
        dev dev-install dev-install-mcp dev-install-backend dev-install-frontend \
        dev-python dev-db dev-db-stop dev-stop dev-restart dev-logs dev-ps dev-clean \
        run-guardrails run-mcp run-backend run-frontend

help: ## Show this help
	@echo "agent-chat — available targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN{FS=":.*?## "}{printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ==============================================================================
# Docker stack
# ==============================================================================

up: ## Build (if needed) and start the whole stack in the background
	$(COMPOSE) up -d --build

up-fg: ## Start the whole stack in the foreground (Ctrl-C to stop)
	$(COMPOSE) up --build

down: ## Stop and remove the stack's containers and network
	$(COMPOSE) down

build: ## Build all service images without starting them
	$(COMPOSE) build

rebuild: ## Rebuild images from scratch (no cache)
	$(COMPOSE) build --no-cache

logs: ## Follow logs from all services
	$(COMPOSE) logs -f

ps: ## Show the status of the stack's services
	$(COMPOSE) ps

restart: ## Restart all services
	$(COMPOSE) restart

clean: ## Stop the stack and remove volumes and locally-built images
	$(COMPOSE) down -v --rmi local

# ==============================================================================
# Docker-free local stack (mcp + backend + frontend as host processes)
# ==============================================================================

# The stack targets CPython 3.14+ (the images are built on python:3.14-slim);
# `requires-python = ">=3.14"` in every pyproject.toml says the same thing.
PY_RANGE_CHECK = -c 'import sys; sys.exit(0 if sys.version_info[:2] >= (3,14) else 1)'

dev-python: ## Verify $(PYTHON) is a supported interpreter for the docker-free stack
	@$(PYTHON) $(PY_RANGE_CHECK) 2>/dev/null || { \
		echo "!!! $(PYTHON) is $$($(PYTHON) -V 2>&1); this stack needs CPython >= 3.14 (images use 3.14)."; \
		echo "    re-run with an explicit interpreter, e.g.: make dev-install PYTHON=python3.14"; \
		exit 1; }

dev-install-mcp: dev-python ## Create mcp/.venv and install agent_core + all agents
	@if [ -x $(MCP_PY) ] && ! $(MCP_PY) $(PY_RANGE_CHECK) 2>/dev/null; then \
		echo "==> $(MCP_VENV) has an unsupported interpreter — recreating"; rm -rf $(MCP_VENV); fi
	@test -x $(MCP_PY) || $(PYTHON) -m venv $(MCP_VENV)
	@$(MCP_PY) -m pip install -q --upgrade pip
	@echo "==> installing mcp agents (agent_core first)"
	# NOT editable: every agent uses the flat layout `sources = { "." = "<pkg>" }`,
	# which hatchling refuses to build in dev mode (it rewrites an import prefix
	# instead of removing one). The Dockerfile installs them the same way. Source
	# stays live anyway — the processes run with cwd=mcp/, so `mcp/<agent>/` is
	# imported ahead of the site-packages copy. Re-run this target after adding a
	# dependency to any agent's pyproject.toml.
	@$(MCP_PY) -m pip install -q ./mcp/agent_core
	@$(MCP_PY) -m pip install -q ./mcp/guardrails ./mcp/web_agent ./mcp/doc_analyzer \
		./mcp/image_analyzer ./mcp/master_orchestrator
	# guardrails has no ML dependency any more (TASK A9-1): structured PII is regex plus
	# checksum, unstructured PII is the model's job. Nothing to download.

dev-install-backend: dev-python ## Create backend/.venv and editable-install the gateway
	@if [ -x $(BACKEND_PY) ] && ! $(BACKEND_PY) $(PY_RANGE_CHECK) 2>/dev/null; then \
		echo "==> $(BACKEND_VENV) has an unsupported interpreter — recreating"; rm -rf $(BACKEND_VENV); fi
	@test -x $(BACKEND_PY) || $(PYTHON) -m venv $(BACKEND_VENV)
	@$(BACKEND_PY) -m pip install -q --upgrade pip
	@echo "==> installing backend gateway"
	# The gateway uses a normal package layout, so editable works here.
	@$(BACKEND_PY) -m pip install -q -e "./backend[sqlite]"

dev-install-frontend: ## Install frontend node_modules (pnpm)
	@command -v $(PNPM) >/dev/null || { echo "pnpm not found — install it (corepack enable)"; exit 1; }
	@echo "==> installing frontend deps"
	@cd frontend && $(PNPM) install --frozen-lockfile

dev-install: dev-install-mcp dev-install-backend dev-install-frontend ## Install every subsystem for the docker-free stack

dev-db: ## Start ONLY postgres in Docker (the host services still need it) and wait for it
	@$(LOAD_ENV); \
	echo "==> starting postgres (container) on port $${POSTGRES_PORT:-5432}"; \
	$(COMPOSE) up -d postgres; \
	for i in $$(seq 1 30); do \
		if $(COMPOSE) exec -T postgres pg_isready -U "$${POSTGRES_USER:-agent}" -d "$${POSTGRES_DB:-agent_chat}" >/dev/null 2>&1; then \
			echo "    postgres ready"; exit 0; \
		fi; sleep 1; \
	done; \
	echo "!!! postgres did not become ready in 30s"; exit 1

dev-db-stop: ## Stop the postgres container (data volume is kept)
	@$(COMPOSE) stop postgres

dev: dev-db ## Start mcp + backend + frontend as background host processes (logs in .dev/logs)
	@$(LOAD_ENV); \
	test -x $(MCP_PY) || { echo "!!! $(MCP_VENV) missing — run: make dev-install"; exit 1; }; \
	test -x $(BACKEND_PY) || { echo "!!! $(BACKEND_VENV) missing — run: make dev-install"; exit 1; }; \
	test -d frontend/node_modules || { echo "!!! frontend/node_modules missing — run: make dev-install"; exit 1; }; \
	test -n "$${GEMMA_API_KEY:-}" || { echo "!!! GEMMA_API_KEY is not set (see .env.example) — agents will not start"; exit 1; }; \
	mkdir -p $(DEV_LOGS) $(DEV_PIDS); \
	db_url="$(DEV_DB_URL)"; \
	mcp_port="$${MCP_PORT:-$(DEV_MCP_PORT)}"; \
	backend_port="$${BACKEND_PORT:-$(DEV_BACKEND_PORT)}"; \
	frontend_port="$${FRONTEND_PORT:-$(DEV_FRONTEND_PORT)}"; \
	\
	guardrails_port="$(DEV_GUARDRAILS_PORT_EXPR)"; \
	echo "==> guardrails gate   $(DEV_GUARDRAILS_URL)"; \
	( cd mcp && \
	  PATH="$(abspath $(MCP_VENV))/bin:$$PATH" \
	  PYTHONPATH="$(abspath mcp)" \
	  GEMMA_API_KEY="$$GEMMA_API_KEY" \
	  GUARDRAILS_TRANSPORT=streamable-http \
	  GUARDRAILS_HTTP_HOST="$(DEV_HOST)" \
	  GUARDRAILS_HTTP_PORT="$$guardrails_port" \
	  GUARDRAILS_HTTP_ALLOWED_HOSTS="[\"localhost:$$guardrails_port\",\"127.0.0.1:$$guardrails_port\"]" \
	  GUARDRAILS_JUDGE_TIMEOUT_S="$${GUARDRAILS_JUDGE_TIMEOUT_S:-8}" \
	  GUARDRAILS_JUDGE_MAX_CHARS="$${GUARDRAILS_JUDGE_MAX_CHARS:-6000}" \
	  GUARDRAILS_MEDICAL_DISCLAIMER="$${GUARDRAILS_MEDICAL_DISCLAIMER:-true}" \
	  $(MCP_PY) -m guardrails.main ) \
	  >$(DEV_LOGS)/guardrails.log 2>&1 & echo $$! > $(DEV_PIDS)/guardrails.pid; \
	for i in $$(seq 1 60); do \
		(echo >/dev/tcp/$(DEV_HOST)/$$guardrails_port) >/dev/null 2>&1 && break; sleep 1; \
	done; \
	\
	echo "==> mcp orchestrator  http://$(DEV_HOST):$$mcp_port/mcp"; \
	( cd mcp && \
	  PATH="$(abspath $(MCP_VENV))/bin:$$PATH" \
	  PYTHONPATH="$(abspath mcp)" \
	  GEMMA_API_KEY="$$GEMMA_API_KEY" \
	  TAVILY_API_KEY="$${TAVILY_API_KEY:-}" \
	  ORCHESTRATOR_TRANSPORT=streamable-http \
	  ORCHESTRATOR_HTTP_HOST="$(DEV_HOST)" \
	  ORCHESTRATOR_HTTP_PORT="$$mcp_port" \
	  ORCHESTRATOR_HTTP_ALLOWED_HOSTS="[\"localhost:$$mcp_port\",\"127.0.0.1:$$mcp_port\"]" \
	  ORCHESTRATOR_DATABASE_URL="$$db_url" \
	  GUARDRAILS_URL="$(DEV_GUARDRAILS_URL)" \
	  GUARDRAILS_TIMEOUT_S="$${GUARDRAILS_TIMEOUT_S:-15}" \
	  ORCHESTRATOR_TURN_BUDGET_S="$${ORCHESTRATOR_TURN_BUDGET_S:-60}" \
	  LLM_REQUEST_TIMEOUT_S="$${LLM_REQUEST_TIMEOUT_S:-30}" \
	  LANGSMITH_TRACING="$${LANGSMITH_TRACING:-false}" \
	  LANGSMITH_API_KEY="$${LANGSMITH_API_KEY:-}" \
	  LANGSMITH_ENDPOINT="$${LANGSMITH_ENDPOINT:-https://api.smith.langchain.com}" \
	  LANGSMITH_PROJECT="$${LANGSMITH_PROJECT:-gemma-chat}" \
	  $(MCP_PY) -m master_orchestrator.main ) \
	  >$(DEV_LOGS)/mcp.log 2>&1 & echo $$! > $(DEV_PIDS)/mcp.pid; \
	for i in $$(seq 1 40); do \
		(echo >/dev/tcp/$(DEV_HOST)/$$mcp_port) >/dev/null 2>&1 && break; sleep 1; \
	done; \
	\
	echo "==> backend gateway   http://$(DEV_HOST):$$backend_port"; \
	( cd backend && \
	  GATEWAY_HOST="$(DEV_HOST)" \
	  GATEWAY_PORT="$$backend_port" \
	  GATEWAY_CORS_ORIGINS="[\"http://localhost:$$frontend_port\",\"http://127.0.0.1:$$frontend_port\"]" \
	  GATEWAY_ORCHESTRATOR_MODE=http \
	  GATEWAY_ORCHESTRATOR_MCP_URL="http://$(DEV_HOST):$$mcp_port/mcp" \
	  GATEWAY_ORCHESTRATOR_TIMEOUT_S="$${GATEWAY_ORCHESTRATOR_TIMEOUT_S:-66}" \
	  $(BACKEND_PY) -m uvicorn gateway.main:app --host "$(DEV_HOST)" --port "$$backend_port" ) \
	  >$(DEV_LOGS)/backend.log 2>&1 & echo $$! > $(DEV_PIDS)/backend.pid; \
	\
	echo "==> frontend          http://localhost:$$frontend_port"; \
	( cd frontend && \
	  NEXT_PUBLIC_API_BASE_URL="http://localhost:$$backend_port" \
	  $(PNPM) dev --port "$$frontend_port" ) \
	  >$(DEV_LOGS)/frontend.log 2>&1 & echo $$! > $(DEV_PIDS)/frontend.pid; \
	\
	echo ""; \
	echo "stack started — logs: make dev-logs | status: make dev-ps | stop: make dev-stop"

# Kill a background service and the children it spawned (next dev, uvicorn reloader).
define dev_kill
	$(LOAD_ENV); \
	port="$(2)"; \
	if [ -f $(DEV_PIDS)/$(1).pid ]; then \
		pid=$$(cat $(DEV_PIDS)/$(1).pid); \
		if kill -0 $$pid 2>/dev/null; then \
			pkill -TERM -P $$pid 2>/dev/null || true; \
			kill -TERM $$pid 2>/dev/null || true; \
			echo "  stopped $(1) (pid $$pid)"; \
		else \
			echo "  $(1) not running (stale pid file)"; \
		fi; \
		rm -f $(DEV_PIDS)/$(1).pid; \
	else \
		echo "  $(1) not running (no pid file)"; \
	fi; \
	if ! command -v lsof >/dev/null 2>&1; then \
		echo "  $(1): lsof not found — port $$port not swept"; \
	else \
		holders=$$(lsof -nP -iTCP:$$port -sTCP:LISTEN -t 2>/dev/null || true); \
		if [ -n "$$holders" ]; then \
			echo "  $(1): port $$port still held by $$(echo $$holders) — sending TERM"; \
			kill -TERM $$holders 2>/dev/null || true; \
			for _ in 1 2 3 4 5; do \
				sleep 1; \
				holders=$$(lsof -nP -iTCP:$$port -sTCP:LISTEN -t 2>/dev/null || true); \
				[ -z "$$holders" ] && break; \
			done; \
			if [ -n "$$holders" ]; then \
				echo "  $(1): port $$port survived TERM — sending KILL to $$(echo $$holders)"; \
				kill -KILL $$holders 2>/dev/null || true; \
				sleep 1; \
			fi; \
			holders=$$(lsof -nP -iTCP:$$port -sTCP:LISTEN -t 2>/dev/null || true); \
			if [ -n "$$holders" ]; then \
				echo "  !! $(1): port $$port STILL held by $$(echo $$holders) — stop it manually"; \
			else \
				echo "  $(1): port $$port free"; \
			fi; \
		fi; \
	fi;
endef

dev-stop: ## Stop the background host processes started by `make dev`
	@echo "==> stopping host services"
	@$(call dev_kill,guardrails,$${GUARDRAILS_PORT:-$(DEV_GUARDRAILS_PORT)})
	@$(call dev_kill,mcp,$${MCP_PORT:-$(DEV_MCP_PORT)})
	@$(call dev_kill,backend,$${BACKEND_PORT:-$(DEV_BACKEND_PORT)})
	@$(call dev_kill,frontend,$${FRONTEND_PORT:-$(DEV_FRONTEND_PORT)})
	@echo "postgres is left running — stop it with: make dev-db-stop"

dev-restart: ## Restart the docker-free stack
	@$(MAKE) dev-stop
	@$(MAKE) dev

dev-logs: ## Follow the logs of the docker-free stack (ARGS="mcp" for one service)
	@test -d $(DEV_LOGS) || { echo "no logs yet — run: make dev"; exit 1; }
	@tail -n 50 -f $(DEV_LOGS)/$(if $(ARGS),$(ARGS),*).log

dev-ps: ## Show which docker-free services are alive and on which ports
	@$(LOAD_ENV); \
	printf "%-10s %-8s %-8s %s\n" SERVICE PID PORT STATE; \
	for s in $(DEV_SERVICES); do \
		case $$s in \
			guardrails) port="$(DEV_GUARDRAILS_PORT_EXPR)";; \
			mcp) port="$${MCP_PORT:-$(DEV_MCP_PORT)}";; \
			backend) port="$${BACKEND_PORT:-$(DEV_BACKEND_PORT)}";; \
			frontend) port="$${FRONTEND_PORT:-$(DEV_FRONTEND_PORT)}";; \
		esac; \
		if [ -f $(DEV_PIDS)/$$s.pid ] && kill -0 $$(cat $(DEV_PIDS)/$$s.pid) 2>/dev/null; then \
			state=running; pid=$$(cat $(DEV_PIDS)/$$s.pid); \
		else state=stopped; pid=-; fi; \
		printf "%-10s %-8s %-8s %s\n" $$s $$pid $$port $$state; \
	done; \
	echo ""; $(COMPOSE) ps postgres

dev-clean: ## Stop everything docker-free and remove .dev/, the venvs and node_modules
	@$(MAKE) dev-stop
	@$(MAKE) dev-db-stop
	@rm -rf $(DEV_DIR) $(MCP_VENV) $(BACKEND_VENV) frontend/node_modules
	@echo "removed $(DEV_DIR), $(MCP_VENV), $(BACKEND_VENV), frontend/node_modules"

# --- single services in the foreground (debugging: full output, Ctrl-C to stop) ---

run-guardrails: ## Run only the guardrails gate in the foreground (`run-mcp` needs it listening)
	@$(LOAD_ENV); \
	guardrails_port="$(DEV_GUARDRAILS_PORT_EXPR)"; \
	cd mcp && \
	PATH="$(abspath $(MCP_VENV))/bin:$$PATH" \
	PYTHONPATH="$(abspath mcp)" \
	GEMMA_API_KEY="$${GEMMA_API_KEY:?GEMMA_API_KEY is required (see .env.example)}" \
	GUARDRAILS_TRANSPORT=streamable-http \
	GUARDRAILS_HTTP_HOST="$(DEV_HOST)" \
	GUARDRAILS_HTTP_PORT="$$guardrails_port" \
	GUARDRAILS_HTTP_ALLOWED_HOSTS="[\"localhost:$$guardrails_port\",\"127.0.0.1:$$guardrails_port\"]" \
	GUARDRAILS_JUDGE_TIMEOUT_S="$${GUARDRAILS_JUDGE_TIMEOUT_S:-8}" \
	GUARDRAILS_JUDGE_MAX_CHARS="$${GUARDRAILS_JUDGE_MAX_CHARS:-6000}" \
	GUARDRAILS_MEDICAL_DISCLAIMER="$${GUARDRAILS_MEDICAL_DISCLAIMER:-true}" \
	$(MCP_PY) -m guardrails.main

run-mcp: ## Run only the mcp orchestrator in the foreground (needs a gate: `make dev` or `run-guardrails`)
	@$(LOAD_ENV); \
	db_url="$(DEV_DB_URL)"; mcp_port="$${MCP_PORT:-$(DEV_MCP_PORT)}"; \
	cd mcp && \
	PATH="$(abspath $(MCP_VENV))/bin:$$PATH" \
	PYTHONPATH="$(abspath mcp)" \
	GEMMA_API_KEY="$${GEMMA_API_KEY:?GEMMA_API_KEY is required (see .env.example)}" \
	TAVILY_API_KEY="$${TAVILY_API_KEY:-}" \
	ORCHESTRATOR_TRANSPORT=streamable-http \
	ORCHESTRATOR_HTTP_HOST="$(DEV_HOST)" \
	ORCHESTRATOR_HTTP_PORT="$$mcp_port" \
	ORCHESTRATOR_HTTP_ALLOWED_HOSTS="[\"localhost:$$mcp_port\",\"127.0.0.1:$$mcp_port\"]" \
	ORCHESTRATOR_DATABASE_URL="$$db_url" \
	GUARDRAILS_URL="$(DEV_GUARDRAILS_URL)" \
	GUARDRAILS_TIMEOUT_S="$${GUARDRAILS_TIMEOUT_S:-15}" \
	$(MCP_PY) -m master_orchestrator.main

run-backend: ## Run only the backend gateway in the foreground (with --reload)
	@$(LOAD_ENV); \
	backend_port="$${BACKEND_PORT:-$(DEV_BACKEND_PORT)}"; \
	mcp_port="$${MCP_PORT:-$(DEV_MCP_PORT)}"; \
	cd backend && \
	GATEWAY_HOST="$(DEV_HOST)" \
	GATEWAY_PORT="$$backend_port" \
	GATEWAY_ORCHESTRATOR_MODE=http \
	GATEWAY_ORCHESTRATOR_MCP_URL="http://$(DEV_HOST):$$mcp_port/mcp" \
	GATEWAY_ORCHESTRATOR_TIMEOUT_S="$${GATEWAY_ORCHESTRATOR_TIMEOUT_S:-66}" \
	$(BACKEND_PY) -m uvicorn gateway.main:app --host "$(DEV_HOST)" --port "$$backend_port" --reload

run-frontend: ## Run only the frontend dev server in the foreground
	@$(LOAD_ENV); \
	backend_port="$${BACKEND_PORT:-$(DEV_BACKEND_PORT)}"; \
	frontend_port="$${FRONTEND_PORT:-$(DEV_FRONTEND_PORT)}"; \
	cd frontend && \
	NEXT_PUBLIC_API_BASE_URL="http://localhost:$$backend_port" \
	$(PNPM) dev --port "$$frontend_port"

# ==============================================================================
# Health checks
# ==============================================================================

gemma-check: ## Check whether the Gemma hosting is reachable (no docker; use ARGS="--json")
	@test -x $(GEMMA_PY) || $(PYTHON) -m venv $(GEMMA_VENV)
	@$(GEMMA_PY) -c 'import langchain_openai, openai, pydantic_settings; from langchain.schema import HumanMessage' 2>/dev/null \
		|| $(GEMMA_PY) -m pip install -q --disable-pip-version-check $(GEMMA_DEPS)
	@$(GEMMA_PY) mcp/scripts/gemma_healthcheck.py $(ARGS)

news-check: ## Direct aiohttp REST call to Tavily search (no agents/orchestrator/LLM invoked)
	@$(PYTHON) mcp/scripts/news_check.py $(ARGS)

tools-check: ## Verify the orchestrator binds a non-empty tool set (search_web present); runs inside the mcp container
	@$(COMPOSE) exec mcp python scripts/tools_check.py $(ARGS)
