import json
from app.agent.state import AssessmentState
from app.services.scoring import reason_and_score_with_openai
from app.core.logging import logger, log_diagnostic_event

# Try importing shapely for geometry intersection
try:
    from shapely.geometry import shape, GeometryCollection
except ImportError:
    shape = None

async def aggregate_node(state: AssessmentState) -> AssessmentState:
    """Stage 5: Aggregation & OpenAI Reasoning Agent Node."""
    if state.status in ("failed", "needs_clarification"):
        return state

    # --- Spatial Filtering for LLM Context ---
    # We want to flag which ATTAINS Assessment Units lie directly on the traced river path.
    annotated_attains_status = []
    
    # Check if we have the tools to do the spatial check
    flowline_shape = None
    if shape and state.hydrology and state.hydrology.get("flowline_geojson"):
        features = state.hydrology["flowline_geojson"].get("features", [])
        if features:
            try:
                # Combine all flowline features into one shape and add a generous buffer (~500m / 0.005 degrees)
                shapes = [shape(f["geometry"]) for f in features if f.get("geometry")]
                if shapes:
                    flowline_shape = GeometryCollection(shapes).buffer(0.005)
            except Exception as e:
                logger.warning(f"Could not parse flowline geometry: {e}")

    for au in state.attains_status:
        is_primary = False
        
        if flowline_shape and au.get("geometry"):
            try:
                au_shape = shape(au["geometry"])
                if flowline_shape.intersects(au_shape):
                    is_primary = True
            except Exception:
                pass
                
        # Add the flag to the actual state so the frontend can see it
        au["is_primary_path"] = is_primary

    # Create a stripped down version for the LLM prompt to save tokens
    llm_attains_status = []
    for au in state.attains_status:
        au_copy = dict(au)
        au_copy.pop("geometry", None)
        llm_attains_status.append(au_copy)

    try:
        score_res = await reason_and_score_with_openai(
            query=state.query,
            attains_summary=getattr(state, "attains_summary", None),
            attains_status=llm_attains_status,
            polluters=state.polluters,
            water_samples=state.water_quality_samples,
            land_risk_points=state.land_risk_points,
            telemetry=state.telemetry,
            run_id=state.run_id
        )
        state.risk_summary = score_res
        
        state.execution_log.append({
            "stage": "Stage 5 — Aggregation & Reasoning",
            "component": "OpenAI Reasoning Agent",
            "status": "SUCCESS",
            "scoring_engine": score_res.get("scoring_engine", "openai_reasoning_agent")
        })
    except Exception as e:
        logger.error(f"Aggregate node scoring failed: {e}")
        error_msg = str(e)
        state.errors.append({
            "stage": "Stage 5 — Aggregation & Reasoning",
            "tool": "reason_and_score_with_openai",
            "message": error_msg
        })
        state.execution_log.append({
            "stage": "Stage 5 — Aggregation & Reasoning",
            "component": "OpenAI Reasoning Agent",
            "status": "FAILED",
            "error": error_msg
        })
        log_diagnostic_event(
            stage="Stage 5 — Aggregation & Reasoning",
            component="aggregate_node",
            status="FAILED",
            details={"error": error_msg},
            run_id=state.run_id
        )
        state.risk_summary = {
            "rating": "Unknown",
            "label": "Unknown",
            "risk_factors": [],
            "mitigating_factors": [],
            "temporal_assessment": "",
            "spatial_assessment": "",
            "data_limitations": "",
            "notes": f"Scoring error: {e}"
        }

    return state
