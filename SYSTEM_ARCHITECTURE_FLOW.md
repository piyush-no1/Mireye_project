# 🏗️ AquaTrace — Complete System Architecture & Node Code Flow Specification

This document provides a detailed technical breakdown of every execution node, data pipeline stage, sub-agent interaction, and hydrographic tool within the **AquaTrace Multi-Agent Platform**.

---

## 📐 Overall Graph Execution Flowchart

```mermaid
flowchart TD
    %% 1. Input Layer
    subgraph S1 ["1. Input (Frontend UI)"]
        direction TB
        Input1["Search Bar (Name / Location Query)"]
        Input2["Map Pinning (Point A ➔ Point B Corridor)"]
    end

    %% 2. Stage 1: Geocoding
    subgraph S2 ["Stage 1: Geocoding (geocode_node.py)"]
        Geocode["📍 GeocodeNode (mireye_geocode_tool.py / Nominatim)"]
    end

    %% 3. Stage 2: Hydrography Geometry
    subgraph S3 ["Stage 2: Spatial Geometry (spatial_translation_node.py)"]
        Hydro["🌊 SpatialTranslationNode (USGS NHD Layer 12/10 & Flowlines)"]
    end

    Input1 --> Geocode
    Input2 --> Hydro
    Geocode --> Hydro

    %% 4. Stage 3: General Baseline Data (EPA ATTAINS)
    subgraph S3_5 ["Stage 3: General Baseline Data"]
        ATTAINS["📋 EPA ATTAINS — General Waterbody Baseline<br/>(Clean Water Act Section 303d Impairments & Listed Causes)"]
    end

    Hydro --> ATTAINS

    %% 5. Stage 4: Specialized Reasoning Lanes
    subgraph S4 ["Stage 4: Specialized Reasoning Lanes"]
        direction LR

        subgraph IndustryLane ["🏭 Industry Processing Lane (industrial_specialist_node.py)"]
            direction TB
            IndNode["Industrial Specialist Agent"]
            ECHO["EPA ECHO — NPDES Facilities & Exceedances"]
            TRI["EPA TRI — Toxic Release Inventory Chemicals"]
            WQP_Ind["USGS WQP — Heavy Metals & Solvents"]
            Mireye_Ind["🛰️ Mireye Earth API — Outfall Utilities & Factory POIs"]
            
            IndNode --> ECHO
            IndNode --> TRI
            IndNode --> WQP_Ind
            IndNode <===> Mireye_Ind
        end

        subgraph AgriLane ["🌾 Agriculture Processing Lane (agricultural_specialist_node.py)"]
            direction TB
            AgriNode["Agricultural Specialist Agent"]
            USDA["USDA Cropland CDL — Agricultural Land % & CAFOs"]
            Sentinel["Sentinel Satellite — Algal Bloom Eutrophication"]
            WQP_Agri["USGS WQP — Nutrients & E. coli"]
            Mireye_Agri["🛰️ Mireye Earth API — Land Cover, Slope & Terrain"]
            
            AgriNode --> USDA
            AgriNode --> Sentinel
            AgriNode --> WQP_Agri
            AgriNode <===> Mireye_Agri
        end
    end

    ATTAINS --> IndustryLane
    ATTAINS --> AgriLane

    %% 6. Stage 5: Master Orchestration & Source Attribution
    subgraph S5 ["Stage 5: Master Synthesis & Source Attribution"]
        MasterNode["🧠 Master Orchestration Node (source_attribution.py)"]
        MireyeCall5["🛰️ Mireye Fallback ReAct Query (query_mireye_ask)"]
        MasterNode --- MireyeCall5
    end

    IndustryLane --> MasterNode
    AgriLane --> MasterNode

    %% 7. Stage 6 & 7: Persistence & Visualization
    subgraph S6_7 ["Stages 6 & 7: Persistence & Dashboard Render"]
        direction LR
        Persist["💾 PersistNode (backend/data/outputs/*.json)"]
        UI_Render["🖥️ React Dashboard (Contaminant Source Attribution & MapView)"]
        Persist --> UI_Render
    end

    MasterNode --> Persist

    %% Styling
    classDef inputStyle fill:#e0f2fe,stroke:#0284c7,stroke-width:2px,color:#0369a1
    classDef purpleStyle fill:#f3e8ff,stroke:#a855f7,stroke-width:2px,color:#6b21a8
    classDef baselineStyle fill:#dbeafe,stroke:#2563eb,stroke-width:3px,color:#1e40af
    classDef greenStyle fill:#dcfce7,stroke:#22c55e,stroke-width:2px,color:#15803d
    classDef orangeStyle fill:#ffedd5,stroke:#f97316,stroke-width:2px,color:#c2410c
    classDef yellowStyle fill:#fef08a,stroke:#eab308,stroke-width:2px,color:#854d0e

    class Input1,Input2 inputStyle
    class Geocode,Hydro purpleStyle
    class ATTAINS baselineStyle
    class ECHO,TRI,WQP_Ind,USDA,Sentinel,WQP_Agri greenStyle
    class IndNode,AgriNode,MasterNode orangeStyle
    class Mireye_Ind,Mireye_Agri,MireyeCall5 yellowStyle
```

