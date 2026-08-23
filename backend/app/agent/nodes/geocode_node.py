from app.agent.state import AssessmentState
from app.tools.mireye_geocode_tool import geocode_location
from app.core.exceptions import GeocodeNotFoundException
from app.core.logging import logger, log_diagnostic_event

async def geocode_node(state: AssessmentState) -> AssessmentState:
    """Stage 1: Intent Parsing & Geocoding Node."""
    if state.status == "failed":
        return state

    # 1. Segment Mode (Point A ➔ Point B)
    if state.is_segment_mode and state.start_lat is not None and state.end_lat is not None:
        state.start_location = {
            "matched_name": state.start_name or f"Point A ({state.start_lat:.4f}, {state.start_lng:.4f})",
            "lat": state.start_lat,
            "lng": state.start_lng
        }
        state.end_location = {
            "matched_name": state.end_name or f"Point B ({state.end_lat:.4f}, {state.end_lng:.4f})",
            "lat": state.end_lat,
            "lng": state.end_lng
        }
        # Set primary resolved location to midpoint
        mid_lat = (state.start_lat + state.end_lat) / 2.0
        mid_lng = (state.start_lng + state.end_lng) / 2.0
        corridor_title = state.query or f"River Segment: {state.start_location['matched_name']} ➔ {state.end_location['matched_name']}"
        state.resolved_location = {
            "matched_name": corridor_title,
            "lat": mid_lat,
            "lng": mid_lng
        }
        state.execution_log.append({
            "stage": "Stage 1 — Intent Parsing & Geocoding",
            "component": "geocode_location",
            "status": "SUCCESS (Segment Mode Coordinates)",
            "start_location": state.start_location,
            "end_location": state.end_location,
            "resolved_location": state.resolved_location
        })
        log_diagnostic_event("Stage 1 — Geocoding", "geocode_location", "SUCCESS", {"mode": "segment", "start": state.start_location, "end": state.end_location}, run_id=state.run_id)
        return state

    # 2. Single Point Mode with direct coordinates
    if state.input_lat is not None and state.input_lng is not None:
        state.resolved_location = {
            "matched_name": state.query if state.query else "Custom Map Selection",
            "lat": state.input_lat,
            "lng": state.input_lng
        }
        state.execution_log.append({
            "stage": "Stage 1 — Intent Parsing & Geocoding",
            "component": "geocode_location",
            "status": "SUCCESS (Direct Coordinate Input)",
            "resolved_location": state.resolved_location
        })
        log_diagnostic_event("Stage 1 — Geocoding", "geocode_location", "SUCCESS", state.resolved_location, run_id=state.run_id)
        return state

    try:
        res = await geocode_location.ainvoke({"query": state.query})
        if not res or not res.get("lat") or not res.get("lng"):
            state.status = "needs_clarification"
            state.error_message = f"Location '{state.query}' could not be unambiguously resolved."
            state.execution_log.append({
                "stage": "Stage 1 — Intent Parsing & Geocoding",
                "component": "geocode_location",
                "status": "NEEDS_CLARIFICATION",
                "error": state.error_message
            })
            log_diagnostic_event("Stage 1 — Geocoding", "geocode_location", "WARNING", {"query": state.query, "reason": "Ambiguous location"}, run_id=state.run_id)
            return state

        state.resolved_location = {
            "matched_name": res.get("matched_name", state.query),
            "lat": float(res["lat"]),
            "lng": float(res["lng"])
        }
        state.execution_log.append({
            "stage": "Stage 1 — Intent Parsing & Geocoding",
            "component": "geocode_location",
            "status": "SUCCESS",
            "resolved_location": state.resolved_location
        })
        log_diagnostic_event("Stage 1 — Geocoding", "geocode_location", "SUCCESS", state.resolved_location, run_id=state.run_id)
    except Exception as e:
        logger.error(f"Geocoding node failed for query '{state.query}': {e}")
        state.status = "needs_clarification"
        state.error_message = f"Geocoding failed for query '{state.query}'."
        err_dict = {
            "stage": "Stage 1 — Intent Parsing & Geocoding",
            "tool": "geocode_location",
            "message": str(e)
        }
        state.errors.append(err_dict)
        state.execution_log.append({
            "stage": "Stage 1 — Intent Parsing & Geocoding",
            "component": "geocode_location",
            "status": "FAILED",
            "error": str(e)
        })
        log_diagnostic_event("Stage 1 — Geocoding", "geocode_location", "FAILED", {"query": state.query, "error": str(e)}, run_id=state.run_id)

    return state
