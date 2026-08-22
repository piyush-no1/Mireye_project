# AquaTrace — Agentic Waterbody Pollution Assessment Platform

AquaTrace is an agentic full-stack application that assesses water quality, hydrologic flow, point-source polluters, and land risk for any user-specified water body in the United States.

## Architecture

- **Backend:** FastAPI, Python 3.11+, LangGraph, LangChain, Pydantic v2, `httpx`, `shapely`/`geopandas`.
- **Frontend:** React (Vite), TypeScript, Leaflet (`react-leaflet`), React Query (`@tanstack/react-query`).
- **Persistence:** JSON reports saved on disk under `backend/data/outputs/`.

## Prerequisites

- Python 3.11+
- Node.js 18+ & npm
- (Optional) Docker & Docker Compose

## Getting Started

### 1. Environment Setup

Copy `.env.example` files to `.env` in both `backend` and `frontend` directories:

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
```

Set your `OPENAI_API_KEY` and `MIREYE_API_KEY` in `backend/.env`. If omitted, AquaTrace will operate using realistic test fallback mode.

### 2. Backend Setup & Run

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Run backend API
uvicorn app.main:app --reload --port 8000
```

Backend API will run at `http://localhost:8000`.

### 3. Frontend Setup & Run

```bash
cd frontend
npm install
npm run dev
```

Frontend UI will run at `http://localhost:5173`.

### 4. Running Tests

```bash
cd backend
pytest
```

## API Specification

- `POST /api/v1/assessments` — Initiate background waterbody assessment (`{ "query": "Potomac River near Great Falls" }`).
- `GET /api/v1/assessments/{run_id}` — Check status (`pending`, `completed`, `failed`, `needs_clarification`).
- `GET /api/v1/assessments/{run_id}/result` — Retrieve full persisted JSON report.
