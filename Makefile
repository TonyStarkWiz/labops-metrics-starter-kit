# LabOps Metrics Starter Kit - Makefile

.PHONY: help install test lint format clean data api dashboard export dq-check

# Default target
help:
	@echo "LabOps Metrics Starter Kit - Available Commands:"
	@echo ""
	@echo "Setup:"
	@echo "  install     Install dependencies"
	@echo "  setup       Initial setup (install + pre-commit)"
	@echo ""
	@echo "Development:"
	@echo "  api         Start FastAPI server"
	@echo "  dashboard   Start Streamlit dashboard"
	@echo "  test        Run tests"
	@echo "  lint        Run linting checks"
	@echo "  format      Format code"
	@echo ""
	@echo "Data:"
	@echo "  data        Generate synthetic data"
	@echo "  export      Export data for Power BI"
	@echo "  dq-check    Run data quality checks"
	@echo ""
	@echo "Utilities:"
	@echo "  clean       Clean generated files"
	@echo "  reset       Reset database and generated data"

# Setup commands
install:
	pip install -r requirements.txt

setup: install
	pre-commit install

# Development commands
api:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

dashboard:
	streamlit run app/dashboards/streamlit_app.py

test:
	pytest tests/ -v --cov=app --cov-report=term-missing

lint:
	pre-commit run --all-files

format:
	black app/ scripts/ tests/
	isort app/ scripts/ tests/

# Data commands
data:
	python scripts/gen_synthetic_data.py --days 3 --per-day 1200

export:
	python scripts/export_for_powerbi.py

dq-check:
	python scripts/dq_check.py data/seeds/synthetic_*.csv

# Utility commands
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/

reset: clean
	rm -f labops.db
	rm -f test.db
	rm -rf data/seeds/synthetic_*.csv
	rm -rf data/seeds/exports/

# Quick start for demo
demo: data api dashboard

# Full development workflow
dev: install setup data
	@echo "Development environment ready!"
	@echo "Run 'make api' to start the API server"
	@echo "Run 'make dashboard' to start the dashboard"
	@echo "Run 'make test' to run tests"
