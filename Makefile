.PHONY: help install uninstall lint test build run verify \
        pdm-install validate-manifests marketplace-add plugin-install verify-skills \
        mermaid-install web-test web-e2e

help:
	@echo "Test Commander - Make targets"
	@echo ""
	@echo "  make install     Install Python deps, validate manifests, register the local"
	@echo "                   marketplace, install the plugin, verify skills, and provision"
	@echo "                   the Mermaid CLI for /tc:render-visuals. Idempotent."
	@echo "  make uninstall   Remove the plugin and unregister the marketplace. Tolerates"
	@echo "                   already-clean state."
	@echo "  make lint        Run the ruff linter."
	@echo "  make test        Run pytest."
	@echo "  make build       Placeholder; runtimes ship in later phases."
	@echo "  make run         Placeholder; docker compose stack starts in Phase 10+."
	@echo "  make verify      Run lint, test, the skill verifier, and the Markdown link checker."

install: pdm-install validate-manifests marketplace-add plugin-install verify-skills mermaid-install

uninstall:
	-claude plugin uninstall test-commander
	-claude plugin marketplace remove test-commander-marketplace

pdm-install:
	pdm install

validate-manifests:
	claude plugin validate .
	claude plugin validate plugins/test-commander

marketplace-add:
	@if claude plugin marketplace list 2>/dev/null | grep -q test-commander-marketplace; then \
		echo "marketplace test-commander-marketplace already registered"; \
	else \
		claude plugin marketplace add "$$PWD"; \
	fi

plugin-install:
	@if claude plugin list 2>/dev/null | grep -q 'test-commander@test-commander-marketplace'; then \
		echo "plugin test-commander@test-commander-marketplace already installed"; \
	else \
		claude plugin install test-commander@test-commander-marketplace; \
	fi

verify-skills:
	pdm run python scripts/verify_skills.py

mermaid-install:
	@if command -v mmdc >/dev/null 2>&1; then \
		echo "mermaid CLI (mmdc) already present; nothing to install"; \
	elif command -v npm >/dev/null 2>&1; then \
		echo "installing @mermaid-js/mermaid-cli (provides mmdc for /tc:render-visuals)"; \
		npm install -g @mermaid-js/mermaid-cli || \
			echo "mermaid CLI install failed; /tc:render-visuals degrades gracefully"; \
	else \
		echo "npm not found; skipping mermaid CLI (/tc:render-visuals degrades gracefully)"; \
	fi

lint:
	pdm run ruff check .

test:
	pdm run pytest

build:
	@echo "The Playwright automation framework is built lazily inside a consuming"
	@echo "project by /tc:build-framework (scripts/build_framework.py). The web/API"
	@echo "runtime arrives in Phase 10+. This repo ships the plugin + Python helpers;"
	@echo "there is no repo-level compile step."

run:
	@echo "Starting the Test Commander web console (api + web) via docker compose."
	@echo "Set TC_WORKSPACE to the project root holding .test-commander/ (default: cwd)."
	docker compose up --build

verify: lint test verify-skills
	pdm run python scripts/check_links.py

# Phase 10 web console frontend test lanes (Node-managed; not part of `verify`).
# The backend is covered by the Python `make test` gate; these cover the
# Next.js frontend.
web-test:
	cd apps/web && npm install && npm run test

web-e2e:
	@echo "Bring the stack up first: make run (or /tc:web-start --up)."
	cd apps/web && npm install && npm run e2e
