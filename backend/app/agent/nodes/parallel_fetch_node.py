import asyncio
from app.agent.state import AssessmentState
from app.tools.epa_wqp_tool import get_epa_water_quality
from app.tools.epa_attains_tool import get_epa_attains_status
from app.tools.epa_echo_tool import get_epa_echo_polluters
from app.tools.mireye_land_risk_tool import get_mireye_land_risk
from app.tools.usgs_nwis_tool import get_usgs_nwis_telemetry
from app.core.logging import logger, log_diagnostic_event

async def fetch_wqp(bbox: list, state: AssessmentState):
    try:
        res = await get_epa_water_quality.ainvoke({"bbox": bbox})
        state.water_quality_samples = res if isinstance(res, list) else []
        state.execution_log.append({
            "stage": "Stage 4 — Parallel Tool Dispatch",
            "component": "get_epa_water_quality",
            "status": "SUCCESS",
            "count": len(state.water_quality_samples)
        })
        log_diagnostic_event("Stage 4 — Tool Dispatch", "get_epa_water_quality", "SUCCESS", {"count": len(state.water_quality_samples)}, run_id=state.run_id)
    except Exception as e:
        logger.warning(f"Stage 4 tool 'get_epa_water_quality' failed: {e}")
        state.errors.append({
            "stage": "Stage 4 — Parallel Tool Dispatch",
            "tool": "get_epa_water_quality",
            "message": str(e)
        })
        state.execution_log.append({
            "stage": "Stage 4 — Parallel Tool Dispatch",
            "component": "get_epa_water_quality",
            "status": "FAILED",
            "error": str(e)
        })
        log_diagnostic_event("Stage 4 — Tool Dispatch", "get_epa_water_quality", "FAILED", {"error": str(e)}, run_id=state.run_id)

async def fetch_attains(bbox: list, state: AssessmentState):
    try:
        res = await get_epa_attains_status.ainvoke({"bbox": bbox})
        state.attains_status = res if isinstance(res, list) else []
        state.execution_log.append({
            "stage": "Stage 4 — Parallel Tool Dispatch",
            "component": "get_epa_attains_status",
            "status": "SUCCESS",
            "count": len(state.attains_status)
        })
        log_diagnostic_event("Stage 4 — Tool Dispatch", "get_epa_attains_status", "SUCCESS", {"count": len(state.attains_status)}, run_id=state.run_id)
    except Exception as e:
        logger.warning(f"Stage 4 tool 'get_epa_attains_status' failed: {e}")
        state.errors.append({
            "stage": "Stage 4 — Parallel Tool Dispatch",
            "tool": "get_epa_attains_status",
            "message": str(e)
        })
        state.execution_log.append({
            "stage": "Stage 4 — Parallel Tool Dispatch",
            "component": "get_epa_attains_status",
            "status": "FAILED",
            "error": str(e)
        })
        log_diagnostic_event("Stage 4 — Tool Dispatch", "get_epa_attains_status", "FAILED", {"error": str(e)}, run_id=state.run_id)

async def fetch_echo(bbox: list, state: AssessmentState):
    try:
        res = await get_epa_echo_polluters.ainvoke({"bbox": bbox})
        state.polluters = res if isinstance(res, list) else []
        state.execution_log.append({
            "stage": "Stage 4 — Parallel Tool Dispatch",
            "component": "get_epa_echo_polluters",
            "status": "SUCCESS",
            "count": len(state.polluters)
        })
        log_diagnostic_event("Stage 4 — Tool Dispatch", "get_epa_echo_polluters", "SUCCESS", {"count": len(state.polluters)}, run_id=state.run_id)
    except Exception as e:
        logger.warning(f"Stage 4 tool 'get_epa_echo_polluters' failed: {e}")
        state.errors.append({
            "stage": "Stage 4 — Parallel Tool Dispatch",
            "tool": "get_epa_echo_polluters",
            "message": str(e)
        })
        state.execution_log.append({
            "stage": "Stage 4 — Parallel Tool Dispatch",
            "component": "get_epa_echo_polluters",
            "status": "FAILED",
            "error": str(e)
        })
        log_diagnostic_event("Stage 4 — Tool Dispatch", "get_epa_echo_polluters", "FAILED", {"error": str(e)}, run_id=state.run_id)

async def fetch_land_risk(bank_points: list, state: AssessmentState):
    try:
        res = await get_mireye_land_risk.ainvoke({"points": bank_points})
        state.land_risk_points = res if isinstance(res, list) else []
        state.execution_log.append({
            "stage": "Stage 4 — Parallel Tool Dispatch",
            "component": "get_mireye_land_risk",
            "status": "SUCCESS",
            "count": len(state.land_risk_points)
        })
        log_diagnostic_event("Stage 4 — Tool Dispatch", "get_mireye_land_risk", "SUCCESS", {"count": len(state.land_risk_points)}, run_id=state.run_id)
    except Exception as e:
        logger.warning(f"Stage 4 tool 'get_mireye_land_risk' failed: {e}")
        state.errors.append({
            "stage": "Stage 4 — Parallel Tool Dispatch",
            "tool": "get_mireye_land_risk",
            "message": str(e)
        })
        state.execution_log.append({
            "stage": "Stage 4 — Parallel Tool Dispatch",
            "component": "get_mireye_land_risk",
            "status": "FAILED",
            "error": str(e)
        })
        log_diagnostic_event("Stage 4 — Tool Dispatch", "get_mireye_land_risk", "FAILED", {"error": str(e)}, run_id=state.run_id)

async def fetch_nwis(bbox: list, state: AssessmentState):
    try:
        res = await get_usgs_nwis_telemetry.ainvoke({"bbox": bbox})
        state.telemetry = res if isinstance(res, list) else []
        state.execution_log.append({
            "stage": "Stage 4 — Parallel Tool Dispatch",
            "component": "get_usgs_nwis_telemetry",
            "status": "SUCCESS",
            "count": len(state.telemetry)
        })
        log_diagnostic_event("Stage 4 — Tool Dispatch", "get_usgs_nwis_telemetry", "SUCCESS", {"count": len(state.telemetry)}, run_id=state.run_id)
    except Exception as e:
        logger.warning(f"Stage 4 tool 'get_usgs_nwis_telemetry' failed: {e}")
        state.errors.append({
            "stage": "Stage 4 — Parallel Tool Dispatch",
            "tool": "get_usgs_nwis_telemetry",
            "message": str(e)
        })
        state.execution_log.append({
            "stage": "Stage 4 — Parallel Tool Dispatch",
            "component": "get_usgs_nwis_telemetry",
            "status": "FAILED",
            "error": str(e)
        })
        log_diagnostic_event("Stage 4 — Tool Dispatch", "get_usgs_nwis_telemetry", "FAILED", {"error": str(e)}, run_id=state.run_id)

async def parallel_fetch_node(state: AssessmentState) -> AssessmentState:
    """Stage 4: Parallel Tool Dispatch Node."""
    if state.status in ("failed", "needs_clarification"):
        return state

    if not state.hydrology or "bbox" not in state.hydrology:
        state.status = "failed"
        state.error_message = "Cannot run parallel fetch node without valid bounding box."
        return state

    bbox = state.hydrology["bbox"]
    bank_points = state.hydrology.get("_bank_points", [])

    # Run all 5 tools concurrently without stopping on individual failures
    await asyncio.gather(
        fetch_wqp(bbox, state),
        fetch_attains(bbox, state),
        fetch_echo(bbox, state),
        fetch_land_risk(bank_points, state),
        fetch_nwis(bbox, state),
        return_exceptions=True
    )

    return state
