# Project Prompt: AquaTrace — Agentic Waterbody Pollution Assessment Platform

You are building **AquaTrace**, a full-stack agentic application that assesses pollution levels and environmental risk for any user-specified water body in the United States. Follow this document as the authoritative spec. Where something is ambiguous, prefer the explicit structure given here over inventing your own — consistency with this spec matters more than stylistic preference.

---

## 1. Project Overview

**Input:** Free-text water body name from the user (e.g., *"Potomac River near Great Falls"*).
**Output:** A persisted JSON report + an interactive React map showing the traced river/stream, water quality sample points, polluting facilities, and land-risk overlays.

**Tech stack:**
- **Backend:** Python 3.11+, FastAPI, LangChain, LangGraph, Pydantic v2, `httpx` (async HTTP client), `shapely`/`geopandas` for geometry.
- **LLM:** OpenAI model with native function/tool calling and parallel tool calling.
- **Frontend:** React (Vite), TypeScript, a map library (Leaflet or Mapbox GL — pick one and use it consistently), a data-fetching layer (React Query/TanStack Query).
- **Persistence:** Flat JSON files on disk under `backend/data/outputs/` (no database in v1 — keep it filesystem-based, but structure the code so a DB could be swapped in later).

---

## 2. System Design

### 2.1 High-Level Architecture

```
┌─────────────────┐        HTTP (REST)        ┌──────────────────────────┐
│   React Frontend │ ─────────────────────────▶ │      FastAPI Backend     │
│   (Vite + TS)    │ ◀───────────────────────── │                          │
└─────────────────┘        JSON responses      │  ┌────────────────────┐  │
                                                 │  │  LangGraph Agent   │  │
                                                 │  │  (orchestrator)    │  │
                                                 │  └─────────┬──────────┘  │
                                                 │            │             │
                                                 │  ┌─────────▼──────────┐  │
                                                 │  │   Tool Layer        │  │
                                                 │  │  (LangChain @tool)  │  │
                                                 │  └─────────┬──────────┘  │
                                                 │            │             │
                                                 └────────────┼─────────────┘
                                                              │
                        ┌───────────────┬────────────┬────────────────┬──────────────────┐
                        ▼               ▼            ▼                ▼                  ▼
                 Mireye Geocode   USGS NLDI     USGS NWIS      EPA WQP / ATTAINS /   Mireye Earth
                     API           API           API              ECHO APIs             API
```

The frontend **never** calls external geospatial/environmental APIs directly. It only ever talks to the FastAPI backend, which owns all third-party API credentials and orchestration.

### 2.2 Request Lifecycle (async job pattern)

1. `POST /api/v1/assessments` with `{ "query": "<text>" }` → backend creates a `run_id`, kicks off the LangGraph pipeline as a background task, returns `{ "run_id": "...", "status": "pending" }` immediately (HTTP 202).
2. Frontend polls `GET /api/v1/assessments/{run_id}` every ~2s until `status` is `completed` or `failed`.
3. On `completed`, frontend calls `GET /api/v1/assessments/{run_id}/result` to fetch the full persisted JSON and renders the map + panels.
4. All intermediate state per run is tracked in an in-memory (or simple file-based) job store — see `backend/app/services/job_store.py` below.

### 2.3 LangGraph Pipeline (Stages — processing logic, unchanged)

Implement as a `StateGraph` with one shared typed state object (`AssessmentState`, a Pydantic model) threaded through every node.

**Stage 1 — Intent Parsing & Geocoding**
- Node: `geocode_node`
- Tool: `geocode_location(query: str) -> GeocodeResult{lat, lng, matched_name}`
- Calls Mireye geocoding endpoint. On no/ambiguous match, sets `state.status = "needs_clarification"` and halts the graph rather than guessing.

**Stage 2 — Hydrologic Snapping & Route Tracing**
- Node: `hydrology_node`
- Tool: `get_usgs_comid(lat, lng) -> {comid}` (USGS NLDI Position API)
- Tool: `trace_network(comid, direction="both") -> GeoJSON LineString` (USGS NLDI Navigation API) — chained automatically after `get_usgs_comid` succeeds, same node, no extra user turn.

