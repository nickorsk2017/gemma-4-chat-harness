# agent-chat — one-command control of the full stack (frontend + backend + mcp).
# Requires Docker with the Compose v2 plugin (`docker compose`).

COMPOSE ?= docker compose
PYTHON ?= python3
# Local venv for the (docker-free) Gemma health-check. The agents get LangChain from the
# mcp image; on the host we bootstrap just what the probe needs into this venv.
GEMMA_VENV ?= .venv-gemma
GEMMA_PY = $(GEMMA_VENV)/bin/python
GEMMA_DEPS = langchain langchain-openai pydantic-settings

.DEFAULT_GOAL := help

.PHONY: help up up-fg down build rebuild logs ps restart clean gemma-check mcp-check tools-check

help: ## Show this help
	@echo "agent-chat — available targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN{FS=":.*?## "}{printf "  \033[36m%-10s\033[0m %s\n", $$1, $$2}'

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

gemma-check: ## Check whether the Gemma hosting is reachable (no docker; use ARGS="--json")
	@test -x $(GEMMA_PY) || $(PYTHON) -m venv $(GEMMA_VENV)
	@$(GEMMA_PY) -c 'import langchain_openai, openai, pydantic_settings; from langchain.schema import HumanMessage' 2>/dev/null \
		|| $(GEMMA_PY) -m pip install -q --disable-pip-version-check $(GEMMA_DEPS)
	@$(GEMMA_PY) mcp/scripts/gemma_healthcheck.py $(ARGS)

news-check: ## Direct aiohttp REST call to Tavily search (no agents/orchestrator/LLM invoked)
	@$(PYTHON) mcp/scripts/news_check.py $(ARGS)

tools-check: ## Verify the orchestrator binds a non-empty tool set (search_web present); runs inside the mcp container
	@$(COMPOSE) exec mcp python scripts/tools_check.py $(ARGS)
