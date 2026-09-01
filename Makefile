.PHONY: help install seed train test run dev docker-up docker-down

help:
	@echo "Smart Transit Intelligence System — CLI Commands"
	@echo "  make install     : Install Python and Dashboard dependencies"
	@echo "  make seed        : Seed the transit database with NCR corridor data"
	@echo "  make train       : Train ML crowd forecasting and ETA models"
	@echo "  make test        : Run full Pytest test suite"
	@echo "  make run         : Launch complete system (API + Simulator + Edge)"
	@echo "  make dev         : Start FastAPI server in reload mode"
	@echo "  make docker-up   : Spin up Docker Compose cluster"
	@echo "  make docker-down : Tear down Docker Compose cluster"

install:
	pip install -r requirements.txt
	cd apps/admin_dashboard && npm install

seed:
	python scripts/seed_data.py

train:
	python ml/training/train_crowd_model.py
	python ml/training/train_eta_model.py

test:
	pytest tests/ -v

run:
	python scripts/run_all.py

demo:
	python scripts/demo_runner.py

dev:
	uvicorn services.api.app.main:app --reload --port 8000

docker-up:
	docker compose up --build

docker-down:
	docker compose down
