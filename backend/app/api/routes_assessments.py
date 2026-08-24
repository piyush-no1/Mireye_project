import uuid
import os
import json
from fastapi import APIRouter, BackgroundTasks, HTTPException, Depends, status
from app.schemas.requests import (
    CreateAssessmentRequest,
    CreateAssessmentResponse,
    AssessmentStatusResponse
)
from app.schemas.assessment import AssessmentResult
from app.services.job_store import job_store, JobStore
from app.api.deps import get_job_store
from app.agent.state import AssessmentState
from app.agent.graph import assessment_graph
from app.config import settings
from app.core.logging import logger

router = APIRouter(prefix="/assessments", tags=["Assessments"])

async def run_assessment_task(
    run_id: str,
    query: str,
    lat: float | None = None,
    lng: float | None = None,
    start_lat: float | None = None,
    start_lng: float | None = None,
    end_lat: float | None = None,
    end_lng: float | None = None,
    start_name: str | None = None,
    end_name: str | None = None
):
    is_segment = bool(start_lat is not None and start_lng is not None and end_lat is not None and end_lng is not None)
    logger.info(f"Starting background assessment task for run_id '{run_id}', query '{query}', segment_mode={is_segment}")
    initial_state = AssessmentState(
        run_id=run_id,
        query=query,
        input_lat=lat,
        input_lng=lng,
        is_segment_mode=is_segment,
        start_lat=start_lat,
        start_lng=start_lng,
        end_lat=end_lat,
        end_lng=end_lng,
        start_name=start_name,
        end_name=end_name,
        status="pending"
    )
    try:
        await assessment_graph.ainvoke(initial_state)
        logger.info(f"Completed assessment task for run_id '{run_id}'")
    except Exception as e:
        logger.error(f"Error executing assessment graph for run_id '{run_id}': {e}")
        job_store.update_status(run_id, "failed", str(e))

@router.post("", response_model=CreateAssessmentResponse, status_code=status.HTTP_202_ACCEPTED)
async def create_assessment(
    payload: CreateAssessmentRequest,
    background_tasks: BackgroundTasks,
    store: JobStore = Depends(get_job_store)
):
    query_str = (payload.query or "").strip()
    if not query_str:
        if payload.start_lat is not None and payload.end_lat is not None:
            query_str = f"River Corridor: ({payload.start_lat:.3f}, {payload.start_lng:.3f}) to ({payload.end_lat:.3f}, {payload.end_lng:.3f})"
        elif payload.lat is not None and payload.lng is not None:
            query_str = f"Map Selection: {payload.lat:.4f}, {payload.lng:.4f}"
        else:
            raise HTTPException(status_code=400, detail="Query or valid coordinates must be provided.")

    run_id = str(uuid.uuid4())
    store.create_job(run_id, query_str)
    
    background_tasks.add_task(
        run_assessment_task,
        run_id,
        query_str,
        payload.lat,
        payload.lng,
        payload.start_lat,
        payload.start_lng,
        payload.end_lat,
        payload.end_lng,
        payload.start_name,
        payload.end_name
    )
    
    return CreateAssessmentResponse(
        run_id=run_id,
        status="pending"
    )

@router.get("/{run_id}", response_model=AssessmentStatusResponse)
async def get_assessment_status(
    run_id: str,
    store: JobStore = Depends(get_job_store)
):
    job = store.get_job(run_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Assessment run_id '{run_id}' not found.")
    
    return AssessmentStatusResponse(
        run_id=job["run_id"],
        status=job["status"],
        error=job.get("error")
    )

@router.get("/{run_id}/result", response_model=AssessmentResult)
async def get_assessment_result(
    run_id: str,
    store: JobStore = Depends(get_job_store)
):
    job = store.get_job(run_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Assessment run_id '{run_id}' not found.")
    
    if job["status"] not in ("assessment_completed", "completed"):
        raise HTTPException(status_code=400, detail=f"Assessment '{run_id}' is still processing (status: {job['status']}). Poll status endpoint.")
    
    file_path = os.path.join(settings.output_dir, f"{run_id}.json")
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"Result file for run_id '{run_id}' not found on disk.")
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return AssessmentResult(**data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read result file: {e}")
