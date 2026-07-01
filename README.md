# AI-IDS: AI-Driven Intrusion Detection System

An AI-powered Intrusion Detection System that detects cyber-attacks using Machine Learning and sends notifications. The frontend is served directly by the backend as a single server.

## Architecture

- **Backend API** (FastAPI + Python 3.12) — Core detection engine with REST APIs, also serves the frontend SPA
- **ML Pipeline** (Scikit-Learn, XGBoost) — Threat classification with 4 model types
- **Database** (PostgreSQL) — Persistent storage for all security events
- **Frontend** (React + TypeScript + Vite) — Modern SOC dashboard (built and served by the backend)

## Quick Start

### Using Docker

```bash
docker compose -f docker/docker-compose.yml up -d
open http://localhost:80
# Admin: admin / Admin123!
```

### Manual Installation

```bash
# Backend
cd backend
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
uvicorn backend.main:app --reload --port 8000

# Frontend (development mode)
cd frontend
npm install
npm run dev
```

### Deploy to Render

Push to GitHub, connect to Render, set:
- **Build Command**: `./build.sh`
- **Start Command**: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT --workers 1`
- **Add a PostgreSQL database** — `DATABASE_URL` is auto-injected

## Features

- ML-based threat classification (Random Forest, XGBoost, Gradient Boosting, Isolation Forest)
- Port scan, DoS/DDoS, Brute Force, Botnet, Malware, SQL injection detection
- 60+ behavioral features extracted per network flow
- Multi-channel alerts (Discord, Slack, Telegram, Email, Webhook, Firebase)
- JWT authentication with role-based access (Admin, Analyst, Viewer)

## Project Structure

```
AI-IDS/
├── backend/
│   ├── api/            # REST API endpoints
│   ├── core/           # Logging, config
│   ├── database/       # Database session and models
│   ├── models/         # SQLAlchemy models
│   ├── schemas/        # Pydantic schemas
│   ├── repositories/   # Data access layer
│   ├── services/       # Business logic
│   ├── feature_engine/ # Feature extraction
│   ├── ml/             # ML pipeline
│   └── alerts/         # Notification engine
├── frontend/           # React dashboard (built into backend)
├── docker/             # Docker configuration
├── scripts/            # Database seeding utilities
├── render.yaml         # Render deployment config
└── build.sh            # Render build script
```

## API

- Swagger UI: `http://localhost:8000/api/docs`
- ReDoc: `http://localhost:8000/api/redoc`
