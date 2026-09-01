from app.agent.state import AssessmentState
from app.services.geometry import simplify_geometry
from app.core.logging import logger, log_diagnostic_event

async def spatial_translation_node(state: AssessmentState) -> AssessmentState:
    """Stage 3: Internal Spatial Translation Node."""
    if state.status in ("failed", "needs_clarification"):
        return state

    if not state.hydrology or "flowline_geojson" not in state.hydrology:
        state.status = "failed"
        state.error_message = "Cannot perform spatial translation without flowline GeoJSON."
        state.execution_log.append({
            "stage": "Stage 3 — Internal Spatial Translation",
            "component": "simplify_geometry",
            "status": "FAILED",
            "error": state.error_message
        })
        log_diagnostic_event("Stage 3 — Spatial Translation", "spatial_translation_node", "FAILED", {"error": state.error_message}, run_id=state.run_id)
        return state

    try:
        c_lat = state.resolved_location.get("lat") if state.resolved_location else None
        c_lng = state.resolved_location.get("lng") if state.resolved_location else None
        translated = simplify_geometry(state.hydrology["flowline_geojson"], center_lat=c_lat, center_lng=c_lng)
        w_type = translated.get("waterbody_type", "river")
        state.hydrology["bbox"] = translated["bbox"]
        state.hydrology["waterbody_type"] = w_type
        state.hydrology["_bank_points"] = translated["bank_points"]
        if state.resolved_location:
            state.resolved_location["waterbody_type"] = w_type
        
        state.execution_log.append({
            "stage": "Stage 3 — Internal Spatial Translation",
            "component": "simplify_geometry",
            "status": "SUCCESS",
            "bbox": translated["bbox"],
            "bank_points_count": len(translated["bank_points"])
        })
        log_diagnostic_event("Stage 3 — Spatial Translation", "simplify_geometry", "SUCCESS", {"bbox": translated["bbox"]}, run_id=state.run_id)
    except Exception as e:
        logger.error(f"Spatial translation node failed: {e}")
        state.status = "failed"
        state.error_message = f"Spatial geometry translation failed: {e}"
        state.errors.append({
            "stage": "Stage 3 — Internal Spatial Translation",
            "tool": "simplify_geometry",
            "message": str(e)
        })
        state.execution_log.append({
            "stage": "Stage 3 — Internal Spatial Translation",
            "component": "simplify_geometry",
            "status": "FAILED",
            "error": str(e)
        })
        log_diagnostic_event("Stage 3 — Spatial Translation", "simplify_geometry", "FAILED", {"error": str(e)}, run_id=state.run_id)

    return state