**Stage 3 — Internal Spatial Translation** (deterministic, not an LLM generation step)
- Node: `spatial_translation_node`
- Function: `simplify_geometry(linestring) -> {bbox, bank_points}`
- Pure Python (`shapely`/`geopandas`). Exposed to the agent as a callable tool so it stays part of the traceable graph, but executed deterministically.

**Stage 4 — Parallel Tool Dispatch**
- Node: `parallel_fetch_node`
- Dispatches these five tools concurrently (native parallel tool calling / `asyncio.gather`):
  - `get_epa_water_quality(bbox)` — EPA Water Quality Portal
  - `get_epa_attains_status(bbox | huc)` — EPA ATTAINS
  - `get_epa_echo_polluters(bbox)` — EPA ECHO / ICIS-NPDES
  - `get_mireye_land_risk(points)` — Mireye Earth API
  - `get_usgs_nwis_telemetry(sites | bbox)` — USGS NWIS Instantaneous Values
- Each tool has its own timeout + retry policy (see 2.5). A single tool failing must not abort the others.

**Stage 5 — Aggregation, Scoring & Persistence**
- Node: `aggregate_node`
- Merges all tool outputs into the schema in Section 4.
- Computes `risk_summary` deterministically (explicit scoring function in `backend/app/services/scoring.py`, not LLM free text).
- Node: `persist_node` — writes `backend/data/outputs/{run_id}.json`, updates job store status to `completed`.

### 2.4 Error/Partial-Failure Policy

- Each Stage 4 tool call is wrapped in try/except; a failure produces `null` for that section plus an entry in `state.errors: List[{stage, tool, message}]`.
- The final persisted JSON always includes an `errors` array (empty if none) so the frontend can show "data unavailable" badges per section instead of failing the whole run.
- Stages 1–3 are **hard-fail**: if geocoding, COMID resolution, or tracing fails, the run stops with `status = "failed"` and a clear `error` message, since nothing downstream is meaningful without them.

### 2.5 Resilience Config (apply uniformly across all tool wrappers)

| Setting | Value |
|---|---|
| HTTP timeout per external call | 15s (30s for Mireye land-risk batch calls) |
| Retries | 2, exponential backoff (0.5s, 2s) |
| Retry-eligible errors | Connection errors, timeouts, HTTP 5xx |
| Non-retry-eligible | HTTP 4xx (log and fail fast) |

---

## 3. Explicit Repository / File Structure

Scaffold the repository **exactly** as follows before writing implementation logic. Do not invent alternate top-level layouts.