---

## 🔍 Detailed Breakdown of Every Node & Code Component

### 1. `GeocodeNode` (`backend/app/agent/nodes/geocode_node.py`)
- **Purpose**: Converts user input (text queries like `"Utah Lake"` or custom Point A ➔ Point B map selections) into standardized geospatial location metadata.
- **Inputs**: `state.query`, `state.start_point`, `state.end_point`.
- **Mireye Integration**: **🛰️ MIREYE CALL 1 (Initial Geocoding Lookup)**: Queries `mireye_geocode_tool.py` (`geocode_waterbody`) and OpenStreetMap Nominatim REST API.
- **Outputs**:
  - `state.resolved_location`: `{ "lat": float, "lng": float, "display_name": str }`.
  - `state.hydrology["bbox"]`: Extended bounding box `[min_lng, min_lat, max_lng, max_lat]`.

---

### 2. `SpatialTranslationNode` (`backend/app/agent/nodes/spatial_translation_node.py`)
- **Purpose**: Generates high-accuracy hydrographic geometries for both river corridors and lake/pond waterbodies.
- **Inputs**: `state.resolved_location`, `state.hydrology["bbox"]`, `waterbody_type`.
- **Tools Invoked**: `usgs_nldi_tool.py` (`fetch_nhd_waterbody`, `fetch_river_segment_flowline`, `fetch_overpass_polygon_geometry`).
- **Detailed Geometry Logic**:
  - **Lotic Waterbodies (Rivers/Streams)**: Stitches continuous USGS NHD flowlines along Point A ➔ Point B.
  - **Lentic Waterbodies (Lakes/Ponds/Reservoirs)**: Multi-Tier Authoritative Polygon Engine:
    - *Tier 1*: Queries **USGS NHD MapServer Layer 12/10** (`NHDWaterbody`) for exact 100% real-world polygon boundaries (e.g., 4,778-point polygon for Utah Lake).
    - *Tier 2*: Queries **OSM Nominatim** (`polygon_geojson=1`).
    - *Tier 3*: Assembles OSM Overpass relations and ways.
    - *Subsampling*: Runs `subsample_polygon_ring(coords, max_points=450)` to ensure lag-free 60fps Leaflet vector rendering.
- **Outputs**:
  - `state.hydrology["flowline_geojson"]`: GeoJSON FeatureCollection (LineString or Polygon).
  - `state.hydrology["_bank_points"]`: Riverbank sampling points for land risk evaluation.

---

### 3. General Baseline Data Layer — EPA ATTAINS (`epa_attains_tool.py`)
- **Purpose**: Establishes the authoritative Clean Water Act Section 303(d) baseline waterbody impairment status, listed causes (e.g. Arsenic, Sediment, Nutrients), affected designated uses, and TMDL requirements.
- **Role in Workflow**: Functions as the primary general data entry point that feeds downstream specialized reasoning lanes.

---

### 4A. Industry Processing Lane — `IndustrialSpecialistNode` (`industrial_specialist_node.py`)
- **Purpose**: Specialized reasoning lane for point-source industrial pollution, NPDES outfall violations, and toxic chemical releases.
- **Datasets & Tools Consumed**:
  - **EPA ECHO Tool** (`epa_echo_tool.py`): NPDES Permitted Industrial Facilities & Effluent Violations
  - **EPA TRI Tool** (`epa_tri_tool.py`): Toxic Release Inventory Chemical Release Volumes
  - **USGS WQP Chemistry**: Filtered Industrial Water Samples (Lead, Arsenic, Cadmium, Mercury, Benzene, Toluene, pH)
  - **Mireye Earth API** (`query_mireye_fetch`, `query_mireye_ask`): `utilities` (Outfall channels), `points_of_interest` (Chemical & Manufacturing POIs)
- **Dynamic Execution**: Possesses **autonomous authority** to execute multi-turn tool calls (up to 4 turns) based on diagnostic relevance.
- **Outputs**: `state.industrial_analysis`.

---

