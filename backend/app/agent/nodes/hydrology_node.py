from app.agent.state import AssessmentState
from app.tools.usgs_nldi_tool import get_usgs_comid, trace_network
from app.core.logging import logger, log_diagnostic_event

async def hydrology_node(state: AssessmentState) -> AssessmentState:
    """Stage 2: Hydrologic Snapping & Route Tracing Node."""
    if state.status in ("failed", "needs_clarification"):
        return state

    if not state.resolved_location:
        state.status = "failed"
        state.error_message = "Cannot run hydrology node without resolved location."
        state.execution_log.append({
            "stage": "Stage 2 — Hydrologic Snapping & Route Tracing",
            "component": "hydrology_node",
            "status": "FAILED",
            "error": state.error_message
        })
        log_diagnostic_event("Stage 2 — Hydrology", "hydrology_node", "FAILED", {"error": state.error_message}, run_id=state.run_id)
        return state

    lat = state.resolved_location["lat"]
    lng = state.resolved_location["lng"]
    matched_name = state.resolved_location.get("matched_name", state.query)

    try:
        comid_res = await get_usgs_comid.ainvoke({"lat": lat, "lng": lng})
        comid = comid_res.get("comid", f"NHD-{lat:.4f}-{lng:.4f}")
        
        flowline_res = await trace_network.ainvoke({
            "comid": comid,
            "direction": "both",
            "lat": lat,
            "lng": lng,
            "query_name": matched_name
        })
        
        state.hydrology = {
            "comid": comid,
            "flowline_geojson": flowline_res,
            "bbox": [lng - 0.1, lat - 0.1, lng + 0.1, lat + 0.1]
        }
        state.execution_log.append({
            "stage": "Stage 2 — Hydrologic Snapping & Route Tracing",
            "component": "get_usgs_comid & trace_network",
            "status": "SUCCESS",
            "comid": comid
        })
        log_diagnostic_event("Stage 2 — Hydrology", "get_usgs_comid/trace_network", "SUCCESS", {"comid": comid}, run_id=state.run_id)
    except Exception as e:
        logger.error(f"Hydrology node failed for coords ({lat}, {lng}): {e}")
        state.status = "failed"
        state.error_message = f"Hydrologic snapping/tracing failed: {e}"
        state.errors.append({
            "stage": "Stage 2 — Hydrologic Snapping & Route Tracing",
            "tool": "get_usgs_comid/trace_network",
            "message": str(e)
        })
        state.execution_log.append({
            "stage": "Stage 2 — Hydrologic Snapping & Route Tracing",
            "component": "get_usgs_comid & trace_network",
            "status": "FAILED",
            "error": str(e)
        })
        log_diagnostic_event("Stage 2 — Hydrology", "hydrology_node", "FAILED", {"error": str(e)}, run_id=state.run_id)

    return state
