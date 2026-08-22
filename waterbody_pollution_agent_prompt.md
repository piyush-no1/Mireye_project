# Project Prompt: AquaTrace — Agentic Waterbody Pollution Assessment Platform

## 1. Project Overview

Build **AquaTrace**, a full-stack agentic application that assesses pollution levels and environmental risk for any user-specified water body in the United States. The user provides a natural-language location (e.g., *"Potomac River near Great Falls"*), and an LLM-driven agent orchestrates a chain of geospatial and environmental-data tool calls to produce a consolidated pollution report, which is persisted to a file and visualized on an interactive map-based frontend.

**Core stack:**
- **Backend orchestration:** Python, LangChain / LangGraph
- **LLM:** OpenAI model with native function/tool calling (including parallel tool calls)
- **Frontend:** React (map-based visualization of the river/stream network and pollution point markers)
- **Data persistence:** Structured file output (JSON, one per assessment run) as the source of truth for the frontend

---

## 2. Agentic Workflow (must be implemented as a LangGraph state graph)

Implement this as a directed graph of nodes, not a single monolithic prompt chain. Each stage below is a distinct node/tool with explicit inputs, outputs, and error handling.

### Stage 1 — Intent Parsing & Geocoding
- **Input:** Free-text location string from the user (e.g., "Potomac River near Great Falls").
- **Agent decision:** The agent recognizes it must first resolve spatial coordinates before anything else.
- **Tool:** `geocode_location(query: str) -> {lat: float, lng: float, matched_name: str}`
  - Calls the Mireye geocoding endpoint.
  - Parses the JSON response and extracts `lat`/`lng` as floats into agent state.
- **Failure handling:** If geocoding returns no match or ambiguous matches, the agent should ask a clarifying follow-up rather than guessing.

### Stage 2 — Hydrologic Snapping & Route Tracing
- **Tool:** `get_usgs_comid(lat: float, lng: float) -> {comid: str}`
  - Calls the USGS NLDI Position API to snap the coordinate to the nearest hydrologic flowline.
- **Tool:** `trace_network(comid: str, direction: str = "both") -> GeoJSON LineString`
  - Calls the USGS NLDI Navigation API to fetch upstream/downstream flowlines.
  - Chain this call automatically after `get_usgs_comid` succeeds — do not wait for a new user turn.

### Stage 3 — Internal Spatial Translation (deterministic utility, not an LLM tool call)
- **Function:** `simplify_geometry(linestring: GeoJSON) -> {bbox: [minLon, minLat, maxLon, maxLat], bank_points: List[Tuple[float, float]]}`
  - Pure Python (e.g., `shapely` / `geopandas`), no external API call.
  - Produces a bounding box for EPA queries and a sampled array of points along the banks (evenly spaced, configurable interval) for Mireye's terrain analysis.
  - Expose this to the agent as a callable tool so it remains part of the traceable execution graph, but implement it as deterministic code, not an LLM generation step.

### Stage 4 — Parallel Tool Dispatch
Once `bbox` and `bank_points` are available, dispatch the following **in parallel** (single LLM turn, native parallel tool calling):

| Tool | Source | Params | Extracted Fields |
|---|---|---|---|
| `get_epa_water_quality` | EPA Water Quality Portal | `bBox` | `MonitoringLocationIdentifier`, `CharacteristicName`, `ResultMeasureValue`, `ResultMeasure.MeasureUnitCode`, `ActivityStartDate` |
| `get_epa_attains_status` | EPA ATTAINS | `huc` or `bBox` | `assessmentUnitIdentifier`, `overallStatus`, `useAttainment`, `parameters`, `tmdlProjects` |
| `get_epa_echo_polluters` | EPA ECHO (ICIS-NPDES) | `p_c1=bbox`, `output=JSON` | `SourceID`, `FacilityName`, `Latitude`, `Longitude`, `PermitStatus`, `EffluentExceedances`, `QuarterInNoncompliance` |
| `get_mireye_land_risk` | Mireye Earth API | `points=[bank_points]` | `slope_degrees`, `elevation`, `lcms_class`, `tree_canopy_pct`, `ndvi_current`, `ndvi_change_5y`, `fema_flood_zone` |
| `get_usgs_nwis_telemetry` | USGS NWIS (Instantaneous Values) | `sites={gage_id}` or `bBox` | `00060` (discharge, cfs), `00065` (gage height, ft), `00010` (water temp, °C), `dateTime` |