```
aquatrace/
├── README.md
├── .gitignore
├── .env.example
├── docker-compose.yml                     # optional but recommended: backend + frontend services
│
├── backend/
│   ├── .env                               # gitignored, local only — see Section 5
│   ├── .env.example                       # committed template — see Section 5
│   ├── pyproject.toml                     # or requirements.txt, pick one and be consistent
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                        # FastAPI app instance, CORS, router includes
│   │   ├── config.py                      # Pydantic Settings, loads from .env
│   │   │
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── routes_assessments.py      # POST /assessments, GET /assessments/{id}, GET /assessments/{id}/result
│   │   │   └── deps.py                    # shared FastAPI dependencies (job store, settings)
│   │   │
│   │   ├── agent/
│   │   │   ├── __init__.py
│   │   │   ├── graph.py                   # LangGraph StateGraph definition, node wiring
│   │   │   ├── state.py                   # AssessmentState Pydantic model
│   │   │   └── nodes/
│   │   │       ├── __init__.py
│   │   │       ├── geocode_node.py
│   │   │       ├── hydrology_node.py
│   │   │       ├── spatial_translation_node.py
│   │   │       ├── parallel_fetch_node.py
│   │   │       ├── aggregate_node.py
│   │   │       └── persist_node.py
│   │   │
│   │   ├── tools/
│   │   │   ├── __init__.py
│   │   │   ├── mireye_geocode_tool.py     # geocode_location
│   │   │   ├── usgs_nldi_tool.py          # get_usgs_comid, trace_network
│   │   │   ├── usgs_nwis_tool.py          # get_usgs_nwis_telemetry
│   │   │   ├── epa_wqp_tool.py            # get_epa_water_quality
│   │   │   ├── epa_attains_tool.py        # get_epa_attains_status
│   │   │   ├── epa_echo_tool.py           # get_epa_echo_polluters
│   │   │   └── mireye_land_risk_tool.py   # get_mireye_land_risk
│   │   │
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── geometry.py                # simplify_geometry() — shapely/geopandas logic
│   │   │   ├── scoring.py                 # deterministic risk_summary scoring function
│   │   │   ├── job_store.py               # in-memory/file-based run status tracker
│   │   │   └── http_client.py             # shared async httpx client w/ retry/backoff wrapper
│   │   │
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   ├── external.py                # Pydantic models for raw external API responses
│   │   │   ├── assessment.py              # Pydantic models for the persisted output (Section 4)
│   │   │   └── requests.py                # request/response models for FastAPI routes
│   │   │
│   │   └── core/
│   │       ├── __init__.py
│   │       ├── logging.py                 # structured logging config (per tool-call logs)
│   │       └── exceptions.py              # custom exception types (GeocodeNotFound, ExternalAPIError, etc.)
│   │
│   ├── data/
│   │   └── outputs/                       # gitignored except .gitkeep — persisted run JSON files land here
│   │       └── .gitkeep
│   │
│   └── tests/
│       ├── __init__.py
│       ├── conftest.py                    # shared fixtures (mocked httpx responses)
│       ├── fixtures/                      # sample JSON payloads per external API for mocking
│       │   ├── mireye_geocode_sample.json
│       │   ├── usgs_nldi_sample.json
│       │   ├── usgs_nwis_sample.json
│       │   ├── epa_wqp_sample.json
│       │   ├── epa_attains_sample.json
│       │   ├── epa_echo_sample.json
│       │   └── mireye_land_risk_sample.json
│       ├── tools/
│       │   ├── test_mireye_geocode_tool.py
│       │   ├── test_usgs_nldi_tool.py
│       │   ├── test_usgs_nwis_tool.py
│       │   ├── test_epa_wqp_tool.py
│       │   ├── test_epa_attains_tool.py
│       │   ├── test_epa_echo_tool.py
│       │   └── test_mireye_land_risk_tool.py
│       ├── services/
│       │   ├── test_geometry.py
│       │   └── test_scoring.py
│       └── api/
│           └── test_routes_assessments.py
│
└── frontend/
    ├── .env                                # gitignored — see Section 5
    ├── .env.example                        # committed template
    ├── package.json
    ├── tsconfig.json
    ├── vite.config.ts
    ├── index.html
    ├── Dockerfile
    ├── src/
    │   ├── main.tsx
    │   ├── App.tsx
    │   ├── api/
    │   │   ├── client.ts                   # base fetch wrapper, reads VITE_API_BASE_URL
    │   │   └── assessments.ts              # createAssessment(), getAssessment(), getAssessmentResult()
    │   ├── types/
    │   │   └── assessment.ts               # TypeScript types mirroring backend schemas/assessment.py
    │   ├── hooks/
    │   │   ├── useCreateAssessment.ts
    │   │   └── useAssessmentPolling.ts     # polls GET /assessments/{id} until completed/failed
    │   ├── components/
    │   │   ├── SearchBar/
    │   │   │   ├── SearchBar.tsx
    │   │   │   └── SearchBar.module.css
    │   │   ├── MapView/
    │   │   │   ├── MapView.tsx             # renders flowline, polluter markers, sample markers, risk overlays
    │   │   │   ├── FlowlineLayer.tsx
    │   │   │   ├── PolluterMarkers.tsx
    │   │   │   ├── WaterQualityMarkers.tsx
    │   │   │   ├── LandRiskOverlay.tsx
    │   │   │   └── MapView.module.css
    │   │   ├── ResultsPanel/
    │   │   │   ├── ResultsPanel.tsx
    │   │   │   ├── AttainsStatusCard.tsx
    │   │   │   ├── TelemetryChart.tsx
    │   │   │   ├── RiskScoreCard.tsx
    │   │   │   └── ErrorsBanner.tsx        # shows which sections failed, from state.errors
    │   │   └── layout/
    │   │       ├── Header.tsx
    │   │       └── Layout.tsx
    │   ├── pages/
    │   │   └── AssessmentPage.tsx          # top-level page: search → poll → map + panel
    │   └── styles/
    │       └── global.css
    └── public/
        └── favicon.svg
```

