# Makefile

.PHONY: up down build rebuild logs test tests

# Colors
GREEN  := $(shell tput -Txterm setaf 2)
YELLOW := $(shell tput -Txterm setaf 3)
WHITE  := $(shell tput -Txterm setaf 7)
RESET  := $(shell tput -Txterm sgr0)

##@ Utils

check-env:
	@if [ ! -f .env ]; then \
		echo "${YELLOW}Error: .env file not found. Run 'make setup' first.${RESET}" >&2; \
		exit 1; \
	fi

help: ## Show this help
	@echo '\nUsage: make ${YELLOW}<target>${RESET}\n\nTargets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  ${YELLOW}%-15s${RESET} %s\n", $$1, $$2}' $(MAKEFILE_LIST)

##@ Environment

setup: ## Copy .env.example to .env if it doesn't exist
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "${GREEN}Created .env file. Please update it with your API credentials.${RESET}"; \
	else \
		echo "${YELLOW}.env file already exists${RESET}"; \
	fi

##@ Docker Compose

up: check-env ## Start all services
	@echo "${GREEN}Starting Assistant environment...${RESET}"
	docker compose up -d --build
	@echo "\n${GREEN}Services started successfully!${RESET}"
	@echo "- API authentification: http://localhost:8001"
	@echo "- API assistant: http://localhost:8000"
	@echo "- Streamlit: http://localhost:8501"
	docker compose up -d auth main streamlit

down: ## Stop all services
	@echo "${YELLOW}Stopping Assistant environment...${RESET}"
	docker compose down

rerun: down up ## Restart all services

build:
	docker compose build

rebuild:
	docker compose down
	docker compose build
	docker compose up -d

logs: ## View logs from all services
	@echo "${YELLOW}Viewing logs (press Ctrl+C to exit)...${RESET}"
	docker compose logs -f --tail=50

clean: ## Stop services and remove containers, volumes, and networks
	@echo "${YELLOW}Cleaning up Assistant environment...${RESET}"
	docker compose down -v --remove-orphans

tests: check-env ## Run integration tests
	@echo "${GREEN}Running integration tests...${RESET}"
	docker compose up -d auth main
	docker compose run --rm tests
	docker compose stop auth main
