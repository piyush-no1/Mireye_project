import json
import os
from datetime import datetime, timezone
from app.agent.state import AssessmentState
from app.config import settings
from app.services.job_store import job_store
from app.core.logging import logger, log_diagnostic_event

def _save_state(state: AssessmentState, stage_name: str) -> None:
    output_dir = settings.output_dir
    os.makedirs(output_dir, exist_ok=True)
    file_path = os.path.join(output_dir, f"{state.run_id}.json")

    hydrology_data = None
    if state.hydrology:
        hydrology_copy = dict(state.hydrology)
        hydrology_copy.pop("_bank_points", None)
        hydrology_data = hydrology_copy

    report_payload = {
        "run_id": state.run_id,
        "status": state.status,
        "query": state.query,
        "segment_mode": getattr(state, "is_segment_mode", False),
        "start_point": getattr(state, "start_location", None),
        "end_point": getattr(state, "end_location", None),
        "resolved_location": state.resolved_location,
        "hydrology": hydrology_data,
        "water_quality_samples": state.water_quality_samples,
        "attains_status": state.attains_status,
        "attains_summary": getattr(state, "attains_summary", None),
        "polluters": state.polluters,
        "land_risk_points": state.land_risk_points,
        "telemetry": state.telemetry,
        "risk_summary": state.risk_summary,
        "industrial_analysis": getattr(state, "industrial_analysis", None),
        "agricultural_analysis": getattr(state, "agricultural_analysis", None),
        "master_synthesis": getattr(state, "master_synthesis", None),
        "source_attribution": getattr(state, "source_attribution", None),
        "source_investigation_log": getattr(state, "source_investigation_log", []),
        "errors": state.errors,
        "execution_log": state.execution_log,
        "generated_at": datetime.now(timezone.utc).isoformat()
    }

    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(report_payload, f, indent=2)
        logger.info(f"Persisted assessment report for run '{state.run_id}' to {file_path}")
        log_diagnostic_event(stage_name, "persist_node", "SUCCESS", {"file_path": file_path}, run_id=state.run_id)
    except Exception as e:
        logger.error(f"Failed to persist report file {file_path}: {e}")
        state.errors.append({
            "stage": stage_name,
            "tool": "persist_node",
            "message": str(e)
        })
        log_diagnostic_event(stage_name, "persist_node", "FAILED", {"file_path": file_path, "error": str(e)}, run_id=state.run_id)

    job_store.update_status(
        run_id=state.run_id,
        status=state.status,
        error=state.error_message
    )

async def persist_assessment_node(state: AssessmentState) -> AssessmentState:
    """Intermediate persistence node after Assessment is complete but before Source Attribution."""
    if state.status not in ("needs_clarification", "failed"):
        state.status = "assessment_completed"
    
    _save_state(state, "Stage 5.5 — Intermediate Persistence")
    return state

async def persist_node(state: AssessmentState) -> AssessmentState:
    """Final Persistence Node — Writes backend/data/outputs/{run_id}.json."""
    if state.status not in ("needs_clarification", "failed"):
        state.status = "completed"

    _save_state(state, "Stage 7 — Final Persistence")
    return state