**Rules for the agent building this:**
- Do not merge the `tools/`, `services/`, and `agent/nodes/` layers — they are separate on purpose: `tools/` = raw external API wrappers, `services/` = pure internal logic, `agent/nodes/` = LangGraph glue that calls tools/services and mutates `AssessmentState`.
- Every file in `tools/` must have a corresponding test file in `tests/tools/` using a fixture from `tests/fixtures/`, not a live API call.
- `data/outputs/*.json` files are build artifacts, not source — add `backend/data/outputs/*.json` to `.gitignore` (keep `.gitkeep`).

---

## 4. Persisted Output Schema

One JSON file per run at `backend/data/outputs/{run_id}.json`, matching `app/schemas/assessment.py`:

```json
{
  "run_id": "string",
  "status": "completed | failed | needs_clarification",
  "query": "string",
  "resolved_location": { "matched_name": "string", "lat": 0.0, "lng": 0.0 },
  "hydrology": {
    "comid": "string",
    "flowline_geojson": { "...GeoJSON LineString or FeatureCollection..." },
    "bbox": [0.0, 0.0, 0.0, 0.0]
  },
  "water_quality_samples": [
    {
      "monitoring_location_id": "string",
      "characteristic_name": "string",
      "result_value": 0.0,
      "unit_code": "string",
      "activity_start_date": "string"
    }
  ],
  "attains_status": [
    {
      "assessment_unit_id": "string",
      "overall_status": "string",
      "use_attainment": {},
      "parameters": [],
      "tmdl_projects": []
    }
  ],
  "polluters": [
    {
      "source_id": "string",
      "facility_name": "string",
      "lat": 0.0,
      "lng": 0.0,
      "permit_status": "string",
      "effluent_exceedances": 0,
      "quarters_in_noncompliance": 0
    }
  ],
  "land_risk_points": [
    {
      "lat": 0.0,
      "lng": 0.0,
      "slope_degrees": 0.0,
      "elevation": 0.0,
      "lcms_class": "string",
      "tree_canopy_pct": 0.0,
      "ndvi_current": 0.0,
      "ndvi_change_5y": 0.0,
      "fema_flood_zone": "string"
    }
  ],
  "telemetry": [
    { "site_id": "string", "discharge_cfs": 0.0, "gage_height_ft": 0.0, "water_temp_c": 0.0, "date_time": "string" }
  ],
  "risk_summary": { "overall_score": 0.0, "label": "string", "notes": "string" },
  "errors": [
    { "stage": "string", "tool": "string", "message": "string" }
  ],
  "generated_at": "ISO 8601 timestamp"
}
```

Every field named in Section 6's API table must map to a field in this schema — do not silently drop any.

---

## 5. Environment Files (exact contents)

### 5.1 Root `.env.example` (committed — documents both services in one place for onboarding)

```dotenv
# ── This file is a reference only. Actual values live in backend/.env and frontend/.env ──
# See backend/.env.example and frontend/.env.example for the authoritative per-service templates.
```

### 5.2 `backend/.env.example` (committed)