All five calls should be independent (no data dependency between them) and issued as a single batch of tool calls in one LLM turn where the underlying model/framework supports it. Each tool must have its own retry/timeout policy so one slow API doesn't block the others.

### Stage 5 — Aggregation, Scoring & Persistence
- A final LangGraph node merges all tool outputs into one normalized JSON document (see schema in Section 3).
- Optionally compute a derived pollution/risk score (e.g., combining `overallStatus`, exceedance counts, and pollutant concentrations) — define the scoring logic explicitly and keep it deterministic/explainable, not an LLM free-text judgment.
- Persist the merged result to disk as `outputs/{run_id}_{waterbody_slug}.json`. This file is the single contract between backend and frontend — the React app should read from an API endpoint that serves this file, not from a live re-run.

---

## 3. Output Data Schema (persisted JSON — design this precisely)

Produce a single well-typed JSON document per assessment containing at minimum:

```json
{
  "run_id": "string",
  "query": "string (original user input)",
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
  "generated_at": "ISO 8601 timestamp"
}
```

Adjust field nesting as needed, but every field named in the source tables above must be represented somewhere in this schema — do not silently drop any.

---

## 4. Backend Requirements

- **Framework:** Python (FastAPI recommended) exposing:
  - `POST /assess` — accepts `{ "query": "<location text>" }`, runs the LangGraph pipeline, returns `run_id` (async job pattern preferred: return immediately with a job/run ID, expose a `GET /assess/{run_id}/status` and `GET /assess/{run_id}/result`).
  - `GET /assess/{run_id}/result` — returns the persisted JSON for frontend consumption.
- **Agent orchestration:** LangGraph state graph with explicit nodes for each stage above; LangChain tool wrappers around each API call.
- **Tool implementation:** Each external API call (Mireye geocode, USGS NLDI, USGS NWIS, EPA WQP, EPA ATTAINS, EPA ECHO, Mireye land risk) should be a standalone, independently testable Python function with typed inputs/outputs, wrapped as a LangChain `@tool`.
- **Resilience:** Timeouts, retries with backoff, and graceful partial-failure handling — if one API fails, the run should still complete with the remaining data and flag the missing section rather than aborting the whole pipeline.
- **Config:** All API base URLs and keys via environment variables / `.env`, never hardcoded.
- **Logging/tracing:** Log each tool call (inputs, latency, success/failure) for debuggability of the agent's decision chain.

## 5. Frontend Requirements (React)

- Input form for the free-text water body query, calling `POST /assess` and polling for completion.
- **Map view** (e.g., Leaflet/Mapbox GL/deck.gl) rendering:
  - The traced river/stream `LineString` geometry.
  - Markers for each polluting facility from `polluters`, styled/colored by `effluent_exceedances` or `permit_status` severity.
  - Markers or heat-layer for water quality sample locations, styled by pollutant concentration/exceedance.
  - Optional overlay for `fema_flood_zone` / `tree_canopy_pct` risk points.
- **Detail panels/sidebar:** Tables or cards summarizing ATTAINS status, telemetry (flow/discharge trends), and the overall risk score.
- **State management:** Fetch the persisted JSON result via the backend `result` endpoint; no direct calls from frontend to external APIs.

## 6. Non-Functional Requirements

- Modular, typed Python (Pydantic models for every API response schema).
- Clear separation between: (a) deterministic utility code, (b) LangChain tool wrappers, (c) LangGraph orchestration, (d) FastAPI routes, (e) React UI.
- Unit tests for each tool function using mocked API responses.
- README documenting setup, required API keys/env vars, and how to run backend + frontend locally.

## 7. Build Instructions for the Agent

1. Scaffold the repo structure first (backend/, frontend/, shared schemas) before writing implementation logic.
2. Implement Stage 1–3 tools and get a single end-to-end trace (geocode → COMID → flowline → bbox/points) working and tested before adding Stage 4's parallel dispatch.
3. Implement each Stage 4 API tool independently with a mock/sample response fixture, verify parsing, then wire into the parallel dispatch node.
4. Implement aggregation + JSON persistence (Section 3 schema) before starting frontend work.
5. Build the FastAPI endpoints against the persisted JSON contract.
6. Build the React frontend against the FastAPI endpoints, starting with static/mock JSON matching the schema, then switching to live backend calls.
7. Add error handling and partial-failure states last, once the happy path works end-to-end.