### 4B. Agriculture Processing Lane — `AgriculturalSpecialistNode` (`agricultural_specialist_node.py`)
- **Purpose**: Specialized reasoning lane for non-point source agricultural runoff, fertilizer intensity, CAFO manure loading, and algal blooms.
- **Datasets & Tools Consumed**:
  - **USDA Cropland CDL Tool** (`usda_cropscape_tool.py`): Agricultural Land %, Crop Breakdown & CAFO Lagoons
  - **Sentinel Satellite Tool** (`sentinel_eutrophication_tool.py`): Algal Bloom Chlorophyll-a Eutrophication Index
  - **Mireye Land Risk Tool** (`mireye_land_risk_tool.py`): Riverbank Slope, Tree Canopy %, Soil Erodibility K-Factor
  - **USGS WQP Chemistry**: Filtered Agricultural Nutrient Samples (Nitrates, Phosphates, Ammonia, E. coli)
  - **Mireye Earth API** (`query_mireye_fetch`, `query_mireye_ask`): `land_cover`, `terrain`, manure lagoons
- **Dynamic Execution**: Possesses **autonomous authority** to execute multi-turn tool calls (up to 4 turns) based on diagnostic relevance.
- **Outputs**: `state.agricultural_analysis`.

---

### 5. `MasterOrchestrationNode` (`backend/app/agent/nodes/master_orchestration_node.py`)
- **Purpose**: Master MoA Orchestrator that synthesizes outputs from both specialized reasoning lanes into a unified Master Synthesis (`master_synthesis`).
- **Mireye Integration**: **🛰️ MIREYE CALL 5 (Fallback ReAct Reasoning Query)**: Executes `query_mireye_ask` inside `source_attribution.py` if remaining uncertainty requires natural language spatial reasoning.
- **Outputs**: `state.master_synthesis` (Overall Risk Score 0–100, Grade A–F, primary polluter category, EPA CWA 303d legal attribution).

---

### 6. `PersistNode` (`backend/app/agent/nodes/persist_node.py`)
- **Purpose**: Saves the complete, structured assessment report to local disk storage (`backend/data/outputs/assessment_<run_id>.json`) and feeds the Vite/React interactive UI dashboard.

---

## 🔄 Complete Execution Data Flow Summary (General Baseline ➔ Industry & Agriculture Lanes)

```text
User Request / Coordinates Selection
       │
       ▼
[Stage 1: GeocodeNode] ──► 🛰️ MIREYE CALL 1: Initial Geocoding Lookup (mireye_geocode_tool.py / Nominatim)
       │                    └─► Converts waterbody name/query ➔ Lat/Lng & Bounding Box
       ▼
[Stage 2: SpatialTranslationNode] ──► Hydrography Tracing & Polygon Engine
       │                            ├─► USGS NHD Layer 12/10 Waterbody Polygons (e.g. Utah Lake 4,778 pts)
       │                            └─► Extracts Riverbank Sampling Points (_bank_points)
       ▼
[Stage 3: EPA ATTAINS General Data] ──► Baseline CWA Section 303(d) Waterbody Impairments & Listed Causes
       │
       ├────────────────────────────────────────────────────────────────────────┐
       ▼                                                                        ▼
[Industry Processing Lane (Stage 4A)]                  [Agriculture Processing Lane (Stage 4B)]
  (industrial_specialist_node.py)                         (agricultural_specialist_node.py)
  │                                                        │
  ├─► EPA ECHO (Permitted Facilities & Exceedances)        ├─► USDA Cropland CDL (Agricultural Land % & CAFOs)
  ├─► EPA TRI (Toxic Release Inventory Chemicals)         ├─► Sentinel Satellite (Algal Bloom Eutrophication)
  ├─► USGS WQP (Heavy Metals, Solvents & pH)              ├─► USGS WQP (Nutrients: Nitrates, Phosphates, E. coli)
  └─► 🛰️ MIREYE DYNAMIC EARTH TOOLS (AUTONOMOUS)           └─► 🛰️ MIREYE DYNAMIC EARTH TOOLS (AUTONOMOUS)
       ├─► query_mireye_fetch(preset='utilities')              ├─► query_mireye_fetch(preset='land_cover')
       ├─► query_mireye_fetch(preset='points_of_interest')     ├─► query_mireye_fetch(preset='terrain')
       └─► query_mireye_ask() [Multi-turn, up to 4 turns]      └─► query_mireye_ask() [Multi-turn, up to 4 turns]
  │                                                        │
  └────────────────────────────────────────────────────────┴────────────────────┘
       │
       ▼
[Stage 5: MasterOrchestrationNode] ──► Synthesizes Evidence Across Lanes & Performs Source Attribution
       │                                └─► 🛰️ MIREYE CALL 5: Fallback ReAct Reasoning (query_mireye_ask)
       ▼
[Stage 6: PersistNode] ──► Save JSON Report (backend/data/outputs/assessment_<run_id>.json)
       │
       ▼
[Interactive Dashboard UI] ──► Contaminant-Centric Source Attribution Cards & Leaflet Map
```
