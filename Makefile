.PHONY: help install dev lint test build clean

# Default target
help:
	@echo "Alter/Ego Development Commands"
	@echo "─────────────────────────────────"
	@echo "  make install    Install dependencies"
	@echo "  make dev        Install with dev dependencies"
	@echo "  make lint       Run linters"
	@echo "  make test       Run tests"
	@echo "  make build      Build package"
	@echo "  make clean      Clean build artifacts"
	@echo ""

install:
	pip install -e .

dev:
	pip install -e ".[dev]"

lint:
	flake8 src/ tests/

test:
	pytest tests/ -v

build:
	python -m build

clean:
	rm -rf dist/ build/ *.egg-info
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
