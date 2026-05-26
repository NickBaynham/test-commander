.PHONY: help install lint test build run verify

help:
	@echo "Test Commander - Make targets"
	@echo ""
	@echo "  make install   Install Python dependencies via PDM."
	@echo "  make lint      Run the ruff linter."
	@echo "  make test      Run pytest."
	@echo "  make build     Placeholder; runtimes ship in later phases."
	@echo "  make run       Placeholder; docker compose stack starts in Phase 10+."
	@echo "  make verify    Run lint, test, and the Markdown link checker."

install:
	pdm install

lint:
	pdm run ruff check .

test:
	pdm run pytest

build:
	@echo "Nothing to build yet. Runtimes ship in Phase 6 (Playwright) and Phase 10+ (web/API)."

run:
	@echo "Nothing to run yet. docker compose stack arrives in Phase 10+."

verify: lint test
	python3 scripts/verify_skills.py
	python3 scripts/check_links.py
