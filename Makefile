.PHONY: help install uninstall lint test build run verify \
        pdm-install validate-manifests marketplace-add plugin-install verify-skills

help:
	@echo "Test Commander - Make targets"
	@echo ""
	@echo "  make install     Install Python deps, validate manifests, register the local"
	@echo "                   marketplace, install the plugin, and verify skills. Idempotent."
	@echo "  make uninstall   Remove the plugin and unregister the marketplace. Tolerates"
	@echo "                   already-clean state."
	@echo "  make lint        Run the ruff linter."
	@echo "  make test        Run pytest."
	@echo "  make build       Placeholder; runtimes ship in later phases."
	@echo "  make run         Placeholder; docker compose stack starts in Phase 10+."
	@echo "  make verify      Run lint, test, the skill verifier, and the Markdown link checker."

install: pdm-install validate-manifests marketplace-add plugin-install verify-skills

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
	python3 scripts/verify_skills.py

lint:
	pdm run ruff check .

test:
	pdm run pytest

build:
	@echo "Nothing to build yet. Runtimes ship in Phase 6 (Playwright) and Phase 10+ (web/API)."

run:
	@echo "Nothing to run yet. docker compose stack arrives in Phase 10+."

verify: lint test verify-skills
	python3 scripts/check_links.py
