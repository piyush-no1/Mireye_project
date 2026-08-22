import json
import os
from datetime import datetime, timezone
from app.agent.state import AssessmentState
from app.config import settings
from app.services.job_store import job_store
from app.core.logging import logger, log_diagnostic_event

async def persist_node(state: AssessmentState) -> AssessmentState:
    """Stage 5: Persistence Node — Writes backend/data/outputs/{run_id}.json."""
    if state.status not in ("needs_clarification", "failed"):
        state.status = "completed"

    output_dir = settings.output_dir
    os.makedirs(output_dir, exist_ok=True)
    file_path = os.path.join(output_dir, f"{state.run_id}.json")

    # Clean up internal metadata keys if present
    hydrology_data = None
    if state.hydrology:
        hydrology_copy = dict(state.hydrology)
        hydrology_copy.pop("_bank_points", None)
        hydrology_data = hydrology_copy

    report_payload = {
        "run_id": state.run_id,
        "status": state.status,
        "query": state.query,
        "resolved_location": state.resolved_location,
        "hydrology": hydrology_data,
        "water_quality_samples": state.water_quality_samples,
        "attains_status": state.attains_status,
        "attains_summary": getattr(state, "attains_summary", None),
        "polluters": state.polluters,
        "land_risk_points": state.land_risk_points,
        "telemetry": state.telemetry,
        "risk_summary": state.risk_summary,
        "errors": state.errors,
        "execution_log": state.execution_log,
        "generated_at": datetime.now(timezone.utc).isoformat()
    }

    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(report_payload, f, indent=2)
        logger.info(f"Persisted assessment report for run '{state.run_id}' to {file_path}")
        log_diagnostic_event("Stage 5 — Persistence", "persist_node", "SUCCESS", {"file_path": file_path}, run_id=state.run_id)
    except Exception as e:
        logger.error(f"Failed to persist report file {file_path}: {e}")
        state.errors.append({
            "stage": "Stage 5 — Persistence",
            "tool": "persist_node",
            "message": str(e)
        })
        log_diagnostic_event("Stage 5 — Persistence", "persist_node", "FAILED", {"file_path": file_path, "error": str(e)}, run_id=state.run_id)

    job_store.update_status(
        run_id=state.run_id,
        status=state.status,
        error=state.error_message
    )

    return state
