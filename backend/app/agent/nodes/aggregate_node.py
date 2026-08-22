from app.agent.state import AssessmentState
from app.services.scoring import reason_and_score_with_openai
from app.core.logging import logger, log_diagnostic_event

async def aggregate_node(state: AssessmentState) -> AssessmentState:
    """Stage 5: Aggregation & OpenAI Reasoning Agent Node."""
    if state.status in ("failed", "needs_clarification"):
        return state

    try:
        score_res = await reason_and_score_with_openai(
            query=state.query,
            attains_status=state.attains_status,
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
            "overall_score": 0.0,
            "label": "Unknown",
            "notes": f"Scoring error: {e}"
        }

    return state