```dotenv
# ── App ──
APP_ENV=development
APP_HOST=0.0.0.0
APP_PORT=8000
LOG_LEVEL=INFO
CORS_ALLOWED_ORIGINS=http://localhost:5173

# ── OpenAI / LLM ──
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4.1
OPENAI_REQUEST_TIMEOUT_SECONDS=30

# ── Mireye Earth API (geocoding + land risk) ──
MIREYE_API_KEY=
MIREYE_BASE_URL=https://api.mireye.com/v1

# ── USGS (no key required, but base URLs configurable for flexibility/testing) ──
USGS_NLDI_BASE_URL=https://labs.waterdata.usgs.gov/api/nldi
USGS_NWIS_BASE_URL=https://waterservices.usgs.gov/nwis/iv

# ── EPA Water Quality Portal ──
EPA_WQP_BASE_URL=https://www.waterqualitydata.usgs.gov/data

# ── EPA ATTAINS ──
EPA_ATTAINS_BASE_URL=https://attains.epa.gov/attains-public/api

# ── EPA ECHO (ICIS-NPDES) ──
EPA_ECHO_BASE_URL=https://echodata.epa.gov/echo

# ── HTTP resilience defaults (used by services/http_client.py) ──
HTTP_TIMEOUT_SECONDS=15
HTTP_TIMEOUT_SECONDS_LONG=30
HTTP_MAX_RETRIES=2
HTTP_RETRY_BACKOFF_BASE_SECONDS=0.5

# ── Storage ──
OUTPUT_DIR=./data/outputs
```

`backend/.env` (gitignored) is a local copy of the above with real secret values filled in. `app/config.py` loads it via `pydantic-settings`:

```python
# app/config.py (structure to implement)
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    log_level: str = "INFO"
    cors_allowed_origins: str = "http://localhost:5173"

    openai_api_key: str
    openai_model: str = "gpt-4.1"
    openai_request_timeout_seconds: int = 30

    mireye_api_key: str
    mireye_base_url: str = "https://api.mireye.com/v1"

    usgs_nldi_base_url: str = "https://labs.waterdata.usgs.gov/api/nldi"
    usgs_nwis_base_url: str = "https://waterservices.usgs.gov/nwis/iv"
    epa_wqp_base_url: str = "https://www.waterqualitydata.usgs.gov/data"
    epa_attains_base_url: str = "https://attains.epa.gov/attains-public/api"
    epa_echo_base_url: str = "https://echodata.epa.gov/echo"

    http_timeout_seconds: int = 15
    http_timeout_seconds_long: int = 30
    http_max_retries: int = 2
    http_retry_backoff_base_seconds: float = 0.5

    output_dir: str = "./data/outputs"

    class Config:
        env_file = ".env"

settings = Settings()
```

### 5.3 `frontend/.env.example` (committed)

```dotenv
VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_MAP_PROVIDER=leaflet
VITE_MAP_TILE_URL=https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png
VITE_POLL_INTERVAL_MS=2000
```

`frontend/.env` (gitignored) mirrors this with real values (only `VITE_*` variables are exposed to the client bundle by Vite — never put secrets here; the frontend must never hold API keys since it never calls external APIs directly).

### 5.4 Root `.gitignore` (must include at minimum)

```gitignore
# env
backend/.env
frontend/.env

# python
__pycache__/
*.pyc
.venv/
*.egg-info/

# node
node_modules/
frontend/dist/

# outputs
backend/data/outputs/*.json
!backend/data/outputs/.gitkeep

# misc
.DS_Store
*.log
```

---

## 6. External API Reference (unchanged processing logic — for tool implementers)

