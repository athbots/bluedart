# Production Deployment & Operations Guide

## 1. Quick Local Execution (Zero-Dependency Mode)

```bash
# 1. Install dependencies
pip install -r requirements.txt
cd apps/admin_dashboard && npm install && cd ../..

# 2. Seed Database
python scripts/seed_data.py

# 3. Train ML Models
python ml/training/train_crowd_model.py
python ml/training/train_eta_model.py

# 4. Start Full System (FastAPI + Simulator + Edge Agent)
python scripts/run_all.py

# 5. Start Admin Dashboard (separate terminal)
cd apps/admin_dashboard && npm run dev
```

---

## 2. Production Deployment via Docker Compose

```bash
cp .env.example .env
docker compose up --build -d
```

### Services Started:
- `postgres`: PostgreSQL 16 on port 5432
- `redis`: Redis 7 on port 6379
- `mosquitto`: MQTT Broker on port 1883
- `api`: FastAPI Backend on port 8000
- `simulator`: Multi-bus physics simulator
- `dashboard`: React TypeScript Admin Dashboard on port 3000

---

## 3. Running Automated Tests

```bash
pytest tests/ -v
```
Verifies all 17 unit, geo, route matching, crowd hysteresis, ML inference, and offline buffering test suites.
