from app.agent.state import AssessmentState
from app.services.source_attribution import run_source_attribution
from app.core.logging import logger

async def source_attribution_node(state: AssessmentState) -> AssessmentState:
    """Stage 6: Source Attribution Node"""
    if state.status in ("failed", "needs_clarification"):
        return state
        
    # We only run source attribution if there are actual impairments or if attains_status exists
    if not state.attains_status:
        state.execution_log.append({
            "stage": "Stage 6 — Source Attribution",
            "component": "Source Reasoning Agent",
            "status": "SKIPPED",
            "reason": "No ATTAINS status available"
        })
        return state

    # Pass the relevant stripped state to the agent
    llm_attains_status = []
    for au in state.attains_status:
        au_copy = dict(au)
        au_copy.pop("geometry", None)
        llm_attains_status.append(au_copy)

    try:
        attribution_res, investigation_log = await run_source_attribution(
            query=state.query,
            attains_status=llm_attains_status,
            polluters=state.polluters,
            water_samples=state.water_quality_samples,
            land_risk_points=state.land_risk_points,
            telemetry=state.telemetry,
            run_id=state.run_id
        )
        
        state.source_attribution = attribution_res
        state.source_investigation_log = investigation_log
        
        state.execution_log.append({
            "stage": "Stage 6 — Source Attribution",
            "component": "Source Reasoning Agent",
            "status": "SUCCESS"
        })
        
    except Exception as e:
        logger.error(f"Source Attribution node failed: {e}")
        state.errors.append({
            "stage": "Stage 6 — Source Attribution",
            "tool": "source_attribution_node",
            "message": str(e)
        })
        state.execution_log.append({
            "stage": "Stage 6 — Source Attribution",
            "component": "Source Reasoning Agent",
            "status": "FAILED",
            "error": str(e)
        })

    return state