| Data Source | Endpoint / Method | Query Parameter | Key Fields to Pull | Purpose |
|---|---|---|---|---|
| USGS NWIS (Water Telemetry) | `GET https://waterservices.usgs.gov/nwis/iv/` | `sites={gage_id}` or `bBox` | `00060` (discharge, cfs), `00065` (gage height, ft), `00010` (water temp, °C), `dateTime` | Physical flow volume/velocity for pollutant mass load calculations |
| EPA Water Quality Portal (WQP) | `GET https://www.waterqualitydata.usgs.gov/data/Result/search` | `bBox={bbox}&mimeType=geojson` | `MonitoringLocationIdentifier`, `CharacteristicName` (pH, DO, Nitrates, PFAS, Lead), `ResultMeasureValue`, `ResultMeasure.MeasureUnitCode`, `ActivityStartDate` | Raw physical/chemical/biological lab sample results |
| EPA ATTAINS (Clean Water Act) | `GET https://attains.epa.gov/attains-public/api/assessmentUnits` | `huc={huc8/huc12}` or `bBox` | `assessmentUnitIdentifier`, `overallStatus`, `useAttainment`, `parameters`, `tmdlProjects` | Legal/regulatory health status under CWA 303(d)/305(b) |
| EPA ECHO (ICIS-NPDES) | `GET https://echodata.epa.gov/echo/cwa_rest_services.get_facility_info` | `output=JSON&p_c1={bbox}` | `SourceID`, `FacilityName`, `Latitude`, `Longitude`, `PermitStatus`, `EffluentExceedances`, `QuarterInNoncompliance` | Active point-source polluters and compliance violations |
| Mireye Earth API | `POST https://api.mireye.com/v1/fetch` | Array of bank `(lat, lon)` points | `slope_degrees`, `elevation`, `lcms_class`, `tree_canopy_pct`, `ndvi_current`, `ndvi_change_5y`, `fema_flood_zone` | Riparian/catchment context: erosion vulnerability, buffer capacity, floodplain risk |

---

## 7. API Contract (FastAPI routes)

```
POST   /api/v1/assessments
       Body: { "query": string }
       202 → { "run_id": string, "status": "pending" }

GET    /api/v1/assessments/{run_id}
       200 → { "run_id": string, "status": "pending" | "completed" | "failed" | "needs_clarification", "error": string | null }

GET    /api/v1/assessments/{run_id}/result
       200 → full persisted JSON (Section 4 schema)
       404 → if run_id unknown or not yet completed
```

---

## 8. Build Order (follow strictly, in this sequence)

1. Scaffold the exact directory tree in Section 3 (empty files/`pass`-only stubs are fine at this point).
2. Implement `config.py` + both `.env.example` files exactly as specified in Section 5.
3. Implement Stage 1–3 tools/nodes (`geocode_node`, `hydrology_node`, `spatial_translation_node`) with unit tests against fixtures; get one end-to-end trace working via a CLI/script before touching FastAPI.
4. Implement each Stage 4 tool independently (`tools/*.py`) against its fixture, with a passing test, before wiring any of them into `parallel_fetch_node`.
5. Wire `parallel_fetch_node`, then `aggregate_node` (+ `services/scoring.py`) and `persist_node`, producing a real JSON file matching Section 4.
6. Build `agent/graph.py` to connect all nodes into the full `StateGraph`; test the whole pipeline end-to-end with mocked tools.
7. Build FastAPI routes (`api/routes_assessments.py`) + `job_store.py`, backed by the working graph.
8. Scaffold the React app per the Section 3 tree; build `SearchBar` → `useCreateAssessment`/`useAssessmentPolling` → fetch flow first against a hard-coded mock JSON matching Section 4.
9. Build `MapView` (flowline + polluter markers + water quality markers + land risk overlay) and `ResultsPanel` against the same mock JSON.
10. Swap the frontend from mock JSON to the live backend endpoints.
11. Add resilience: retries/timeouts (Section 2.5), partial-failure banners (`ErrorsBanner`), and the `needs_clarification` UX path last.

---

## 9. Non-Functional Requirements

- All Pydantic models fully typed — no bare `dict`/`Any` for known API shapes.
- Every `tools/*.py` file independently unit-testable via fixtures in `tests/fixtures/` — no live network calls in tests.
- Structured logging (`core/logging.py`) for every tool call: tool name, inputs, latency, success/failure — the agent's decision chain must be reconstructable from logs.
- `README.md` at repo root documenting: prerequisites, how to fill in `backend/.env` and `frontend/.env`, how to run backend (`uvicorn app.main:app --reload`) and frontend (`npm run dev`) locally, and how to run tests (`pytest`).
