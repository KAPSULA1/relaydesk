SHELL := /bin/sh

BE_DIR := backend
FE_DIR := frontend
BE_VENV := $(BE_DIR)/venv_relaydesk_pro
BE_PY := $(BE_VENV)/bin/python
BE_PIP := $(BE_VENV)/bin/pip

COLOR_INFO := \033[1;34m
COLOR_DONE := \033[1;32m
COLOR_RESET := \033[0m

.PHONY: be-install be-run be-migrate be-test be-lint be-shell be-superuser be-seed \
        fe-install fe-dev fe-build fe-lint fe-test \
        up down logs restart \
        format clean cov-html help

help:
	@printf "$(COLOR_INFO)RelayDesk Make Targets$(COLOR_RESET)\n"
	@printf "make be-install | be-run | be-test | fe-dev | up ...\n"

# ---------------------- Backend Commands ----------------------
be-install:
	@printf "$(COLOR_INFO)[Backend] Creating virtualenv and installing deps...$(COLOR_RESET)\n"
	@test -d $(BE_VENV) || python3 -m venv $(BE_VENV)
	@$(BE_PIP) install --upgrade pip
	@$(BE_PIP) install -r $(BE_DIR)/requirements.txt
	@printf "$(COLOR_DONE)Backend dependencies ready.$(COLOR_RESET)\n"

be-run:
	@printf "$(COLOR_INFO)[Backend] Starting Django dev server on :8010...$(COLOR_RESET)\n"
	@cd $(BE_DIR) && ../$(BE_PY) manage.py runserver 0.0.0.0:8010

be-migrate:
	@printf "$(COLOR_INFO)[Backend] Running migrations...$(COLOR_RESET)\n"
	@cd $(BE_DIR) && ../$(BE_PY) manage.py migrate

be-test:
	@printf "$(COLOR_INFO)[Backend] Running pytest with coverage...$(COLOR_RESET)\n"
	@cd $(BE_DIR) && ../$(BE_VENV)/bin/pytest --cov=chat --cov=relaydesk --cov-report=term-missing --cov-report=html

be-lint:
	@printf "$(COLOR_INFO)[Backend] Running black, ruff, mypy...$(COLOR_RESET)\n"
	@$(BE_VENV)/bin/black $(BE_DIR)
	@$(BE_VENV)/bin/ruff check $(BE_DIR)
	@cd $(BE_DIR) && ../$(BE_VENV)/bin/mypy .

be-shell:
	@cd $(BE_DIR) && ../$(BE_PY) manage.py shell

be-superuser:
	@cd $(BE_DIR) && ../$(BE_PY) manage.py createsuperuser

be-seed:
	@printf "$(COLOR_INFO)[Backend] Loading demo seed data...$(COLOR_RESET)\n"
	@cd $(BE_DIR) && ../$(BE_PY) manage.py seed_demo_data

# ---------------------- Frontend Commands ----------------------
fe-install:
	@printf "$(COLOR_INFO)[Frontend] Installing pnpm dependencies...$(COLOR_RESET)\n"
	@cd $(FE_DIR) && pnpm install

fe-dev:
	@printf "$(COLOR_INFO)[Frontend] Starting Next.js dev server on :3100...$(COLOR_RESET)\n"
	@cd $(FE_DIR) && PORT=3100 pnpm dev

fe-build:
	@cd $(FE_DIR) && pnpm build

fe-lint:
	@printf "$(COLOR_INFO)[Frontend] Running ESLint and Prettier check...$(COLOR_RESET)\n"
	@cd $(FE_DIR) && pnpm lint && pnpm prettier --check .

fe-test:
	@cd $(FE_DIR) && pnpm test

# ---------------------- Docker Commands ----------------------
up:
	@printf "$(COLOR_INFO)[Docker] compose up --build...$(COLOR_RESET)\n"
	@docker compose up -d --build

down:
	@docker compose down

logs:
	@docker compose logs -f

restart:
	@docker compose restart

# ---------------------- Utility ----------------------
format:
	@printf "$(COLOR_INFO)[Format] Running black + prettier...$(COLOR_RESET)\n"
	@$(BE_VENV)/bin/black $(BE_DIR)
	@cd $(FE_DIR) && pnpm prettier --write .

clean:
	@printf "$(COLOR_INFO)[Clean] Removing caches...$(COLOR_RESET)\n"
	@find $(BE_DIR) -name '__pycache__' -prune -exec rm -rf {} +
	@rm -rf $(BE_DIR)/.pytest_cache $(FE_DIR)/.next $(FE_DIR)/.turbo $(FE_DIR)/node_modules/.cache

cov-html:
	@printf "$(COLOR_INFO)[Coverage] Opening HTML report...$(COLOR_RESET)\n"
	@python3 -m webbrowser $(BE_DIR)/htmlcov/index.html
